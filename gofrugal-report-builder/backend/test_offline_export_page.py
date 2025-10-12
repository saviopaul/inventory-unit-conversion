import asyncio
from playwright.async_api import async_playwright
import os
from pathlib import Path

async def test_offline_export_page():
    """
    Test script to inspect the Offline Export report page structure
    """
    print("="*60)
    print("🔍 Inspecting Offline Export Report Page")
    print("="*60)
    
    logs_dir = "/app/gofrugal-report-builder/logs"
    Path(logs_dir).mkdir(parents=True, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        try:
            # Login
            print("\n1. Logging in...")
            await page.goto('https://bbcohq.gofrugal.com/RayMedi_HQ/index.do',
                          wait_until='networkidle', timeout=60000)
            await asyncio.sleep(2)
            
            await page.fill('#username', 'admin1')
            await page.fill('#password', 'De!!@88981')
            await asyncio.sleep(1)
            
            await page.click('button:has-text("Login")')
            await page.wait_for_load_state('networkidle', timeout=30000)
            await asyncio.sleep(5)
            print("   ✅ Logged in")
            
            # Navigate to Offline Export report directly
            print("\n2. Navigating to Offline Export report page...")
            url = 'https://bbcohq.gofrugal.com/RayMedi_HQ/mainIndex.do?page=%2Fsmartreport%2Findex.html%23%2Freports%3FreportId%3D40000230%26productId%3D5'
            await page.goto(url, wait_until='networkidle', timeout=60000)
            await asyncio.sleep(5)
            print("   ✅ Page loaded")
            
            # Take initial screenshot
            await page.screenshot(path=f'{logs_dir}/test_offline_01_initial.png')
            print(f"   Screenshot saved: test_offline_01_initial.png")
            
            # List all frames
            print(f"\n3. Found {len(page.frames)} frames:")
            for i, frame in enumerate(page.frames):
                try:
                    frame_url = frame.url
                    print(f"   Frame {i}: {frame_url[:100]}")
                except:
                    print(f"   Frame {i}: <error getting URL>")
            
            # Find the dynamicBodyIframe
            print("\n4. Looking for dynamicBodyIframe...")
            target_frame = None
            
            for frame in page.frames:
                try:
                    if 'smartreport' in frame.url and 'reportId=40000230' in frame.url:
                        target_frame = frame
                        print(f"   ✅ Found target iframe: {frame.url[:100]}")
                        break
                except:
                    pass
            
            if not target_frame:
                print("   ❌ Could not find target iframe")
                return
            
            # Wait for content to load in the iframe
            print("\n5. Waiting for iframe content to load...")
            await asyncio.sleep(10)
            
            # Take screenshot after waiting
            await page.screenshot(path=f'{logs_dir}/test_offline_02_after_wait.png')
            print(f"   Screenshot saved: test_offline_02_after_wait.png")
            
            # Try to find various elements in the iframe
            print("\n6. Looking for elements in iframe...")
            
            # Check for tables
            tables = target_frame.locator('table')
            table_count = await tables.count()
            print(f"   Tables: {table_count}")
            
            # Check for rows
            rows = target_frame.locator('tr')
            row_count = await rows.count()
            print(f"   Table rows: {row_count}")
            
            # Check for links
            links = target_frame.locator('a')
            link_count = await links.count()
            print(f"   Links: {link_count}")
            
            # Check for buttons
            buttons = target_frame.locator('button')
            button_count = await buttons.count()
            print(f"   Buttons: {button_count}")
            
            # Check for download icons
            download_icons = target_frame.locator('i.fa-download, i.fa-arrow-down')
            icon_count = await download_icons.count()
            print(f"   Download icons: {icon_count}")
            
            # Get all button and link text
            if button_count > 0:
                print(f"\n7. Button texts:")
                for i in range(min(button_count, 10)):  # First 10 buttons
                    try:
                        text = await buttons.nth(i).inner_text()
                        print(f"   Button {i}: '{text}'")
                    except:
                        pass
            
            if link_count > 0:
                print(f"\n8. Link texts (first 20):")
                for i in range(min(link_count, 20)):
                    try:
                        text = await links.nth(i).inner_text()
                        if text and text.strip():
                            print(f"   Link {i}: '{text[:50]}'")
                    except:
                        pass
            
            # Get the HTML content
            print(f"\n9. Saving iframe HTML...")
            html_content = await target_frame.content()
            with open(f'{logs_dir}/test_offline_iframe.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"   HTML saved: test_offline_iframe.html")
            
            # Try to find download elements by various selectors
            print(f"\n10. Testing various download selectors...")
            
            selectors = [
                'a[href*="download"]',
                'a[href*="export"]',
                'button:has-text("Download")',
                'button:has-text("download")',
                'i.fa-download',
                'i.fa-file',
                '[class*="download"]',
                'td a',  # Links in table cells
                'tbody a',  # Links in table body
            ]
            
            for selector in selectors:
                try:
                    elements = target_frame.locator(selector)
                    count = await elements.count()
                    if count > 0:
                        print(f"   ✅ '{selector}': {count} elements")
                        # Get first element details
                        first = elements.first
                        text = await first.inner_text() if await first.count() > 0 else ''
                        print(f"      First element text: '{text[:50]}'")
                except Exception as e:
                    if count > 0:  # Only show error if elements were found
                        print(f"   ⚠️ '{selector}': Error - {str(e)[:50]}")
            
            print("\n" + "="*60)
            print("✅ Inspection complete! Check logs folder for:")
            print("   - test_offline_01_initial.png")
            print("   - test_offline_02_after_wait.png")
            print("   - test_offline_iframe.html")
            print("="*60)
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_offline_export_page())
