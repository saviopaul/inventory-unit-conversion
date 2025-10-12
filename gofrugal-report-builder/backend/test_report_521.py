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
                
                if attempt == 0:
                    print(f"   Attempt {attempt+1}: Found {len(frames)} frames")
                
                for i, frame in enumerate(frames):
                    frame_url = frame.url
                    if 'smartreport' in frame_url or 'reportsclient' in frame_url:
                        if attempt == 0:
                            print(f"   Checking frame {i}: {frame_url[:80]}")
                        
                        # Try multiple selectors to find the report content
                        try:
                            # Check for various elements that indicate the report is loaded
                            has_content = False
                            
                            # Check for buttons
                            button_count = await frame.locator('button').count()
                            if button_count > 0:
                                has_content = True
                                if attempt % 3 == 0:  # Print every 3 attempts
                                    print(f"   Attempt {attempt+1}: Frame {i} has {button_count} buttons")
                            
                            # Check for main content div
                            main_content = await frame.locator('#filtersPanel, .filter-panel, .main-content, sr-sidebar').count()
                            if main_content > 0:
                                has_content = True
                                if attempt % 3 == 0:
                                    print(f"   Attempt {attempt+1}: Frame {i} has main content elements")
                            
                            if has_content:
                                report_frame = frame
                                print(f"✅ Report iframe loaded (frame {i}) after {attempt+1} attempts")
                                break
                        except Exception as e:
                            if attempt == 0:
                                print(f"   Error checking frame {i}: {str(e)[:50]}")
                
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
            
            # Try different selectors for Apply button
            apply_clicked = False
            try:
                apply_btn = report_frame.locator('button:has-text("Apply")').first
                if await apply_btn.is_visible(timeout=3000):
                    await apply_btn.click()
                    apply_clicked = True
                    print("   Apply button clicked")
            except:
                pass
            
            # Try alternate selector
            if not apply_clicked:
                try:
                    apply_btn = await report_frame.evaluate('''() => {
                        const buttons = Array.from(document.querySelectorAll('button'));
                        const applyBtn = buttons.find(btn => btn.textContent.trim() === 'Apply');
                        if (applyBtn) {
                            applyBtn.click();
                            return true;
                        }
                        return false;
                    }''')
                    if apply_btn:
                        apply_clicked = True
                        print("   Apply button clicked (JavaScript)")
                except:
                    pass
            
            if apply_clicked:
                await asyncio.sleep(8)
                await page.screenshot(path=f'{logs_dir}/r521_03_after_apply.png')
                print("✅ Filters applied")
            else:
                print("⚠️ Apply button not found, continuing...")
                await page.screenshot(path=f'{logs_dir}/r521_03_no_apply.png')
            
            # Step 6: Try Export
            print("\n💾 Step 7: Attempting export")
            await asyncio.sleep(3)
            await page.screenshot(path=f'{logs_dir}/r521_04_before_export.png')
            
            # List all available buttons first
            try:
                all_buttons = await report_frame.evaluate('''() => {
                    return Array.from(document.querySelectorAll('button, a, [role="button"]')).map(btn => ({
                        text: btn.textContent.trim(),
                        id: btn.id,
                        class: btn.className
                    }));
                }''')
                print(f"   Available buttons/links: {len(all_buttons)}")
                for btn in all_buttons:
                    if any(word in btn['text'].lower() for word in ['export', 'download', 'csv', 'excel']):
                        print(f"     - {btn['text'][:40]} (id: {btn['id']}, class: {btn['class'][:30]})")
            except:
                pass
            
            # Try clicking export button
            export_clicked = False
            
            # Method 1: Export as CSV button
            try:
                export_btn = report_frame.locator('button:has-text("Export as CSV"), button:has-text("Export")').first
                if await export_btn.is_visible(timeout=3000):
                    print("   Method 1: Clicking export button...")
                    # Set up download listener
                    download_promise = page.wait_for_event('download', timeout=20000)
                    await export_btn.click()
                    export_clicked = True
                    
                    # Try to get download
                    try:
                        download = await download_promise
                        timestamp = time.strftime("%Y%m%d_%H%M%S")
                        suggested = download.suggested_filename
                        ext = suggested.split('.')[-1] if '.' in suggested else 'xls'
                        filename = f"report_521_{timestamp}.{ext}"
                        filepath = os.path.join(download_dir, filename)
                        await download.save_as(filepath)
                        print(f"✅ Downloaded: {filepath}")
                        if os.path.exists(filepath):
                            print(f"✅ File verified: {os.path.getsize(filepath)} bytes")
                            return filepath
                    except asyncio.TimeoutError:
                        print("   Method 1: No immediate download, checking for dialog...")
            except Exception as e:
                print(f"   Method 1 failed: {str(e)[:50]}")
            
            # Method 2: Look for export icon/link
            if not export_clicked:
                try:
                    export_elem = report_frame.locator('#export, [id*="export"], [class*="export"]').first
                    if await export_elem.is_visible(timeout=3000):
                        print("   Method 2: Clicking export element...")
                        await export_elem.click()
                        await asyncio.sleep(2)
                        await page.screenshot(path=f'{logs_dir}/r521_05_after_export_click.png')
                        
                        # Look for download/confirm button
                        confirm_buttons = await report_frame.locator('button').all()
                        for btn in confirm_buttons:
                            btn_text = await btn.text_content()
                            if any(word in btn_text.lower() for word in ['download', 'ok', 'confirm', 'export']):
                                print(f"   Found confirm button: {btn_text[:30]}")
                                download_promise = page.wait_for_event('download', timeout=15000)
                                await btn.click()
                                try:
                                    download = await download_promise
                                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                                    filename = f"report_521_{timestamp}.xls"
                                    filepath = os.path.join(download_dir, filename)
                                    await download.save_as(filepath)
                                    print(f"✅ Downloaded: {filepath}")
                                    return filepath
                                except:
                                    pass
                except Exception as e:
                    print(f"   Method 2 failed: {str(e)[:50]}")
            
            print("❌ Could not trigger export/download")
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
