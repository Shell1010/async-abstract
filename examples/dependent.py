import asyncio
from async_abstract import DependentTaskRunner
import random

runner = DependentTaskRunner(semaphore=50)

@runner.task(name="fetch_user_data")
async def fetch_user():
    print("Fetching user data...")
    await asyncio.sleep(1)
    return {"id": random.randint(100, 1000000000), "name": "Alice"}

@runner.task(name="fetch_account_data", dependencies=["fetch_user_data"])
async def fetch_account(user):
    print(f"Fetching account data for user {user['name']}...")
    await asyncio.sleep(1)
    return {"balance": 500}

@runner.task(name="generate_report", dependencies=["fetch_user_data", "fetch_account_data"])
async def generate_report(user, account_data):
    print("Generating report...")
    await asyncio.sleep(1)
    return {
        "user": user["name"],
        "balance": account_data["balance"]
    }

async def main():
    async for result in runner.run():
        print("Task result:", result)

asyncio.run(main())
