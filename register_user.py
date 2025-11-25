import aiohttp
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def register_and_login():
    cloud_url = os.getenv("COGNEE_CLOUD_API_URL")
    # Ensure URL ends with /api/v1 if not already (though I patched code, here I use raw requests)
    # My .env has http://116.203.232.88:8000
    # So I need to append /api/v1
    
    base_url = f"{cloud_url}/api/v1"
    
    email = "gearcrew_test@example.com"
    password = "password123"
    
    async with aiohttp.ClientSession() as session:
        # 1. Register
        print(f"Registering {email}...")
        reg_url = f"{base_url}/auth/register"
        payload = {"email": email, "password": password}
        async with session.post(reg_url, json=payload) as resp:
            print(f"Register Status: {resp.status}")
            print(f"Register Response: {await resp.text()}")
            
        # 2. Login
        print(f"Logging in...")
        login_url = f"{base_url}/auth/login"
        # Login usually expects form data or json? Openapi said x-www-form-urlencoded
        data = {"username": email, "password": password}
        async with session.post(login_url, data=data) as resp:
            print(f"Login Status: {resp.status}")
            if resp.status == 200:
                token_data = await resp.json()
                print(f"Login Response: {token_data}")
                # Check if token is in response or cookie
                # Openapi said "Auth:Cookie.Login".
                # But maybe it returns a token too?
                # If it sets a cookie, I need to extract it.
                cookies = resp.cookies
                print(f"Cookies: {cookies}")
            else:
                print(f"Login Failed: {await resp.text()}")

if __name__ == "__main__":
    asyncio.run(register_and_login())
