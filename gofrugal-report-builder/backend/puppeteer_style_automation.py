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
            
            # Step 8: Fill mandatory fields and apply filters
            print("\n🔍 Step 8: Fill mandatory fields")
            await asyncio.sleep(2)
            
            # Select outlet (mandatory field)
            print("   Selecting outlet...")
            try:
                # Look for the outlet dropdown/selector
                outlet_field = report_frame.locator('input[placeholder*="Choose Outlet"], select[name*="outlet"], #outlet').first
                if await outlet_field.is_visible(timeout=3000):
                    await outlet_field.click()
                    await asyncio.sleep(1)
                    
                    # Type "Bandra" to filter options
                    await outlet_field.fill("Bandra")
                    await asyncio.sleep(1)
                    
                    # Select from dropdown (try multiple methods)
                    try:
                        bandra_option = report_frame.locator('text=Bandra Provenance').first
                        if await bandra_option.is_visible(timeout=2000):
                            await bandra_option.click()
                            print("✅ Selected 'Bandra Provenance'")
                    except:
                        # Try JavaScript selection
                        await report_frame.evaluate('''() => {
                            const options = Array.from(document.querySelectorAll('li, option'));
                            const bandraOption = options.find(opt => opt.textContent.includes('Bandra'));
                            if (bandraOption) bandraOption.click();
                        }''')
                        print("✅ Selected outlet via JavaScript")
                    
                    await asyncio.sleep(1)
            except Exception as e:
                print(f"   ⚠️ Could not select outlet: {str(e)[:50]}")
            
            # Now apply filters
            print("   Applying filters...")
            await asyncio.sleep(1)
            
            # Click Apply button
            apply_btn = report_frame.locator('button:has-text("Apply")').first
            if await apply_btn.is_visible(timeout=5000):
                await apply_btn.click()
                await asyncio.sleep(5)
                await page.screenshot(path=f'{logs_dir}/pup_05_after_apply.png')
                print("✅ Filters applied")
            else:
                print("⚠️ Apply button not found")
            
            # Step 9: Wait for data to load
            print("\n⏳ Step 9: Waiting for report data to load...")
            # Wait longer for data to populate
            await asyncio.sleep(8)
            await page.screenshot(path=f'{logs_dir}/pup_05b_data_loaded.png')
            
            # Step 10: Export
            print("\n💾 Step 10: Export report")
            
            # The "Export as CSV" button should directly trigger download
            # Based on puppeteer recording, clicking export icon, then clicking download button
            
            try:
                # Look for export element in the right panel/toolbar
                # From the Puppeteer recording: #export is the container
                export_container = report_frame.locator('#export').first
                if not await export_container.is_visible(timeout=3000):
                    print("❌ Export container not visible, trying alternate method...")
                    # Try clicking "Export as CSV" button in sidebar
                    export_csv_btn = report_frame.locator('button:has-text("Export as CSV")').first
                    await export_csv_btn.click()
                    await asyncio.sleep(2)
                else:
                    # Click the export icon within the container
                    export_icon = report_frame.locator('#export i, #export a, #export button').first
                    await export_icon.click()
                    await asyncio.sleep(2)
                    print("✅ Export menu opened")
                
                await page.screenshot(path=f'{logs_dir}/pup_06_export_clicked.png')
                
                # Now look for the download button (from recording: sr-sidebar div:nth-of-type(2) button)
                print("⏳ Looking for download button...")
                
                # Set up download listener
                download_promise = page.wait_for_event('download', timeout=15000)
                
                # Try multiple selectors for the download button
                download_triggered = False
                
                #Try 1: Recording selector
                try:
                    download_btn = report_frame.locator('sr-sidebar div button, sr-sidebar button').first
                    if await download_btn.is_visible(timeout=2000):
                        await download_btn.click()
                        download_triggered = True
                        print("✅ Download button clicked (recording selector)")
                except:
                    pass
                
                # Try 2: Any visible button after export was clicked
                if not download_triggered:
                    try:
                        # Look for buttons that appeared after clicking export
                        all_buttons = await report_frame.locator('button').all()
                        for btn in all_buttons:
                            if await btn.is_visible():
                                btn_text = await btn.text_content()
                                if any(word in btn_text.lower() for word in ['download', 'export', 'ok', 'confirm', 'csv']):
                                    await btn.click()
                                    download_triggered = True
                                    print(f"✅ Download button clicked: {btn_text[:30]}")
                                    break
                    except:
                        pass
                
                if not download_triggered:
                    print("❌ Could not find download button")
                    await page.screenshot(path=f'{logs_dir}/pup_error_no_download_btn.png')
                    return None
                
                # Wait for download to complete
                print("⏳ Waiting for download...")
                download = await download_promise
                
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
                    
            except Exception as e:
                print(f"❌ Export/Download failed: {str(e)}")
                await page.screenshot(path=f'{logs_dir}/pup_error_export_failed.png')
                
                # Debug info
                try:
                    html = await report_frame.content()
                    with open(f'{logs_dir}/pup_frame_html_debug.html', 'w', encoding='utf-8') as f:
                        f.write(html)
                    print("   Debug HTML saved")
                except:
                    pass
                
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
