import asyncio
from async_abstract import DependentTaskRunner
import random
import asyncio

shared_runner = DependentTaskRunner()

@shared_runner.task(name="task1")
async def task1():
    print("Running task1")
    return str(random.randint(10000, 999999))

@shared_runner.task(name="task2", dependencies=["task1"])
async def task2(result1):
    print("Running task2")
    return f"result2 depends on {result1}"

@shared_runner.task(name="task3", dependencies=["task1", "task2"])
async def task3(result1, result2):
    print("Running task3")
    return f"result3 depends on {result1} and {result2}"

async def main():
    async for result in shared_runner.run():
        print(len(shared_runner.tasks))
        print(f"Task completed with result: {result}")

asyncio.run(main())
