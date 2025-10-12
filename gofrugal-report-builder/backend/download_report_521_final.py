import asyncio
from playwright.async_api import async_playwright
import os
from pathlib import Path
from datetime import datetime
import csv

async def download_report_521_with_schema():
    """
    Download Report 521 CSV and extract schema
    Key: Configure browser to auto-download without showing Save As dialog
    """
    print("="*80)
    print("📥 REPORT 521 - DOWNLOAD & SCHEMA EXTRACTION")
    print("="*80)
    
    download_dir = "/app/gofrugal-report-builder/downloads"
    output_dir = "/app/gofrugal-report-builder/database/schemas"
    logs_dir = "/app/gofrugal-report-builder/logs"
    
    Path(download_dir).mkdir(parents=True, exist_ok=True)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(logs_dir).mkdir(parents=True, exist_ok=True)
    
    async with async_playwright() as p:
        # Launch browser with download behavior configured
        browser = await p.chromium.launch(
            headless=True,
            downloads_path=download_dir  # Set default download location
        )
        
        # Create context with auto-download enabled
        context = await browser.new_context(
            viewport={'width': 1388, 'height': 913},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            accept_downloads=True
        )
        
        page = await context.new_page()
        
        try:
            # ===== STEP 1: LOGIN =====
            print("\n📍 Step 1: Login...")
            await page.goto('https://bbcohq.gofrugal.com/RayMedi_HQ/index.do',
                          wait_until='networkidle', timeout=60000)
            await asyncio.sleep(2)
            
            await page.fill('#username', 'admin1')
            await page.fill('#password', 'De!!@88981')
            await page.click('button:has-text("Login")')
            await page.wait_for_load_state('networkidle', timeout=30000)
            await asyncio.sleep(5)
            print("✅ Logged in")
            
            # ===== STEP 2: NAVIGATE TO REPORT 521 =====
            print("\n📊 Step 2: Navigate to Report 521...")
            report_url = 'https://bbcohq.gofrugal.com/RayMedi_HQ/mainIndex.do?page=%2Fsmartreport%2Findex.html%23%2Freports%3FreportId%3D521%26productId%3D2'
            await page.goto(report_url, wait_until='networkidle', timeout=60000)
            await asyncio.sleep(8)
            print("✅ Report page loaded")
            
            # ===== STEP 3: FIND IFRAME =====
            print("\n🔍 Step 3: Find report iframe...")
            report_frame = None
            for i, frame in enumerate(page.frames):
                try:
                    if 'smartreport' in frame.url and 'reportId=521' in frame.url:
                        report_frame = frame
                        print(f"✅ Found iframe (frame {i})")
                        break
                except:
                    pass
            
            if not report_frame:
                print("❌ No iframe found")
                return None
            
            # ===== STEP 4: LOAD DATA =====
            print("\n📋 Step 4: Click Apply to load data...")
            await asyncio.sleep(5)
            
            try:
                apply_btn = report_frame.locator('#filtersPanel button.btn-primary:has-text("Apply")').first
                await apply_btn.click()
                print("   ✅ Apply clicked")
                
                print("   ⏳ Waiting for data to load...")
                await asyncio.sleep(15)
                
                await page.screenshot(path=f'{logs_dir}/download_521_01_data_loaded.png')
            except Exception as e:
                print(f"   ⚠️ Apply issue: {str(e)[:50]}")
            
            # ===== STEP 5: TRIGGER DOWNLOAD =====
            print("\n💾 Step 5: Download CSV...")
            
            # Click export icon to open menu
            print("   Clicking export icon...")
            try:
                export_icon = report_frame.locator('#export i').first
                await export_icon.wait_for(state='visible', timeout=10000)
                await export_icon.click()
                await asyncio.sleep(2)
                print("   ✅ Export menu opened")
                
                await page.screenshot(path=f'{logs_dir}/download_521_02_export_menu.png')
            except Exception as e:
                print(f"   ❌ Export icon failed: {str(e)[:100]}")
                return None
            
            # Click "Export as .csv" button - THIS TRIGGERS THE DOWNLOAD
            print("   Clicking 'Export as .csv'...")
            try:
                # Set up download promise BEFORE clicking
                download_promise = page.wait_for_event('download', timeout=60000)
                
                # Click the CSV export button (3rd option in the sidebar)
                csv_export_btn = report_frame.locator('sr-sidebar div:nth-of-type(3) button').first
                await csv_export_btn.click()
                print("   ✅ Export as CSV clicked")
                
                # Wait for the "Please wait..." message
                await asyncio.sleep(3)
                
                # Wait for download to complete
                print("   ⏳ Waiting for download...")
                download = await download_promise
                
                # Save the downloaded file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"report_521_{timestamp}.csv"
                filepath = os.path.join(download_dir, filename)
                
                await download.save_as(filepath)
                print(f"   ✅ Downloaded: {filename}")
                
            except asyncio.TimeoutError:
                print(f"   ❌ Download timeout (60s)")
                await page.screenshot(path=f'{logs_dir}/download_521_error_timeout.png')
                return None
            except Exception as e:
                print(f"   ❌ Download error: {str(e)}")
                import traceback
                traceback.print_exc()
                await page.screenshot(path=f'{logs_dir}/download_521_error.png')
                return None
            
            # ===== STEP 6: VERIFY & EXTRACT SCHEMA =====
            print("\n📊 Step 6: Extract schema from CSV...")
            
            if not os.path.exists(filepath):
                print(f"   ❌ File not found: {filepath}")
                return None
            
            file_size = os.path.getsize(filepath)
            print(f"   ✅ File size: {file_size:,} bytes ({file_size/1024:.2f} KB)")
            
            # Parse CSV to get schema
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    csv_reader = csv.reader(f)
                    
                    # First row = column headers
                    columns = next(csv_reader)
                    
                    # Count total rows
                    row_count = sum(1 for row in csv_reader)
                    
                    # Get sample data (read first 3 rows again)
                    f.seek(0)
                    csv_reader = csv.reader(f)
                    next(csv_reader)  # Skip header
                    sample_data = [next(csv_reader, None) for _ in range(3)]
                    sample_data = [row for row in sample_data if row]  # Remove None
                
                print(f"   ✅ Schema extracted!")
                print(f"   Columns: {len(columns)}")
                print(f"   Data rows: {row_count}")
                
                print(f"\n   📋 Column Headers:")
                for i, col in enumerate(columns, 1):
                    print(f"      {i}. {col}")
                
                # Save schema
                schema = {
                    "report_id": "521",
                    "report_name": "Sale - Bill Wise Item Detailed",
                    "report_url": report_url,
                    "extracted_at": datetime.now().isoformat(),
                    "extraction_method": "csv_download",
                    "column_count": len(columns),
                    "columns": columns,
                    "total_rows": row_count,
                    "sample_data": sample_data,
                    "download_file": filepath,
                    "file_size_bytes": file_size
                }
                
                schema_file = f'{output_dir}/report_521_schema.json'
                import json
                with open(schema_file, 'w', encoding='utf-8') as f:
                    json.dump(schema, f, indent=2, ensure_ascii=False)
                
                print(f"\n   ✅ Schema saved to: {schema_file}")
                
                return schema
                
            except Exception as e:
                print(f"   ❌ CSV parsing error: {str(e)}")
                import traceback
                traceback.print_exc()
                return None
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            await page.screenshot(path=f'{logs_dir}/download_521_fatal_error.png')
            return None
        finally:
            await browser.close()
            print("\n🏁 Browser closed")

async def main():
    print("\n" + "="*80)
    print("Report 521 - Download CSV & Extract Schema")
    print("="*80 + "\n")
    
    result = await download_report_521_with_schema()
    
    if result:
        print("\n" + "="*80)
        print("✅ SUCCESS!")
        print("="*80)
        print(f"\n✅ Downloaded and parsed Report 521")
        print(f"✅ Columns: {result['column_count']}")
        print(f"✅ Data rows: {result['total_rows']}")
        print(f"\n📁 Files:")
        print(f"   - CSV: {result['download_file']}")
        print(f"   - Schema: /app/gofrugal-report-builder/database/schemas/report_521_schema.json")
        print("="*80 + "\n")
    else:
        print("\n" + "="*80)
        print("❌ FAILED")
        print("="*80 + "\n")
    
    return result

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
