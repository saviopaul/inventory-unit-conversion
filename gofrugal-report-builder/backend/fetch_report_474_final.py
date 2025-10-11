"""
Final scraper for Report 474 with correct navigation
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


async def fetch_report_474():
    """Fetch Report 474 using correct navigation path"""
    
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
        # STEP 1: Login
        logger.info(f"STEP 1: Logging in to {url}")
        await page.goto(url, wait_until='networkidle', timeout=30000)
        
        await page.fill('input[type="text"]', username)
        await page.fill('input[type="password"]', password)
        
        logger.info("Submitting login and waiting for redirect...")
        await page.click('button[type="submit"]')
        
        # Wait and let the page redirect
        try:
            await page.wait_for_url(lambda url: 'j_security_check' not in url, timeout=15000)
        except:
            pass
        
        await asyncio.sleep(5)
        
        logger.info(f"After login URL: {page.url}")
        
        # Get cookies for debugging
        cookies = await context.cookies()
        logger.info(f"Session cookies: {len(cookies)} cookies set")
        
        # STEP 2: Try to navigate to main dashboard first
        logger.info("\nSTEP 2: Navigating to main dashboard")
        
        try:
            await page.goto("https://bbcohq.gofrugal.com/RayMedi_HQ/mainIndex.do", wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(10)
            logger.info(f"Dashboard URL: {page.url}")
            await page.screenshot(path='/app/gofrugal-report-builder/logs/dashboard_main.png', full_page=True)
        except Exception as e:
            logger.error(f"Error navigating to dashboard: {e}")
        
        current_url = page.url
        logger.info(f"Current URL: {current_url}")
        
        # STEP 3: Navigate directly to Report 474
        logger.info("\nSTEP 3: Navigating directly to Report 474")
        report_474_url = "https://bbcohq.gofrugal.com/RayMedi_HQ/mainIndex.do?page=%2Fsmartreport%2Findex.html%23%2Freports%3FreportId%3D474%26productId%3D2"
        
        await page.goto(report_474_url, wait_until='networkidle', timeout=60000)
        
        logger.info(f"Waiting for report content to load...")
        await asyncio.sleep(20)  # Wait for AJAX/JavaScript to load data
        
        logger.info(f"✓ Navigated to Report 474!")
        await page.screenshot(path='/app/gofrugal-report-builder/logs/report_474_loaded.png', full_page=True)
        
        # Log page title and URL
        title = await page.title()
        logger.info(f"Page title: {title}")
        logger.info(f"Current URL: {page.url}")
        
        # STEP 4: Wait for content to load (it might be in an iframe)
        logger.info("\nSTEP 4: Checking for iframes")
        
        # Check if content is in an iframe
        iframes = await page.query_selector_all('iframe')
        logger.info(f"Found {len(iframes)} iframes")
        
        # If there's an iframe, switch to it
        if iframes:
            logger.info("Report might be inside an iframe, checking each one...")
            for idx, iframe_element in enumerate(iframes):
                try:
                    frame = await iframe_element.content_frame()
                    if frame:
                        logger.info(f"Checking iframe {idx+1}")
                        
                        # Check if this frame has tables
                        tables_in_frame = await frame.query_selector_all('table')
                        if tables_in_frame:
                            logger.info(f"✓ Found {len(tables_in_frame)} tables in iframe {idx+1}!")
                            page = frame  # Switch to this frame for data extraction
                            break
                except Exception as e:
                    logger.error(f"Error checking iframe {idx+1}: {e}")
        
        # STEP 5: Search for Report 474 or Current Stock
        logger.info("\nSTEP 5: Searching for Report 474 / Current Stock")
        
        # List all visible links
        all_links = await page.query_selector_all('a')
        logger.info(f"Found {len(all_links)} links on page")
        
        found_report = False
        for link in all_links:
            try:
                text = await link.inner_text()
                href = await link.get_attribute('href')
                
                # Look for Report 474 or Current Stock
                if text and ('474' in text or 'Current Stock' in text.lower() or 'current stock' in text.lower()):
                    logger.info(f"✓✓✓ FOUND IT! {text} -> {href}")
                    
                    # Click on it
                    await link.click()
                    await asyncio.sleep(10)  # Wait for report to load
                    
                    await page.screenshot(path='/app/gofrugal-report-builder/logs/report_474_page.png', full_page=True)
                    logger.info("✓ Report page loaded!")
                    
                    found_report = True
                    break
            except:
                continue
        
        if not found_report:
            # Try searching in page
            logger.info("Report not found by link, searching entire page...")
            
            # Try to find any element with "474" or "Current Stock"
            search_patterns = [
                'text=/.*474.*/i',
                'text=/.*current stock.*/i',
                'text=/.*stock.*/i',
            ]
            
            for pattern in search_patterns:
                try:
                    elements = await page.query_selector_all(pattern)
                    logger.info(f"Pattern '{pattern}': found {len(elements)} elements")
                    
                    for elem in elements[:10]:
                        text = await elem.inner_text()
                        logger.info(f"  - {text}")
                        
                        if '474' in text or 'current stock' in text.lower():
                            logger.info(f"Attempting to click: {text}")
                            await elem.click()
                            await asyncio.sleep(10)
                            found_report = True
                            break
                    
                    if found_report:
                        break
                except Exception as e:
                    logger.error(f"Error with pattern {pattern}: {e}")
        
        # STEP 6: Extract table data
        logger.info("\nSTEP 6: Extracting table data")
        
        # Try to wait for table to appear
        try:
            logger.info("Waiting for table element...")
            await page.wait_for_selector('table', timeout=30000)
            logger.info("✓ Table element found!")
        except:
            logger.warning("Table element not found after 30 seconds")
        
        # Check for tables
        tables = await page.query_selector_all('table')
        logger.info(f"Found {len(tables)} tables on page")
        
        # Also check for common data grid selectors
        data_selectors = ['div[role="grid"]', '.ag-grid', '.data-table', '[class*="table"]', '[class*="grid"]']
        for selector in data_selectors:
            elements = await page.query_selector_all(selector)
            if elements:
                logger.info(f"Found {len(elements)} elements with selector: {selector}")
        
        if tables:
            # Extract from first data table
            for idx, table in enumerate(tables):
                try:
                    # Get all rows
                    rows = await table.query_selector_all('tr')
                    logger.info(f"Table {idx+1}: {len(rows)} rows")
                    
                    if len(rows) > 1:  # Has header and data
                        # Extract headers
                        header_row = rows[0]
                        header_cells = await header_row.query_selector_all('th, td')
                        
                        headers = []
                        for cell in header_cells:
                            text = await cell.inner_text()
                            headers.append(text.strip())
                        
                        if headers:
                            logger.info(f"✓✓✓ Table {idx+1} headers: {headers}")
                            
                            # Extract sample data rows
                            data_rows = []
                            for row in rows[1:min(6, len(rows))]:  # Get first 5 data rows
                                cells = await row.query_selector_all('td')
                                row_data = []
                                for cell in cells:
                                    text = await cell.inner_text()
                                    row_data.append(text.strip())
                                if row_data:
                                    data_rows.append(row_data)
                            
                            logger.info(f"Sample data rows: {len(data_rows)}")
                            for i, row in enumerate(data_rows[:3]):
                                logger.info(f"  Row {i+1}: {row}")
                            
                            # Save schema
                            schema = {
                                'report_id': 474,
                                'report_name': 'Current Stock',
                                'url': page.url,
                                'columns': headers,
                                'sample_data': data_rows,
                                'extracted_at': datetime.now().isoformat(),
                                'total_rows': len(rows) - 1
                            }
                            
                            with open('/app/gofrugal-report-builder/database/schemas/report_474_schema.json', 'w') as f:
                                json.dump(schema, f, indent=2)
                            
                            logger.info("\n✓✓✓ SUCCESS! Schema saved to report_474_schema.json")
                            
                            # Try to download/export if button available
                            logger.info("\nSTEP 7: Looking for download/export button")
                            
                            download_selectors = [
                                'text=Download',
                                'text=Export',
                                'text=Excel',
                                'text=CSV',
                                'button:has-text("Download")',
                                'button:has-text("Export")',
                                'a:has-text("Download")',
                                'a:has-text("Export")',
                            ]
                            
                            for selector in download_selectors:
                                try:
                                    btn = await page.query_selector(selector)
                                    if btn:
                                        text = await btn.inner_text()
                                        logger.info(f"Found download button: {text}")
                                        
                                        # Try to click and download
                                        async with page.expect_download() as download_info:
                                            await btn.click()
                                            download = await download_info.value
                                            
                                            # Save file
                                            filename = download.suggested_filename
                                            save_path = f'/app/gofrugal-report-builder/database/report_474_{datetime.now().strftime("%Y%m%d_%H%M%S")}.{filename.split(".")[-1]}'
                                            await download.save_as(save_path)
                                            logger.info(f"✓ Downloaded file: {save_path}")
                                            break
                                except:
                                    continue
                            
                            return schema
                
                except Exception as e:
                    logger.error(f"Error extracting table {idx+1}: {e}")
        
        # Save final page state
        await page.screenshot(path='/app/gofrugal-report-builder/logs/final_state.png', full_page=True)
        
        content = await page.content()
        with open('/app/gofrugal-report-builder/logs/final_page.html', 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("\nDone! Check logs folder for screenshots and HTML.")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Save error screenshot
        try:
            await page.screenshot(path='/app/gofrugal-report-builder/logs/error_screenshot.png', full_page=True)
        except:
            pass
    finally:
        await browser.close()
        await playwright.stop()


if __name__ == "__main__":
    asyncio.run(fetch_report_474())
