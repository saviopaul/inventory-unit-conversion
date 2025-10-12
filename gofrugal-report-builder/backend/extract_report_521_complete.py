import asyncio
from playwright.async_api import async_playwright
import json
import os
from pathlib import Path
from datetime import datetime

async def extract_report_521_complete():
    """
    Complete Report 521 extraction:
    1. Load the report
    2. Extract column schema
    3. Optionally download if more than 250 records
    """
    print("="*80)
    print("📊 REPORT 521 - COMPLETE SCHEMA EXTRACTION & DOWNLOAD")
    print("="*80)
    
    logs_dir = "/app/gofrugal-report-builder/logs"
    output_dir = "/app/gofrugal-report-builder/database/schemas"
    download_dir = "/app/gofrugal-report-builder/downloads"
    
    Path(logs_dir).mkdir(parents=True, exist_ok=True)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(download_dir).mkdir(parents=True, exist_ok=True)
    
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
            
            # ===== STEP 2: NAVIGATE DIRECTLY TO REPORT 521 =====
            print("\n📊 Step 2: Navigate directly to Report 521...")
            report_url = 'https://bbcohq.gofrugal.com/RayMedi_HQ/mainIndex.do?page=%2Fsmartreport%2Findex.html%23%2Freports%3FreportId%3D521%26productId%3D2'
            await page.goto(report_url, wait_until='networkidle', timeout=60000)
            await asyncio.sleep(8)
            print("✅ Report 521 page loaded")
            
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
            
            # ===== STEP 4: CLICK APPLY TO LOAD DATA =====
            print("\n📋 Step 4: Click Apply to load data...")
            await asyncio.sleep(5)
            
            try:
                apply_btn = report_frame.locator('#filtersPanel button.btn-primary:has-text("Apply")').first
                await apply_btn.click()
                print("   ✅ Apply clicked")
                
                print("   ⏳ Waiting for data to load...")
                await asyncio.sleep(15)
                
                await page.screenshot(path=f'{logs_dir}/complete_521_01_data_loaded.png')
            except Exception as e:
                print(f"   ⚠️ Apply button issue: {str(e)[:50]}")
            
            # ===== STEP 5: EXTRACT COLUMN SCHEMA =====
            print("\n📊 Step 5: Extract column schema...")
            
            # Get comprehensive table info
            table_info = await report_frame.evaluate('''() => {
                // Method 1: Look for table with sr-grid-table class or id
                const mainTable = document.querySelector('table.sr-grid-table, table[id*="grid"], div.sr-grid table');
                
                if (mainTable) {
                    // Get all th elements
                    const ths = Array.from(mainTable.querySelectorAll('thead th'));
                    const thTexts = ths.map(th => th.textContent.trim()).filter(t => t);
                    
                    // Get first data row
                    const firstRow = mainTable.querySelector('tbody tr');
                    const firstRowData = firstRow ? 
                        Array.from(firstRow.querySelectorAll('td')).map(td => td.textContent.trim()) : [];
                    
                    // Count rows
                    const rowCount = mainTable.querySelectorAll('tbody tr').length;
                    
                    return {
                        method: 'sr-grid-table',
                        columns: thTexts,
                        sampleData: firstRowData,
                        rowCount: rowCount
                    };
                }
                
                // Method 2: Find largest table
                const tables = Array.from(document.querySelectorAll('table'));
                let largestTable = null;
                let maxRows = 0;
                
                for (const table of tables) {
                    const rows = table.querySelectorAll('tbody tr').length;
                    if (rows > maxRows) {
                        maxRows = rows;
                        largestTable = table;
                    }
                }
                
                if (largestTable && maxRows > 0) {
                    const ths = Array.from(largestTable.querySelectorAll('thead th, thead td'));
                    const columns = ths.map(th => th.textContent.trim()).filter(t => t);
                    
                    const firstRow = largestTable.querySelector('tbody tr');
                    const sampleData = firstRow ?
                        Array.from(firstRow.querySelectorAll('td')).map(td => td.textContent.trim()) : [];
                    
                    return {
                        method: 'largest-table',
                        columns: columns,
                        sampleData: sampleData,
                        rowCount: maxRows
                    };
                }
                
                return { method: 'none', columns: [], sampleData: [], rowCount: 0 };
            }''')
            
            print(f"   Method used: {table_info['method']}")
            print(f"   Columns found: {len(table_info['columns'])}")
            print(f"   Data rows: {table_info['rowCount']}")
            
            if len(table_info['columns']) > 0:
                print(f"\n   ✅ Column Schema Extracted!")
                print(f"\n   📋 Columns ({len(table_info['columns'])}):")
                for i, col in enumerate(table_info['columns'], 1):
                    print(f"      {i}. {col}")
                
                # Save schema
                schema = {
                    "report_id": "521",
                    "report_name": "Sale - Bill Wise Item Detailed",
                    "report_url": report_url,
                    "extracted_at": datetime.now().isoformat(),
                    "extraction_method": table_info['method'],
                    "column_count": len(table_info['columns']),
                    "columns": table_info['columns'],
                    "visible_rows": table_info['rowCount'],
                    "sample_data": table_info['sampleData'][:10]
                }
                
                schema_file = f'{output_dir}/report_521_schema_final.json'
                with open(schema_file, 'w', encoding='utf-8') as f:
                    json.dump(schema, f, indent=2, ensure_ascii=False)
                
                print(f"\n   ✅ Schema saved to: {schema_file}")
                
                # ===== STEP 6: CHECK PAGINATION & DOWNLOAD IF NEEDED =====
                print("\n📄 Step 6: Check pagination...")
                
                # Look for pagination info
                pagination_info = await report_frame.evaluate('''() => {
                    // Look for pagination text like "1-50 of 1234"
                    const paginationElements = Array.from(document.querySelectorAll('[class*="pagination"], [class*="page-info"]'));
                    for (const el of paginationElements) {
                        const text = el.textContent;
                        const match = text.match(/(\\d+)\\s*-\\s*(\\d+)\\s+of\\s+(\\d+)/i);
                        if (match) {
                            return {
                                found: true,
                                start: parseInt(match[1]),
                                end: parseInt(match[2]),
                                total: parseInt(match[3]),
                                text: text.trim()
                            };
                        }
                    }
                    return { found: false };
                }''')
                
                if pagination_info['found']:
                    total_records = pagination_info['total']
                    print(f"   ✅ Total records: {total_records}")
                    print(f"   Showing: {pagination_info['start']}-{pagination_info['end']}")
                    
                    if total_records > 250:
                        print(f"\n   ⚠️  More than 250 records ({total_records} total)")
                        print(f"   📥 Triggering download...")
                        
                        # Click export icon
                        try:
                            export_icon = report_frame.locator('#export i').first
                            await export_icon.click()
                            await asyncio.sleep(2)
                            print("   ✅ Export menu opened")
                            
                            # Click download button and wait for download
                            download_btn = report_frame.locator('sr-sidebar div:nth-of-type(3) button').first
                            
                            async with page.expect_download(timeout=60000) as download_info:
                                await download_btn.click()
                                print("   ✅ Download triggered")
                            
                            download = await download_info.value
                            
                            # Save the file
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"report_521_{timestamp}.csv"
                            filepath = os.path.join(download_dir, filename)
                            
                            await download.save_as(filepath)
                            print(f"   ✅ Downloaded: {filepath}")
                            
                            if os.path.exists(filepath):
                                file_size = os.path.getsize(filepath)
                                print(f"   ✅ File size: {file_size:,} bytes ({file_size/1024:.2f} KB)")
                                
                                schema['download_file'] = filepath
                                schema['download_size_bytes'] = file_size
                                
                                # Update schema file
                                with open(schema_file, 'w', encoding='utf-8') as f:
                                    json.dump(schema, f, indent=2, ensure_ascii=False)
                        
                        except Exception as e:
                            print(f"   ❌ Download failed: {str(e)}")
                    else:
                        print(f"   ℹ️  {total_records} records - no download needed (< 250)")
                else:
                    print(f"   ℹ️  Pagination info not found")
                
                return schema
                
            else:
                print(f"   ❌ No columns extracted")
                
                # Dump HTML for debugging
                html = await report_frame.content()
                with open(f'{logs_dir}/complete_521_frame.html', 'w', encoding='utf-8') as f:
                    f.write(html)
                print(f"   📄 HTML saved for debugging: complete_521_frame.html")
                
                return None
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            await page.screenshot(path=f'{logs_dir}/complete_521_error.png')
            return None
        finally:
            await browser.close()
            print("\n🏁 Browser closed")

async def main():
    print("\n" + "="*80)
    print("Report 521 - Complete Extraction with Download Support")
    print("="*80 + "\n")
    
    result = await extract_report_521_complete()
    
    if result:
        print("\n" + "="*80)
        print("✅ SUCCESS!")
        print("="*80)
        print(f"\n✅ Extracted schema with {result['column_count']} columns")
        print(f"✅ Visible rows: {result['visible_rows']}")
        if 'download_file' in result:
            print(f"✅ Downloaded full report: {result['download_file']}")
        print(f"\n📁 Files created:")
        print(f"   - Schema: /app/gofrugal-report-builder/database/schemas/report_521_schema_final.json")
        if 'download_file' in result:
            print(f"   - Data: {result['download_file']}")
        print("="*80 + "\n")
    else:
        print("\n" + "="*80)
        print("❌ FAILED")
        print("="*80 + "\n")
    
    return result

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
