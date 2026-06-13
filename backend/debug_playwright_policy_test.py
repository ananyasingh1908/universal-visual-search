import sys
import asyncio
from playwright.async_api import async_playwright

print('platform', sys.platform)
print('initial policy', type(asyncio.get_event_loop_policy()).__name__)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        pg = await b.new_page()
        await pg.goto('https://example.com')
        print('title', await pg.title())
        await b.close()

try:
    asyncio.run(main())
except Exception as e:
    print('default failed', type(e).__name__, e)

asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
print('after selector policy', type(asyncio.get_event_loop_policy()).__name__)

try:
    asyncio.run(main())
except Exception as e:
    print('selector failed', type(e).__name__, e)
