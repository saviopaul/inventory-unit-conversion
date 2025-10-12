import asyncio
from playwright.async_api import async_playwright
import os
import glob
import time
from pathlib import Path
from datetime import datetime
import csv
import json

async def download_report_521_working():
    """
    Download Report 521 CSV - Working version
    Strategy: Monitor downloads folder for new files instead of waiting for download event
    """
    print("="*80)
    print("📥 REPORT 521 - WORKING DOWNLOAD & SCHEMA EXTRACTION")
    print("="*80)
    
    download_dir = "/app/gofrugal-report-builder/downloads"
    output_dir = "/app/gofrugal-report-builder/database/schemas"
    logs_dir = "/app/gofrugal-report-builder/logs"
    
    Path(download_dir).mkdir(parents=True, exist_ok=True)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(logs_dir).mkdir(parents=True, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
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
            except Exception as e:
                print(f"   ⚠️ Apply issue: {str(e)[:50]}")
            
            # ===== STEP 5: GET FILES BEFORE DOWNLOAD =====
            print("\n💾 Step 5: Prepare for download...")
            
            # Get list of existing files
            existing_files = set(os.listdir(download_dir))
            print(f"   Existing files in download folder: {len(existing_files)}")
            
            # ===== STEP 6: TRIGGER DOWNLOAD =====
            print("\n📥 Step 6: Trigger CSV download...")
            
            # Click export icon
            try:
                export_icon = report_frame.locator('#export i').first
                await export_icon.click()
                await asyncio.sleep(2)
                print("   ✅ Export menu opened")
            except Exception as e:
                print(f"   ❌ Export icon failed: {str(e)[:100]}")
                return None
            
            # Click "Export as .csv" button
            try:
                csv_export_btn = report_frame.locator('sr-sidebar div:nth-of-type(3) button').first
                await csv_export_btn.click()
                print("   ✅ Export as CSV clicked")
                
                # Wait for "Please wait..." message and download to start
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"   ❌ CSV export button failed: {str(e)}")
                return None
            
            # ===== STEP 7: WAIT FOR NEW FILE =====
            print("\n⏳ Step 7: Waiting for download to complete...")
            
            downloaded_file = None
            max_wait = 30  # 30 seconds max
            
            for i in range(max_wait):
                await asyncio.sleep(1)
                
                current_files = set(os.listdir(download_dir))
                new_files = current_files - existing_files
                
                if new_files:
                    # Found new file(s)
                    downloaded_file = list(new_files)[0]
                    filepath = os.path.join(download_dir, downloaded_file)
                    
                    # Check if file is still being written (size changing)
                    size1 = os.path.getsize(filepath)
                    await asyncio.sleep(1)
                    size2 = os.path.getsize(filepath)
                    
                    if size1 == size2:
                        # File is complete
                        print(f"   ✅ Downloaded: {downloaded_file}")
                        print(f"   File size: {size2:,} bytes ({size2/1024:.2f} KB)")
                        break
                    else:
                        print(f"   ⏳ Download in progress... ({i+1}s)")
                else:
                    if i % 5 == 0 and i > 0:
                        print(f"   ⏳ Still waiting... ({i}s)")
            
            if not downloaded_file:
                print(f"   ❌ No new file detected after {max_wait}s")
                return None
            
            # ===== STEP 8: PARSE CSV AND EXTRACT SCHEMA =====
            print("\n📊 Step 8: Parse CSV and extract schema...")
            
            filepath = os.path.join(download_dir, downloaded_file)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                    # Skip first 3 lines (company name, report title, filters)
                    # Line 4 has the column headers
                    header_line_index = 3
                    if header_line_index < len(lines):
                        csv_reader = csv.reader([lines[header_line_index]])
                        columns = next(csv_reader)
                        
                        # Count data rows (total lines - header lines - 1 for header)
                        data_row_count = len(lines) - header_line_index - 1
                        
                        # Get sample data (first 3 data rows)
                        sample_data = []
                        for i in range(header_line_index + 1, min(header_line_index + 4, len(lines))):
                            csv_reader = csv.reader([lines[i]])
                            sample_data.append(next(csv_reader))
                    else:
                        print(f"   ❌ CSV format unexpected")
                        return None
                
                print(f"   ✅ Schema extracted!")
                print(f"   Columns: {len(columns)}")
                print(f"   Data rows: {data_row_count}")
                
                print(f"\n   📋 Column Headers ({len(columns)} total):")
                for i, col in enumerate(columns[:20], 1):  # Show first 20
                    print(f"      {i}. {col}")
                if len(columns) > 20:
                    print(f"      ... and {len(columns) - 20} more columns")
                
                # Rename file to something meaningful
                new_filename = f"report_521_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                new_filepath = os.path.join(download_dir, new_filename)
                os.rename(filepath, new_filepath)
                print(f"\n   ✅ Renamed to: {new_filename}")
                
                # Save schema
                schema = {
                    "report_id": "521",
                    "report_name": "Sale - Bill Wise Item Detailed",
                    "report_url": report_url,
                    "extracted_at": datetime.now().isoformat(),
                    "extraction_method": "csv_download",
                    "column_count": len(columns),
                    "columns": columns,
                    "total_rows": data_row_count,
                    "sample_data": sample_data,
                    "download_file": new_filepath,
                    "file_size_bytes": os.path.getsize(new_filepath)
                }
                
                schema_file = f'{output_dir}/report_521_schema.json'
                with open(schema_file, 'w', encoding='utf-8') as f:
                    json.dump(schema, f, indent=2, ensure_ascii=False)
                
                print(f"   ✅ Schema saved to: report_521_schema.json")
                
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
            return None
        finally:
            await browser.close()
            print("\n🏁 Browser closed")

async def main():
    print("\n" + "="*80)
    print("Report 521 - Working Download & Schema Extraction")
    print("="*80 + "\n")
    
    result = await download_report_521_working()
    
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
        
        return 0
    else:
        print("\n" + "="*80)
        print("❌ FAILED")
        print("="*80 + "\n")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
