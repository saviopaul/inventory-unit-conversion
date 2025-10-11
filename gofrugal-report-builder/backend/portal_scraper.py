"""
GoFrugal Portal Scraper
Automates login and extracts all available reports and their schemas
"""
import asyncio
import os
import json
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GoFrugalPortalScraper:
    def __init__(self):
        self.url = os.getenv('GOFRUGAL_URL')
        self.username = os.getenv('GOFRUGAL_USERNAME')
        self.password = os.getenv('GOFRUGAL_PASSWORD')
        self.browser = None
        self.context = None
        self.page = None
        
    async def initialize(self):
        """Initialize browser and context"""
        logger.info("Initializing browser...")
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        self.page = await self.context.new_page()
        logger.info("Browser initialized successfully")
        
    async def login(self):
        """Login to GoFrugal portal"""
        try:
            logger.info(f"Navigating to {self.url}")
            await self.page.goto(self.url, wait_until='networkidle', timeout=30000)
            
            # Take screenshot of login page
            await self.page.screenshot(path='/app/gofrugal-report-builder/logs/login_page.png')
            logger.info("Login page screenshot saved")
            
            # Wait a bit for page to fully load
            await asyncio.sleep(2)
            
            # Get page content to understand structure
            content = await self.page.content()
            
            # Try to find login form elements
            # Common patterns: input[name="username"], input[type="text"], input[id*="user"]
            username_selectors = [
                'input[name="username"]',
                'input[name="userName"]',
                'input[name="userid"]',
                'input[name="user"]',
                'input[type="text"]',
                'input[id*="user"]',
                'input[placeholder*="user" i]',
                'input[placeholder*="User" i]',
            ]
            
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[id*="pass"]',
                'input[placeholder*="password" i]',
            ]
            
            # Find username field
            username_field = None
            for selector in username_selectors:
                try:
                    username_field = await self.page.wait_for_selector(selector, timeout=2000)
                    if username_field:
                        logger.info(f"Found username field with selector: {selector}")
                        break
                except:
                    continue
                    
            if not username_field:
                logger.error("Could not find username field")
                # Save page HTML for debugging
                with open('/app/gofrugal-report-builder/logs/login_page.html', 'w') as f:
                    f.write(content)
                return False
                
            # Find password field
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = await self.page.wait_for_selector(selector, timeout=2000)
                    if password_field:
                        logger.info(f"Found password field with selector: {selector}")
                        break
                except:
                    continue
                    
            if not password_field:
                logger.error("Could not find password field")
                return False
            
            # Fill in credentials
            logger.info("Filling in credentials...")
            await username_field.fill(self.username)
            await password_field.fill(self.password)
            
            # Find and click login button
            login_button_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Sign In")',
                'a:has-text("Login")',
                '.login-button',
                '#loginButton',
            ]
            
            login_button = None
            for selector in login_button_selectors:
                try:
                    login_button = await self.page.wait_for_selector(selector, timeout=2000)
                    if login_button:
                        logger.info(f"Found login button with selector: {selector}")
                        break
                except:
                    continue
                    
            if login_button:
                logger.info("Clicking login button...")
                await login_button.click()
            else:
                # Try pressing Enter
                logger.info("No login button found, trying Enter key...")
                await password_field.press('Enter')
            
            # Wait for navigation after login
            await asyncio.sleep(5)
            
            # Take screenshot after login
            await self.page.screenshot(path='/app/gofrugal-report-builder/logs/after_login.png')
            logger.info("After login screenshot saved")
            
            # Check if login was successful
            current_url = self.page.url
            if 'login' not in current_url.lower() or current_url != self.url:
                logger.info(f"Login successful! Current URL: {current_url}")
                return True
            else:
                logger.warning("Login may have failed - still on login page")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            await self.page.screenshot(path='/app/gofrugal-report-builder/logs/login_error.png')
            return False
            
    async def discover_reports(self):
        """Discover all available reports in the portal"""
        try:
            logger.info("Discovering reports...")
            
            # Wait for page to load
            await asyncio.sleep(3)
            
            # Take screenshot of main page
            await self.page.screenshot(path='/app/gofrugal-report-builder/logs/main_page.png')
            
            # Look for Reports menu/section
            reports_selectors = [
                'a:has-text("Reports")',
                'a:has-text("Report")',
                'button:has-text("Reports")',
                '[href*="report"]',
                '.menu-item:has-text("Reports")',
            ]
            
            reports_menu = None
            for selector in reports_selectors:
                try:
                    reports_menu = await self.page.wait_for_selector(selector, timeout=3000)
                    if reports_menu:
                        logger.info(f"Found reports menu with selector: {selector}")
                        break
                except:
                    continue
                    
            if reports_menu:
                await reports_menu.click()
                await asyncio.sleep(3)
                await self.page.screenshot(path='/app/gofrugal-report-builder/logs/reports_page.png')
            else:
                logger.warning("Could not find Reports menu")
            
            # Get all links and buttons on page
            all_links = await self.page.query_selector_all('a, button')
            
            reports = []
            for link in all_links:
                try:
                    text = await link.inner_text()
                    href = await link.get_attribute('href') or ''
                    
                    # Look for report-like items
                    if any(keyword in text.lower() for keyword in ['report', 'stock', 'inventory', 'item', 'master', 'current']):
                        reports.append({
                            'text': text.strip(),
                            'href': href,
                            'type': 'link'
                        })
                except:
                    continue
            
            logger.info(f"Found {len(reports)} potential reports")
            
            # Save discovered reports
            with open('/app/gofrugal-report-builder/database/schemas/discovered_reports.json', 'w') as f:
                json.dump(reports, f, indent=2)
            
            return reports
            
        except Exception as e:
            logger.error(f"Error discovering reports: {str(e)}")
            return []
            
    async def extract_report_schema(self, report_id=None, report_url=None):
        """Extract schema from a specific report"""
        try:
            if report_id:
                logger.info(f"Extracting schema for Report ID: {report_id}")
                # Try to navigate to report by ID
                # Common patterns: /report?id=474, /reports/474, etc.
                possible_urls = [
                    f"{self.url}/report?id={report_id}",
                    f"{self.url}/reports/{report_id}",
                    f"{self.url}/report/{report_id}",
                    f"{self.url}/Report.aspx?ReportId={report_id}",
                ]
                
                for url in possible_urls:
                    try:
                        logger.info(f"Trying URL: {url}")
                        await self.page.goto(url, wait_until='networkidle', timeout=15000)
                        await asyncio.sleep(3)
                        
                        # Check if we got a valid page
                        if 'error' not in self.page.url.lower() and '404' not in await self.page.content():
                            logger.info(f"Successfully navigated to report at {url}")
                            break
                    except:
                        continue
                        
            elif report_url:
                logger.info(f"Navigating to report URL: {report_url}")
                await self.page.goto(report_url, wait_until='networkidle', timeout=15000)
                await asyncio.sleep(3)
            
            # Take screenshot
            screenshot_path = f'/app/gofrugal-report-builder/logs/report_{report_id or "custom"}.png'
            await self.page.screenshot(path=screenshot_path)
            logger.info(f"Report screenshot saved: {screenshot_path}")
            
            # Try to find table headers (common in reports)
            schema = {
                'report_id': report_id,
                'report_url': report_url or self.page.url,
                'extracted_at': datetime.now().isoformat(),
                'columns': []
            }
            
            # Look for table headers
            header_selectors = [
                'thead th',
                'table th',
                '.table-header',
                '.grid-header',
                '[role="columnheader"]',
            ]
            
            headers = []
            for selector in header_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        for elem in elements:
                            text = await elem.inner_text()
                            if text.strip():
                                headers.append(text.strip())
                        if headers:
                            break
                except:
                    continue
            
            if headers:
                logger.info(f"Found {len(headers)} columns: {headers}")
                schema['columns'] = headers
            else:
                logger.warning("Could not find table headers")
                
            # Try to get sample data
            try:
                rows = await self.page.query_selector_all('tbody tr')
                if rows and len(rows) > 0:
                    first_row = rows[0]
                    cells = await first_row.query_selector_all('td')
                    sample_data = []
                    for cell in cells:
                        sample_data.append(await cell.inner_text())
                    schema['sample_data'] = sample_data
                    logger.info(f"Sample data: {sample_data[:5]}...")
            except:
                pass
            
            return schema
            
        except Exception as e:
            logger.error(f"Error extracting report schema: {str(e)}")
            return None
            
    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
            logger.info("Browser closed")


async def main():
    """Main function to test the scraper"""
    scraper = GoFrugalPortalScraper()
    
    try:
        await scraper.initialize()
        
        # Login
        login_success = await scraper.login()
        if not login_success:
            logger.error("Login failed!")
            return
        
        # Discover reports
        reports = await scraper.discover_reports()
        logger.info(f"Discovered {len(reports)} reports")
        
        # Try to extract Report 474 (Current Stock)
        schema = await scraper.extract_report_schema(report_id=474)
        if schema:
            logger.info(f"Schema extracted: {json.dumps(schema, indent=2)}")
            
            # Save schema
            with open('/app/gofrugal-report-builder/database/schemas/report_474_schema.json', 'w') as f:
                json.dump(schema, f, indent=2)
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
