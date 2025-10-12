import asyncio
from playwright.async_api import async_playwright
import os
from pathlib import Path
import time

class GoFrugalReportFetcher:
    """Complete automation for GoFrugal Report 474 fetching"""
    
    def __init__(self):
        self.base_url = "https://bbcohq.gofrugal.com"
        self.username = "admin1"
        self.password = "De!!@88981"
        self.download_dir = "/app/gofrugal-report-builder/downloads"
        self.logs_dir = "/app/gofrugal-report-builder/logs"
        
        # Create directories
        Path(self.download_dir).mkdir(parents=True, exist_ok=True)
        Path(self.logs_dir).mkdir(parents=True, exist_ok=True)
    
    async def fetch_report_474(self, location="Bandra Provenance"):
        """
        Complete flow to fetch Report 474
        
        Args:
            location: Store location to filter by (default: "Bandra Provenance")
        
        Returns:
            Path to downloaded file or None if failed
        """
        print("="*60)
        print("🚀 Starting GoFrugal Report 474 Automation")
        print("="*60)
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            # Create context with download path
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                accept_downloads=True
            )
            
            page = await context.new_page()
            
            try:
                # Step 1: Navigate and Login
                print("\n📍 Step 1: Navigating to login page...")
                await page.goto(f'{self.base_url}/RayMedi_HQ/mainIndex.do', 
                              wait_until='networkidle', 
                              timeout=60000)
                await asyncio.sleep(2)
                await page.screenshot(path=f'{self.logs_dir}/auto_01_login_page.png')
                print("✅ Login page loaded")
                
                # Check if already logged in
                try:
                    logout_btn = page.locator('text=Signout').first
                    if await logout_btn.is_visible(timeout=2000):
                        print("⚠️ Already logged in, logging out...")
                        await logout_btn.click()
                        await asyncio.sleep(2)
                except:
                    pass
                
                # Fill credentials
                print("\n🔑 Step 2: Entering credentials...")
                await page.wait_for_selector('#username', state='visible', timeout=10000)
                await page.fill('#username', self.username)
                await page.fill('#password', self.password)
                await asyncio.sleep(1)
                
                # Click login
                print("🔐 Logging in...")
                await page.click('button:has-text("Login")')
                
                # Wait for navigation to complete
                print("⏳ Waiting for dashboard to load...")
                await page.wait_for_load_state('networkidle', timeout=30000)
                await asyncio.sleep(5)
                await page.screenshot(path=f'{self.logs_dir}/auto_02_after_login.png')
                print("✅ Logged in successfully")
                
                # Step 2: Navigate to Reports
                print("\n📊 Step 3: Navigating to Reports menu...")
                # Wait for navigation bar to be ready
                nav_bar = page.locator('nav').first
                await nav_bar.wait_for(state='visible', timeout=10000)
                
                # Find and click Reports menu
                reports_menu = page.locator('nav a:has-text("Reports")').first
                await reports_menu.wait_for(state='visible', timeout=10000)
                await reports_menu.click()
                await asyncio.sleep(2)
                print("✅ Reports menu clicked")
                
                # Navigate to Inventory -> Current Stock -> Current Stock - Item Wise Detail
                print("\n📦 Step 4: Navigating to Report 474...")
                
                # Click Inventory
                inventory_menu = page.locator('a:has-text("Inventory")').first
                await inventory_menu.wait_for(state='visible', timeout=5000)
                await inventory_menu.click()
                await asyncio.sleep(1)
                
                # Click Current Stock
                current_stock_menu = page.locator('a:has-text("Current Stock")').first
                await current_stock_menu.wait_for(state='visible', timeout=5000)
                await current_stock_menu.click()
                await asyncio.sleep(1)
                
                # Click Current Stock - Item Wise Detail (Report 474)
                report_474_link = page.locator('a:has-text("Current Stock - Item Wise Detail")').first
                await report_474_link.wait_for(state='visible', timeout=5000)
                await report_474_link.click()
                await asyncio.sleep(3)
                await page.screenshot(path=f'{self.logs_dir}/auto_03_report_page.png')
                print("✅ Report 474 page loaded")
                
                # Step 3: Work with iframe (report loads in iframe)
                print("\n🔧 Step 5: Accessing report iframe...")
                await asyncio.sleep(2)
                
                # Get all frames
                frames = page.frames
                print(f"   Found {len(frames)} frames")
                
                # Find the report frame (usually index 1)
                report_frame = None
                for i, frame in enumerate(frames):
                    try:
                        # Check if this frame has the Apply button
                        apply_btn = frame.locator('button:has-text("Apply")').first
                        if await apply_btn.is_visible(timeout=1000):
                            report_frame = frame
                            print(f"✅ Found report frame at index {i}")
                            break
                    except:
                        continue
                
                if not report_frame:
                    print("❌ Could not find report frame")
                    return None
                
                # Step 4: Apply filters
                print("\n🔍 Step 6: Applying filters...")
                await asyncio.sleep(1)
                
                # Click Apply button first time
                apply_button = report_frame.locator('button:has-text("Apply")').first
                await apply_button.click()
                await asyncio.sleep(3)
                await page.screenshot(path=f'{self.logs_dir}/auto_04_after_apply.png')
                print("✅ Filters applied")
                
                # Step 5: Export report
                print("\n💾 Step 7: Exporting report...")
                
                # Click export icon
                export_icon = report_frame.locator('#export i').first
                await export_icon.wait_for(state='visible', timeout=5000)
                await export_icon.click()
                await asyncio.sleep(1)
                print("✅ Export menu opened")
                
                # Click export button (this triggers download)
                print("⏳ Initiating download...")
                
                # Set up download promise before clicking
                async with page.expect_download() as download_info:
                    export_button = report_frame.locator('sr-sidebar div:nth-of-type(2) button').first
                    await export_button.click()
                    await asyncio.sleep(2)
                
                # Get download
                download = await download_info.value
                
                # Generate filename with timestamp
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"report_474_{timestamp}.xls"
                filepath = os.path.join(self.download_dir, filename)
                
                # Save download
                await download.save_as(filepath)
                print(f"✅ Report downloaded: {filepath}")
                
                # Verify file exists
                if os.path.exists(filepath):
                    file_size = os.path.getsize(filepath)
                    print(f"✅ File verified: {file_size} bytes")
                    
                    await page.screenshot(path=f'{self.logs_dir}/auto_05_success.png')
                    
                    return filepath
                else:
                    print("❌ Download failed - file not found")
                    return None
                    
            except Exception as e:
                print(f"\n❌ Error during automation: {str(e)}")
                await page.screenshot(path=f'{self.logs_dir}/auto_error.png')
                
                # Get page content for debugging
                try:
                    html_content = await page.content()
                    with open(f'{self.logs_dir}/auto_error.html', 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    print("   Debug info saved to auto_error.html")
                except:
                    pass
                
                return None
            finally:
                await browser.close()
                print("\n🏁 Browser closed")

async def main():
    """Test the complete automation"""
    fetcher = GoFrugalReportFetcher()
    
    print("\n" + "="*60)
    print("Testing GoFrugal Report 474 Automation")
    print("="*60 + "\n")
    
    result = await fetcher.fetch_report_474()
    
    print("\n" + "="*60)
    if result:
        print(f"✅ SUCCESS! Report downloaded to: {result}")
    else:
        print("❌ FAILED - Could not download report")
    print("="*60 + "\n")
    
    return result

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
