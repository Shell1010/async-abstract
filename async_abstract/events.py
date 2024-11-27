import asyncio
import inspect
from dataclasses import dataclass
from typing import Any, Callable, Coroutine, Dict, List

@dataclass()
class Event:
    name: str
    coro: Callable[..., Coroutine[Any, Any, Any]]

    
    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Event):
            return self.name == other.name
        if isinstance(other, str):
            return self.name == other
        return NotImplemented


    def __hash__(self) -> int:
        return hash((self.name, self.coro))


class EventHandler:
    def __init__(self) -> None:
        self.events: Dict[str, List[Event]] = {}

    def add_event(self, name: str, listener: Callable[..., Coroutine[Any, Any, Any]]) -> Event:
        if name not in self.events:
            self.events[name] = []
        event = Event(name, listener)
        self.events[name].append(event)
        return event

    def on(self, event: str) -> Callable:
        def decorator(coro: Callable[..., Coroutine[Any, Any, Any]]):
            if not inspect.iscoroutinefunction(coro):
                raise ValueError("Not a Coroutine")
            self.add_event(event, coro)
            return coro

        return decorator

    async def emit(self, name: str, *args):
        if name in self.events:
            await asyncio.gather(*(
                asyncio.create_task(event.coro(*args)) 
                for event in self.events[name]
            )) 
