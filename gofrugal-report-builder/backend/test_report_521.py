import asyncio
from playwright.async_api import async_playwright
import os
from pathlib import Path
import time

async def fetch_report_521():
    """
    Try fetching Report 521 instead of 474
    """
    print("="*60)
    print("🚀 Testing Report 521 Automation")
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
            # Step 1: Navigate and Login
            print("\n📍 Step 1: Navigate to login page")
            await page.goto('https://bbcohq.gofrugal.com/RayMedi_HQ/mainIndex.do',
                          wait_until='networkidle', timeout=60000)
            await asyncio.sleep(2)
            
            # Check if already logged in, logout if needed
            try:
                frames = page.frames
                for frame in frames:
                    try:
                        signout = frame.locator('text=Signout').first
                        if await signout.is_visible(timeout=2000):
                            print("   Logging out...")
                            await signout.click()
                            await asyncio.sleep(2)
                            break
                    except:
                        continue
            except:
                pass
            
            # Login
            print("\n🔑 Step 2: Login")
            await page.wait_for_selector('#username', state='visible', timeout=10000)
            await page.fill('#username', 'admin1')
            await page.fill('#password', 'De!!@88981')
            await asyncio.sleep(1)
            
            await page.click('button:has-text("Login")')
            await page.wait_for_load_state('networkidle', timeout=30000)
            await asyncio.sleep(5)
            await page.screenshot(path=f'{logs_dir}/r521_01_after_login.png')
            print("✅ Logged in")
            
            # Step 2: Navigate directly to Report 521
            print("\n📦 Step 3: Navigating to Report 521")
            report_url = f'https://bbcohq.gofrugal.com/RayMedi_HQ/mainIndex.do?page=%2Fsmartreport%2Findex.html%23%2Freports%3FreportId%3D521%26productId%3D5'
            await page.goto(report_url, wait_until='networkidle', timeout=60000)
            await asyncio.sleep(7)
            await page.screenshot(path=f'{logs_dir}/r521_02_report_page.png')
            print("✅ Report 521 page loaded")
            
            # Step 3: Wait for iframe to load
            print("\n🔧 Step 4: Wait for report iframe")
            max_waits = 15
            report_frame = None
            
            for attempt in range(max_waits):
                await asyncio.sleep(2)
                frames = page.frames
                print(f"   Attempt {attempt+1}: Found {len(frames)} frames")
                
                for i, frame in enumerate(frames):
                    frame_url = frame.url
                    if 'smartreport' in frame_url or 'reportsclient' in frame_url:
                        print(f"   Checking frame {i}: {frame_url[:80]}")
                        
                        try:
                            apply_btn = frame.locator('button:has-text("Apply")')
                            if await apply_btn.count() > 0:
                                report_frame = frame
                                print(f"✅ Report iframe loaded")
                                break
                        except:
                            pass
                
                if report_frame:
                    break
            
            if not report_frame:
                print("❌ Report iframe not found")
                return None
            
            # Step 4: Check what filters are available
            print("\n🔍 Step 5: Checking available filters")
            await asyncio.sleep(2)
            
            # Try to get filter information
            try:
                filter_info = await report_frame.evaluate('''() => {
                    const filters = Array.from(document.querySelectorAll('input, select, [placeholder]'));
                    return filters.map(f => ({
                        tag: f.tagName,
                        type: f.type,
                        placeholder: f.placeholder,
                        name: f.name,
                        id: f.id,
                        required: f.required
                    }));
                }''')
                print(f"   Found {len(filter_info)} input/select elements")
                for i, f in enumerate(filter_info[:5]):  # Show first 5
                    print(f"     {i+1}. {f}")
            except:
                pass
            
            # Step 5: Try clicking Apply directly (some reports don't need filters)
            print("\n✅ Step 6: Applying filters")
            await asyncio.sleep(2)
            
            apply_btn = report_frame.locator('button:has-text("Apply")').first
            if await apply_btn.is_visible(timeout=5000):
                await apply_btn.click()
                await asyncio.sleep(8)
                await page.screenshot(path=f'{logs_dir}/r521_03_after_apply.png')
                print("✅ Filters applied")
            
            # Step 6: Try Export
            print("\n💾 Step 7: Attempting export")
            await asyncio.sleep(3)
            
            # Set up download listener BEFORE clicking export
            download_promise = page.wait_for_event('download', timeout=20000)
            
            # Try clicking export button
            export_clicked = False
            
            # Method 1: Export as CSV button
            try:
                export_btn = report_frame.locator('button:has-text("Export as CSV")').first
                if await export_btn.is_visible(timeout=3000):
                    print("   Clicking 'Export as CSV' button...")
                    await export_btn.click()
                    export_clicked = True
            except:
                pass
            
            # Method 2: Look for #export element
            if not export_clicked:
                try:
                    export_icon = report_frame.locator('#export').first
                    if await export_icon.is_visible(timeout=3000):
                        print("   Clicking export icon...")
                        await export_icon.click()
                        await asyncio.sleep(2)
                        
                        # Now click download button
                        download_btn = report_frame.locator('button').filter(has_text="Download").first
                        if await download_btn.is_visible(timeout=3000):
                            await download_btn.click()
                            export_clicked = True
                except:
                    pass
            
            if not export_clicked:
                print("❌ Could not trigger export")
                await page.screenshot(path=f'{logs_dir}/r521_error_no_export.png')
                return None
            
            # Wait for download
            print("⏳ Waiting for download...")
            try:
                download = await download_promise
                
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                suggested_filename = download.suggested_filename
                extension = suggested_filename.split('.')[-1] if '.' in suggested_filename else 'xls'
                filename = f"report_521_{timestamp}.{extension}"
                filepath = os.path.join(download_dir, filename)
                
                await download.save_as(filepath)
                print(f"✅ Downloaded: {filepath}")
                
                if os.path.exists(filepath):
                    file_size = os.path.getsize(filepath)
                    print(f"✅ File verified: {file_size} bytes")
                    return filepath
                else:
                    print("❌ File not found")
                    return None
                    
            except asyncio.TimeoutError:
                print("❌ Download timeout - export button might not trigger download")
                await page.screenshot(path=f'{logs_dir}/r521_error_download_timeout.png')
                
                # Check if there's an error message
                try:
                    error_msg = await report_frame.evaluate('''() => {
                        const alerts = Array.from(document.querySelectorAll('.alert, .error, .warning, [role="alert"]'));
                        return alerts.map(a => a.textContent.trim());
                    }''')
                    if error_msg:
                        print(f"   Error messages found: {error_msg}")
                except:
                    pass
                
                return None
                
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            await page.screenshot(path=f'{logs_dir}/r521_error.png')
            return None
        finally:
            await browser.close()
            print("\n🏁 Browser closed")

async def main():
    print("\n" + "="*60)
    print("Testing Report 521 Export")
    print("="*60 + "\n")
    
    result = await fetch_report_521()
    
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
