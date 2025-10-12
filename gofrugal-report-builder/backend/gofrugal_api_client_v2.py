"""
GoFrugal API Client v2 - With complete authentication including CSRF and SSO tokens
Uses Playwright for initial authentication, then requests for API calls
"""
import requests
import asyncio
from playwright.async_api import async_playwright
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
import logging
import json
import time

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GoFrugalAPIClient:
    def __init__(self):
        self.base_url = "https://bbcohq.gofrugal.com"
        self.username = os.getenv('GOFRUGAL_USERNAME')
        self.password = os.getenv('GOFRUGAL_PASSWORD')
        self.session = requests.Session()
        self.cookies = {}
        
    async def authenticate_with_browser(self):
        """
        Use Playwright to complete full browser-based authentication
        and capture all required cookies (JSESSIONID, JSESSIONIDSSO, csrfCookie, _zcsr_tmp)
        """
        logger.info("="*80)
        logger.info("AUTHENTICATING WITH BROWSER TO GET ALL TOKENS")
        logger.info("="*80)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            try:
                logger.info("Step 1: Navigating to login page...")
                await page.goto(f'{self.base_url}/RayMedi_HQ/index.do', wait_until='networkidle')
                await asyncio.sleep(2)
                
                logger.info("Step 2: Entering credentials...")
                await page.fill('input[name="j_username"]', self.username)
                await page.fill('input[name="j_password"]', self.password)
                
                logger.info("Step 3: Submitting login...")
                await page.click('button[type="submit"]')
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(3)
                
                # Check for 2FA popup
                try:
                    two_fa_popup = await page.query_selector('text=Verify')
                    if two_fa_popup:
                        logger.warning("⚠️  2FA popup detected - clicking Skip/Close...")
                        # Try to close/skip the 2FA
                        skip_button = await page.query_selector('button:has-text("Skip")')
                        if skip_button:
                            await skip_button.click()
                            await asyncio.sleep(2)
                        else:
                            close_button = await page.query_selector('[aria-label="Close"]')
                            if close_button:
                                await close_button.click()
                                await asyncio.sleep(2)
                except Exception as e:
                    logger.debug(f"No 2FA popup or already handled: {e}")
                
                logger.info("Step 4: Navigating to dashboard to ensure full session...")
                await page.goto(f'{self.base_url}/RayMedi_HQ/index.do#/dashboard', wait_until='networkidle')
                await asyncio.sleep(2)
                
                logger.info("Step 4b: Navigating to Report 474 page...")
                await page.goto(f'{self.base_url}/RayMedi_HQ/index.do#/smartreport?reportId=474&productId=2&HQ_DEFA_ROLE_ID=2', wait_until='networkidle')
                await asyncio.sleep(3)
                
                logger.info("Step 5: Extracting all cookies...")
                cookies = await context.cookies()
                
                for cookie in cookies:
                    self.cookies[cookie['name']] = cookie['value']
                    logger.info(f"  ✓ {cookie['name']}: {cookie['value'][:20]}...")
                
                # Update requests session with all cookies
                for name, value in self.cookies.items():
                    self.session.cookies.set(name, value, domain='bbcohq.gofrugal.com')
                
                # Set proper headers
                self.session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Connection': 'keep-alive',
                    'sec-ch-ua': '"Chromium";v="141", "Not=A?Brand";v="24"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin'
                })
                
                logger.info(f"\n✓✓✓ Authentication complete!")
                logger.info(f"  Total cookies: {len(self.cookies)}")
                
                # Verify we have the critical tokens
                required_tokens = ['JSESSIONID', 'JSESSIONIDSSO', 'csrfCookie', '_zcsr_tmp']
                missing_tokens = [token for token in required_tokens if token not in self.cookies]
                
                if missing_tokens:
                    logger.warning(f"⚠️  Missing tokens: {missing_tokens}")
                    logger.info("  Available cookies: " + ", ".join(self.cookies.keys()))
                else:
                    logger.info(f"✓ All required tokens present!")
                
                await browser.close()
                return True
                
            except Exception as e:
                logger.error(f"Authentication error: {e}")
                import traceback
                traceback.print_exc()
                await browser.close()
                return False
    
    def fetch_report_474(self, from_date=None, to_date=None):
        """
        Fetch Report 474 (Current Stock) with conversions applied
        """
        logger.info("\n" + "="*80)
        logger.info("FETCHING REPORT 474 - CURRENT STOCK")
        logger.info("="*80)
        
        # Use today's date if not specified
        if not from_date:
            from_date = datetime.now().strftime('%d-%m-%Y')
        if not to_date:
            to_date = datetime.now().strftime('%d-%m-%Y')
        
        logger.info(f"Date range: {from_date} to {to_date}")
        
        # Step 1: Call export API to generate the file
        logger.info("\nSTEP 1: Calling export API...")
        
        export_url = f"{self.base_url}/smartreport/export"
        
        params = {
            'inline': 'false',
            'exportType': 'csv',
            'reportId': '474',
            'productId': '2',
            'HQ_DEFA_ROLE_ID': '2',
            'popup': 'false',
            'fromdate': from_date,
            'todate': to_date,
            'gst_company': '-1',
            'areaCode': '-1',
            'retail': '-1',
            'referrerProduct': '',
            'companyCode': '',
            'isHQ': 'false'
        }
        
        payload = {
            "groupby": None,
            "groupByLevel": None,
            "reportId": 474,
            "reportname": "Current Stock",
            "productId": 2,
            "displayLength": 50,
            "displayStart": 0,
            "advFilters": [],
            "advSumFilters": [],
            "filters": [],
            "sumFilters": [],
            "sort": [],
            "needColumns": False,
            "isProcedureReport": False,
            "invtype": 1,
            "dipsQry": "",
            "currencyPattern": "##,##,##,##0.00",
            "currencyDecimal": "2",
            "dateFormat": "DD-MM-YYYY",
            "numericalDecimal": "2",
            "qtyDecimal": "2",
            "colDisplay": "",
            "colExport": "",
            "allFilterValue": "",
            "isSubGroup": False,
            "defaultGroupByEnabled": True,
            "isMultipleUse": 1,
            "isPrintPreview": False,
            "timeFormat": "24",
            "isGrouped": False,
            "entireGroupBy": "",
            "useSessionCache": True,
            "isFromSetting": False,
            "groupBy": "-1",
            "hidedCols": ""
        }
        
        # Add CSRF token to headers if available
        export_headers = {
            'Content-Type': 'application/json',
            'Referer': f'{self.base_url}/RayMedi_HQ/index.do#/smartreport?reportId=474&productId=2',
            'Origin': self.base_url
        }
        
        # Add CSRF token headers if available
        if 'csrfCookie' in self.cookies:
            export_headers['X-CSRF-TOKEN'] = self.cookies['csrfCookie']
            export_headers['CSRF-Token'] = self.cookies['csrfCookie']
        
        response = self.session.post(
            export_url,
            params=params,
            json=payload,
            headers=export_headers
        )
        
        logger.info(f"Export API response: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                logger.info(f"Export response: {result}")
                
                # Extract fileName from response
                file_name = result.get('fileName') or result.get('filename')
                
                if file_name:
                    logger.info(f"✓ File generated: {file_name}")
                    
                    # Step 2: Download the file
                    logger.info("\nSTEP 2: Downloading file...")
                    
                    download_url = f"{self.base_url}/smartreport/download"
                    
                    download_params = {
                        'inline': 'false',
                        'exportType': 'csv',
                        'fileName': file_name,
                        'isPivot': 'false',
                        'login_Id': self.username,
                        'reportId': '474',
                        'productId': '2',
                        'HQ_DEFA_ROLE_ID': '2',
                        'popup': 'false',
                        'fromdate': from_date,
                        'todate': to_date,
                        'gst_company': '-1',
                        'areaCode': '-1',
                        'retail': '-1',
                        'referrerProduct': '',
                        'companyCode': '',
                        'isHQ': 'false'
                    }
                    
                    download_response = self.session.get(
                        download_url,
                        params=download_params,
                        headers={'Referer': f'{self.base_url}/RayMedi_HQ/index.do'}
                    )
                    
                    logger.info(f"Download response: {download_response.status_code}")
                    logger.info(f"Content length: {len(download_response.content)} bytes")
                    
                    if download_response.status_code == 200:
                        # Save the CSV
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        save_path = f'/app/gofrugal-report-builder/database/downloads/report_474_{timestamp}.csv'
                        
                        with open(save_path, 'wb') as f:
                            f.write(download_response.content)
                        
                        logger.info(f"✓✓✓ File downloaded: {save_path}")
                        
                        # Step 3: Parse and apply conversions
                        logger.info("\nSTEP 3: Parsing CSV and applying conversions...")
                        return self.apply_conversions(save_path)
                    else:
                        logger.error(f"Download failed: {download_response.text[:500]}")
                        return None
                else:
                    logger.error("No fileName in response")
                    return None
            except Exception as e:
                logger.error(f"Error parsing export response: {e}")
                logger.error(f"Response content: {response.text[:1000]}")
                return None
        else:
            logger.error(f"Export API failed: {response.status_code}")
            logger.error(f"Response: {response.text[:500]}")
            return None
    
    def apply_conversions(self, csv_file):
        """Apply conversion rules to add Cartons, Boxes, Pieces columns"""
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
    client = GoFrugalAPIClient()
    
    # Authenticate with browser to get all tokens
    if not await client.authenticate_with_browser():
        logger.error("Authentication failed!")
        return
    
    # Fetch Report 474 with conversions
    result = client.fetch_report_474()
    
    if result:
        logger.info(f"\n{'='*80}")
        logger.info(f"🎉 SUCCESS! Report saved to:")
        logger.info(f"   {result}")
        logger.info(f"{'='*80}")
    else:
        logger.error("\n❌ Failed to fetch report")


if __name__ == "__main__":
    asyncio.run(main())
