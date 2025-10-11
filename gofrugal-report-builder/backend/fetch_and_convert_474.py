"""
Complete solution: Fetch Report 474 and apply conversions
"""
import asyncio
import json
import pandas as pd
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fetch_report_474_and_convert():
    """
    1. Login to GoFrugal
    2. Navigate to Report 474
    3. Click Apply (use default filters - today's date)
    4. Click Export as CSV
    5. Download CSV
    6. Apply conversion rules (add Cartons, Boxes, Pieces columns)
    """
    
    url = os.getenv('GOFRUGAL_URL')
    username = os.getenv('GOFRUGAL_USERNAME')
    password = os.getenv('GOFRUGAL_PASSWORD')
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox']
    )
    
    # Set download path
    download_path = '/app/gofrugal-report-builder/database/downloads'
    os.makedirs(download_path, exist_ok=True)
    
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        accept_downloads=True
    )
    page = await context.new_page()
    
    try:
        # STEP 1: Login
        logger.info("="*80)
        logger.info("STEP 1: Logging in")
        logger.info("="*80)
        
        await page.goto(url, wait_until='networkidle', timeout=30000)
        await page.fill('input[type="text"]', username)
        await page.fill('input[type="password"]', password)
        await page.click('button[type="submit"]')
        await asyncio.sleep(5)
        
        logger.info("✓ Login successful")
        
        # STEP 2: Navigate to dashboard
        logger.info("\n" + "="*80)
        logger.info("STEP 2: Navigating to dashboard")
        logger.info("="*80)
        
        await page.goto("https://bbcohq.gofrugal.com/RayMedi_HQ/mainIndex.do", 
                       wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(5)
        
        logger.info("✓ Dashboard loaded")
        
        # STEP 3: Navigate to Report 474
        logger.info("\n" + "="*80)
        logger.info("STEP 3: Opening Report 474")
        logger.info("="*80)
        
        report_url = "https://bbcohq.gofrugal.com/RayMedi_HQ/mainIndex.do?page=%2Fsmartreport%2Findex.html%23%2Freports%3FreportId%3D474%26productId%3D2"
        await page.goto(report_url, wait_until='networkidle', timeout=60000)
        
        # Wait extra time for SPA to load
        logger.info("Waiting for filter page to load...")
        await asyncio.sleep(15)
        
        await page.screenshot(path='/app/gofrugal-report-builder/logs/step3_filter_page.png', full_page=True)
        logger.info("✓ Report 474 filter page loaded")
        
        # STEP 4: Click Apply button (use default filters)
        logger.info("\n" + "="*80)
        logger.info("STEP 4: Clicking Apply button (using default today's date)")
        logger.info("="*80)
        
        # Try different selectors for Apply button
        apply_selectors = [
            'button:has-text("Apply")',
            'button:text("Apply")',
            'text=Apply',
            '//button[contains(text(), "Apply")]',
            '//button[text()="Apply"]',
        ]
        
        apply_clicked = False
        for selector in apply_selectors:
            try:
                logger.info(f"Trying selector: {selector}")
                
                if selector.startswith('//'):
                    # XPath selector
                    button = await page.query_selector(f'xpath={selector}')
                else:
                    button = await page.query_selector(selector)
                
                if button:
                    logger.info(f"✓ Found Apply button!")
                    await button.click()
                    apply_clicked = True
                    logger.info("✓✓✓ Apply button clicked!")
                    break
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        if not apply_clicked:
            logger.error("Could not find Apply button!")
            # Take screenshot for debugging
            await page.screenshot(path='/app/gofrugal-report-builder/logs/apply_button_not_found.png', full_page=True)
            
            # Try to find all buttons
            all_buttons = await page.query_selector_all('button')
            logger.info(f"Found {len(all_buttons)} buttons on page:")
            for i, btn in enumerate(all_buttons[:20]):
                try:
                    text = await btn.inner_text()
                    logger.info(f"  Button {i+1}: {text}")
                except:
                    pass
        
        # STEP 5: Wait for report to generate
        logger.info("\n" + "="*80)
        logger.info("STEP 5: Waiting for report to generate...")
        logger.info("="*80)
        
        await asyncio.sleep(15)  # Wait for report data to load
        
        await page.screenshot(path='/app/gofrugal-report-builder/logs/step5_report_generated.png', full_page=True)
        logger.info("✓ Report generated")
        
        # STEP 6: Click Export as CSV
        logger.info("\n" + "="*80)
        logger.info("STEP 6: Clicking 'Export as CSV' button")
        logger.info("="*80)
        
        export_selectors = [
            'button:has-text("Export as CSV")',
            'button:text("Export as CSV")',
            'text=Export as CSV',
            '//button[contains(text(), "Export as CSV")]',
            '//button[text()="Export as CSV"]',
        ]
        
        export_clicked = False
        download_file = None
        
        for selector in export_selectors:
            try:
                logger.info(f"Trying selector: {selector}")
                
                if selector.startswith('//'):
                    button = await page.query_selector(f'xpath={selector}')
                else:
                    button = await page.query_selector(selector)
                
                if button:
                    logger.info(f"✓ Found Export button!")
                    
                    # Wait for download
                    async with page.expect_download(timeout=60000) as download_info:
                        await button.click()
                        download = await download_info.value
                        
                        # Save the file
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f'report_474_{timestamp}.csv'
                        save_path = os.path.join(download_path, filename)
                        
                        await download.save_as(save_path)
                        download_file = save_path
                        
                        logger.info(f"✓✓✓ CSV downloaded: {save_path}")
                        export_clicked = True
                        break
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        if not export_clicked:
            logger.error("Could not download CSV!")
            await page.screenshot(path='/app/gofrugal-report-builder/logs/export_failed.png', full_page=True)
            return None
        
        # STEP 7: Parse CSV and apply conversions
        logger.info("\n" + "="*80)
        logger.info("STEP 7: Parsing CSV and applying conversions")
        logger.info("="*80)
        
        # Load the downloaded CSV
        df_report = pd.read_csv(download_file)
        logger.info(f"✓ CSV loaded: {len(df_report)} rows, {len(df_report.columns)} columns")
        logger.info(f"Columns: {list(df_report.columns)}")
        
        # Show sample
        logger.info("\nFirst 3 rows:")
        logger.info(df_report.head(3).to_string())
        
        # Load conversion master
        conversion_file = '/app/conversion_master_clean.csv'
        if os.path.exists(conversion_file):
            df_conversion = pd.read_csv(conversion_file)
            logger.info(f"\n✓ Conversion master loaded: {len(df_conversion)} items")
            
            # Apply conversions - add Cartons, Boxes, Pieces columns
            logger.info("\nApplying conversions...")
            
            # Create conversion lookup dictionary
            # Assuming conversion master has: Item Code, Base Conversion Name, Conversion Volume/Qty, Conversion Name
            conversion_dict = {}
            for _, row in df_conversion.iterrows():
                item_code = row.get('Item Code')
                base_unit = row.get('Base Conversion Name', 'UNIT')
                conv_qty = row.get('Conversion Volume/Qty', 1)
                conv_name = row.get('Conversion Name', 'UNIT')
                
                if pd.notna(item_code):
                    conversion_dict[item_code] = {
                        'base_unit': base_unit,
                        'conversion_qty': float(conv_qty) if pd.notna(conv_qty) else 1,
                        'conversion_name': conv_name
                    }
            
            logger.info(f"Conversion rules for {len(conversion_dict)} items")
            
            # Find stock quantity column (could be "Stock", "Qty", "Quantity", "Current Stock", etc.)
            stock_col = None
            for col in df_report.columns:
                if any(keyword in col.lower() for keyword in ['stock', 'qty', 'quantity', 'balance']):
                    stock_col = col
                    logger.info(f"✓ Found stock column: {stock_col}")
                    break
            
            # Find item code column
            item_col = None
            for col in df_report.columns:
                if any(keyword in col.lower() for keyword in ['item code', 'itemcode', 'item_code', 'code']):
                    item_col = col
                    logger.info(f"✓ Found item code column: {item_col}")
                    break
            
            if stock_col and item_col:
                # Add conversion columns
                df_report['Cartons'] = 0
                df_report['Boxes'] = 0
                df_report['Pieces'] = 0
                
                for idx, row in df_report.iterrows():
                    item_code = row[item_col]
                    stock_qty = row[stock_col]
                    
                    if pd.notna(item_code) and pd.notna(stock_qty):
                        try:
                            stock_qty = float(stock_qty)
                            
                            # Get conversion rule for this item
                            if item_code in conversion_dict:
                                conv_info = conversion_dict[item_code]
                                conv_name = conv_info['conversion_name']
                                conv_qty = conv_info['conversion_qty']
                                
                                # Apply conversion logic
                                # Example: if 1 BOX = 12 PIECES, and stock is 120 PIECES
                                # Then: Boxes = 120 / 12 = 10
                                
                                if 'BOX' in conv_name.upper():
                                    df_report.at[idx, 'Boxes'] = stock_qty / conv_qty if conv_qty > 0 else stock_qty
                                elif 'CARTON' in conv_name.upper():
                                    df_report.at[idx, 'Cartons'] = stock_qty / conv_qty if conv_qty > 0 else stock_qty
                                else:
                                    # Default to pieces
                                    df_report.at[idx, 'Pieces'] = stock_qty
                            else:
                                # No conversion rule - default to pieces
                                df_report.at[idx, 'Pieces'] = stock_qty
                        except:
                            pass
                
                logger.info("✓ Conversions applied!")
                
                # Show sample with conversions
                logger.info("\nSample data with conversions (first 5 rows):")
                display_cols = [item_col, stock_col, 'Cartons', 'Boxes', 'Pieces']
                logger.info(df_report[display_cols].head(5).to_string())
            else:
                logger.warning(f"Could not find stock column or item code column. Stock: {stock_col}, Item: {item_col}")
        else:
            logger.warning("Conversion master file not found, skipping conversions")
        
        # STEP 8: Save final report
        logger.info("\n" + "="*80)
        logger.info("STEP 8: Saving final report")
        logger.info("="*80)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'/app/gofrugal-report-builder/database/report_474_with_conversions_{timestamp}.csv'
        df_report.to_csv(output_file, index=False)
        
        logger.info(f"✓✓✓ SUCCESS! Final report saved: {output_file}")
        logger.info(f"Total rows: {len(df_report)}")
        logger.info(f"Total columns: {len(df_report.columns)}")
        
        # Save summary
        summary = {
            'report_id': 474,
            'report_name': 'Current Stock',
            'downloaded_at': datetime.now().isoformat(),
            'total_items': len(df_report),
            'columns': list(df_report.columns),
            'original_file': download_file,
            'output_file': output_file
        }
        
        summary_file = f'/app/gofrugal-report-builder/database/report_474_summary_{timestamp}.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"✓ Summary saved: {summary_file}")
        
        return output_file
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        try:
            await page.screenshot(path='/app/gofrugal-report-builder/logs/error_final.png', full_page=True)
        except:
            pass
        
        return None
    finally:
        await browser.close()
        await playwright.stop()


if __name__ == "__main__":
    result = asyncio.run(fetch_report_474_and_convert())
    if result:
        print(f"\n{'='*80}")
        print(f"🎉 SUCCESS! Report saved to: {result}")
        print(f"{'='*80}")
    else:
        print(f"\n{'='*80}")
        print(f"❌ FAILED! Check logs for details")
        print(f"{'='*80}")
