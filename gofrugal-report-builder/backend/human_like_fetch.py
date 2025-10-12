"""
Human-like browser automation to fetch Report 474
Acts like a real person using the browser
"""
import asyncio
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

username = os.getenv('GOFRUGAL_USERNAME')
password = os.getenv('GOFRUGAL_PASSWORD')

async def human_delay(min_ms=500, max_ms=1500):
    """Random delay to mimic human behavior"""
    import random
    delay = random.randint(min_ms, max_ms) / 1000
    await asyncio.sleep(delay)

async def main():
    logger.info("🤖 Starting human-like browser automation...")
    logger.info("="*80)
    
    async with async_playwright() as p:
        # Launch browser (headless in server environment, with slow_mo for human-like behavior)
        browser = await p.chromium.launch(
            headless=True,  # Must be headless in server environment
            slow_mo=500  # Slow down actions to be more human-like
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        # Track downloads
        download_promise = None
        downloaded_file = None
        
        try:
            # STEP 1: Navigate to login page
            logger.info("\n👤 Step 1: Opening GoFrugal portal...")
            await page.goto('https://bbcohq.gofrugal.com/RayMedi_HQ/index.do')
            await page.wait_for_load_state('networkidle')
            await human_delay(2000, 3000)
            
            # Take screenshot
            await page.screenshot(path='/app/gofrugal-report-builder/logs/step1_login_page.png')
            logger.info("   ✓ Login page loaded")
            
            # STEP 2: Fill username (like a human typing)
            logger.info("\n👤 Step 2: Entering username...")
            username_field = await page.wait_for_selector('input[name="j_username"]', timeout=10000)
            await username_field.click()
            await human_delay()
            await username_field.type(username, delay=100)  # Type with delay between keystrokes
            await human_delay()
            logger.info("   ✓ Username entered")
            
            # STEP 3: Fill password (like a human typing)
            logger.info("\n👤 Step 3: Entering password...")
            password_field = await page.wait_for_selector('input[name="j_password"]')
            await password_field.click()
            await human_delay()
            await password_field.type(password, delay=100)
            await human_delay()
            logger.info("   ✓ Password entered")
            
            # STEP 4: Click login button
            logger.info("\n👤 Step 4: Clicking login button...")
            await page.screenshot(path='/app/gofrugal-report-builder/logs/step2_before_login.png')
            
            login_button = await page.wait_for_selector('button[type="submit"]')
            await login_button.click()
            logger.info("   ⏳ Waiting for login to complete...")
            
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(5)  # Give extra time for any redirects
            
            await page.screenshot(path='/app/gofrugal-report-builder/logs/step3_after_login.png')
            logger.info("   ✓ Login completed")
            
            # STEP 5: Handle 2FA or any popup
            logger.info("\n👤 Step 5: Checking for popups...")
            try:
                # Look for any modal or popup
                modal = await page.wait_for_selector('.modal, [role="dialog"], .popup', timeout=3000)
                if modal:
                    logger.info("   ⚠️  Popup detected, looking for Skip/Close button...")
                    
                    # Try multiple ways to close it
                    close_buttons = [
                        'button:has-text("Skip")',
                        'button:has-text("Close")',
                        'button:has-text("Cancel")',
                        'button:has-text("Later")',
                        '[aria-label="Close"]',
                        '.close',
                        '.modal-close'
                    ]
                    
                    for selector in close_buttons:
                        try:
                            btn = await page.wait_for_selector(selector, timeout=2000)
                            if btn:
                                await btn.click()
                                logger.info(f"   ✓ Clicked: {selector}")
                                await asyncio.sleep(2)
                                break
                        except:
                            continue
            except:
                logger.info("   ✓ No popups detected")
            
            await page.screenshot(path='/app/gofrugal-report-builder/logs/step4_popups_handled.png')
            
            # STEP 6: Navigate to dashboard first (like a human would)
            logger.info("\n👤 Step 6: Going to dashboard...")
            current_url = page.url
            logger.info(f"   Current URL: {current_url}")
            
            # If not already on dashboard, navigate there
            if '#/dashboard' not in current_url:
                await page.goto('https://bbcohq.gofrugal.com/RayMedi_HQ/index.do#/dashboard')
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(3)
                logger.info("   ✓ Dashboard loaded")
            
            await page.screenshot(path='/app/gofrugal-report-builder/logs/step5_dashboard.png')
            
            # STEP 7: Navigate to Reports section
            logger.info("\n👤 Step 7: Opening Report 474...")
            
            # Navigate to the report URL
            await page.goto('https://bbcohq.gofrugal.com/RayMedi_HQ/index.do#/smartreport?reportId=474&productId=2&HQ_DEFA_ROLE_ID=2')
            logger.info("   ⏳ Waiting for report to load...")
            await page.wait_for_load_state('networkidle')
            await asyncio.sleep(5)  # Extra time for Angular to render
            
            await page.screenshot(path='/app/gofrugal-report-builder/logs/step6_report_page.png')
            logger.info("   ✓ Report page loaded")
            
            # STEP 8: Wait for report data to load
            logger.info("\n👤 Step 8: Waiting for report data...")
            await asyncio.sleep(5)
            
            # Look for any loading indicators to disappear
            try:
                await page.wait_for_selector('.loading, .spinner, [class*="loading"]', state='hidden', timeout=10000)
            except:
                pass
            
            await page.screenshot(path='/app/gofrugal-report-builder/logs/step7_report_loaded.png')
            logger.info("   ✓ Report data loaded")
            
            # STEP 9: Find and click export button
            logger.info("\n👤 Step 9: Looking for Export button...")
            
            # Save page content for inspection
            content = await page.content()
            with open('/app/gofrugal-report-builder/logs/report_page_content.html', 'w') as f:
                f.write(content)
            
            # Try to find export button with various methods
            export_clicked = False
            
            # Method 1: Look for visible buttons/links with "export" text
            try:
                logger.info("   Trying method 1: Looking for Export button...")
                elements = await page.query_selector_all('button, a, span, div')
                for element in elements:
                    text = await element.inner_text()
                    if text and 'export' in text.lower():
                        logger.info(f"   Found element with text: {text}")
                        try:
                            # Check if visible
                            is_visible = await element.is_visible()
                            if is_visible:
                                logger.info("   Clicking export element...")
                                await element.click()
                                export_clicked = True
                                await asyncio.sleep(3)
                                break
                        except Exception as e:
                            logger.debug(f"   Could not click: {e}")
            except Exception as e:
                logger.info(f"   Method 1 failed: {e}")
            
            # Method 2: Look in page HTML for export-related attributes
            if not export_clicked:
                logger.info("   Trying method 2: Looking in page structure...")
                try:
                    # Find elements with export in ng-click, onclick, etc.
                    export_elem = await page.evaluate('''() => {
                        const all = document.querySelectorAll('*');
                        for (let elem of all) {
                            const onclick = elem.getAttribute('ng-click') || elem.getAttribute('onclick') || '';
                            const title = elem.getAttribute('title') || '';
                            const text = elem.textContent || '';
                            
                            if (onclick.toLowerCase().includes('export') || 
                                title.toLowerCase().includes('export') ||
                                text.toLowerCase().includes('export')) {
                                return elem.outerHTML.substring(0, 200);
                            }
                        }
                        return null;
                    }''')
                    
                    if export_elem:
                        logger.info(f"   Found export element: {export_elem}")
                except Exception as e:
                    logger.info(f"   Method 2 failed: {e}")
            
            # Method 3: Try keyboard shortcut if exists
            if not export_clicked:
                logger.info("   Trying method 3: Checking for export in menus...")
                # Right-click to see context menu
                try:
                    await page.mouse.click(500, 500, button='right')
                    await asyncio.sleep(2)
                    await page.screenshot(path='/app/gofrugal-report-builder/logs/step8_context_menu.png')
                except:
                    pass
            
            # STEP 10: Manual inspection mode
            logger.info("\n👤 Step 10: Manual inspection mode...")
            logger.info("   📸 Screenshots saved in /app/gofrugal-report-builder/logs/")
            logger.info("   📄 HTML content saved to report_page_content.html")
            logger.info("\n   Please check the screenshots to see what's on screen.")
            logger.info("   The browser will stay open for 30 seconds for inspection...")
            
            # Keep browser open for inspection
            await asyncio.sleep(30)
            
            logger.info("\n   Closing browser...")
            await browser.close()
            
        except Exception as e:
            logger.error(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            
            await page.screenshot(path='/app/gofrugal-report-builder/logs/error_screenshot.png')
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
