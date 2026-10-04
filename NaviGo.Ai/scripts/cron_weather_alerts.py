import os
import sys
import asyncio
import httpx
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.app.config import settings
from backend.app.routers.internal_cron import run_weather_alerts_cron

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("navigo.cron_script")

async def main():
    logger.info("Executing scheduled weather alerts check...")
    try:
        # Directly invoke the logic for zero-network local reliability
        secret_header = f"Bearer {settings.cron_secret}"
        result = await run_weather_alerts_cron(authorization=secret_header)
        logger.info("Weather alerts check completed: %s destinations checked, %s alerts generated.",
                    result.get("checked_destinations_count"), result.get("alerts_generated_count"))
        print(result)
    except Exception as e:
        logger.error("Cron execution failed: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
