"""
Navigate through GoFrugal tabs to find Report 474
"""
import asyncio
import json
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import os
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def navigate_to_report_474():
    """Navigate through tabs to find Report 474"""
    
    url = os.getenv('GOFRUGAL_URL')
    username = os.getenv('GOFRUGAL_USERNAME')
    password = os.getenv('GOFRUGAL_PASSWORD')
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)  # Visible browser for debugging
    context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
    page = await context.new_page()
    
    try:
        # Login
        logger.info(f"Navigating to {url}")
        await page.goto(url, wait_until='networkidle', timeout=30000)
        
        await page.fill('input[type="text"]', username)
        await page.fill('input[type="password"]', password)
        
        logger.info("Clicking login...")
        await page.click('button[type="submit"]')
        
        # Wait for dashboard to load - try different wait strategies
        logger.info("Waiting for dashboard to load...")
        await asyncio.sleep(10)  # Give it time to load
        
        logger.info(f"Current URL after login: {page.url}")
        
        # Take screenshot of dashboard
        await page.screenshot(path='/app/gofrugal-report-builder/logs/step1_dashboard.png', full_page=True)
        
        # Look for all tabs on the page
        logger.info("\n" + "="*80)
        logger.info("STEP 1: Finding all main tabs on dashboard")
        logger.info("="*80)
        
        # Try different selectors for tabs
        tab_selectors = [
            'ul.nav li',  # Bootstrap tabs
            '.nav-tabs li',
            '.tabs li',
            '[role="tab"]',
            'a[data-toggle="tab"]',
            'button[role="tab"]',
            'nav a',
            'nav button',
            '.navbar li',
            'div[class*="tab"]',
            'span[class*="tab"]',
        ]
        
        all_tabs = []
        for selector in tab_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    logger.info(f"✓ Found {len(elements)} elements with selector: {selector}")
                    for elem in elements:
                        text = await elem.inner_text()
                        if text and text.strip():
                            all_tabs.append({
                                'text': text.strip(),
                                'element': elem,
                                'selector': selector
                            })
            except Exception as e:
                continue
        
        # Display all tabs found
        logger.info(f"\nFound {len(all_tabs)} potential tabs:")
        for i, tab in enumerate(all_tabs[:30]):  # Show first 30
            logger.info(f"{i+1}. {tab['text']}")
        
        # Look specifically for Reports tab
        logger.info("\n" + "="*80)
        logger.info("STEP 2: Looking for 'Reports' tab")
        logger.info("="*80)
        
        reports_tab = None
        for tab in all_tabs:
            if 'report' in tab['text'].lower():
                logger.info(f"✓ Found Reports tab: {tab['text']}")
                reports_tab = tab
                break
        
        if not reports_tab:
            # Try more aggressive search
            logger.info("Reports tab not found in tabs list, trying direct search...")
            search_patterns = [
                'text=/.*report.*/i',
                ':has-text("Report")',
                ':has-text("Reports")',
            ]
            
            for pattern in search_patterns:
                try:
                    elements = await page.query_selector_all(pattern)
                    logger.info(f"Pattern '{pattern}': found {len(elements)} elements")
                    for elem in elements:
                        text = await elem.inner_text()
                        logger.info(f"  - {text}")
                        if text and 'report' in text.lower() and len(text) < 50:
                            reports_tab = {'element': elem, 'text': text}
                            break
                except:
                    continue
        
        if reports_tab:
            logger.info(f"\n✓ Clicking on Reports tab: {reports_tab['text']}")
            try:
                await reports_tab['element'].click()
                await asyncio.sleep(3)
                await page.screenshot(path='/app/gofrugal-report-builder/logs/step2_reports_tab.png', full_page=True)
                logger.info("Reports tab clicked!")
            except Exception as e:
                logger.error(f"Error clicking Reports tab: {e}")
        else:
            logger.warning("Could not find Reports tab!")
            # List all clickable elements
            logger.info("\nAll clickable elements on page:")
            clickables = await page.query_selector_all('a, button, [onclick]')
            for i, elem in enumerate(clickables[:50]):
                try:
                    text = await elem.inner_text()
                    if text and text.strip():
                        logger.info(f"{i+1}. {text.strip()}")
                except:
                    continue
        
        # Now look for sub-tabs
        logger.info("\n" + "="*80)
        logger.info("STEP 3: Looking for sub-tabs under Reports")
        logger.info("="*80)
        
        await asyncio.sleep(2)
        
        # Look for sub-tabs
        subtab_selectors = [
            'ul.nav li',
            '.sub-tabs li',
            '.nav-tabs li',
            '[role="tab"]',
            'a[data-toggle="tab"]',
        ]
        
        all_subtabs = []
        for selector in subtab_selectors:
            try:
                elements = await page.query_selector_all(selector)
                for elem in elements:
                    text = await elem.inner_text()
                    if text and text.strip() and len(text.strip()) < 100:
                        all_subtabs.append({
                            'text': text.strip(),
                            'element': elem
                        })
            except:
                continue
        
        logger.info(f"\nFound {len(all_subtabs)} potential sub-tabs:")
        for i, tab in enumerate(all_subtabs[:30]):
            logger.info(f"{i+1}. {tab['text']}")
        
        # Search for Report 474 or Current Stock in sub-tabs and page content
        logger.info("\n" + "="*80)
        logger.info("STEP 4: Searching for Report 474 / Current Stock")
        logger.info("="*80)
        
        search_terms = ['474', 'Current Stock', 'Stock', 'Inventory']
        
        for term in search_terms:
            try:
                logger.info(f"\nSearching for: {term}")
                elements = await page.query_selector_all(f'text=/{term}/i')
                logger.info(f"Found {len(elements)} matches")
                
                for i, elem in enumerate(elements[:5]):
                    try:
                        text = await elem.inner_text()
                        logger.info(f"  {i+1}. {text}")
                        
                        # Try clicking the first match
                        if i == 0 and '474' in text or 'Current Stock' in text:
                            logger.info(f"Attempting to click: {text}")
                            await elem.click()
                            await asyncio.sleep(5)
                            await page.screenshot(path='/app/gofrugal-report-builder/logs/step4_report_474.png', full_page=True)
                            
                            # Check for tables
                            tables = await page.query_selector_all('table')
                            if tables:
                                logger.info(f"✓✓✓ SUCCESS! Found {len(tables)} tables on Report 474!")
                                
                                # Extract headers from first table
                                table = tables[0]
                                headers = []
                                header_cells = await table.query_selector_all('th')
                                for cell in header_cells:
                                    h_text = await cell.inner_text()
                                    headers.append(h_text.strip())
                                
                                logger.info(f"Table columns: {headers}")
                                
                                # Save schema
                                schema = {
                                    'report_id': 474,
                                    'report_name': 'Current Stock',
                                    'columns': headers,
                                    'url': page.url,
                                    'extracted_at': str(asyncio.get_event_loop().time())
                                }
                                
                                with open('/app/gofrugal-report-builder/database/schemas/report_474_schema.json', 'w') as f:
                                    json.dump(schema, f, indent=2)
                                
                                logger.info("✓ Schema saved!")
                                return
                    except Exception as e:
                        logger.error(f"Error processing element: {e}")
                        continue
            except Exception as e:
                logger.error(f"Error searching for {term}: {e}")
                continue
        
        # If we still haven't found it, take final screenshots
        logger.info("\nTaking final screenshots for manual review...")
        await page.screenshot(path='/app/gofrugal-report-builder/logs/final_state.png', full_page=True)
        
        # Save page HTML
        content = await page.content()
        with open('/app/gofrugal-report-builder/logs/final_state.html', 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("Done! Please check the screenshots in /app/gofrugal-report-builder/logs/")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Keep browser open for manual inspection
        logger.info("\n⏸️  Browser will stay open for 60 seconds for manual inspection...")
        await asyncio.sleep(60)
        await browser.close()
        await playwright.stop()


if __name__ == "__main__":
    asyncio.run(navigate_to_report_474())
