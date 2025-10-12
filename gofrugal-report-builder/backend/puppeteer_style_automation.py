import asyncio
from playwright.async_api import async_playwright
import os
from pathlib import Path
import time

async def fetch_report_474_puppeteer_style():
    """
    Replicate the exact Puppeteer recording flow using Playwright
    """
    print("="*60)
    print("🚀 Starting Puppeteer-Style Automation")
    print("="*60)
    
    download_dir = "/app/gofrugal-report-builder/downloads"
    logs_dir = "/app/gofrugal-report-builder/logs"
    Path(download_dir).mkdir(parents=True, exist_ok=True)
    Path(logs_dir).mkdir(parents=True, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            accept_downloads=True
        )
        page = await context.new_page()
        
        try:
            # Step 1: Navigate to mainIndex
            print("\n📍 Step 1: Navigate to main page")
            await page.goto('https://bbcohq.gofrugal.com/RayMedi_HQ/mainIndex.do',
                          wait_until='networkidle', timeout=60000)
            await asyncio.sleep(2)
            await page.screenshot(path=f'{logs_dir}/pup_01_main_page.png')
            
            # Step 2: Check if logged in, logout if needed
            print("\n🚪 Step 2: Check login status")
            try:
                # Look for Signout in iframe
                frames = page.frames
                for frame in frames:
                    try:
                        signout = frame.locator('text=Signout').first
                        if await signout.is_visible(timeout=2000):
                            print("   Already logged in, signing out...")
                            await signout.click()
                            await asyncio.sleep(2)
                            break
                    except:
                        continue
            except:
                print("   Not logged in")
            
            # Step 3: Fill credentials
            print("\n🔑 Step 3: Enter credentials")
            await page.wait_for_selector('#username', state='visible', timeout=10000)
            await page.fill('#username', 'admin1')
            await page.fill('#password', 'De!!@88981')
            await asyncio.sleep(1)
            await page.screenshot(path=f'{logs_dir}/pup_02_before_login.png')
            
            # Step 4: Click Login
            print("\n🔐 Step 4: Click Login")
            await page.click('button:has-text("Login")')
            await page.wait_for_load_state('networkidle', timeout=30000)
            await asyncio.sleep(5)
            await page.screenshot(path=f'{logs_dir}/pup_03_after_login.png')
            print("✅ Logged in")
            
            # Step 5: Click Reports menu - use JavaScript to ensure it's visible
            print("\n📊 Step 5: Click Reports menu")
            # The Reports link is in the menu structure
            # From recording: div > ul > li:nth-of-type(5) > a with text "Reports"
            await page.eval_on_selector(
                'nav.menu-item-navbar li:nth-of-type(5) > a:has-text("Reports")',
                'el => el.scrollIntoView()'
            )
            await asyncio.sleep(1)
            reports_link = page.locator('nav.menu-item-navbar li:nth-of-type(5) > a').first
            await reports_link.click()
            await asyncio.sleep(2)
            print("✅ Reports menu clicked")
            
            # Step 6: Navigate menu hierarchy: Inventory -> Current Stock -> Current Stock - Item Wise Detail
            print("\n📦 Step 6: Navigate to Report 474")
            
            # The nested menu appears on hover/click
            # From recording selectors:
            # Inventory: li:nth-of-type(5) li:nth-of-type(3) > a
            # Current Stock: same path with li:nth-of-type(2)
            # Current Stock - Item Wise Detail: adds li:nth-of-type(5)
            
            #Instead, let's try clicking by text with retries
            print("   Clicking 'Current Stock - Item Wise Detail'...")
            
            # Wait a bit for menu to expand
            await asyncio.sleep(1)
            
            # Try to find and click the exact menu item
            target_link = page.locator('a:has-text("Current Stock - Item Wise Detail")').first
            await target_link.wait_for(state='attached', timeout=10000)
            await target_link.scroll_into_view_if_needed()
            await asyncio.sleep(1)
            await target_link.click()
            await asyncio.sleep(5)
            await page.screenshot(path=f'{logs_dir}/pup_04_report_page.png')
            print("✅ Report page loaded")
            
            # Step 7: Work with iframe
            print("\n🔧 Step 7: Access report iframe")
            await asyncio.sleep(3)
            
            frames = page.frames
            print(f"   Found {len(frames)} frames")
            
            # Frame 1 should have the report based on Puppeteer recording
            report_frame = None
            if len(frames) > 1:
                report_frame = frames[1]  # Index 1 from recording
                print(f"   Using frame 1: {report_frame.url[:80]}")
            
            if not report_frame:
                print("❌ No iframe found")
                return None
            
            # Step 8: Apply filters
            print("\n🔍 Step 8: Apply filters")
            await asyncio.sleep(2)
            
            # Click Apply button (from recording: #filtersPanel button.btn-primary)
            apply_btn = report_frame.locator('#filtersPanel button.btn-primary').first
            if await apply_btn.is_visible(timeout=5000):
                await apply_btn.click()
                await asyncio.sleep(3)
                await page.screenshot(path=f'{logs_dir}/pup_05_after_apply.png')
                print("✅ Filters applied")
            else:
                print("⚠️ Apply button not found, continuing...")
            
            # Step 9: Export
            print("\n💾 Step 9: Export report")
            
            # Click export icon (#export i)
            export_icon = report_frame.locator('#export i').first
            if await export_icon.is_visible(timeout=5000):
                await export_icon.click()
                await asyncio.sleep(2)
                print("✅ Export menu opened")
                
                # Click export button (from recording: sr-sidebar div:nth-of-type(2) button)
                print("⏳ Initiating download...")
                
                async with page.expect_download() as download_info:
                    export_btn = report_frame.locator('sr-sidebar div:nth-of-type(2) button').first
                    await export_btn.click()
                    await asyncio.sleep(2)
                
                download = await download_info.value
                
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"report_474_{timestamp}.xls"
                filepath = os.path.join(download_dir, filename)
                
                await download.save_as(filepath)
                print(f"✅ Downloaded: {filepath}")
                
                if os.path.exists(filepath):
                    file_size = os.path.getsize(filepath)
                    print(f"✅ File verified: {file_size} bytes")
                    return filepath
                else:
                    print("❌ File not found after download")
                    return None
            else:
                print("❌ Export icon not found")
                await page.screenshot(path=f'{logs_dir}/pup_error_no_export.png')
                return None
                
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            await page.screenshot(path=f'{logs_dir}/pup_error.png')
            return None
        finally:
            await browser.close()
            print("\n🏁 Browser closed")

async def main():
    print("\n" + "="*60)
    print("Testing Puppeteer-Style Automation")
    print("="*60 + "\n")
    
    result = await fetch_report_474_puppeteer_style()
    
    print("\n" + "="*60)
    if result:
        print(f"✅ SUCCESS! Report: {result}")
    else:
        print("❌ FAILED")
    print("="*60 + "\n")
    
    return result

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
