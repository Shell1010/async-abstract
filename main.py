from async_abstract import ConcurrencyGuardGui
import asyncio

async def timer(i: float):
    await asyncio.sleep(i)

async def gather(guard: ConcurrencyGuardGui):
    coros = [timer(i/10) for i in range(100)]
    await guard.gather(coros)

async def process_tasks(guard: ConcurrencyGuardGui):
    coros = [timer(i/100) for i in range(100)]
    async for i in guard.process_tasks(coros):
        pass

async def main():
    guard = ConcurrencyGuardGui(50)
    await process_tasks(guard) 

asyncio.run(main())
