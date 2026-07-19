import asyncio
import logging
import aiohttp

logger = logging.getLogger(__name__)

FLARESOLVERR_URL = "http://localhost:8191"

async def ensure_flaresolverr():
    for attempt in range(30):
        try:
            async with aiohttp.ClientSession() as s:
                payload = {"cmd": "request.get", "url": "http://example.com", "maxTimeout": 5000}
                async with s.post(f"{FLARESOLVERR_URL}/v1", json=payload, timeout=aiohttp.ClientTimeout(total=5)) as r:
                    if r.status < 500:
                        return True
        except Exception:
            pass
        await asyncio.sleep(1)
    logger.error("FlareSolverr non risponde dopo 30s")
    return False
