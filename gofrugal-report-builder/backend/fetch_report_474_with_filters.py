"""
Fetch Report 474 with filter handling
"""
import asyncio
import json
import pandas as pd
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import os
import logging
from datetime import datetime, timedelta

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fetch_report_474_with_filters():
    """Fetch Report 474 after applying filters"""
    
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
        
        logger.info("Submitting login...")
        await page.click('button[type="submit"]')
        
        await asyncio.sleep(5)
        logger.info(f"✓ Login successful")
        
        # STEP 2: Navigate to dashboard
        logger.info("\nSTEP 2: Navigating to dashboard")
        await page.goto("https://bbcohq.gofrugal.com/RayMedi_HQ/mainIndex.do", wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(5)
        logger.info(f"✓ Dashboard loaded")
        
        # STEP 3: Navigate to Report 474
        logger.info("\nSTEP 3: Navigating to Report 474")
        report_474_url = "https://bbcohq.gofrugal.com/RayMedi_HQ/mainIndex.do?page=%2Fsmartreport%2Findex.html%23%2Freports%3FreportId%3D474%26productId%3D2"
        
        await page.goto(report_474_url, wait_until='networkidle', timeout=60000)
        await asyncio.sleep(10)
        
        logger.info(f"✓ Report 474 page loaded")
        await page.screenshot(path='/app/gofrugal-report-builder/logs/step3_filters_page.png', full_page=True)
        
        # STEP 4: Handle filters
        logger.info("\nSTEP 4: Looking for filter elements and Apply button")
        
        # Save HTML to analyze filter structure
        content = await page.content()
        with open('/app/gofrugal-report-builder/logs/filters_page.html', 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Look for all input fields
        inputs = await page.query_selector_all('input')
        logger.info(f"Found {len(inputs)} input fields")
        
        for i, inp in enumerate(inputs[:20]):  # Check first 20
            try:
                input_type = await inp.get_attribute('type')
                input_name = await inp.get_attribute('name')
                input_id = await inp.get_attribute('id')
                input_placeholder = await inp.get_attribute('placeholder')
                logger.info(f"  Input {i+1}: type={input_type}, name={input_name}, id={input_id}, placeholder={input_placeholder}")
            except:
                pass
        
        # Look for date inputs
        logger.info("\nLooking for date range inputs...")
        date_selectors = [
            'input[type="date"]',
            'input[placeholder*="date" i]',
            'input[placeholder*="Date" i]',
            'input[name*="date" i]',
            'input[id*="date" i]',
            'input[name*="from" i]',
            'input[name*="to" i]',
        ]
        
        from_date = None
        to_date = None
        
        for selector in date_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    logger.info(f"✓ Found {len(elements)} date fields with selector: {selector}")
                    
                    # Try to fill with default dates (last 30 days)
                    today = datetime.now()
                    thirty_days_ago = today - timedelta(days=30)
                    
                    from_date_str = thirty_days_ago.strftime('%Y-%m-%d')
                    to_date_str = today.strftime('%Y-%m-%d')
                    
                    if len(elements) >= 2:
                        # Assume first is "from", second is "to"
                        logger.info(f"Setting date range: {from_date_str} to {to_date_str}")
                        try:
                            await elements[0].fill(from_date_str)
                            await elements[1].fill(to_date_str)
                            logger.info("✓ Date range set!")
                            from_date = elements[0]
                            to_date = elements[1]
                            break
                        except:
                            pass
            except:
                continue
        
        # Look for outlet/location dropdowns
        logger.info("\nLooking for outlet/location selectors...")
        select_elements = await page.query_selector_all('select')
        logger.info(f"Found {len(select_elements)} select dropdowns")
        
        for i, sel in enumerate(select_elements[:10]):
            try:
                sel_name = await sel.get_attribute('name')
                sel_id = await sel.get_attribute('id')
                logger.info(f"  Select {i+1}: name={sel_name}, id={sel_id}")
                
                # Get options
                options = await sel.query_selector_all('option')
                logger.info(f"    Has {len(options)} options")
                
                # Select first option (usually "All" or default)
                if options and len(options) > 0:
                    first_option = await options[0].get_attribute('value')
                    if first_option:
                        await sel.select_option(value=first_option)
                        logger.info(f"    Selected first option: {first_option}")
            except:
                pass
        
        # Take screenshot after filling filters
        await page.screenshot(path='/app/gofrugal-report-builder/logs/step4_filters_filled.png', full_page=True)
        
        # STEP 5: Find and click Apply button
        logger.info("\nSTEP 5: Looking for Apply button")
        
        apply_button_selectors = [
            'button:has-text("Apply")',
            'button:has-text("apply")',
            'button:has-text("APPLY")',
            'input[type="submit"]',
            'input[value*="Apply" i]',
            'button[type="submit"]',
            'a:has-text("Apply")',
            'text=Apply',
            'text=apply',
            'text=APPLY',
        ]
        
        apply_clicked = False
        for selector in apply_button_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    logger.info(f"✓ Found {len(elements)} Apply buttons with selector: {selector}")
                    
                    for elem in elements:
                        try:
                            text = await elem.inner_text()
                            logger.info(f"  Button text: {text}")
                            
                            if 'apply' in text.lower():
                                logger.info(f"  Clicking Apply button...")
                                await elem.click()
                                apply_clicked = True
                                logger.info("✓✓✓ Apply button clicked!")
                                break
                        except:
                            continue
                    
                    if apply_clicked:
                        break
            except:
                continue
        
        if not apply_clicked:
            logger.warning("Could not find Apply button! Listing all buttons...")
            all_buttons = await page.query_selector_all('button')
            for i, btn in enumerate(all_buttons):
                try:
                    text = await btn.inner_text()
                    logger.info(f"  Button {i+1}: {text}")
                except:
                    pass
        
        # STEP 6: Wait for report to load
        logger.info("\nSTEP 6: Waiting for report data to load...")
        await asyncio.sleep(15)  # Wait for report to generate
        
        await page.screenshot(path='/app/gofrugal-report-builder/logs/step6_report_generated.png', full_page=True)
        
        # Try to wait for table
        try:
            await page.wait_for_selector('table', timeout=30000)
            logger.info("✓ Table element appeared!")
        except:
            logger.warning("Table element not found")
        
        # STEP 7: Extract table data
        logger.info("\nSTEP 7: Extracting table data")
        
        # Check for iframes (report might be in iframe)
        iframes = await page.query_selector_all('iframe')
        logger.info(f"Found {len(iframes)} iframes")
        
        target_page = page
        
        if iframes:
            logger.info("Checking iframes for report data...")
            for idx, iframe_element in enumerate(iframes):
                try:
                    frame = await iframe_element.content_frame()
                    if frame:
                        tables_in_frame = await frame.query_selector_all('table')
                        logger.info(f"  Iframe {idx+1}: {len(tables_in_frame)} tables")
                        
                        if tables_in_frame:
                            logger.info(f"✓ Found tables in iframe {idx+1}!")
                            target_page = frame
                            break
                except Exception as e:
                    logger.error(f"Error checking iframe {idx+1}: {e}")
        
        # Extract tables
        tables = await target_page.query_selector_all('table')
        logger.info(f"Found {len(tables)} tables")
        
        if tables:
            for idx, table in enumerate(tables):
                try:
                    rows = await table.query_selector_all('tr')
                    logger.info(f"\nTable {idx+1}: {len(rows)} rows")
                    
                    if len(rows) > 1:
                        # Extract headers
                        header_row = rows[0]
                        header_cells = await header_row.query_selector_all('th, td')
                        
                        headers = []
                        for cell in header_cells:
                            text = await cell.inner_text()
                            headers.append(text.strip())
                        
                        if headers:
                            logger.info(f"✓✓✓ SUCCESS! Found headers: {headers}")
                            
                            # Extract all data rows
                            all_data = []
                            for row in rows[1:]:
                                cells = await row.query_selector_all('td')
                                row_data = []
                                for cell in cells:
                                    text = await cell.inner_text()
                                    row_data.append(text.strip())
                                if row_data:
                                    all_data.append(row_data)
                            
                            logger.info(f"Extracted {len(all_data)} data rows")
                            
                            # Show sample
                            for i, row in enumerate(all_data[:5]):
                                logger.info(f"  Row {i+1}: {row}")
                            
                            # Save schema
                            schema = {
                                'report_id': 474,
                                'report_name': 'Current Stock',
                                'url': page.url,
                                'columns': headers,
                                'total_rows': len(all_data),
                                'sample_data': all_data[:10],
                                'extracted_at': datetime.now().isoformat()
                            }
                            
                            with open('/app/gofrugal-report-builder/database/schemas/report_474_schema.json', 'w') as f:
                                json.dump(schema, f, indent=2)
                            
                            logger.info("\n✓✓✓ SUCCESS! Schema saved!")
                            
                            # Save full data as CSV
                            df = pd.DataFrame(all_data, columns=headers if len(headers) == len(all_data[0]) else None)
                            csv_path = f'/app/gofrugal-report-builder/database/report_474_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
                            df.to_csv(csv_path, index=False)
                            logger.info(f"✓ Full data saved to: {csv_path}")
                            
                            return schema
                
                except Exception as e:
                    logger.error(f"Error extracting table {idx+1}: {e}")
        else:
            logger.warning("No tables found in report!")
        
        # Save final state
        await page.screenshot(path='/app/gofrugal-report-builder/logs/final_report_state.png', full_page=True)
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        try:
            await page.screenshot(path='/app/gofrugal-report-builder/logs/error_screenshot.png', full_page=True)
        except:
            pass
    finally:
        await browser.close()
        await playwright.stop()


if __name__ == "__main__":
    asyncio.run(fetch_report_474_with_filters())
