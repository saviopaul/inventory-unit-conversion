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
            
            # Step 5: Click Reports menu
            print("\n📊 Step 5: Click Reports menu")
            # Simple approach: just find any link with text "Reports"
            await asyncio.sleep(2)
            
            # Use JavaScript to click to avoid hover issues
            await page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll('a'));
                const reportsLink = links.find(link => link.textContent.trim() === 'Reports');
                if (reportsLink) {
                    reportsLink.click();
                    return true;
                }
                return false;
            }''')
            
            await asyncio.sleep(2)
            print("✅ Reports menu clicked")
            
            # Step 6: Navigate to Report 474
            print("\n📦 Step 6: Navigate to Report 474")
            print("   Clicking 'Current Stock - Item Wise Detail'...")
            
            # Wait for menu to expand
            await asyncio.sleep(2)
            
            # Use JavaScript to find and click the report link
            result = await page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll('a'));
                const reportLink = links.find(link => 
                    link.textContent.trim().includes('Current Stock - Item Wise Detail')
                );
                if (reportLink) {
                    reportLink.click();
                    return {success: true, url: reportLink.href};
                }
                return {success: false};
            }''')
            
            if result.get('success'):
                print(f"✅ Clicked report link: {result.get('url', 'unknown')[:80]}")
                await asyncio.sleep(7)
                await page.screenshot(path=f'{logs_dir}/pup_04_report_page.png')
                print("✅ Report page loaded")
            else:
                print("❌ Could not find report link")
                await page.screenshot(path=f'{logs_dir}/pup_error_no_report_link.png')
                return None
            
            # Step 7: Wait for iframe to load with actual content
            print("\n🔧 Step 7: Wait for report iframe to load")
            
            # Wait longer for the Angular app to load in the iframe
            max_waits = 15
            report_frame = None
            
            for attempt in range(max_waits):
                await asyncio.sleep(2)
                frames = page.frames
                print(f"   Attempt {attempt+1}: Found {len(frames)} frames")
                
                # Look for a frame with actual content (not about:blank)
                for i, frame in enumerate(frames):
                    frame_url = frame.url
                    if 'smartreport' in frame_url or 'reportsclient' in frame_url:
                        print(f"   Found report frame {i}: {frame_url[:80]}")
                        
                        # Check if it has the expected elements
                        try:
                            apply_btn = frame.locator('button:has-text("Apply")')
                            if await apply_btn.count() > 0:
                                report_frame = frame
                                print(f"✅ Report iframe loaded with content")
                                break
                        except:
                            pass
                
                if report_frame:
                    break
            
            if not report_frame:
                print("❌ Report iframe never loaded with content")
                await page.screenshot(path=f'{logs_dir}/pup_error_iframe_timeout.png')
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
