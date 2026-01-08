"""
BrowserUse Tool for Cirkelline Research Team
=============================================
AI-powered browser automation for web research tasks.

Requires: pip install browser-use

Usage:
    from cirkelline.tools.browser_use_tool import BrowserUseTool, BROWSERUSE_AVAILABLE

    if BROWSERUSE_AVAILABLE:
        tool = BrowserUseTool()
        # Use with agent
"""

import os
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# Check if browser-use is available
BROWSERUSE_AVAILABLE = False
BrowserAgent = None
Controller = None

try:
    from browser_use import Agent as BrowserAgent
    from browser_use import Controller
    BROWSERUSE_AVAILABLE = True
    logger.info("browser-use available - web automation enabled")
except ImportError:
    logger.warning("browser-use not installed - run: pip install browser-use")


def _get_llm():
    """Get LLM for browser-use - uses Google Gemini via google-genai."""
    google_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not google_key:
        raise ValueError("GOOGLE_API_KEY not set")

    # Use google-genai directly (same as Cirkelline uses)
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=google_key)
    return client


class BrowserUseTool:
    """
    BrowserUse integration for AI-powered browser automation.

    Features:
    - Natural language web browsing
    - Form filling and data extraction
    - Multi-page workflows
    - Screenshot capture
    """

    def __init__(
        self,
        headless: bool = True,
    ):
        """
        Initialize BrowserUse tool.

        Args:
            headless: Run browser in headless mode (default: True)
        """
        if not BROWSERUSE_AVAILABLE:
            raise ImportError(
                "browser-use not installed. Run: pip install browser-use"
            )

        self.headless = headless
        self._controller: Optional[Controller] = None

        # Initialize LLM for browser control
        self._llm = _get_llm()

    async def browse(
        self,
        task: str,
        starting_url: Optional[str] = None,
        max_steps: int = 10,
    ) -> Dict[str, Any]:
        """
        Execute a browser automation task.

        Args:
            task: Natural language description of the task
            starting_url: Optional URL to start from
            max_steps: Maximum number of browser actions

        Returns:
            Dict with results, extracted data, and history
        """
        try:
            # Create browser agent
            agent = BrowserAgent(
                task=task,
                llm=self._llm,
                controller=self._controller,
            )

            # Configure starting URL if provided
            if starting_url:
                agent.initial_url = starting_url

            # Run the task
            result = await agent.run(max_steps=max_steps)

            return {
                "success": True,
                "result": result.final_result if hasattr(result, 'final_result') else str(result),
                "extracted_data": result.extracted_data if hasattr(result, 'extracted_data') else None,
                "history": result.history if hasattr(result, 'history') else [],
                "steps_taken": len(result.history) if hasattr(result, 'history') else 0,
            }

        except Exception as e:
            logger.error(f"BrowserUse error: {e}")
            return {
                "success": False,
                "error": str(e),
                "result": None,
            }

    async def extract_content(
        self,
        url: str,
        extraction_prompt: str,
    ) -> Dict[str, Any]:
        """
        Extract specific content from a webpage.

        Args:
            url: URL to extract from
            extraction_prompt: What to extract (natural language)

        Returns:
            Dict with extracted content
        """
        task = f"Go to {url} and extract: {extraction_prompt}"
        return await self.browse(task, starting_url=url, max_steps=5)

    async def fill_form(
        self,
        url: str,
        form_data: Dict[str, str],
        submit: bool = False,
    ) -> Dict[str, Any]:
        """
        Fill out a form on a webpage.

        Args:
            url: URL with the form
            form_data: Field names and values to fill
            submit: Whether to submit the form

        Returns:
            Dict with result
        """
        fields_str = ", ".join(f"{k}: {v}" for k, v in form_data.items())
        task = f"Go to {url}, fill the form with: {fields_str}"
        if submit:
            task += ", then submit the form"

        return await self.browse(task, starting_url=url, max_steps=10)

    async def search_and_extract(
        self,
        search_query: str,
        search_engine: str = "google",
        num_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search and extract results from search engine.

        Args:
            search_query: What to search for
            search_engine: google, bing, or duckduckgo
            num_results: Number of results to extract

        Returns:
            List of extracted search results
        """
        engine_urls = {
            "google": "https://www.google.com",
            "bing": "https://www.bing.com",
            "duckduckgo": "https://duckduckgo.com",
        }

        url = engine_urls.get(search_engine, "https://www.google.com")
        task = f"Search for '{search_query}' and extract the top {num_results} results with their titles, URLs, and descriptions"

        result = await self.browse(task, starting_url=url, max_steps=8)

        if result.get("success") and result.get("extracted_data"):
            return result["extracted_data"]
        return [result]

    def close(self):
        """Close the browser controller."""
        if self._controller:
            self._controller.close()
            self._controller = None


# Convenience function for quick usage
async def browser_search(query: str, max_steps: int = 5) -> Dict[str, Any]:
    """
    Quick browser search utility.

    Args:
        query: What to search for
        max_steps: Maximum browser actions

    Returns:
        Search results
    """
    if not BROWSERUSE_AVAILABLE:
        return {
            "success": False,
            "error": "browser-use not installed",
        }

    tool = BrowserUseTool()
    try:
        return await tool.browse(
            task=f"Search the web for: {query}",
            max_steps=max_steps,
        )
    finally:
        tool.close()
