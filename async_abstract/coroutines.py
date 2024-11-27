from collections.abc import Generator
from typing import Any, AsyncGenerator, List, Iterable, Coroutine, Sequence
import asyncio


class ConcurrencyGuard:
    """
    A utility class for managing concurrency in asyncio programs using a bounded semaphore.

    This class provides abstractions to make asyncio easier to use when handling multiple coroutines.
    The semaphore ensures that no more than a specified number of tasks are executed concurrently.
    """

    def __init__(self, semaphore: int) -> None:
        """
        Initialize a ConcurrencyGuard instance.

        Args:
            semaphore (int): The maximum number of tasks allowed to run concurrently.
        """
        self.semaphore: asyncio.BoundedSemaphore = asyncio.BoundedSemaphore(semaphore)

    async def gather(self, coros: Sequence[Coroutine[Any, Any, Any]]) -> List[Any]:
        """
        Gathers results from multiple coroutines, respecting the concurrency limit.

        Runs all coroutines concurrently up to the semaphore limit and waits for all of them to complete.

        Args:
            coros (Sequence[Coroutine[Any, Any, Any]]): A sequence of coroutines to execute.

        Returns:
            List[Any]: A list of results from all coroutines.
        """
        async with self.semaphore:
            return await asyncio.gather(*coros)

    async def process_tasks(self, coros: Sequence[Coroutine[Any, Any, Any]]) -> AsyncGenerator[Any, None]:
        """
        Processes coroutines sequentially, yielding results one by one.

        Each coroutine is executed one at a time while respecting the semaphore limit. 
        Results are yielded as soon as they are available.

        Args:
            coros (Sequence[Coroutine[Any, Any, Any]]): A sequence of coroutines to execute.

        Yields:
            Any: The result of each coroutine as it completes.
        """
        for task in coros:
            async with self.semaphore:
                yield await task

    async def chunked_gather(self, coros: Sequence[Coroutine[Any, Any, Any]], chunks: int) -> AsyncGenerator[List[Any], None]:
        """
        Executes coroutines in chunks and gathers results for each chunk.

        Divides the coroutines into chunks of a specified size and executes each chunk concurrently 
        while respecting the semaphore limit. Results for each chunk are yielded sequentially.

        Args:
            coros (Sequence[Coroutine[Any, Any, Any]]): A sequence of coroutines to execute.
            chunks (int): The number of coroutines to process per chunk.

        Yields:
            List[Any]: A list of results for each chunk of coroutines.
        """
        for i in range(0, len(coros), chunks):
            async with self.semaphore:
                chunk = coros[i:i + chunks]
                yield await asyncio.gather(*chunk)

    async def cancel_pending_tasks(self, tasks: Iterable[asyncio.Task]) -> AsyncGenerator[bool, None]:
        """
        Cancels pending asyncio tasks and yields the result of the cancellation.

        Iterates over the given tasks, checks if they are still pending, and cancels them if necessary.
        Yields `True` for each successfully canceled task, or `False` if the task was already completed.

        Args:
            tasks (Iterable[asyncio.Task]): An iterable of asyncio tasks to cancel.

        Yields:
            bool: `True` if the task was successfully canceled, or `False` if it was already completed.
        """
        for task in tasks:
            if not task.done():
                yield task.cancel()

