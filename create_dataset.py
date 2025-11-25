import aiohttp
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def create_dataset():
    cloud_url = os.getenv("COGNEE_CLOUD_API_URL")
    api_key = os.getenv("COGNEE_CLOUD_AUTH_TOKEN")
    
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
    url = f"{cloud_url}/api/v1/datasets"
    
    payload = {"name": "geargraph"}
    
    print(f"Creating dataset 'geargraph' at {url}...")

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            print(f"Status: {resp.status}")
            print(f"Response: {await resp.text()}")

if __name__ == "__main__":
    asyncio.run(create_dataset())
