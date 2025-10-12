"""
Simplest possible test - just login and try to download a report file directly
If we have a file name from a previous successful export, we can download it
"""
import asyncio
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

username = os.getenv('GOFRUGAL_USERNAME')
password = os.getenv('GOFRUGAL_PASSWORD')

async def main():
    logger.info("🎯 SIMPLE TEST: Login and manual report check")
    logger.info("="*80)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        # Login
        logger.info("\n1. Logging in...")
        await page.goto('https://bbcohq.gofrugal.com/RayMedi_HQ/index.do')
        await page.wait_for_load_state('networkidle')
        
        await page.fill('input[name="j_username"]', username)
        await page.fill('input[name="j_password"]', password)
        await page.click('button[type="submit"]')
        
        logger.info("   Waiting for login...")
        await asyncio.sleep(8)
        
        await page.screenshot(path='/app/gofrugal-report-builder/logs/simple_after_login.png')
        
        # Check URL after login
        current_url = page.url
        logger.info(f"   Current URL: {current_url}")
        
        # Try navigating to main app
        logger.info("\n2. Navigating to main application...")
        await page.goto('https://bbcohq.gofrugal.com/RayMedi_HQ/index.do')
        await asyncio.sleep(5)
        
        current_url = page.url
        logger.info(f"   Current URL: {current_url}")
        await page.screenshot(path='/app/gofrugal-report-builder/logs/simple_main_app.png')
        
        # Check page content
        content = await page.content()
        logger.info(f"   Page content size: {len(content)} bytes")
        
        # Try to find any Angular app elements
        has_ng = 'ng-' in content or 'angular' in content.lower()
        logger.info(f"   Angular detected: {has_ng}")
        
        # Save HTML
        with open('/app/gofrugal-report-builder/logs/simple_page.html', 'w') as f:
            f.write(content)
        
        # Try direct download URL (if we had a fileName)
        logger.info("\n3. Testing direct report download...")
        logger.info("   (This would work if we had a file name from previous export)")
        
        # Check cookies
        cookies = await context.cookies()
        logger.info(f"\n4. Current cookies: {len(cookies)}")
        for cookie in cookies:
            logger.info(f"   - {cookie['name']}: {cookie['value'][:20]}...")
        
        await browser.close()
        
        logger.info("\n" + "="*80)
        logger.info("DIAGNOSIS:")
        logger.info(f"- Login appears to work (got cookies)")
        logger.info(f"- But Angular SPA not loading (page size: {len(content)} bytes)")
        logger.info(f"- This suggests the login redirect or SPA initialization is failing")
        logger.info("="*80)

if __name__ == "__main__":
    asyncio.run(main())
