import asyncio
from playwright.async_api import async_playwright
import os
from pathlib import Path
import time

async def fetch_report_521_with_download():
    """
    Complete automation for Report 521 with offline export download
    Steps:
    1. Login to GoFrugal portal
    2. Navigate to Report 521 (Sale - Bill Wise Item Detailed)
    3. Queue the export (offline export)
    4. Navigate to "Offline Export report" section
    5. Download the generated file
    """
    print("="*60)
    print("🚀 Report 521 - Complete Flow with Download")
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
            # ===== STEP 1: LOGIN =====
            print("\n📍 Step 1: Login")
            await page.goto('https://bbcohq.gofrugal.com/RayMedi_HQ/index.do',
                          wait_until='networkidle', timeout=60000)
            await asyncio.sleep(2)
            
            await page.fill('#username', 'admin1')
            await page.fill('#password', 'De!!@88981')
            await asyncio.sleep(1)
            
            await page.click('button:has-text("Login")')
            await page.wait_for_load_state('networkidle', timeout=30000)
            await asyncio.sleep(5)
            await page.screenshot(path=f'{logs_dir}/complete_01_logged_in.png')
            print("✅ Logged in")
            
            # ===== STEP 2: NAVIGATE TO REPORT 521 =====
            print("\n📊 Step 2: Navigate to Report 521")
            
            # Click Reports
            await page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll('a'));
                const reportsLink = links.find(link => link.textContent.trim() === 'Reports');
                if (reportsLink) reportsLink.click();
            }''')
            await asyncio.sleep(1)
            print("   Clicked Reports")
            
            # Click Sales
            await page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll('a'));
                const salesLink = links.find(link => link.textContent.trim() === 'Sales');
                if (salesLink) salesLink.click();
            }''')
            await asyncio.sleep(1)
            print("   Clicked Sales")
            
            # Click Item wise
            await page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll('a'));
                const itemWiseLink = links.find(link => link.textContent.trim() === 'Item wise');
                if (itemWiseLink) itemWiseLink.click();
            }''')
            await asyncio.sleep(1)
            print("   Clicked Item wise")
            
            # Click Sale - Bill Wise Item Detailed
            await page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll('a'));
                const reportLink = links.find(link => link.textContent.includes('Sale - Bill Wise'));
                if (reportLink) reportLink.click();
            }''')
            await asyncio.sleep(7)
            await page.screenshot(path=f'{logs_dir}/complete_02_report_page.png')
            print("✅ Report 521 page loaded")
            
            # ===== STEP 3: WAIT FOR IFRAME AND QUEUE EXPORT =====
            print("\n🔧 Step 3: Queue export")
            
            max_waits = 20
            report_frame = None
            
            for attempt in range(max_waits):
                await asyncio.sleep(2)
                frames = page.frames
                
                if attempt == 0:
                    print(f"   Found {len(frames)} frames")
                
                # Find the frame with Export as CSV button
                for i, frame in enumerate(frames):
                    try:
                        export_btn = frame.locator('button:has-text("Export as CSV")')
                        btn_count = await export_btn.count()
                        
                        if btn_count > 0:
                            report_frame = frame
                            print(f"✅ Report iframe loaded (frame {i}) after {attempt+1} attempts")
                            break
                    except:
                        pass
                
                if report_frame:
                    break
            
            if not report_frame:
                print("❌ Report iframe never loaded")
                await page.screenshot(path=f'{logs_dir}/complete_error_iframe.png')
                return None
            
            # Click "Export as CSV" button
            print("   Clicking 'Export as CSV' button...")
            try:
                export_csv_btn = report_frame.locator('button.btn-success:has-text("Export as CSV")').first
                await export_csv_btn.wait_for(state='visible', timeout=5000)
                await export_csv_btn.click()
                await asyncio.sleep(2)
                await page.screenshot(path=f'{logs_dir}/complete_03_after_export_click.png')
                print("✅ Export as CSV clicked")
            except Exception as e:
                print(f"❌ Failed to click Export as CSV: {str(e)[:100]}")
                return None
            
            # Click "Yes" confirmation
            print("   Clicking 'Yes' on confirmation dialog...")
            await asyncio.sleep(2)
            
            yes_clicked = False
            
            # Try Playwright locator
            try:
                yes_btn = report_frame.locator('button:has-text("Yes")').first
                if await yes_btn.is_visible(timeout=3000):
                    await yes_btn.click()
                    yes_clicked = True
                    print("✅ Yes button clicked")
            except:
                pass
            
            # Try JavaScript
            if not yes_clicked:
                try:
                    result = await report_frame.evaluate('''() => {
                        const buttons = Array.from(document.querySelectorAll('button'));
                        const yesBtn = buttons.find(btn => btn.textContent.trim() === 'Yes');
                        if (yesBtn) {
                            yesBtn.click();
                            return true;
                        }
                        return false;
                    }''')
                    if result:
                        yes_clicked = True
                        print("✅ Yes button clicked (JavaScript)")
                except:
                    pass
            
            if yes_clicked:
                await asyncio.sleep(3)
                await page.screenshot(path=f'{logs_dir}/complete_04_export_queued.png')
                print("✅ Export queued successfully")
            else:
                print("⚠️ Yes button not found, but may be queued")
            
            # Wait for export to process (typically takes a few seconds)
            print("\n⏳ Waiting for export to process (10 seconds)...")
            await asyncio.sleep(10)
            
            # ===== STEP 4: NAVIGATE TO OFFLINE EXPORT REPORT =====
            print("\n📥 Step 4: Navigate to Offline Export report")
            
            # Navigate to main page to access menu
            await page.goto('https://bbcohq.gofrugal.com/RayMedi_HQ/index.do',
                          wait_until='networkidle', timeout=60000)
            await asyncio.sleep(3)
            
            # Click Reports
            await page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll('a'));
                const reportsLink = links.find(link => link.textContent.trim() === 'Reports');
                if (reportsLink) reportsLink.click();
            }''')
            await asyncio.sleep(1)
            print("   Clicked Reports")
            
            # Click Admin or Utility (try both)
            # First try Admin Reports
            await page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll('a'));
                const adminLink = links.find(link => 
                    link.textContent.trim() === 'Admin Reports' || 
                    link.textContent.trim() === 'Admin'
                );
                if (adminLink) adminLink.click();
            }''')
            await asyncio.sleep(1)
            print("   Clicked Admin Reports")
            
            # Look for "Offline Export report" link
            await page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll('a'));
                const offlineLink = links.find(link => 
                    link.textContent.includes('Offline Export') ||
                    link.textContent.includes('offline export')
                );
                if (offlineLink) offlineLink.click();
            }''')
            await asyncio.sleep(5)
            await page.screenshot(path=f'{logs_dir}/complete_05_offline_export_page.png')
            print("✅ Navigated to Offline Export report page")
            
            # ===== STEP 5: FIND AND DOWNLOAD THE FILE =====
            print("\n💾 Step 5: Download the generated file")
            
            # Wait for the iframe with ID dynamicBodyIframe
            print("   Waiting for dynamicBodyIframe to load...")
            await asyncio.sleep(8)  # Give Angular app time to initialize and load data
            
            # Find the iframe by name or URL pattern
            max_waits = 20
            offline_frame = None
            
            for attempt in range(max_waits):
                await asyncio.sleep(2)
                frames = page.frames
                
                if attempt == 0:
                    print(f"   Found {len(frames)} frames on offline export page")
                
                # Find the frame with reportId=40000230 in smartreport
                for i, frame in enumerate(frames):
                    try:
                        frame_url = frame.url
                        # Must match both smartreport AND reportId=40000230
                        if 'smartreport' in frame_url and 'reportId=40000230' in frame_url:
                            # Check if the frame has loaded with file links in tbody
                            tbody_links = frame.locator('tbody a')
                            link_count = await tbody_links.count()
                            
                            if link_count > 0 and link_count < 100:  # Has reasonable number of download files
                                offline_frame = frame
                                print(f"✅ Offline export iframe loaded (frame {i}) with {link_count} download links after {attempt+1} attempts")
                                print(f"   Frame URL: {frame_url[:100]}")
                                break
                            elif attempt % 5 == 0:
                                # Check rows for debugging
                                rows = frame.locator('tbody tr')
                                row_count = await rows.count()
                                print(f"   Attempt {attempt+1}: Frame {i} has {row_count} rows, {link_count} tbody links, waiting...")
                    except Exception as e:
                        pass
                
                if offline_frame:
                    break
            
            if not offline_frame:
                print("⚠️ Could not find offline export iframe with ZIP files")
                print("   Trying to find smartreport frame anyway...")
                # Try to get frame even without ZIP files
                await asyncio.sleep(3)
                frames = page.frames
                for i, frame in enumerate(frames):
                    try:
                        frame_url = frame.url
                        if 'smartreport' in frame_url and 'reportId=40000230' in frame_url:
                            offline_frame = frame
                            print(f"   Using smartreport frame at index {i} (no ZIP files detected yet)")
                            break
                    except:
                        pass
            
            if not offline_frame:
                print("❌ Still no iframe found, cannot proceed")
                await page.screenshot(path=f'{logs_dir}/complete_error_no_iframe.png')
                return None
            
            # Take a screenshot to see the page structure
            await asyncio.sleep(2)
            await page.screenshot(path=f'{logs_dir}/complete_06_looking_for_download.png')
            
            # Try to find and click the most recent download link
            print("   Looking for Report 521 export files...")
            
            try:
                # Look for links in table cells (td a or tbody a)
                download_links = offline_frame.locator('tbody a, td a')
                link_count = await download_links.count()
                print(f"   Found {link_count} download links in table")
                
                if link_count > 0:
                    # Get all link texts to find Report 521
                    report_521_link = None
                    report_521_index = -1
                    
                    print("   Scanning for Report 521 files...")
                    for i in range(link_count):
                        try:
                            link = download_links.nth(i)
                            link_text = await link.inner_text()
                            
                            # Look for files starting with "521"
                            if link_text.startswith('521'):
                                report_521_link = link
                                report_521_index = i
                                print(f"   ✅ Found Report 521: {link_text}")
                                # Take the first (most recent) match
                                break
                        except:
                            pass
                    
                    if report_521_link:
                        # Click the Report 521 download link
                        download_promise = page.wait_for_event('download', timeout=30000)
                        await report_521_link.click()
                        print("   Clicked Report 521 link, waiting for download...")
                        
                        download = await download_promise
                        
                        # Save the file
                        timestamp = time.strftime("%Y%m%d_%H%M%S")
                        suggested = download.suggested_filename
                        extension = suggested.split('.')[-1] if '.' in suggested else 'zip'
                        filename = f"report_521_{timestamp}.{extension}"
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
                        print("⚠️ No Report 521 file found in the list")
                        print("   Available files:")
                        for i in range(min(link_count, 10)):
                            try:
                                link_text = await download_links.nth(i).inner_text()
                                print(f"     - {link_text}")
                            except:
                                pass
                        
                        # Maybe the export is still processing - take screenshot
                        await page.screenshot(path=f'{logs_dir}/complete_07_no_521_found.png')
                        return "NO_REPORT_521_YET"
                else:
                    print("❌ No download links found in table")
                    
                    # Dump HTML to analyze structure
                    print("   Dumping HTML for analysis...")
                    html_content = await offline_frame.content()
                    with open(f'{logs_dir}/complete_offline_export_html.html', 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    print(f"   HTML saved to: {logs_dir}/complete_offline_export_html.html")
                    
                    # Take detailed screenshot
                    await page.screenshot(path=f'{logs_dir}/complete_07_no_download_found.png', full_page=True)
                    return None
                        
            except asyncio.TimeoutError:
                print("❌ Download timeout")
                await page.screenshot(path=f'{logs_dir}/complete_error_download_timeout.png')
                return None
            except Exception as e:
                print(f"❌ Download error: {str(e)}")
                import traceback
                traceback.print_exc()
                await page.screenshot(path=f'{logs_dir}/complete_error_download.png')
                return None
                
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            await page.screenshot(path=f'{logs_dir}/complete_error_main.png')
            return None
        finally:
            await browser.close()
            print("\n🏁 Browser closed")

async def main():
    print("\n" + "="*60)
    print("Testing Complete Report 521 Flow with Download")
    print("="*60 + "\n")
    
    result = await fetch_report_521_with_download()
    
    print("\n" + "="*60)
    if result:
        print(f"✅ SUCCESS! Report downloaded: {result}")
    else:
        print("❌ FAILED - Could not complete download")
        print("\nNext steps:")
        print("1. Check screenshots in /app/gofrugal-report-builder/logs/")
        print("2. Check HTML dump: complete_offline_export_html.html")
        print("3. May need to adjust selectors based on page structure")
    print("="*60 + "\n")
    
    return result

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
