"""
Kommandant API Client
=====================
HTTP and WebSocket client for communicating with Cirkelline backend.
"""

import time
import logging
from typing import Optional, Dict, Any
import httpx

from cli.config import load_config
from cli.auth import get_auth_manager

logger = logging.getLogger(__name__)


class KommandantClient:
    """
    Client for Kommandant Terminal API.

    Handles:
    - HTTP requests to REST API
    - WebSocket connections for real-time communication
    - Authentication header management
    - Error handling and retries
    """

    def __init__(self):
        self.config = load_config()
        self.auth = get_auth_manager()

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers including auth."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Cirkelline-CLI/1.0",
        }
        headers.update(self.auth.get_auth_headers())
        return headers

    async def _request(
        self,
        method: str,
        endpoint: str,
        json: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to API."""
        url = f"{self.config.api_base_url}{endpoint}"

        try:
            async with httpx.AsyncClient(timeout=self.config.request_timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    json=json,
                    params=params,
                    headers=self._get_headers(),
                )

                if response.status_code == 401:
                    # Try refresh token
                    if await self.auth.refresh():
                        response = await client.request(
                            method=method,
                            url=url,
                            json=json,
                            params=params,
                            headers=self._get_headers(),
                        )

                if response.status_code >= 400:
                    return {
                        "success": False,
                        "error": response.json().get("detail", f"HTTP {response.status_code}"),
                        "status_code": response.status_code,
                    }

                return {
                    "success": True,
                    **response.json(),
                }

        except httpx.TimeoutException:
            return {"success": False, "error": "Request timed out"}
        except httpx.ConnectError:
            return {"success": False, "error": "Cannot connect to server"}
        except Exception as e:
            logger.error(f"Request error: {e}")
            return {"success": False, "error": str(e)}

    async def ping(self) -> Dict[str, Any]:
        """Test connection to Kommandanten."""
        start_time = time.time()

        result = await self._request("GET", "/health")

        if result.get("success"):
            latency = int((time.time() - start_time) * 1000)
            result["latency_ms"] = latency

        return result

    async def get_health(self) -> Dict[str, Any]:
        """Get system health status."""
        result = await self._request("GET", "/health")

        if result.get("success"):
            return {
                "api_status": "healthy",
                "api_version": result.get("version", "unknown"),
                **result,
            }
        else:
            return {
                "api_status": "offline",
                "error": result.get("error", "Unknown error"),
            }

    async def ask(
        self,
        question: str,
        context: Optional[Dict] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Ask Kommandanten a question.

        Args:
            question: The question text
            context: Optional Git/terminal context
            session_id: Optional session ID for conversation continuity

        Returns:
            Dict with 'success' and 'answer' or 'error'
        """
        payload = {
            "message": question,
            "context": context or {},
        }

        if session_id:
            payload["session_id"] = session_id

        # Use terminal-specific endpoint
        result = await self._request("POST", "/api/terminal/ask", json=payload)

        return result

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return await self._request("GET", "/api/terminal/status")

    async def get_user_features(self) -> Dict[str, Any]:
        """Get current user's available features based on tier."""
        return await self._request("GET", "/api/auth/features")

    async def send_feedback(
        self,
        message_id: str,
        rating: int,
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send feedback on a response."""
        return await self._request(
            "POST",
            "/api/feedback",
            json={
                "message_id": message_id,
                "rating": rating,
                "comment": comment,
            },
        )
