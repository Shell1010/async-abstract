import asyncio
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set, AsyncGenerator
from functools import wraps


class DependentTask:
    """
    Represents a single task with a name, a coroutine, and dependencies.

    Attributes:
        name (str): Unique name of the task.
        coro (Callable[..., Coroutine[Any, Any, Any]]): The coroutine function to execute.
        dependencies (Set[str]): Names of tasks that this task depends on.
    """
    def __init__(self, name: str, coro: Callable[..., Coroutine[Any, Any, Any]], dependencies: Optional[Set[str]] = None) -> None:
        self.name = name
        self.coro = coro
        self.dependencies = dependencies or set()


class DependentTaskRunner:
    """
    Manages and executes tasks with dependency resolution and result passing.

    Attributes:
        tasks (Dict[str, DependentTask]): A dictionary of tasks by their names.
        semaphore (asyncio.BoundedSemaphore): Semaphore to respect concurrency limits.
    """
    def __init__(self, max_concurrent_tasks: int = 100) -> None:
        self.tasks: Dict[str, DependentTask] = {}
        self.semaphore = asyncio.BoundedSemaphore(max_concurrent_tasks)
    
    def add_task(self, name: str, coro: Callable[..., Coroutine[Any, Any, Any]], dependencies: Optional[List[str]] = None) -> DependentTask:
        dependencies = dependencies or []
        dep_task = DependentTask(name, coro, set(dependencies))
        self.tasks[name] = dep_task
        return dep_task


    def task(self, name: str, dependencies: Optional[List[str]] = None) -> Callable:
        """
        Decorator to define a task with optional dependencies.

        Args:
            name (str): Unique name of the task.
            dependencies (List[str], optional): Names of tasks that this task depends on.

        Returns:
            Callable: The decorator function.
        """

        def decorator(coro: Callable[..., Coroutine[Any, Any, Any]]):
            if not asyncio.iscoroutinefunction(coro):
                raise ValueError(f"Task '{name}' must be a coroutine function.")

            self.add_task(name, coro, dependencies)

            @wraps(coro)
            async def wrapper(*args, **kwargs) -> Any:
                return await coro(*args, **kwargs)

            return wrapper

        return decorator

    async def run(self, *args: Any, **kwargs: Any) -> AsyncGenerator[Any, None]:
        """
        Resolves dependencies and executes tasks in the correct order, passing results to dependent tasks.

        Args:
            *args: Arguments passed to tasks without dependencies.
            **kwargs: Keyword arguments passed to tasks without dependencies.

        Yields:
            Any: The result of each executed task.

        Raises:
            RuntimeError: If there is a cyclic dependency in the tasks.
        """
        executed: Dict[str, Any] = {}  
        pending = set(self.tasks.keys())

        async def execute_task(task: DependentTask) -> Any:
            async with self.semaphore:
                dependency_results = [executed[dep] for dep in task.dependencies]
                result = await task.coro(*dependency_results, *args, **kwargs)
                return result

        while pending:
            for task_name in list(pending):
                task = self.tasks[task_name]

                if task.dependencies.issubset(executed.keys()):
                    result = await execute_task(task)
                    executed[task_name] = result  
                    yield result
                    pending.remove(task_name)
                    break
            else:
                raise RuntimeError("Cyclic dependency detected in tasks!")

    async def run_with_timeout(self, timeout: float, *args: Any, **kwargs: Any) -> AsyncGenerator[Any, None]:
        """
        Executes tasks with a timeout, passing dependency results as arguments.

        Args:
            timeout (float): Timeout in seconds for each task.
            *args: Arguments passed to tasks without dependencies.
            **kwargs: Keyword arguments passed to tasks without dependencies.

        Yields:
            Any: The result of each executed task.

        Raises:
            TimeoutError: If a task exceeds the timeout.
            RuntimeError: If there is a cyclic dependency in the tasks.
        """
        executed: Dict[str, Any] = {}
        pending = set(self.tasks.keys())

        async def execute_task(task: DependentTask) -> Any:
            async with self.semaphore:
                dependency_results = [executed[dep] for dep in task.dependencies]
                try:
                    result = await asyncio.wait_for(
                        task.coro(*dependency_results, *args, **kwargs),
                        timeout,
                    )
                    return result
                except asyncio.TimeoutError:
                    raise TimeoutError(f"Task '{task.name}' timed out.")

        while pending:
            for task_name in list(pending):
                task = self.tasks[task_name]
                if task.dependencies.issubset(executed.keys()):
                    result = await execute_task(task)
                    executed[task_name] = result
                    yield result
                    pending.remove(task_name)
                    break
            else:
                raise RuntimeError("Cyclic dependency detected in tasks!")
