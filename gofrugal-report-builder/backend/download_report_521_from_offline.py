import asyncio
from playwright.async_api import async_playwright
import os
from pathlib import Path
import time

async def download_report_521_from_offline():
    """
    Download Report 521 from the Offline Export report page
    Assumes the report has already been queued and processed
    """
    print("="*60)
    print("📥 Download Report 521 from Offline Export")
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
            print("✅ Logged in")
            
            # ===== STEP 2: NAVIGATE TO OFFLINE EXPORT REPORT =====
            print("\n📊 Step 2: Navigate to Offline Export report")
            url = 'https://bbcohq.gofrugal.com/RayMedi_HQ/mainIndex.do?page=%2Fsmartreport%2Findex.html%23%2Freports%3FreportId%3D40000230%26productId%3D5'
            await page.goto(url, wait_until='networkidle', timeout=60000)
            await asyncio.sleep(10)
            await page.screenshot(path=f'{logs_dir}/download_01_offline_page.png')
            print("✅ Offline Export report page loaded")
            
            # ===== STEP 3: FIND THE CORRECT IFRAME =====
            print("\n🔍 Step 3: Find the smartreport iframe")
            
            offline_frame = None
            max_waits = 15
            
            for attempt in range(max_waits):
                await asyncio.sleep(2)
                frames = page.frames
                
                if attempt == 0:
                    print(f"   Found {len(frames)} total frames")
                
                # Find Frame 2: smartreport/index.html with reportId=40000230
                for i, frame in enumerate(frames):
                    try:
                        frame_url = frame.url
                        
                        # IMPORTANT: Must be 'smartreport/index.html', not 'smartreport%2Findex.html'
                        if 'smartreport/index.html' in frame_url and 'reportId=40000230' in frame_url:
                            # Check if it has download links
                            tbody_links = frame.locator('tbody a')
                            link_count = await tbody_links.count()
                            
                            # Should have between 1-50 links (reasonable range for download files)
                            if 0 < link_count < 100:
                                offline_frame = frame
                                print(f"✅ Found target iframe (frame {i}) with {link_count} download links")
                                print(f"   Frame URL: {frame_url[:100]}")
                                break
                            elif attempt % 5 == 0:
                                print(f"   Attempt {attempt+1}: Frame {i} has {link_count} links (waiting for reasonable count)")
                    except Exception as e:
                        pass
                
                if offline_frame:
                    break
            
            if not offline_frame:
                print("❌ Could not find the offline export iframe")
                await page.screenshot(path=f'{logs_dir}/download_error_no_iframe.png')
                return None
            
            # ===== STEP 4: FIND AND DOWNLOAD REPORT 521 =====
            print("\n💾 Step 4: Find and download Report 521")
            
            # Get all tbody links
            download_links = offline_frame.locator('tbody a')
            link_count = await download_links.count()
            print(f"   Found {link_count} download links")
            
            # Find Report 521 file
            report_521_link = None
            report_521_filename = None
            
            print("   Scanning for Report 521...")
            for i in range(link_count):
                try:
                    link = download_links.nth(i)
                    link_text = await link.inner_text()
                    
                    # Look for files starting with "521" and ending with ".zip"
                    if link_text.startswith('521') and link_text.endswith('.zip'):
                        report_521_link = link
                        report_521_filename = link_text
                        print(f"✅ Found Report 521: {link_text}")
                        break
                except Exception as e:
                    pass
            
            if not report_521_link:
                print("⚠️ No Report 521 file found in offline exports")
                print("   This likely means:")
                print("   1. The export is still being processed")
                print("   2. The export failed")
                print("   3. The export has expired and been deleted")
                print("\n   Available files:")
                for i in range(min(link_count, 10)):
                    try:
                        text = await download_links.nth(i).inner_text()
                        if text and '.zip' in text:
                            print(f"     - {text}")
                    except:
                        pass
                
                await page.screenshot(path=f'{logs_dir}/download_no_521_found.png')
                return "NO_REPORT_521"
            
            # Download the file
            print(f"\n⏬ Downloading: {report_521_filename}")
            
            # Get the onclick attribute to extract the download URL
            onclick_attr = await report_521_link.get_attribute('onclick')
            print(f"   Link onclick: {onclick_attr[:100] if onclick_attr else 'None'}")
            
            # Extract the download URL from onclick
            if onclick_attr and 'window.open' in onclick_attr:
                # Parse: window.open('/smartreport/download?...','_blank')
                import re
                match = re.search(r"window\.open\('([^']+)'", onclick_attr)
                if match:
                    download_path = match.group(1)
                    print(f"   Extracted download path: {download_path}")
                    
                    # Construct full URL
                    base_url = 'https://bbcohq.gofrugal.com'
                    download_url = base_url + download_path
                    print(f"   Full download URL: {download_url}")
                    
                    # Method 1: Try handling new page/popup
                    print("   Method 1: Trying popup handler...")
                    try:
                        # Listen for new pages (popups)
                        async with context.expect_page(timeout=5000) as new_page_info:
                            await report_521_link.click()
                        
                        new_page = await new_page_info.value
                        print(f"   ✅ Popup opened: {new_page.url[:80]}")
                        
                        # Wait for download from the new page
                        async with new_page.expect_download(timeout=30000) as download_info:
                            await asyncio.sleep(1)  # Give it time to start
                        
                        download = await download_info.value
                        await new_page.close()
                        
                    except asyncio.TimeoutError:
                        print("   Method 1 failed (no popup), trying Method 2...")
                        
                        # Method 2: Direct download using requests-like approach
                        # Create a new page and navigate directly
                        download_page = await context.new_page()
                        
                        async with download_page.expect_download(timeout=30000) as download_info:
                            await download_page.goto(download_url)
                        
                        download = await download_info.value
                        await download_page.close()
                else:
                    print("   ❌ Could not parse download URL from onclick")
                    return None
            else:
                # Fallback: try clicking normally
                print("   Using fallback click method...")
                async with page.expect_download(timeout=30000) as download_info:
                    await report_521_link.click()
                download = await download_info.value
            
            # Save the file
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(download_dir, f"report_521_{timestamp}.zip")
            
            await download.save_as(filepath)
            print(f"✅ Downloaded to: {filepath}")
            
            # Verify the file
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                print(f"✅ File verified: {file_size:,} bytes ({file_size / 1024:.2f} KB)")
                
                # Check if it's a valid ZIP file
                if file_size > 100:  # Reasonable minimum size
                    print("✅ File size looks valid")
                    return filepath
                else:
                    print("⚠️ File size is very small, may be corrupted")
                    return filepath
            else:
                print("❌ File not found after download")
                return None
                
        except asyncio.TimeoutError:
            print("\n❌ Timeout error during download")
            await page.screenshot(path=f'{logs_dir}/download_error_timeout.png')
            return None
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            await page.screenshot(path=f'{logs_dir}/download_error.png')
            return None
        finally:
            await browser.close()
            print("\n🏁 Browser closed")

async def main():
    print("\n" + "="*60)
    print("Testing Download from Offline Export Report")
    print("="*60 + "\n")
    
    result = await download_report_521_from_offline()
    
    print("\n" + "="*60)
    if result == "NO_REPORT_521":
        print("⚠️ No Report 521 file available for download")
        print("\nPossible reasons:")
        print("1. Export is still processing (wait a few minutes)")
        print("2. Need to queue the export first")
        print("3. Export has expired")
    elif result:
        print(f"✅ SUCCESS! Downloaded: {result}")
    else:
        print("❌ FAILED - Could not download report")
    print("="*60 + "\n")
    
    return result

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result and result != "NO_REPORT_521" else 1)
