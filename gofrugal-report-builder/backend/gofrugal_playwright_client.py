"""
GoFrugal Client - Pure Playwright approach for Report 474
Intercepts the export API call made by the browser
"""
import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
import logging
import json
import time
import re

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GoFrugalPlaywrightClient:
    def __init__(self):
        self.base_url = "https://bbcohq.gofrugal.com"
        self.username = os.getenv('GOFRUGAL_USERNAME')
        self.password = os.getenv('GOFRUGAL_PASSWORD')
        self.export_response = None
        self.download_completed = False
        self.downloaded_file = None
        
    async def fetch_report_474(self, from_date=None, to_date=None):
        """
        Fetch Report 474 using Playwright to trigger the export
        """
        logger.info("="*80)
        logger.info("FETCHING REPORT 474 WITH PLAYWRIGHT")
        logger.info("="*80)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                accept_downloads=True
            )
            
            page = await context.new_page()
            
            # Track network responses
            export_file_name = None
            
            async def handle_response(response):
                nonlocal export_file_name
                if '/smartreport/export' in response.url:
                    logger.info(f"✓ Export API called: {response.status}")
                    try:
                        data = await response.json()
                        logger.info(f"Export response: {data}")
                        export_file_name = data.get('fileName') or data.get('filename')
                        if export_file_name:
                            logger.info(f"✓ File name: {export_file_name}")
                    except Exception as e:
                        logger.error(f"Error parsing export response: {e}")
            
            page.on('response', handle_response)
            
            try:
                logger.info("Step 1: Logging in...")
                await page.goto(f'{self.base_url}/RayMedi_HQ/index.do')
                await page.wait_for_load_state('networkidle')
                
                await page.fill('input[name="j_username"]', self.username)
                await page.fill('input[name="j_password"]', self.password)
                await page.click('button[type="submit"]')
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(3)
                
                # Handle 2FA popup if present
                try:
                    skip_button = await page.wait_for_selector('button:has-text("Skip")', timeout=5000)
                    if skip_button:
                        logger.info("  Clicking Skip on 2FA...")
                        await skip_button.click()
                        await asyncio.sleep(2)
                except:
                    logger.info("  No 2FA popup")
                
                logger.info("\nStep 2: Navigating to Report 474...")
                await page.goto(f'{self.base_url}/RayMedi_HQ/index.do#/smartreport?reportId=474&productId=2&HQ_DEFA_ROLE_ID=2')
                await asyncio.sleep(5)
                
                # Wait for report to load
                logger.info("  Waiting for report to load...")
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(3)
                
                # Take screenshot
                await page.screenshot(path='/app/gofrugal-report-builder/logs/report_loaded.png')
                logger.info("  Screenshot saved: report_loaded.png")
                
                logger.info("\nStep 3: Looking for export button...")
                
                # Try different selectors for export button
                export_selectors = [
                    'button:has-text("Export")',
                    'button:has-text("CSV")',
                    '[title="Export"]',
                    '.export-btn',
                    'button[ng-click*="export"]',
                    'a:has-text("Export")',
                    'span:has-text("Export")'
                ]
                
                export_button = None
                for selector in export_selectors:
                    try:
                        export_button = await page.wait_for_selector(selector, timeout=2000)
                        if export_button:
                            logger.info(f"  ✓ Found export button: {selector}")
                            break
                    except:
                        continue
                
                if not export_button:
                    # Try to find any button with "export" in attributes
                    logger.info("  Trying to find export option via page content...")
                    content = await page.content()
                    
                    # Save HTML for inspection
                    with open('/app/gofrugal-report-builder/logs/report_page.html', 'w') as f:
                        f.write(content)
                    logger.info("  HTML saved: report_page.html")
                    
                    # Try clicking via JavaScript evaluation
                    try:
                        await page.evaluate('''() => {
                            const buttons = document.querySelectorAll('button, a, span');
                            for (let btn of buttons) {
                                if (btn.textContent.toLowerCase().includes('export') || 
                                    btn.textContent.toLowerCase().includes('csv') ||
                                    btn.getAttribute('title')?.toLowerCase().includes('export')) {
                                    btn.click();
                                    return true;
                                }
                            }
                            return false;
                        }''')
                        logger.info("  Clicked export via JavaScript")
                        await asyncio.sleep(2)
                    except Exception as e:
                        logger.error(f"  Could not find export button: {e}")
                else:
                    logger.info("  Clicking export button...")
                    await export_button.click()
                    await asyncio.sleep(2)
                
                # Wait for export API call
                logger.info("\nStep 4: Waiting for export to complete...")
                await asyncio.sleep(5)
                
                if export_file_name:
                    logger.info(f"\n✓✓ Export successful! File: {export_file_name}")
                    
                    # Now download the file using the API
                    logger.info("\nStep 5: Downloading file...")
                    
                    download_url = f"{self.base_url}/smartreport/download?inline=false&exportType=csv&fileName={export_file_name}&reportId=474&productId=2"
                    
                    logger.info(f"  Download URL: {download_url}")
                    
                    # Navigate to download URL
                    download_response = await page.goto(download_url)
                    
                    if download_response and download_response.status == 200:
                        content = await download_response.body()
                        
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        save_path = f'/app/gofrugal-report-builder/database/downloads/report_474_{timestamp}.csv'
                        
                        with open(save_path, 'wb') as f:
                            f.write(content)
                        
                        logger.info(f"✓✓✓ File downloaded: {save_path}")
                        logger.info(f"  Size: {len(content)} bytes")
                        
                        await browser.close()
                        
                        # Apply conversions
                        return self.apply_conversions(save_path)
                    else:
                        logger.error(f"Download failed: {download_response.status if download_response else 'No response'}")
                else:
                    logger.error("❌ Export did not complete - no file name received")
                    logger.info("  Check logs/report_page.html and logs/report_loaded.png for debugging")
                
                await browser.close()
                return None
                
            except Exception as e:
                logger.error(f"Error: {e}")
                import traceback
                traceback.print_exc()
                await browser.close()
                return None
    
    def apply_conversions(self, csv_file):
        """Apply conversion rules to add Cartons, Boxes, Pieces columns"""
        logger.info(f"\n{'='*80}")
        logger.info(f"APPLYING CONVERSIONS")
        logger.info(f"{'='*80}")
        logger.info(f"Loading CSV: {csv_file}")
        
        try:
            df_report = pd.read_csv(csv_file)
            logger.info(f"✓ CSV loaded: {len(df_report)} rows, {len(df_report.columns)} columns")
            logger.info(f"Columns: {list(df_report.columns)}")
            
            # Show sample
            logger.info("\nFirst 3 rows:")
            print(df_report.head(3).to_string())
            
            # Load conversion master
            conversion_file = '/app/conversion_master_clean.csv'
            
            if not os.path.exists(conversion_file):
                logger.warning("Conversion master not found, skipping conversions")
                return csv_file
            
            df_conversion = pd.read_csv(conversion_file)
            logger.info(f"\n✓ Conversion master loaded: {len(df_conversion)} items")
            
            # Create conversion lookup
            conversion_dict = {}
            for _, row in df_conversion.iterrows():
                item_code = row.get('Item Code')
                base_unit = row.get('Base Conversion Name', 'UNIT')
                conv_qty = row.get('Conversion Volume/Qty', 1)
                conv_name = row.get('Conversion Name', 'UNIT')
                
                if pd.notna(item_code):
                    conversion_dict[str(item_code)] = {
                        'base_unit': base_unit,
                        'conversion_qty': float(conv_qty) if pd.notna(conv_qty) else 1,
                        'conversion_name': str(conv_name)
                    }
            
            logger.info(f"Conversion rules for {len(conversion_dict)} items")
            
            # Find relevant columns in report
            stock_col = None
            item_col = None
            
            # Look for stock column
            for col in df_report.columns:
                col_lower = str(col).lower()
                if any(keyword in col_lower for keyword in ['stock', 'qty', 'quantity', 'balance', 'closing']):
                    stock_col = col
                    logger.info(f"✓ Found stock column: {stock_col}")
                    break
            
            # Look for item code column
            for col in df_report.columns:
                col_lower = str(col).lower()
                if any(keyword in col_lower for keyword in ['item code', 'itemcode', 'item_code', 'code', 'item']):
                    item_col = col
                    logger.info(f"✓ Found item code column: {item_col}")
                    break
            
            if not stock_col or not item_col:
                logger.warning(f"Could not find required columns. Stock: {stock_col}, Item: {item_col}")
                return csv_file
            
            # Add conversion columns
            logger.info("\nApplying conversions...")
            
            df_report['Cartons'] = 0.0
            df_report['Boxes'] = 0.0
            df_report['Pieces'] = 0.0
            
            conversions_applied = 0
            
            for idx, row in df_report.iterrows():
                item_code = str(row[item_col]).strip()
                stock_qty = row[stock_col]
                
                if pd.notna(item_code) and pd.notna(stock_qty):
                    try:
                        stock_qty = float(stock_qty)
                        
                        # Get conversion rule
                        if item_code in conversion_dict:
                            conv_info = conversion_dict[item_code]
                            conv_name = conv_info['conversion_name'].upper()
                            conv_qty = conv_info['conversion_qty']
                            
                            # Apply conversion
                            if 'BOX' in conv_name:
                                df_report.at[idx, 'Boxes'] = stock_qty / conv_qty if conv_qty > 0 else stock_qty
                            elif 'CARTON' in conv_name:
                                df_report.at[idx, 'Cartons'] = stock_qty / conv_qty if conv_qty > 0 else stock_qty
                            else:
                                df_report.at[idx, 'Pieces'] = stock_qty
                            
                            conversions_applied += 1
                        else:
                            # No conversion rule - default to pieces
                            df_report.at[idx, 'Pieces'] = stock_qty
                    except Exception as e:
                        logger.debug(f"Error converting row {idx}: {e}")
            
            logger.info(f"✓ Conversions applied to {conversions_applied} items")
            
            # Save enhanced CSV
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'/app/gofrugal-report-builder/database/report_474_with_conversions_{timestamp}.csv'
            df_report.to_csv(output_file, index=False)
            
            logger.info(f"\n✓✓✓ SUCCESS! Enhanced report saved: {output_file}")
            
            # Show sample with conversions
            logger.info("\nSample data with conversions (first 5 rows):")
            display_cols = [item_col, stock_col, 'Cartons', 'Boxes', 'Pieces']
            print(df_report[display_cols].head(5).to_string())
            
            return output_file
            
        except Exception as e:
            logger.error(f"Error applying conversions: {e}")
            import traceback
            traceback.print_exc()
            return csv_file


async def main():
    """Main function"""
    client = GoFrugalPlaywrightClient()
    
    # Fetch Report 474
    result = await client.fetch_report_474()
    
    if result:
        logger.info(f"\n{'='*80}")
        logger.info(f"🎉 SUCCESS! Report saved to:")
        logger.info(f"   {result}")
        logger.info(f"{'='*80}")
    else:
        logger.error("\n❌ Failed to fetch report")


if __name__ == "__main__":
    asyncio.run(main())
