import asyncio
# Same methods as Concurrency Guard, except there's progress bar
# Why? Because I thought it was cool
# Check docstrings for more info, lib is relatively simple
from async_abstract import ConcurrencyGuardGui


async def timer(i: float):
    await asyncio.sleep(i)

async def gather(guard: ConcurrencyGuardGui):
    coros = [timer(i/10) for i in range(100)]
    await guard.gather(coros)

async def process_tasks(guard: ConcurrencyGuardGui):
    coros = [timer(i/100) for i in range(100)]
    async for i in guard.process_tasks(coros):
        pass

async def chunk_gather(guard: ConcurrencyGuardGui):
    coros = [timer(i/10) for i in range(100)]
    async for i in guard.chunked_gather(coros, 10):
        pass


async def main():
    guard = ConcurrencyGuardGui(10)
    await gather(guard)
    await process_tasks(guard)
    await chunk_gather(guard)

asyncio.run(main())
