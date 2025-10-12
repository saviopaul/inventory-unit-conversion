import asyncio
from playwright.async_api import async_playwright
import os
from pathlib import Path

async def test_report_521_load():
    """
    Test if Report 521 loads properly after clicking Apply
    Following the Puppeteer recording flow
    """
    print("="*80)
    print("🔍 TEST REPORT 521 DATA LOAD")
    print("="*80)
    
    logs_dir = "/app/gofrugal-report-builder/logs"
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
            print("✅ Logged in")
            
            # ===== STEP 2: NAVIGATE TO REPORT 521 =====
            print("\n📊 Step 2: Navigate to Report 521...")
            
            # Click through menu as per Puppeteer recording
            await page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll('a'));
                const reportsLink = links.find(link => link.textContent.trim() === 'Reports');
                if (reportsLink) reportsLink.click();
            }''')
            await asyncio.sleep(1)
            print("   ✅ Clicked Reports")
            
            await page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll('a'));
                const salesLink = links.find(link => link.textContent.trim() === 'Sales');
                if (salesLink) salesLink.click();
            }''')
            await asyncio.sleep(1)
            print("   ✅ Clicked Sales")
            
            await page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll('a'));
                const itemWiseLink = links.find(link => link.textContent.trim() === 'Item wise');
                if (itemWiseLink) itemWiseLink.click();
            }''')
            await asyncio.sleep(1)
            print("   ✅ Clicked Item wise")
            
            await page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll('a'));
                const reportLink = links.find(link => link.textContent.includes('Sale - Bill Wise'));
                if (reportLink) reportLink.click();
            }''')
            await asyncio.sleep(7)
            await page.screenshot(path=f'{logs_dir}/test_load_01_report_page.png')
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
                return False
            
            # ===== STEP 4: SET FILTERS AND CLICK APPLY =====
            print("\n📋 Step 4: Set filters and click Apply...")
            
            # Wait a bit for filters to be ready
            await asyncio.sleep(5)
            await page.screenshot(path=f'{logs_dir}/test_load_02_before_filters.png')
            
            # Following Puppeteer recording: Click on Standard header to expand
            print("   Expanding Standard filters...")
            try:
                standard_header = report_frame.locator('#filtersPanel div:nth-of-type(2) h4').first
                await standard_header.click()
                await asyncio.sleep(1)
                print("   ✅ Standard filters expanded")
            except:
                print("   ⚠️ Could not expand Standard filters")
            
            # Select "All Shop Name" (as per Puppeteer recording)
            print("   Selecting 'All Shop Name'...")
            try:
                shop_input = report_frame.locator('#\\31  > div > div > div:nth-of-type(2) input').first
                await shop_input.click()
                await asyncio.sleep(1)
                
                # Click the first option (All Shop Name)
                all_shop_option = report_frame.locator('li.select2-results__option--highlighted').first
                await all_shop_option.click()
                await asyncio.sleep(1)
                print("   ✅ Selected 'All Shop Name'")
            except Exception as e:
                print(f"   ⚠️ Could not select shop: {str(e)[:50]}")
            
            await page.screenshot(path=f'{logs_dir}/test_load_03_filters_set.png')
            
            # Click Apply button (as per Puppeteer recording)
            print("   Clicking Apply button...")
            try:
                apply_btn = report_frame.locator('#filtersPanel button.btn-primary:has-text("Apply")').first
                await apply_btn.wait_for(state='visible', timeout=10000)
                print("   ✅ Apply button found")
                
                await apply_btn.click()
                print("   ✅ Apply clicked!")
                
                # Wait for report to load (as per Puppeteer recording)
                print("   ⏳ Waiting for report data to load...")
                await asyncio.sleep(15)
                
                await page.screenshot(path=f'{logs_dir}/test_load_04_after_apply.png')
                
            except Exception as e:
                print(f"   ❌ Error clicking Apply: {str(e)[:100]}")
                return False
            
            # ===== STEP 5: CHECK IF DATA LOADED =====
            print("\n📊 Step 5: Checking if report data loaded...")
            
            # Count table rows
            row_count = await report_frame.evaluate('''() => {
                const rows = document.querySelectorAll('tbody tr');
                return rows.length;
            }''')
            print(f"   Table rows found: {row_count}")
            
            # Look for data table
            has_data_table = await report_frame.evaluate('''() => {
                const tables = document.querySelectorAll('table');
                for (const table of tables) {
                    const rows = table.querySelectorAll('tbody tr');
                    if (rows.length > 5) {  // More than 5 rows = likely data table
                        return true;
                    }
                }
                return false;
            }''')
            print(f"   Has data table with rows: {has_data_table}")
            
            # Get column headers from the largest table
            columns = await report_frame.evaluate('''() => {
                const tables = Array.from(document.querySelectorAll('table'));
                let mainTable = null;
                let maxRows = 0;
                
                // Find table with most rows
                for (const table of tables) {
                    const rows = table.querySelectorAll('tbody tr');
                    if (rows.length > maxRows) {
                        maxRows = rows.length;
                        mainTable = table;
                    }
                }
                
                if (mainTable && maxRows > 0) {
                    // Get headers from this table
                    const headers = Array.from(mainTable.querySelectorAll('thead th, thead td'));
                    const headerTexts = headers.map(h => h.textContent.trim()).filter(t => t && t.length > 0);
                    
                    return {
                        found: true,
                        rowCount: maxRows,
                        columns: headerTexts
                    };
                }
                
                return { found: false, rowCount: 0, columns: [] };
            }''')
            
            if columns['found']:
                print(f"   ✅ REPORT LOADED SUCCESSFULLY!")
                print(f"   Data rows: {columns['rowCount']}")
                print(f"   Columns found: {len(columns['columns'])}")
                print(f"\n   📋 Column Headers:")
                for i, col in enumerate(columns['columns'], 1):
                    print(f"      {i}. {col}")
                
                # Take final screenshot
                await page.screenshot(path=f'{logs_dir}/test_load_05_data_loaded.png', full_page=False)
                
                # Get sample data from first row
                print(f"\n   📄 Sample Data (first row):")
                first_row_data = await report_frame.evaluate('''() => {
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
                        const firstRow = mainTable.querySelector('tbody tr');
                        if (firstRow) {
                            const cells = Array.from(firstRow.querySelectorAll('td'));
                            return cells.map(c => c.textContent.trim());
                        }
                    }
                    return [];
                }''')
                
                for i, val in enumerate(first_row_data[:10], 1):  # First 10 values
                    print(f"      {i}. {val}")
                
                return True
            else:
                print(f"   ❌ NO DATA LOADED")
                print(f"   The report might be loading slowly or there's no data")
                
                # Take screenshot for debugging
                await page.screenshot(path=f'{logs_dir}/test_load_05_no_data.png', full_page=False)
                
                return False
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            await page.screenshot(path=f'{logs_dir}/test_load_error.png')
            return False
        finally:
            await browser.close()
            print("\n🏁 Browser closed")

async def main():
    print("\n" + "="*80)
    print("Testing if Report 521 loads data after clicking Apply")
    print("="*80 + "\n")
    
    result = await test_report_521_load()
    
    print("\n" + "="*80)
    if result:
        print("✅ SUCCESS - Report 521 loads data properly!")
        print("\nNext step: Extract column schema from loaded report")
    else:
        print("❌ FAILED - Report 521 did not load data")
        print("\nCheck screenshots in /app/gofrugal-report-builder/logs/")
    print("="*80 + "\n")
    
    return result

if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)
