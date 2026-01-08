"""Quick BrowserUse test"""
import asyncio
from cirkelline.tools.browser_use_tool import BrowserUseTool, BROWSERUSE_AVAILABLE

async def test():
    if not BROWSERUSE_AVAILABLE:
        print('BrowserUse ikke tilgængelig')
        return

    print("Starter BrowserUse test...")
    tool = BrowserUseTool(headless=True)
    result = await tool.browse('Search Google for AI agents 2025', max_steps=3)
    print(result)
    tool.close()

if __name__ == "__main__":
    asyncio.run(test())
