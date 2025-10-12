import asyncio
from playwright.async_api import async_playwright
import os

async def test_login():
    """Test login with credentials from Puppeteer recording"""
    print("🚀 Starting login test with recording credentials...")
    
    async with async_playwright() as p:
        # Launch browser in headless mode
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        try:
            # Navigate to login page
            print("📍 Navigating to login page...")
            await page.goto('https://bbcohq.gofrugal.com/RayMedi_HQ/mainIndex.do', 
                          wait_until='networkidle', 
                          timeout=60000)
            await asyncio.sleep(3)
            
            # Take screenshot of initial page
            await page.screenshot(path='/app/gofrugal-report-builder/logs/01_initial_page.png')
            print("✅ Initial page loaded")
            
            # Check if already logged in, logout if needed
            try:
                logout_button = page.locator('text=Signout').first
                if await logout_button.is_visible(timeout=3000):
                    print("⚠️ Already logged in, logging out first...")
                    await logout_button.click()
                    await asyncio.sleep(2)
            except:
                print("ℹ️ Not logged in, proceeding to login...")
            
            # Wait for login form
            print("⏳ Waiting for login form...")
            await page.wait_for_selector('#username', state='visible', timeout=10000)
            await asyncio.sleep(1)
            
            # Fill in credentials from recording
            print("🔑 Entering credentials...")
            await page.fill('#username', 'admin1')
            await page.fill('#password', 'De!!@88981')
            await asyncio.sleep(1)
            
            # Take screenshot before login
            await page.screenshot(path='/app/gofrugal-report-builder/logs/02_before_login.png')
            print("📸 Screenshot taken before login")
            
            # Click login button
            print("🔐 Clicking login button...")
            await page.click('button:has-text("Login")')
            
            # Wait for navigation after login
            print("⏳ Waiting for post-login navigation...")
            await asyncio.sleep(5)
            
            # Take screenshot after login
            await page.screenshot(path='/app/gofrugal-report-builder/logs/03_after_login.png')
            print("📸 Screenshot taken after login")
            
            # Check current URL
            current_url = page.url
            print(f"📍 Current URL: {current_url}")
            
            # Get page title
            title = await page.title()
            print(f"📄 Page Title: {title}")
            
            # Check for dashboard elements
            print("\n🔍 Checking for dashboard elements...")
            
            # Look for Reports menu (from recording)
            try:
                reports_menu = page.locator('text=Reports').first
                if await reports_menu.is_visible(timeout=5000):
                    print("✅ SUCCESS! 'Reports' menu is visible - Dashboard loaded!")
                    
                    # Take screenshot of dashboard
                    await page.screenshot(path='/app/gofrugal-report-builder/logs/04_dashboard_success.png')
                    
                    # Try to get HTML of the page
                    html_content = await page.content()
                    with open('/app/gofrugal-report-builder/logs/dashboard_html.html', 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    print("✅ Dashboard HTML saved")
                    
                    return True
                else:
                    print("❌ 'Reports' menu not visible")
                    return False
            except Exception as e:
                print(f"❌ Error checking for dashboard elements: {str(e)}")
                
                # Check if still on login page
                try:
                    if await page.locator('#username').is_visible(timeout=2000):
                        print("❌ FAILED - Still on login page!")
                        
                        # Check for error messages
                        error_messages = await page.locator('.error, .alert, .message').all_text_contents()
                        if error_messages:
                            print(f"⚠️ Error messages found: {error_messages}")
                    else:
                        print("❓ Unknown state - not on login page, but no dashboard elements found")
                except:
                    pass
                
                return False
            
        except Exception as e:
            print(f"❌ Error during login test: {str(e)}")
            await page.screenshot(path='/app/gofrugal-report-builder/logs/error_screenshot.png')
            return False
        finally:
            print("\n⏳ Keeping browser open for 10 seconds for inspection...")
            await asyncio.sleep(10)
            await browser.close()
            print("🏁 Browser closed")

if __name__ == "__main__":
    result = asyncio.run(test_login())
    print(f"\n{'='*50}")
    print(f"FINAL RESULT: {'✅ SUCCESS' if result else '❌ FAILED'}")
    print(f"{'='*50}")
