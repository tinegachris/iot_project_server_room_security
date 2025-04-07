"""
raspberry_pi_client.py

This module provides a client for communicating with the Raspberry Pi.
It handles all API requests to the Raspberry Pi, including sensor data,
camera operations, and RFID operations.
"""

import logging
import aiohttp
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RaspberryPiClient:
    """Client for communicating with Raspberry Pi."""

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """Initialize the Raspberry Pi client."""
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.retry_count = 3
        self.retry_delay = 1

    async def __aenter__(self):
        """Create aiohttp session when entering context."""
        headers = {}
        if self.api_key:
            headers['X-API-Key'] = self.api_key
            logger.debug("RaspberryPiClient using API Key for session.")
        else:
             logger.debug("RaspberryPiClient session without API Key.")

        self.session = aiohttp.ClientSession(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=headers
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close aiohttp session when exiting context."""
        if self.session:
            await self.session.close()

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request with retry logic."""
        if not self.session:
            raise RuntimeError("Client session not initialized")

        for attempt in range(self.retry_count):
            try:
                url = f"{self.base_url}{endpoint}"
                logger.debug(f"Making request: {method.upper()} {url}")
                async with getattr(self.session, method)(endpoint, **kwargs) as response:
                    logger.debug(f"Response status for {method.upper()} {endpoint}: {response.status}")
                    response.raise_for_status()
                    content_type = response.headers.get('Content-Type', '')
                    if response.status == 204 or 'application/json' not in content_type:
                         logger.debug(f"Received non-JSON or empty response ({response.status}) for {endpoint}")
                         return {"status": "success", "response_code": response.status}
                    return await response.json()
            except aiohttp.ClientResponseError as e:
                 logger.error(f"HTTP error during {method.upper()} {endpoint}: {e.status} - {e.message}")
                 if attempt == self.retry_count - 1:
                     raise
                 await asyncio.sleep(self.retry_delay * (attempt + 1))
            except aiohttp.ClientError as e:
                logger.error(f"Client error during {method.upper()} {endpoint}: {e}")
                if attempt == self.retry_count - 1:
                    raise
                await asyncio.sleep(self.retry_delay * (attempt + 1))
            except asyncio.TimeoutError:
                 logger.error(f"Request timeout during {method.upper()} {endpoint}")
                 if attempt == self.retry_count - 1:
                     raise
                 await asyncio.sleep(self.retry_delay * (attempt + 1))

        raise RuntimeError(f"Failed to {method.upper()} {endpoint} after {self.retry_count} attempts")

    async def get_status(self) -> Dict[str, Any]:
        """Get Raspberry Pi status."""
        return await self._make_request("get", "/status")

    async def get_sensor_data(self, sensor_type: str) -> Dict[str, Any]:
        """Get data from a specific sensor."""
        return await self._make_request("get", f"/sensors/{sensor_type}")

    async def get_camera_status(self) -> Dict[str, Any]:
        """Get camera status and settings."""
        return await self._make_request("get", "/camera/status")

    async def get_rfid_status(self) -> Dict[str, Any]:
        """Get RFID reader status and last read card."""
        return await self._make_request("get", "/rfid/status")

    async def execute_command(self, command: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a command on the Raspberry Pi."""
        return await self._make_request(
            "post",
            "/control",
            json={"action": command, "parameters": params}
        )

    async def capture_image(self) -> Dict[str, Any]:
        """Capture an image using the camera."""
        return await self.execute_command("capture_image")

    async def record_video(self, duration: int = 30) -> Dict[str, Any]:
        """Record a video using the camera."""
        return await self.execute_command("record_video", {"duration": duration})

    async def test_sensors(self) -> Dict[str, Any]:
        """Test all sensors."""
        return await self.execute_command("test_sensors")

    async def restart_system(self) -> Dict[str, Any]:
        """Restart the Raspberry Pi system."""
        return await self.execute_command("restart_system")

    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics."""
        return await self._make_request("get", "/health")

    async def get_storage_status(self) -> Dict[str, Any]:
        """Get storage status and usage."""
        return await self._make_request("get", "/storage")

    async def get_network_status(self) -> Dict[str, Any]:
        """Get network status and connectivity."""
        return await self._make_request("get", "/network")

    async def update_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update Raspberry Pi configuration."""
        return await self._make_request(
            "post",
            "/config",
            json=config
        )

    async def get_logs(self, limit: int = 100) -> Dict[str, Any]:
        """Get system logs from Raspberry Pi."""
        return await self._make_request("get", f"/logs?limit={limit}")

    async def clear_logs(self) -> Dict[str, Any]:
        """Clear system logs on Raspberry Pi."""
        return await self.execute_command("clear_logs")

    async def get_firmware_version(self) -> Dict[str, Any]:
        """Get firmware version information."""
        return await self._make_request("get", "/firmware/version")

    async def check_for_updates(self) -> Dict[str, Any]:
        """Check for firmware updates."""
        return await self._make_request("get", "/firmware/check-updates")

    async def perform_update(self) -> Dict[str, Any]:
        """Perform firmware update."""
        return await self.execute_command("update_firmware")

    async def get_sensor_events(self, sensor_type: str, limit: int = 100) -> Dict[str, Any]:
        """Get events from a specific sensor."""
        return await self._make_request("get", f"/sensors/{sensor_type}/events?limit={limit}")

    async def get_sensor_stats(self, sensor_type: str) -> Dict[str, Any]:
        """Get statistics for a specific sensor."""
        return await self._make_request("get", f"/sensors/{sensor_type}/stats")