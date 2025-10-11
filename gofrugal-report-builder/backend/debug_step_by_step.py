"""
Debug step by step - what do we actually see?
"""
import asyncio
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import os
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def debug_navigation():
    """Check what we actually see at each step"""
    
    url = os.getenv('GOFRUGAL_URL')
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
        # Login
        logger.info("STEP 1: Logging in...")
        await page.goto(url, wait_until='networkidle', timeout=30000)
        await page.fill('input[type="text"]', username)
        await page.fill('input[type="password"]', password)
        await page.click('button[type="submit"]')
        await asyncio.sleep(5)
        logger.info(f"✓ After login, URL: {page.url}")
        
        # Navigate to the Report 474 URL
        logger.info("\nSTEP 2: Navigating to Report 474 URL")
        report_url = "https://bbcohq.gofrugal.com/RayMedi_HQ/mainIndex.do?page=%2Fsmartreport%2Findex.html%23%2Freports%3FreportId%3D474%26productId%3D2"
        
        await page.goto(report_url, wait_until='networkidle', timeout=60000)
        logger.info(f"✓ Current URL: {page.url}")
        
        # Wait for JavaScript to execute
        logger.info("\nWaiting 20 seconds for JavaScript/SPA to load...")
        await asyncio.sleep(20)
        
        # Take screenshot
        await page.screenshot(path='/app/gofrugal-report-builder/logs/debug_what_i_see.png', full_page=True)
        logger.info("✓ Screenshot saved")
        
        # Check what's visible
        logger.info("\n" + "="*80)
        logger.info("WHAT I SEE ON THE PAGE:")
        logger.info("="*80)
        
        # Check for main tabs
        logger.info("\n1. Looking for main tabs (Home, MDM, BPM, Reports, etc.):")
        tab_texts = ['Home', 'MDM', 'BPM', 'Reports', 'Accounts', 'Admin']
        
        for tab_name in tab_texts:
            elements = await page.query_selector_all(f'text={tab_name}')
            if elements:
                logger.info(f"   ✓ Found '{tab_name}' - {len(elements)} matches")
            else:
                logger.info(f"   ✗ NOT found: '{tab_name}'")
        
        # Check page title
        title = await page.title()
        logger.info(f"\n2. Page Title: {title}")
        
        # Count total elements
        all_buttons = await page.query_selector_all('button')
        all_links = await page.query_selector_all('a')
        all_inputs = await page.query_selector_all('input')
        
        logger.info(f"\n3. Element counts:")
        logger.info(f"   Buttons: {len(all_buttons)}")
        logger.info(f"   Links: {len(all_links)}")
        logger.info(f"   Inputs: {len(all_inputs)}")
        
        # List all visible text on buttons
        logger.info(f"\n4. All buttons on page:")
        for i, btn in enumerate(all_buttons[:20]):
            try:
                text = await btn.inner_text()
                if text.strip():
                    logger.info(f"   Button {i+1}: {text.strip()}")
            except:
                pass
        
        # Check for iframes
        logger.info(f"\n5. Iframes:")
        frames = page.frames
        logger.info(f"   Total frames: {len(frames)}")
        for i, frame in enumerate(frames):
            logger.info(f"   Frame {i}: {frame.url}")
        
        # Get HTML snippet
        logger.info(f"\n6. HTML Body (first 500 chars):")
        body_text = await page.inner_text('body')
        logger.info(f"   {body_text[:500]}")
        
        # Save full HTML
        html_content = await page.content()
        with open('/app/gofrugal-report-builder/logs/debug_page.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"\n7. Full HTML saved to: debug_page.html")
        
        # Check for specific filter elements
        logger.info(f"\n8. Looking for filter page elements:")
        
        filter_keywords = ['Apply', 'Export', 'Date', 'Outlet', 'Filter', 'Generate']
        for keyword in filter_keywords:
            elements = await page.query_selector_all(f'text=/{keyword}/i')
            if elements:
                logger.info(f"   ✓ Found '{keyword}': {len(elements)} matches")
            else:
                logger.info(f"   ✗ NOT found: '{keyword}'")
        
        # Final verdict
        logger.info("\n" + "="*80)
        logger.info("VERDICT:")
        logger.info("="*80)
        
        # Check if we see the dashboard tabs
        has_reports_tab = len(await page.query_selector_all('text=Reports')) > 0
        has_mdm_tab = len(await page.query_selector_all('text=MDM')) > 0
        has_apply_button = len(await page.query_selector_all('text=Apply')) > 0
        
        if has_reports_tab and has_mdm_tab:
            logger.info("✓ YES - I can see the dashboard with tabs (MDM, Reports, etc.)")
        else:
            logger.info("✗ NO - I cannot see the dashboard tabs")
        
        if has_apply_button:
            logger.info("✓ YES - I can see the Apply button (filter page loaded)")
        else:
            logger.info("✗ NO - I cannot see the Apply button (filter page NOT loaded)")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await browser.close()
        await playwright.stop()


if __name__ == "__main__":
    asyncio.run(debug_navigation())
