import asyncio
from playwright.async_api import async_playwright
import json
import os
from pathlib import Path
from datetime import datetime

async def extract_report_521_schema():
    """
    Extract column schema from Report 521 (Sale - Bill Wise Item Detailed)
    """
    print("="*80)
    print("🔍 EXTRACT REPORT 521 SCHEMA")
    print("="*80)
    
    output_dir = "/app/gofrugal-report-builder/database/schemas"
    logs_dir = "/app/gofrugal-report-builder/logs"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(logs_dir).mkdir(parents=True, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        try:
            # ===== STEP 1: LOGIN =====
            print("\n📍 Step 1: Logging in...")
            await page.goto('https://bbcohq.gofrugal.com/RayMedi_HQ/index.do',
                          wait_until='networkidle', timeout=60000)
            await asyncio.sleep(2)
            
            await page.fill('#username', 'admin1')
            await page.fill('#password', 'De!!@88981')
            await page.click('button:has-text("Login")')
            await page.wait_for_load_state('networkidle', timeout=30000)
            await asyncio.sleep(5)
            print("✅ Logged in successfully")
            
            # ===== STEP 2: NAVIGATE TO REPORT 521 =====
            print("\n📊 Step 2: Navigate to Report 521...")
            
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
            await asyncio.sleep(8)
            
            report_url = page.url
            await page.screenshot(path=f'{logs_dir}/schema_521_01_report_page.png')
            print("✅ Report 521 page loaded")
            
            # ===== STEP 3: FIND THE REPORT IFRAME =====
            print("\n🔍 Step 3: Find the report iframe...")
            
            report_frame = None
            for i, frame in enumerate(page.frames):
                try:
                    frame_url = frame.url
                    if 'smartreport' in frame_url and 'reportId=521' in frame_url:
                        report_frame = frame
                        print(f"✅ Found report iframe (frame {i})")
                        print(f"   URL: {frame_url[:100]}")
                        break
                except:
                    pass
            
            if not report_frame:
                print("❌ Could not find report iframe")
                await page.screenshot(path=f'{logs_dir}/schema_521_error_no_iframe.png')
                return None
            
            # Wait for report content to load and click Apply to load data
            print("   Waiting for report filters to load...")
            await asyncio.sleep(5)
            
            # Click Apply button to load report data
            print("   Clicking Apply to load report data...")
            try:
                apply_btn = report_frame.locator('#filtersPanel button.btn-primary:has-text("Apply")').first
                await apply_btn.wait_for(state='visible', timeout=10000)
                await apply_btn.click()
                print("   ✅ Apply clicked")
                await asyncio.sleep(10)  # Wait for data to load
            except Exception as e:
                print(f"   ⚠️ Could not click Apply: {str(e)[:50]}")
                print("   Continuing anyway...")
                await asyncio.sleep(5)
            
            # ===== STEP 4: EXTRACT COLUMN HEADERS =====
            print("\n📋 Step 4: Extract column headers...")
            
            # Take screenshot of the report with data
            await page.screenshot(path=f'{logs_dir}/schema_521_02_with_data.png')
            
            # Method 1: Extract from table headers in the data table
            # Look for tables with actual data (not the filter/settings tables)
            columns_th = await report_frame.evaluate('''() => {
                // Find the main data table (usually has many rows)
                const tables = Array.from(document.querySelectorAll('table'));
                let mainTable = null;
                let maxRows = 0;
                
                for (const table of tables) {
                    const rows = table.querySelectorAll('tbody tr');
                    if (rows.length > maxRows) {
                        maxRows = rows.length;
                        mainTable = table;
                    }
                }
                
                if (mainTable) {
                    const headers = Array.from(mainTable.querySelectorAll('thead th, thead td'));
                    return headers.map(h => h.textContent.trim()).filter(t => t && t.length > 0 && t !== 'S no');
                }
                
                // Fallback: get all th elements
                const allHeaders = Array.from(document.querySelectorAll('th'));
                return allHeaders.map(h => h.textContent.trim()).filter(t => t && t.length > 0 && t !== 'S no');
            }''')
            print(f"   Method 1 (main table th): Found {len(columns_th)} columns")
            if len(columns_th) > 0:
                print(f"   Sample: {columns_th[:5]}")
            
            # Method 2: Extract from thead td
            columns_thead = await report_frame.evaluate('''() => {
                const headers = Array.from(document.querySelectorAll('thead td'));
                return headers.map(h => h.textContent.trim()).filter(t => t && t.length > 0);
            }''')
            print(f"   Method 2 (thead td): Found {len(columns_thead)} columns")
            
            # Method 3: Look for column headers with specific classes
            columns_class = await report_frame.evaluate('''() => {
                const headers = Array.from(document.querySelectorAll('[class*="column"], [class*="header"], .th'));
                return headers.map(h => h.textContent.trim()).filter(t => t && t.length > 0);
            }''')
            print(f"   Method 3 (class selectors): Found {len(columns_class)} columns")
            
            # Method 4: Get all text from first row
            columns_first_row = await report_frame.evaluate('''() => {
                const firstRow = document.querySelector('tr:first-child, tbody tr:first-child');
                if (!firstRow) return [];
                const cells = Array.from(firstRow.querySelectorAll('td, th'));
                return cells.map(c => c.textContent.trim()).filter(t => t && t.length > 0);
            }''')
            print(f"   Method 4 (first row): Found {len(columns_first_row)} columns")
            
            # Method 5: Look for Angular directives
            columns_angular = await report_frame.evaluate('''() => {
                const elements = Array.from(document.querySelectorAll('[ng-bind], [data-ng-bind], [ng-repeat*="column"]'));
                return elements.map(el => el.textContent.trim()).filter(t => t && t.length > 0);
            }''')
            print(f"   Method 5 (Angular): Found {len(columns_angular)} columns")
            
            # Method 6: Dump HTML for analysis
            print("\n   Dumping iframe HTML for analysis...")
            html_content = await report_frame.content()
            with open(f'{logs_dir}/schema_521_iframe.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"   HTML saved to: {logs_dir}/schema_521_iframe.html")
            
            # Choose the best result
            all_methods = [
                ("th", columns_th),
                ("thead td", columns_thead),
                ("class selectors", columns_class),
                ("first row", columns_first_row),
                ("Angular", columns_angular)
            ]
            
            # Select the method with most columns
            best_method = max(all_methods, key=lambda x: len(x[1]))
            method_name, columns = best_method
            
            print(f"\n✅ Best method: {method_name} with {len(columns)} columns")
            
            if len(columns) > 0:
                print(f"\n📊 Extracted Columns:")
                for i, col in enumerate(columns, 1):
                    print(f"   {i}. {col}")
                
                # Save schema
                report_schema = {
                    "report_id": "521",
                    "report_name": "Sale - Bill Wise Item Detailed",
                    "report_url": report_url,
                    "extracted_at": datetime.now().isoformat(),
                    "extraction_method": method_name,
                    "column_count": len(columns),
                    "columns": columns
                }
                
                schema_file = f'{output_dir}/report_521_schema.json'
                with open(schema_file, 'w', encoding='utf-8') as f:
                    json.dump(report_schema, f, indent=2, ensure_ascii=False)
                
                print(f"\n✅ Schema saved to: {schema_file}")
                
                return report_schema
            else:
                print("\n❌ No columns extracted from any method")
                print("   Check the HTML dump and screenshots for debugging")
                return None
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            await page.screenshot(path=f'{logs_dir}/schema_521_error.png')
            return None
        finally:
            await browser.close()
            print("\n🏁 Browser closed")

async def main():
    print("\n" + "="*80)
    print("Starting Report 521 Schema Extraction")
    print("="*80 + "\n")
    
    result = await extract_report_521_schema()
    
    if result:
        print("\n" + "="*80)
        print("✅ EXTRACTION SUCCESSFUL!")
        print("="*80)
        print(f"\nExtracted {result['column_count']} columns from Report 521")
        print(f"\nFiles created:")
        print(f"1. /app/gofrugal-report-builder/database/schemas/report_521_schema.json")
        print(f"2. /app/gofrugal-report-builder/logs/schema_521_iframe.html")
        print(f"3. Screenshots in /app/gofrugal-report-builder/logs/")
        print("="*80 + "\n")
    else:
        print("\n" + "="*80)
        print("❌ EXTRACTION FAILED")
        print("="*80 + "\n")
    
    return result

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
