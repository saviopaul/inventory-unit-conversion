"""
Test the complete login flow with redirects
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
    """Test login and track all redirects"""
    
    username = os.getenv('GOFRUGAL_USERNAME')
    password = os.getenv('GOFRUGAL_PASSWORD')
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox']
    )
    
    context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
    page = await context.new_page()
    
    # Track all navigations
    page.on('framenavigated', lambda frame: logger.info(f"Navigation: {frame.url}"))
    
    try:
        logger.info("="*80)
        logger.info("TESTING LOGIN FLOW")
        logger.info("="*80)
        
        # Go to login page
        login_url = "https://bbcohq.gofrugal.com/RayMedi_HQ/index.do"
        logger.info(f"\n1. Going to: {login_url}")
        await page.goto(login_url, wait_until='networkidle', timeout=30000)
        
        logger.info(f"   Current URL: {page.url}")
        await page.screenshot(path='/app/gofrugal-report-builder/logs/test_login_page.png')
        
        # Fill credentials
        logger.info(f"\n2. Filling credentials...")
        await page.fill('input[type="text"]', username)
        await page.fill('input[type="password"]', password)
        
        # Submit and wait for navigation
        logger.info(f"\n3. Submitting login form...")
        await page.click('button[type="submit"]')
        
        # Wait and track redirects
        logger.info(f"\n4. Waiting for redirects...")
        await asyncio.sleep(10)
        
        logger.info(f"   Final URL after login: {page.url}")
        
        # Check cookies
        cookies = await context.cookies()
        logger.info(f"\n5. Cookies set: {len(cookies)}")
        for cookie in cookies:
            logger.info(f"   {cookie['name']}: {cookie['value'][:20]}...")
        
        # Take screenshot
        await page.screenshot(path='/app/gofrugal-report-builder/logs/test_after_login.png', full_page=True)
        
        # Check what's on the page
        logger.info(f"\n6. Checking page content...")
        title = await page.title()
        logger.info(f"   Title: {title}")
        
        # Look for tabs
        tabs_found = []
        for tab_name in ['Home', 'MDM', 'BPM', 'Reports', 'Accounts']:
            elements = await page.query_selector_all(f'text={tab_name}')
            if elements:
                tabs_found.append(tab_name)
        
        if tabs_found:
            logger.info(f"   ✓ Found tabs: {tabs_found}")
        else:
            logger.info(f"   ✗ No tabs found")
            
            # Show what buttons we do see
            buttons = await page.query_selector_all('button')
            logger.info(f"   Buttons on page:")
            for i, btn in enumerate(buttons[:10]):
                try:
                    text = await btn.inner_text()
                    if text.strip():
                        logger.info(f"      {i+1}. {text.strip()}")
                except:
                    pass
        
        # Try to navigate to mainIndex.do explicitly
        logger.info(f"\n7. Trying to navigate to mainIndex.do...")
        await page.goto("https://bbcohq.gofrugal.com/RayMedi_HQ/mainIndex.do", 
                       wait_until='networkidle', timeout=30000)
        await asyncio.sleep(5)
        
        logger.info(f"   URL: {page.url}")
        await page.screenshot(path='/app/gofrugal-report-builder/logs/test_mainindex.png', full_page=True)
        
        # Check for tabs again
        tabs_found = []
        for tab_name in ['Home', 'MDM', 'BPM', 'Reports', 'Accounts']:
            elements = await page.query_selector_all(f'text={tab_name}')
            if elements:
                tabs_found.append(tab_name)
        
        if tabs_found:
            logger.info(f"   ✓ Found tabs: {tabs_found}")
            logger.info(f"\n✓✓✓ SUCCESS! Dashboard is visible!")
        else:
            logger.info(f"   ✗ Still no tabs found")
            logger.info(f"\n✗✗✗ FAILED! Dashboard not loading")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await browser.close()
        await playwright.stop()


if __name__ == "__main__":
    asyncio.run(test_login())
