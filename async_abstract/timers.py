from itertools import cycle
import asyncio
import time
from typing import List, Optional, Dict


class Timer:
    """
    Represents a single timer for a specific resource or a global rate limit.
    """

    def __init__(self, duration: float) -> None:
        """
        Initialize the timer.

        Args:
            duration (float): The duration (in seconds) for which the timer is active.
        """
        self.expiry: float = time.monotonic() + duration

    def is_expired(self) -> bool:
        """
        Check if the timer has expired.

        Returns:
            bool: True if the timer has expired, otherwise False.
        """
        return time.monotonic() >= self.expiry

    def time_remaining(self) -> float:
        """
        Get the time remaining until the timer expires.

        Returns:
            float: Time remaining in seconds. Returns 0 if the timer has expired.
        """
        return max(0, self.expiry - time.monotonic())


class ResourceTimer:
    """
    Manages timers for resource-specific and global rate limits.
    Intended for use with requests to respect ratelimits
    """

    def __init__(self) -> None:
        """
        Initialize the ResourceTimer with separate storage for global and resource-specific timers.
        """
        self.global_timer: Optional[Timer] = None
        self.resource_timers: Dict[str, Timer] = {}
        self.lock = asyncio.Lock()

    async def set_global_timer(self, duration: float) -> None:
        """
        Set a global rate limit timer.

        Args:
            duration (float): The duration (in seconds) for the global timer.
        """
        async with self.lock:
            self.global_timer = Timer(duration)

    async def set_resource_timer(self, resource: str, duration: float) -> None:
        """
        Set a timer for a specific resource.

        Args:
            resource (str): The resource identifier (e.g., endpoint name).
            duration (float): The duration (in seconds) for the resource timer.
        """
        async with self.lock:
            self.resource_timers[resource] = Timer(duration)

    async def check_timer(self, resource: str) -> None:
        """
        Check if a coroutine can proceed for the given resource.

        If either the global timer or the resource-specific timer is active (not expired),
        this will delay the coroutine execution until the timer(s) expire.

        Args:
            resource (str): The resource identifier to check.

        Raises:
            RuntimeError: If the resource is being ratelimited or globally ratelimited.
        """
        while True:
            async with self.lock:
                global_expired = self.global_timer is None or self.global_timer.is_expired()
                resource_expired = (
                    resource not in self.resource_timers or self.resource_timers[resource].is_expired()
                )

                # If both timers are expired, allow execution
                if global_expired and resource_expired:
                    break

                # Determine the earliest expiry time
                wait_time = float("inf")
                if self.global_timer and not self.global_timer.is_expired():
                    wait_time = min(wait_time, self.global_timer.time_remaining())
                if resource in self.resource_timers and not self.resource_timers[resource].is_expired():
                    wait_time = min(wait_time, self.resource_timers[resource].time_remaining())

            # Wait for the shortest required time before rechecking
            await asyncio.sleep(wait_time)

    async def reset_resource_timer(self, resource: str) -> None:
        """
        Reset the timer for a specific resource.

        Args:
            resource (str): The resource identifier to reset.
        """
        async with self.lock:
            if resource in self.resource_timers:
                del self.resource_timers[resource]

    async def reset_global_timer(self) -> None:
        """
        Reset the global timer.
        """
        async with self.lock:
            self.global_timer = None


class ProxyResourceTimer:
    """
    Manages timers for resource-specific and global rate limits.
    Intended for use with requests to respect ratelimits
    Used with proxies
    """

    def __init__(self, proxies: List[str] = []) -> None:
        """
        Initialize the ResourceTimer with separate storage for global and resource-specific timers.
        """
        self.global_timer: Optional[Timer] = None
        self.resource_timers: Dict[str, Timer] = {}
        self.proxies = cycle(proxies)
        self.current_proxy = next(self.proxies)
        self.lock = asyncio.Lock()

    @property
    def proxy(self) -> str:
        return self.current_proxy


    async def set_global_timer(self, duration: float) -> None:
        """
        Set a global rate limit timer.

        Args:
            duration (float): The duration (in seconds) for the global timer.
        """
        async with self.lock:
            self.global_timer = Timer(duration)

    async def set_resource_timer(self, resource: str, duration: float) -> None:
        """
        Set a timer for a specific resource.

        Args:
            resource (str): The resource identifier (e.g., endpoint name).
            duration (float): The duration (in seconds) for the resource timer.
        """
        async with self.lock:
            self.resource_timers[resource] = Timer(duration)

    async def check_timer(self, resource: str) -> None:
        """
        Check if a coroutine can proceed for the given resource.

        If either the global timer or the resource-specific timer is active (not expired),
        this will delay the coroutine execution until the timer(s) expire.

        Args:
            resource (str): The resource identifier to check.

        Raises:
            RuntimeError: If the resource is being ratelimited or globally ratelimited.
        """
        while True:
            async with self.lock:
                global_expired = self.global_timer is None or self.global_timer.is_expired()
                resource_expired = (
                    resource not in self.resource_timers or self.resource_timers[resource].is_expired()
                )

                if global_expired and resource_expired:
                    break

                wait_time = float("inf")
                if self.global_timer and not self.global_timer.is_expired():
                    wait_time = min(wait_time, self.global_timer.time_remaining())
                if resource in self.resource_timers and not self.resource_timers[resource].is_expired():
                    self.current_proxy = next(self.proxies)
                    wait_time = min(wait_time, self.resource_timers[resource].time_remaining())

            await asyncio.sleep(wait_time)

    async def reset_resource_timer(self, resource: str) -> None:
        """
        Reset the timer for a specific resource.

        Args:
            resource (str): The resource identifier to reset.
        """
        async with self.lock:
            if resource in self.resource_timers:
                del self.resource_timers[resource]

    async def reset_global_timer(self) -> None:
        """
        Reset the global timer.
        """
        async with self.lock:
            self.global_timer = None

