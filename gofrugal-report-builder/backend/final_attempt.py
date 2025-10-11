"""
Final attempt - wait for actual dashboard to load after login
"""
import asyncio
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import os
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_full_flow():
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
        # Step 1: Login
        logger.info("STEP 1: Login")
        await page.goto("https://bbcohq.gofrugal.com/RayMedi_HQ/index.do", 
                       wait_until='networkidle', timeout=30000)
        
        await page.fill('input[name="j_username"]', username)
        await page.fill('input[name="j_password"]', password)
        await page.click('button[type="submit"]')
        
        # Wait for redirect from j_security_check
        logger.info("Waiting for post-login redirect...")
        
        # Try to wait for URL change from j_security_check
        try:
            await page.wait_for_url(lambda url: 'j_security_check' not in url, timeout=15000)
            logger.info(f"✓ Redirected to: {page.url}")
        except:
            logger.info(f"Still at: {page.url}")
        
        await asyncio.sleep(5)
        
        # Step 2: If still on j_security_check, navigate to mainIndex.do (without page parameter)
        logger.info("\nSTEP 2: Navigate to main dashboard")
        
        if 'mainIndex.do' not in page.url:
            await page.goto("https://bbcohq.gofrugal.com/RayMedi_HQ/mainIndex.do", 
                           wait_until='networkidle', timeout=30000)
        
        # Wait longer for dashboard to render
        logger.info("Waiting 30 seconds for dashboard to fully load...")
        await asyncio.sleep(30)
        
        await page.screenshot(path='/app/gofrugal-report-builder/logs/dashboard_wait30.png', full_page=True)
        
        # Check for tabs
        logger.info("\nChecking for dashboard tabs...")
        tabs_found = []
        for tab_name in ['Home', 'MDM', 'BPM', 'Reports', 'Accounts', 'Admin']:
            try:
                elements = await page.locator(f'text={tab_name}').all()
                if elements:
                    tabs_found.append(tab_name)
                    logger.info(f"  ✓ Found: {tab_name}")
            except:
                pass
        
        if tabs_found:
            logger.info(f"\n✓✓✓ SUCCESS! Dashboard loaded with tabs: {tabs_found}")
        else:
            logger.info(f"\n✗ No dashboard tabs found")
            
            # Check all text on page
            body_text = await page.inner_text('body')
            logger.info(f"Body text (first 1000 chars): {body_text[:1000]}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await browser.close()
        await playwright.stop()


if __name__ == "__main__":
    asyncio.run(test_full_flow())
