import asyncio
from functools import wraps
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set, AsyncGenerator

# TODO: Passing of args from dependency returns to base coro

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
    Manages and executes tasks with dependency resolution using decorators and topological sorting.

    Attributes:
        tasks (Dict[str, DependentTask]): A dictionary of tasks by their names.
        semaphore (asyncio.BoundedSemaphore): Semaphore to respect concurrency limits.
    """
    def __init__(self, semaphore: int = 100) -> None:
        """
        Initializes the task runner with an optional semaphore for concurrency control.

        Args:
            semaphore (int, optional): Maximum number of concurrent tasks (default is 100).
        """
        self.tasks: Dict[str, DependentTask] = {}
        self.semaphore = asyncio.BoundedSemaphore(semaphore)

    def task(self, name: str, dependencies: Optional[List[str]] = None) -> Callable:
        """
        Decorator to define a task with optional dependencies.

        Args:
            name (str): Unique name of the task.
            dependencies (List[str], optional): Names of tasks that this task depends on.

        Returns:
            Callable: The decorator function.
        """
        dependencies = dependencies or []

        def decorator(coro: Callable[..., Coroutine[Any, Any, Any]]):
            if not asyncio.iscoroutinefunction(coro):
                raise ValueError(f"Task '{name}' must be a coroutine function.")

            self.tasks[name] = DependentTask(name, coro, set(dependencies))

            @wraps(coro)
            async def wrapper(*args, **kwargs) -> Any:
                return await coro(*args, **kwargs)

            return wrapper

        return decorator

    async def run(self) -> AsyncGenerator[Any, None]:
        """
        Resolves dependencies and executes tasks in the correct order, yielding results as tasks are executed.

        Yields:
            Any: The result of the executed task.

        Raises:
            RuntimeError: If there is a cyclic dependency in the tasks.
        """
        executed = set()
        pending = set(self.tasks.keys())

        async def execute_task(task: DependentTask) -> None:
            async with self.semaphore:
                await asyncio.gather(*(execute_task(self.tasks[dep]) for dep in task.dependencies if dep not in executed))
                if task.name not in executed:
                    result = await task.coro()
                    executed.add(task.name)
                    return result

        while pending:
            for task_name in list(pending):
                task = self.tasks[task_name]
                if task.dependencies.issubset(executed):
                    result = await execute_task(task)
                    yield result
                    pending.remove(task_name)
                    break
            else:
                raise RuntimeError("Cyclic dependency detected in tasks!")
