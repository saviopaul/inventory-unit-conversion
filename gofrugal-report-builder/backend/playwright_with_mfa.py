"""
Playwright scraper with MFA popup handling
"""
import asyncio
import pandas as pd
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import os
import logging
from datetime import datetime

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fetch_report_with_mfa(report_id=521):
    """Fetch report with MFA handling"""
    
    username = os.getenv('GOFRUGAL_USERNAME')
    password = os.getenv('GOFRUGAL_PASSWORD')
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox']
    )
    
    download_path = '/app/gofrugal-report-builder/database/downloads'
    os.makedirs(download_path, exist_ok=True)
    
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        accept_downloads=True
    )
    page = await context.new_page()
    
    try:
        logger.info("="*80)
        logger.info(f"FETCHING REPORT {report_id} WITH MFA HANDLING")
        logger.info("="*80)
        
        # Step 1: Login
        logger.info("\nSTEP 1: Login")
        await page.goto("https://bbcohq.gofrugal.com/RayMedi_HQ/index.do", 
                       wait_until='networkidle', timeout=30000)
        
        await page.fill('input[name="j_username"]', username)
        await page.fill('input[name="j_password"]', password)
        await page.click('button[type="submit"]')
        
        logger.info("Waiting for post-login...")
        await asyncio.sleep(5)
        
        # Step 2: Handle MFA popup - click "Not Now"
        logger.info("\nSTEP 2: Looking for MFA popup")
        
        try:
            # Try to find "Not Now" button
            not_now_button = await page.wait_for_selector('text=Not Now', timeout=10000)
            if not_now_button:
                logger.info("✓ Found 'Not Now' button!")
                await not_now_button.click()
                logger.info("✓✓✓ Clicked 'Not Now' - MFA popup dismissed!")
                await asyncio.sleep(3)
        except Exception as e:
            logger.info(f"No MFA popup found: {e}")
        
        # Step 3: Check if dashboard loaded
        logger.info("\nSTEP 3: Checking for dashboard")
        await asyncio.sleep(5)
        
        await page.screenshot(path='/app/gofrugal-report-builder/logs/pw_after_mfa.png', full_page=True)
        
        # Look for tabs
        tabs_found = []
        for tab_name in ['Home', 'MDM', 'BPM', 'Reports']:
            elements = await page.query_selector_all(f'text={tab_name}')
            if elements:
                tabs_found.append(tab_name)
                logger.info(f"  ✓ Found tab: {tab_name}")
        
        if tabs_found:
            logger.info(f"\n✓✓✓ SUCCESS! Dashboard loaded with tabs: {tabs_found}")
        else:
            logger.info("\n✗ Dashboard tabs not found yet")
            
            # Navigate to mainIndex.do explicitly
            logger.info("Trying to navigate to mainIndex.do...")
            await page.goto("https://bbcohq.gofrugal.com/RayMedi_HQ/mainIndex.do",
                           wait_until='networkidle', timeout=30000)
            await asyncio.sleep(10)
            
            await page.screenshot(path='/app/gofrugal-report-builder/logs/pw_mainindex_after_mfa.png', full_page=True)
            
            # Check again
            tabs_found = []
            for tab_name in ['Home', 'MDM', 'BPM', 'Reports']:
                elements = await page.query_selector_all(f'text={tab_name}')
                if elements:
                    tabs_found.append(tab_name)
            
            if tabs_found:
                logger.info(f"✓✓✓ NOW dashboard is visible: {tabs_found}")
            else:
                logger.info("✗ Still no dashboard")
                return None
        
        # Step 4: Navigate to report
        logger.info(f"\n✓ Dashboard accessible! Navigating to Report {report_id}...")
        
        report_url = f"https://bbcohq.gofrugal.com/RayMedi_HQ/mainIndex.do?page=%2Fsmartreport%2Findex.html%23%2Freports%3FreportId%3D{report_id}%26productId%3D2"
        await page.goto(report_url, wait_until='networkidle', timeout=60000)
        
        logger.info("Waiting for report filter page...")
        await asyncio.sleep(20)
        
        await page.screenshot(path=f'/app/gofrugal-report-builder/logs/pw_report_{report_id}_filters.png', full_page=True)
        
        # Step 5: Look for Apply button
        logger.info(f"\nSTEP 5: Looking for Apply button")
        
        try:
            apply_button = await page.wait_for_selector('text=Apply', timeout=15000)
            if apply_button:
                logger.info("✓✓✓ Found Apply button!")
                await apply_button.click()
                logger.info("✓ Clicked Apply")
                
                await asyncio.sleep(15)
                await page.screenshot(path=f'/app/gofrugal-report-builder/logs/pw_report_{report_id}_generated.png', full_page=True)
                
                # Look for Export button
                logger.info("\nSTEP 6: Looking for Export button")
                
                export_selectors = [
                    'text=Export as CSV',
                    'text=Export',
                    'button:has-text("Export")',
                    'button:has-text("CSV")',
                ]
                
                for selector in export_selectors:
                    try:
                        export_button = await page.query_selector(selector)
                        if export_button:
                            text = await export_button.inner_text()
                            logger.info(f"✓✓✓ Found export button: {text}")
                            
                            # Try to download
                            async with page.expect_download(timeout=60000) as download_info:
                                await export_button.click()
                                download = await download_info.value
                                
                                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                filename = f'report_{report_id}_{timestamp}.csv'
                                save_path = os.path.join(download_path, filename)
                                
                                await download.save_as(save_path)
                                logger.info(f"\n✓✓✓ CSV DOWNLOADED: {save_path}")
                                
                                # Parse and show
                                df = pd.read_csv(save_path)
                                logger.info(f"\n📊 Report {report_id} Data:")
                                logger.info(f"  Rows: {len(df)}")
                                logger.info(f"  Columns: {list(df.columns)}")
                                logger.info(f"\nFirst 5 rows:")
                                logger.info(df.head(5).to_string())
                                
                                return save_path
                            
                    except Exception as e:
                        logger.debug(f"Selector {selector} failed: {e}")
                        continue
                
                logger.warning("Export button not found")
                
        except Exception as e:
            logger.error(f"Apply button not found: {e}")
        
        return None
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        await browser.close()
        await playwright.stop()


if __name__ == "__main__":
    result = asyncio.run(fetch_report_with_mfa(521))
    if result:
        print(f"\n✓✓✓ SUCCESS! Downloaded: {result}")
    else:
        print(f"\n✗ Failed to download report")
