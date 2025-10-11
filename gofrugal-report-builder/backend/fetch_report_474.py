"""
Enhanced scraper specifically for fetching Report 474
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


async def fetch_report_474():
    """Fetch Report 474 from GoFrugal portal"""
    
    url = os.getenv('GOFRUGAL_URL')
    username = os.getenv('GOFRUGAL_USERNAME')
    password = os.getenv('GOFRUGAL_PASSWORD')
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
    page = await context.new_page()
    
    try:
        # Login
        logger.info(f"Navigating to {url}")
        await page.goto(url, wait_until='networkidle', timeout=30000)
        
        # Fill credentials
        await page.fill('input[type="text"]', username)
        await page.fill('input[type="password"]', password)
        
        # Click login and wait for navigation
        logger.info("Submitting login...")
        async with page.expect_navigation(timeout=30000):
            await page.click('button[type="submit"]')
        
        logger.info(f"After login URL: {page.url}")
        
        # Wait for dashboard to load
        logger.info("Waiting for dashboard to load...")
        await asyncio.sleep(5)
        
        # Check current URL
        current_url = page.url
        logger.info(f"Current URL: {current_url}")
        
        # If we're still on login page or got redirected, try to navigate to main app
        if 'login' in current_url.lower() or current_url == url:
            logger.info("Still on login page, trying to navigate to main app...")
            # Try common dashboard URLs
            possible_urls = [
                f"{url}/dashboard",
                f"{url}/home",
                f"{url}/main",
                f"{url.replace('/RayMedi_HQ/j_security_check', '')}/dashboard",
                url.replace('/RayMedi_HQ/j_security_check', ''),
            ]
            
            for test_url in possible_urls:
                try:
                    logger.info(f"Trying: {test_url}")
                    await page.goto(test_url, wait_until='networkidle', timeout=15000)
                    await asyncio.sleep(3)
                    if 'login' not in page.url.lower():
                        logger.info(f"✓ Successfully navigated to: {page.url}")
                        break
                except:
                    continue
        
        await asyncio.sleep(5)
        
        # Take screenshot of dashboard
        await page.screenshot(path='/app/gofrugal-report-builder/logs/dashboard.png', full_page=True)
        logger.info("Dashboard screenshot saved")
        
        # Save dashboard HTML
        content = await page.content()
        with open('/app/gofrugal-report-builder/logs/dashboard.html', 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Try to find and click on Reports menu
        logger.info("Looking for Reports menu...")
        
        # Try multiple selectors
        report_selectors = [
            'text=Reports',
            'text=Report',
            'a:has-text("Reports")',
            'a:has-text("Report")',
            '[href*="report" i]',
            '[href*="Report"]',
            'span:has-text("Reports")',
            'li:has-text("Reports")',
            'div:has-text("Reports")',
        ]
        
        for selector in report_selectors:
            try:
                elements = await page.query_selector_all(selector)
                logger.info(f"Selector '{selector}': found {len(elements)} elements")
                
                for elem in elements:
                    text = await elem.inner_text()
                    if text and 'report' in text.lower():
                        logger.info(f"Found report element: {text}")
                        
                        # Try to click it
                        try:
                            await elem.click(timeout=3000)
                            await asyncio.sleep(3)
                            await page.screenshot(path='/app/gofrugal-report-builder/logs/after_report_click.png')
                            logger.info("Clicked on Reports menu")
                            break
                        except:
                            continue
            except:
                continue
        
        # Now try to search for Report 474 or Current Stock
        logger.info("Searching for Report 474 / Current Stock...")
        
        # Try searching in page
        search_terms = ['474', 'Current Stock', 'Stock Report', 'Inventory']
        
        for term in search_terms:
            try:
                # Try to find search box
                search_selectors = [
                    'input[type="search"]',
                    'input[placeholder*="search" i]',
                    'input[placeholder*="Search" i]',
                    'input[name*="search" i]',
                ]
                
                for search_sel in search_selectors:
                    try:
                        search_box = await page.query_selector(search_sel)
                        if search_box:
                            logger.info(f"Found search box, searching for: {term}")
                            await search_box.fill(term)
                            await asyncio.sleep(2)
                            await page.screenshot(path=f'/app/gofrugal-report-builder/logs/search_{term}.png')
                            break
                    except:
                        continue
                        
                # Try to find links with the search term
                links = await page.query_selector_all(f'text={term}')
                logger.info(f"Found {len(links)} links with text '{term}'")
                
                if links:
                    for link in links[:3]:  # Try first 3 matches
                        try:
                            await link.click(timeout=3000)
                            await asyncio.sleep(5)
                            await page.screenshot(path=f'/app/gofrugal-report-builder/logs/report_474_loaded.png', full_page=True)
                            logger.info(f"Clicked on: {term}")
                            
                            # Check if we have a table now
                            tables = await page.query_selector_all('table')
                            if tables:
                                logger.info(f"✓ Found {len(tables)} tables!")
                                
                                # Extract table data
                                for idx, table in enumerate(tables):
                                    # Get headers
                                    headers = []
                                    header_cells = await table.query_selector_all('th')
                                    for cell in header_cells:
                                        text = await cell.inner_text()
                                        headers.append(text.strip())
                                    
                                    if headers:
                                        logger.info(f"Table {idx+1} headers: {headers}")
                                        
                                        # Save to file
                                        with open(f'/app/gofrugal-report-builder/database/schemas/report_474_columns.json', 'w') as f:
                                            json.dump({
                                                'report_id': 474,
                                                'report_name': 'Current Stock',
                                                'columns': headers,
                                                'extracted_at': asyncio.get_event_loop().time()
                                            }, f, indent=2)
                                        
                                        return headers
                            
                            # Try to find download button
                            download_buttons = await page.query_selector_all('button:has-text("Download"), button:has-text("Export"), a:has-text("Download"), a:has-text("Export")')
                            if download_buttons:
                                logger.info(f"Found {len(download_buttons)} download buttons")
                                for btn in download_buttons:
                                    text = await btn.inner_text()
                                    logger.info(f"Download button: {text}")
                            
                            break
                        except Exception as e:
                            logger.error(f"Error clicking link: {e}")
                            continue
                            
            except Exception as e:
                logger.error(f"Error searching for {term}: {e}")
                continue
        
        # If we still haven't found it, list all links on the page
        logger.info("\n=== All links on dashboard ===")
        all_links = await page.query_selector_all('a')
        for i, link in enumerate(all_links[:50]):  # First 50 links
            try:
                text = await link.inner_text()
                href = await link.get_attribute('href')
                if text.strip():
                    logger.info(f"{i+1}. {text.strip()} -> {href}")
            except:
                continue
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await browser.close()
        await playwright.stop()


if __name__ == "__main__":
    asyncio.run(fetch_report_474())
