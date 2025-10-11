"""
Test login with correct field names
"""
import asyncio
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import os
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_login():
    username = os.getenv('GOFRUGAL_USERNAME')
    password = os.getenv('GOFRUGAL_PASSWORD')
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox']
    )
    
    context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
    page = await context.new_page()
    
    try:
        logger.info("Testing login with CORRECT field names (j_username, j_password)...")
        
        await page.goto("https://bbcohq.gofrugal.com/RayMedi_HQ/index.do", 
                       wait_until='networkidle', timeout=30000)
        
        # Use correct field names
        logger.info("Filling j_username and j_password...")
        await page.fill('input[name="j_username"]', username)
        await page.fill('input[name="j_password"]', password)
        
        logger.info("Submitting...")
        await page.click('button[type="submit"]')
        
        await asyncio.sleep(10)
        
        logger.info(f"URL after login: {page.url}")
        await page.screenshot(path='/app/gofrugal-report-builder/logs/correct_login_after.png', full_page=True)
        
        # Check for tabs
        tabs_found = []
        for tab_name in ['Home', 'MDM', 'BPM', 'Reports']:
            elements = await page.query_selector_all(f'text={tab_name}')
            if elements:
                tabs_found.append(tab_name)
        
        if tabs_found:
            logger.info(f"✓✓✓ SUCCESS! Found tabs: {tabs_found}")
        else:
            logger.info(f"✗ No tabs found")
            buttons = await page.query_selector_all('button')
            logger.info(f"Buttons: ")
            for btn in buttons[:5]:
                text = await btn.inner_text()
                logger.info(f"  - {text.strip()}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await browser.close()
        await playwright.stop()


if __name__ == "__main__":
    asyncio.run(test_login())
