from async_abstract import EventHandler
import asyncio

event_handler = EventHandler()

@event_handler.on("greet")
async def say_hello(name: str):
    print(f"Hello, {name}!")

@event_handler.on("greet")
async def say_goodbye(name: str):
    print(f"Goodbye, {name}!")

async def main():
    await event_handler.emit("greet", "Joe Biden")

asyncio.run(main())
