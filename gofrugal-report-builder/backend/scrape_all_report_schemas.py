import asyncio
from playwright.async_api import async_playwright
import json
import os
from pathlib import Path
from datetime import datetime
import re

async def scrape_all_report_schemas():
    """
    Comprehensive scraper to extract all reports and their column schemas
    from the GoFrugal portal
    """
    print("="*80)
    print("🔍 GOFRUGAL REPORT SCHEMA SCRAPER")
    print("="*80)
    
    output_dir = "/app/gofrugal-report-builder/database/schemas"
    logs_dir = "/app/gofrugal-report-builder/logs"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    Path(logs_dir).mkdir(parents=True, exist_ok=True)
    
    master_schema = {
        "scraped_at": datetime.now().isoformat(),
        "portal_url": "https://bbcohq.gofrugal.com",
        "total_reports": 0,
        "reports": {}
    }
    
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
            await page.screenshot(path=f'{logs_dir}/scrape_01_logged_in.png')
            print("✅ Logged in successfully")
            
            # ===== STEP 2: DISCOVER ALL REPORTS =====
            print("\n📊 Step 2: Discovering all reports from menu...")
            
            # Click on Reports menu to expand it
            await page.evaluate('''() => {
                const links = Array.from(document.querySelectorAll('a'));
                const reportsLink = links.find(link => link.textContent.trim() === 'Reports');
                if (reportsLink) reportsLink.click();
            }''')
            await asyncio.sleep(2)
            
            # Get all report links from the navigation
            # Reports are typically in format: <a href="mainIndex.do?page=...reportId=XXX...">Report Name</a>
            report_links = await page.evaluate('''() => {
                const allLinks = Array.from(document.querySelectorAll('a'));
                const reportLinks = allLinks.filter(link => link.href && link.href.includes('reportId'));
                
                return reportLinks.map(link => {
                    const reportIdMatch = link.href.match(/reportId=(\\d+)/);
                    return {
                        name: link.textContent.trim(),
                        href: link.href,
                        reportId: reportIdMatch ? reportIdMatch[1] : null
                    };
                }).filter(item => item.reportId && item.name && item.name.length > 0);
            }''')
            
            print(f"✅ Found {len(report_links)} reports")
            
            # Remove duplicates by reportId
            unique_reports = {}
            for report in report_links:
                if report['reportId'] not in unique_reports:
                    unique_reports[report['reportId']] = report
            
            report_links = list(unique_reports.values())
            print(f"✅ {len(report_links)} unique reports after deduplication")
            
            # Save report list
            with open(f'{output_dir}/report_list.json', 'w') as f:
                json.dump(report_links, f, indent=2)
            print(f"   Saved report list to report_list.json")
            
            # ===== STEP 3: EXTRACT SCHEMA FROM EACH REPORT =====
            print(f"\n📋 Step 3: Extracting schemas from all reports...")
            
            # Option to limit reports for testing (set to None for all reports)
            max_reports = int(os.environ.get('MAX_REPORTS', len(report_links)))
            reports_to_process = report_links[:max_reports]
            
            print(f"   Processing {len(reports_to_process)} reports...")
            print(f"   Estimated time: ~{len(reports_to_process) * 15} seconds\n")
            
            successful_extractions = 0
            failed_extractions = 0
            
            for idx, report_info in enumerate(reports_to_process, 1):
                report_id = report_info['reportId']
                report_name = report_info['name']
                report_href = report_info['href']
                
                print(f"[{idx}/{len(report_links)}] Processing: {report_name} (ID: {report_id})")
                
                try:
                    # Navigate to the report
                    if report_href.startswith('http'):
                        report_url = report_href
                    else:
                        report_url = f"https://bbcohq.gofrugal.com/RayMedi_HQ/{report_href}"
                    
                    await page.goto(report_url, wait_until='networkidle', timeout=60000)
                    await asyncio.sleep(5)  # Wait for report to load
                    
                    # Find the report iframe (smartreport iframe)
                    report_frame = None
                    for frame in page.frames:
                        try:
                            if 'smartreport' in frame.url and f'reportId={report_id}' in frame.url:
                                report_frame = frame
                                break
                        except:
                            pass
                    
                    if not report_frame:
                        print(f"   ⚠️  No iframe found")
                        failed_extractions += 1
                        continue
                    
                    # Wait for report content to load
                    await asyncio.sleep(8)
                    
                    # Extract column headers
                    # Method 1: Try table headers (th)
                    columns = await report_frame.evaluate('''() => {
                        const headers = Array.from(document.querySelectorAll('th, thead td, .column-header'));
                        let cols = headers.map(h => h.textContent.trim()).filter(t => t && t.length > 0);
                        
                        // If no headers found, try data-ng-bind or other Angular directives
                        if (cols.length === 0) {
                            const ngBinds = Array.from(document.querySelectorAll('[data-ng-bind], [ng-bind]'));
                            cols = ngBinds.map(el => el.textContent.trim()).filter(t => t && t.length > 0);
                        }
                        
                        // Remove duplicates
                        return [...new Set(cols)];
                    }''')
                    
                    if len(columns) > 0:
                        print(f"   ✅ Extracted {len(columns)} columns")
                        
                        # Save individual report schema
                        report_schema = {
                            "report_id": report_id,
                            "report_name": report_name,
                            "report_url": report_url,
                            "extracted_at": datetime.now().isoformat(),
                            "column_count": len(columns),
                            "columns": columns
                        }
                        
                        # Add to master schema
                        master_schema["reports"][report_id] = report_schema
                        successful_extractions += 1
                        
                        # Save screenshot
                        screenshot_path = f'{logs_dir}/report_{report_id}.png'
                        await page.screenshot(path=screenshot_path)
                        
                        # Show first few columns
                        preview = columns[:5]
                        print(f"   Preview: {', '.join(preview)}{'...' if len(columns) > 5 else ''}")
                    else:
                        print(f"   ⚠️  No columns extracted")
                        failed_extractions += 1
                    
                    # Small delay between reports
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    print(f"   ❌ Error: {str(e)[:80]}")
                    failed_extractions += 1
                    continue
            
            # ===== STEP 4: SAVE MASTER SCHEMA =====
            print(f"\n💾 Step 4: Saving master schema...")
            
            master_schema["total_reports"] = len(master_schema["reports"])
            master_schema["successful_extractions"] = successful_extractions
            master_schema["failed_extractions"] = failed_extractions
            
            # Save master schema
            master_file = f'{output_dir}/master_schema.json'
            with open(master_file, 'w', encoding='utf-8') as f:
                json.dump(master_schema, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Master schema saved to: {master_file}")
            print(f"\n📊 Summary:")
            print(f"   Total reports found: {len(report_links)}")
            print(f"   Successfully extracted: {successful_extractions}")
            print(f"   Failed extractions: {failed_extractions}")
            if len(report_links) > 0:
                print(f"   Success rate: {(successful_extractions/len(report_links)*100):.1f}%")
            else:
                print(f"   Success rate: N/A (no reports found)")
            
            return master_schema
            
        except Exception as e:
            print(f"\n❌ Fatal Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            await browser.close()
            print("\n🏁 Browser closed")

async def main():
    print("\n" + "="*80)
    print("Starting GoFrugal Report Schema Extraction")
    print("="*80 + "\n")
    
    result = await scrape_all_report_schemas()
    
    if result:
        print("\n" + "="*80)
        print("✅ EXTRACTION COMPLETE!")
        print("="*80)
        print(f"\nFiles created:")
        print(f"1. /app/gofrugal-report-builder/database/schemas/master_schema.json")
        print(f"2. /app/gofrugal-report-builder/database/schemas/report_list.json")
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
