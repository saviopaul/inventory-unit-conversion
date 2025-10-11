"""
Quick test with Report 521 and 677 (smaller reports)
"""
import asyncio
import json
import pandas as pd
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import os
import logging
from datetime import datetime

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fetch_report(report_id):
    """
    Fetch a report by ID
    """
    
    url = os.getenv('GOFRUGAL_URL')
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
        logger.info(f"FETCHING REPORT {report_id}")
        logger.info("="*80)
        
        # STEP 1: Login
        logger.info("\nSTEP 1: Logging in")
        await page.goto(url, wait_until='networkidle', timeout=30000)
        await page.fill('input[type="text"]', username)
        await page.fill('input[type="password"]', password)
        await page.click('button[type="submit"]')
        await asyncio.sleep(5)
        logger.info("✓ Login successful")
        
        # STEP 2: Navigate to dashboard
        logger.info("\nSTEP 2: Navigating to dashboard")
        await page.goto("https://bbcohq.gofrugal.com/RayMedi_HQ/mainIndex.do", 
                       wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(5)
        logger.info("✓ Dashboard loaded")
        
        # STEP 3: Navigate to Report
        logger.info(f"\nSTEP 3: Opening Report {report_id}")
        report_url = f"https://bbcohq.gofrugal.com/RayMedi_HQ/mainIndex.do?page=%2Fsmartreport%2Findex.html%23%2Freports%3FreportId%3D{report_id}%26productId%3D2"
        
        await page.goto(report_url, wait_until='networkidle', timeout=60000)
        
        logger.info("Waiting for page to fully load...")
        await asyncio.sleep(20)  # Extra wait for SPA
        
        # Take screenshot
        screenshot_path = f'/app/gofrugal-report-builder/logs/report_{report_id}_filter.png'
        await page.screenshot(path=screenshot_path, full_page=True)
        logger.info(f"✓ Screenshot saved: {screenshot_path}")
        
        # Check for iframes
        logger.info("\nChecking for iframes...")
        iframes = page.frames
        logger.info(f"Total frames: {len(iframes)}")
        
        for i, frame in enumerate(iframes):
            logger.info(f"  Frame {i}: {frame.url}")
        
        # Try to find content in main page or iframes
        target_frame = page
        
        # Check each frame for buttons
        for frame_idx, frame in enumerate(iframes):
            try:
                buttons = await frame.query_selector_all('button')
                logger.info(f"  Frame {frame_idx} has {len(buttons)} buttons")
                
                # Show button texts
                for btn_idx, btn in enumerate(buttons[:10]):
                    try:
                        text = await btn.inner_text()
                        if text.strip():
                            logger.info(f"    Button {btn_idx+1}: {text.strip()}")
                            
                            # If we find Apply button, use this frame
                            if 'apply' in text.lower():
                                target_frame = frame
                                logger.info(f"✓✓✓ Found Apply button in frame {frame_idx}!")
                                break
                    except:
                        pass
            except Exception as e:
                logger.debug(f"Error checking frame {frame_idx}: {e}")
        
        # STEP 4: Click Apply button
        logger.info("\nSTEP 4: Looking for Apply button")
        
        apply_selectors = [
            'button:has-text("Apply")',
            'button:text-is("Apply")',
            '//button[text()="Apply"]',
            '//button[contains(text(), "Apply")]',
            '//button[contains(@class, "apply")]',
        ]
        
        apply_clicked = False
        for selector in apply_selectors:
            try:
                logger.info(f"Trying: {selector}")
                
                if selector.startswith('//'):
                    elements = await target_frame.query_selector_all(f'xpath={selector}')
                else:
                    elements = await target_frame.query_selector_all(selector)
                
                logger.info(f"  Found {len(elements)} matches")
                
                if elements:
                    for elem in elements:
                        try:
                            text = await elem.inner_text()
                            logger.info(f"  Clicking button: {text}")
                            await elem.click()
                            apply_clicked = True
                            logger.info("✓✓✓ Apply button clicked!")
                            break
                        except:
                            pass
                
                if apply_clicked:
                    break
                    
            except Exception as e:
                logger.debug(f"Selector failed: {e}")
                continue
        
        if not apply_clicked:
            logger.warning("Apply button not found, trying without clicking...")
        
        # STEP 5: Wait for report
        logger.info("\nSTEP 5: Waiting for report to generate...")
        await asyncio.sleep(15)
        
        screenshot_path = f'/app/gofrugal-report-builder/logs/report_{report_id}_generated.png'
        await page.screenshot(path=screenshot_path, full_page=True)
        logger.info(f"✓ Screenshot saved: {screenshot_path}")
        
        # STEP 6: Look for Export button
        logger.info("\nSTEP 6: Looking for Export button")
        
        export_selectors = [
            'button:has-text("Export")',
            'button:has-text("CSV")',
            'button:has-text("Download")',
            'text=Export as CSV',
            '//button[contains(text(), "Export")]',
            '//button[contains(text(), "CSV")]',
            '//a[contains(text(), "Export")]',
        ]
        
        for selector in export_selectors:
            try:
                logger.info(f"Trying: {selector}")
                
                if selector.startswith('//'):
                    elements = await target_frame.query_selector_all(f'xpath={selector}')
                else:
                    elements = await target_frame.query_selector_all(selector)
                
                logger.info(f"  Found {len(elements)} matches")
                
                if elements:
                    for elem in elements:
                        try:
                            text = await elem.inner_text()
                            logger.info(f"  Found button: {text}")
                            
                            if any(keyword in text.lower() for keyword in ['export', 'csv', 'download']):
                                logger.info(f"  Clicking: {text}")
                                
                                # Try to download
                                try:
                                    async with page.expect_download(timeout=60000) as download_info:
                                        await elem.click()
                                        download = await download_info.value
                                        
                                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                        filename = f'report_{report_id}_{timestamp}.csv'
                                        save_path = os.path.join(download_path, filename)
                                        
                                        await download.save_as(save_path)
                                        logger.info(f"✓✓✓ CSV downloaded: {save_path}")
                                        
                                        # Parse and display
                                        df = pd.read_csv(save_path)
                                        logger.info(f"\n📊 Report {report_id} Data:")
                                        logger.info(f"  Rows: {len(df)}")
                                        logger.info(f"  Columns: {list(df.columns)}")
                                        logger.info(f"\nFirst 5 rows:")
                                        logger.info(df.head(5).to_string())
                                        
                                        return save_path
                                except Exception as download_error:
                                    logger.warning(f"Download failed: {download_error}")
                                    # Button might not trigger download, continue searching
                        except:
                            pass
                    
            except Exception as e:
                logger.debug(f"Selector failed: {e}")
                continue
        
        logger.warning("Could not download CSV")
        
        # List all buttons for debugging
        logger.info("\nAll buttons on page:")
        all_buttons = await target_frame.query_selector_all('button, a[role="button"]')
        for i, btn in enumerate(all_buttons[:30]):
            try:
                text = await btn.inner_text()
                if text.strip():
                    logger.info(f"  {i+1}. {text.strip()}")
            except:
                pass
        
        return None
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        await browser.close()
        await playwright.stop()


async def main():
    """Test with both reports"""
    
    logger.info("\n" + "="*80)
    logger.info("TESTING WITH REPORT 521")
    logger.info("="*80)
    result_521 = await fetch_report(521)
    
    logger.info("\n" + "="*80)
    logger.info("TESTING WITH REPORT 677")
    logger.info("="*80)
    result_677 = await fetch_report(677)
    
    logger.info("\n" + "="*80)
    logger.info("RESULTS")
    logger.info("="*80)
    logger.info(f"Report 521: {'✓ Success - ' + result_521 if result_521 else '✗ Failed'}")
    logger.info(f"Report 677: {'✓ Success - ' + result_677 if result_677 else '✗ Failed'}")


if __name__ == "__main__":
    asyncio.run(main())
