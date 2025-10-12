import asyncio
from playwright.async_api import async_playwright
import json
from pathlib import Path
from datetime import datetime

async def test_report_521_exact_flow():
    """
    Follow the EXACT Puppeteer recording flow for Report 521
    """
    print("="*80)
    print("🔍 REPORT 521 - EXACT RECORDING FLOW")
    print("="*80)
    
    logs_dir = "/app/gofrugal-report-builder/logs"
    output_dir = "/app/gofrugal-report-builder/database/schemas"
    Path(logs_dir).mkdir(parents=True, exist_ok=True)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1388, 'height': 913},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        try:
            # STEP 1: Login
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
            
            # STEP 2: Navigate - Reports → Analysis → Sale - Bill Wise Item Detailed
            print("\n📊 Step 2: Navigate to Report 521...")
            print("   (Following recording: Reports → Analysis → Item Wise → Report 521)")
            
            # Click Reports
            await page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll('a'));
                const reportsLink = links.find(link => link.textContent.trim() === 'Reports');
                if (reportsLink) reportsLink.click();
            }''')
            await asyncio.sleep(1)
            print("   ✅ Clicked Reports")
            
            # Click Sales (parent category)
            await page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll('a'));
                const salesLink = links.find(link => link.textContent.trim() === 'Sales');
                if (salesLink) salesLink.click();
            }''')
            await asyncio.sleep(1)
            print("   ✅ Clicked Sales")
            
            # Click Analysis (as per recording)
            await page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll('a'));
                const analysisLink = links.find(link => link.textContent.trim() === 'Analysis');
                if (analysisLink) analysisLink.click();
            }''')
            await asyncio.sleep(1)
            print("   ✅ Clicked Analysis")
            
            # Click Sale - Bill Wise Item Detailed
            await page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll('a'));
                const reportLink = links.find(link => link.textContent.includes('Sale - Bill Wise'));
                if (reportLink) reportLink.click();
            }''')
            await asyncio.sleep(7)
            await page.screenshot(path=f'{logs_dir}/exact_01_report_page.png')
            print("✅ Report 521 page loaded")
            
            # STEP 3: Find iframe
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
            
            # STEP 4: First Apply click (as per recording)
            print("\n📋 Step 4: Click Apply (first time - to load filter form)...")
            await asyncio.sleep(3)
            try:
                apply_btn = report_frame.locator('#filtersPanel button.btn-primary:has-text("Apply")').first
                await apply_btn.click()
                print("   ✅ First Apply clicked")
                await asyncio.sleep(2)
            except Exception as e:
                print(f"   ⚠️ First Apply failed: {str(e)[:50]}")
            
            # STEP 5: Select Shop Name
            print("\n🏪 Step 5: Select 'All Shop Name'...")
            await asyncio.sleep(2)
            try:
                # Click on the shop input
                shop_input = report_frame.locator('#\\31  > div > div > div:nth-of-type(2) input').first
                await shop_input.click()
                await asyncio.sleep(1)
                print("   ✅ Shop selector clicked")
                
                # Select "All Shop Name" (first highlighted option)
                all_shop = report_frame.locator('li.select2-results__option--highlighted').first
                await all_shop.click()
                await asyncio.sleep(1)
                print("   ✅ 'All Shop Name' selected")
            except Exception as e:
                print(f"   ⚠️ Shop selection failed: {str(e)[:50]}")
            
            await page.screenshot(path=f'{logs_dir}/exact_02_shop_selected.png')
            
            # STEP 6: Collapse Standard filters (double click as per recording)
            print("\n📦 Step 6: Collapse Standard filters...")
            try:
                standard_header = report_frame.locator('div:nth-of-type(2) h4 span').first
                await standard_header.dblclick()
                await asyncio.sleep(1)
                print("   ✅ Standard filters collapsed")
            except Exception as e:
                print(f"   ⚠️ Collapse failed: {str(e)[:50]}")
            
            # STEP 7: Save filters (as per recording)
            print("\n💾 Step 7: Click 'Save this filters'...")
            try:
                save_btn = report_frame.locator('div:nth-of-type(2) > a:has-text("Save this filters")').first
                await save_btn.click()
                await asyncio.sleep(1)
                print("   ✅ Filters saved")
            except Exception as e:
                print(f"   ⚠️ Save filters failed: {str(e)[:50]}")
            
            # STEP 8: Second Apply click (to actually load data)
            print("\n✅ Step 8: Click Apply (second time - to load report data)...")
            await asyncio.sleep(1)
            try:
                apply_btn2 = report_frame.locator('#filtersPanel button.btn-primary:has-text("Apply")').first
                await apply_btn2.click()
                print("   ✅ Second Apply clicked")
                
                print("   ⏳ Waiting for data to load...")
                await asyncio.sleep(15)
                
                await page.screenshot(path=f'{logs_dir}/exact_03_data_loading.png')
            except Exception as e:
                print(f"   ❌ Second Apply failed: {str(e)[:50]}")
                return None
            
            # STEP 9: Extract schema
            print("\n📊 Step 9: Extract column schema...")
            
            # Check if data loaded
            row_count = await report_frame.evaluate('''() => {
                const rows = document.querySelectorAll('tbody tr');
                return rows.length;
            }''')
            print(f"   Data rows found: {row_count}")
            
            if row_count > 0:
                # Extract columns from the data table
                schema_info = await report_frame.evaluate('''() => {
                    // Find the main data table
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
                    
                    if (!mainTable) return { success: false, columns: [], rows: 0 };
                    
                    // Get headers
                    const headerRow = mainTable.querySelector('thead tr');
                    if (!headerRow) return { success: false, columns: [], rows: maxRows };
                    
                    const headers = Array.from(headerRow.querySelectorAll('th, td'));
                    const columns = headers.map(h => h.textContent.trim()).filter(t => t && t.length > 0);
                    
                    // Get sample data from first row
                    const firstDataRow = mainTable.querySelector('tbody tr');
                    const sampleData = firstDataRow ? 
                        Array.from(firstDataRow.querySelectorAll('td')).map(c => c.textContent.trim()) : 
                        [];
                    
                    return {
                        success: true,
                        columns: columns,
                        rows: maxRows,
                        sampleData: sampleData
                    };
                }''')
                
                if schema_info['success'] and len(schema_info['columns']) > 0:
                    print(f"   ✅ Schema extracted successfully!")
                    print(f"   Columns found: {len(schema_info['columns'])}")
                    print(f"   Data rows: {schema_info['rows']}")
                    
                    print(f"\n   📋 Column Headers:")
                    for i, col in enumerate(schema_info['columns'], 1):
                        print(f"      {i}. {col}")
                    
                    print(f"\n   📄 Sample Data (first row):")
                    for i, val in enumerate(schema_info['sampleData'][:10], 1):
                        print(f"      {i}. {val}")
                    
                    # Save schema
                    report_schema = {
                        "report_id": "521",
                        "report_name": "Sale - Bill Wise Item Detailed",
                        "navigation_path": "Reports → Sales → Analysis → Sale - Bill Wise Item Detailed",
                        "extracted_at": datetime.now().isoformat(),
                        "column_count": len(schema_info['columns']),
                        "columns": schema_info['columns'],
                        "data_row_count": schema_info['rows'],
                        "sample_data": schema_info['sampleData']
                    }
                    
                    schema_file = f'{output_dir}/report_521_schema_complete.json'
                    with open(schema_file, 'w', encoding='utf-8') as f:
                        json.dump(report_schema, f, indent=2, ensure_ascii=False)
                    
                    print(f"\n   ✅ Schema saved to: {schema_file}")
                    
                    await page.screenshot(path=f'{logs_dir}/exact_04_final.png')
                    
                    return report_schema
                else:
                    print(f"   ⚠️ Could not extract column headers")
                    print(f"   But found {schema_info['rows']} data rows")
                    return None
            else:
                print(f"   ❌ No data rows found")
                await page.screenshot(path=f'{logs_dir}/exact_error_no_data.png')
                return None
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            await page.screenshot(path=f'{logs_dir}/exact_error.png')
            return None
        finally:
            await browser.close()
            print("\n🏁 Browser closed")

async def main():
    print("\n" + "="*80)
    print("Testing Report 521 with EXACT Puppeteer Recording Flow")
    print("="*80 + "\n")
    
    result = await test_report_521_exact_flow()
    
    if result:
        print("\n" + "="*80)
        print("✅ SUCCESS!")
        print("="*80)
        print(f"\n✅ Extracted {result['column_count']} columns from Report 521")
        print(f"✅ Found {result['data_row_count']} data rows")
        print(f"\nSchema saved to:")
        print(f"  /app/gofrugal-report-builder/database/schemas/report_521_schema_complete.json")
        print("="*80 + "\n")
    else:
        print("\n" + "="*80)
        print("❌ FAILED")
        print("="*80 + "\n")
    
    return result

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
