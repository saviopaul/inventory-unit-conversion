"""
Direct API client for GoFrugal portal - No browser automation needed!
"""
import requests
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
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
        })
        
    def login(self):
        """Login and establish session"""
        logger.info("="*80)
        logger.info("LOGGING IN VIA API")
        logger.info("="*80)
        
        login_url = f"{self.base_url}/RayMedi_HQ/index.do"
        
        # First, get the login page to set initial cookies
        response = self.session.get(login_url)
        logger.info(f"✓ GET login page: {response.status_code}")
        
        # Submit login form
        login_post_url = f"{self.base_url}/RayMedi_HQ/j_security_check"
        
        data = {
            'j_username': self.username,
            'j_password': self.password
        }
        
        response = self.session.post(
            login_post_url,
            data=data,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Referer': login_url
            },
            allow_redirects=True
        )
        
        logger.info(f"✓ POST login: {response.status_code}")
        logger.info(f"  Final URL: {response.url}")
        
        # Check cookies
        cookies = self.session.cookies.get_dict()
        logger.info(f"  Cookies: {list(cookies.keys())}")
        
        if 'JSESSIONID' in cookies:
            logger.info(f"✓✓✓ Login successful! JSESSIONID: {cookies['JSESSIONID'][:20]}...")
            return True
        else:
            logger.error("✗ Login failed - no JSESSIONID")
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
            from_date = datetime.now().strftime('%Y-%m-%d')
        if not to_date:
            to_date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"Date range: {from_date} to {to_date}")
        
        # Step 1: Call export API to generate the file
        logger.info("\nSTEP 1: Calling export API...")
        
        export_url = f"{self.base_url}/smartreport/export"
        
        params = {
            'inline': 'false',
            'exportType': 'csv',  # CSV is easier to parse
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
        
        response = self.session.post(
            export_url,
            params=params,
            json=payload,
            headers={
                'Content-Type': 'application/json',
                'Referer': f'{self.base_url}/',
                'Origin': self.base_url
            }
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
                        headers={'Referer': f'{self.base_url}/'}
                    )
                    
                    logger.info(f"Download response: {download_response.status_code}")
                    
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


def main():
    """Main function"""
    client = GoFrugalAPIClient()
    
    # Login
    if not client.login():
        logger.error("Login failed!")
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
    main()
