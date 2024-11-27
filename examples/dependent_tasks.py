import asyncio
from async_abstract import DependentTaskRunner


runner = DependentTaskRunner()


@runner.task(name="A")
async def task_a():
    print("Task A executed")
    await asyncio.sleep(1)
    return "Result of A"


@runner.task(name="B", dependencies=["A"])
async def task_b():
    print("Task B executed")
    await asyncio.sleep(1)
    return "Result of B"


@runner.task(name="C", dependencies=["A"])
async def task_c():
    print("Task C executed")
    await asyncio.sleep(1)
    return "Result of C"


@runner.task(name="D", dependencies=["B", "C"])
async def task_d():
    print("Task D executed")
    await asyncio.sleep(1)
    return "Result of D"


async def main():
    async for result in runner.run():
        # Executes 1 by 1, and makes sures dependencies are ran first
        print(f"Task result: {result}")



asyncio.run(main())
