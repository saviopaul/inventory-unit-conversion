"""
Try fetching report data first, then exporting
"""
import requests
import os
from dotenv import load_dotenv
import logging
import json
import time
from datetime import datetime

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

base_url = "https://bbcohq.gofrugal.com"
username = os.getenv('GOFRUGAL_USERNAME')
password = os.getenv('GOFRUGAL_PASSWORD')

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
})

# Login
logger.info("Logging in...")
login_url = f"{base_url}/RayMedi_HQ/index.do"
session.get(login_url)

login_post_url = f"{base_url}/RayMedi_HQ/j_security_check"
response = session.post(
    login_post_url,
    data={'j_username': username, 'j_password': password},
    headers={'Content-Type': 'application/x-www-form-urlencoded', 'Referer': login_url}
)

cookies = session.cookies.get_dict()
if 'JSESSIONID' not in cookies:
    logger.error("Login failed!")
    exit(1)

logger.info(f"✓ Login successful: {cookies['JSESSIONID'][:20]}...")
time.sleep(1)

today = datetime.now().strftime('%d-%m-%Y')

# Step 1: Try to fetch the report data first (this might initialize the report in session)
logger.info("\n" + "="*80)
logger.info("STEP 1: Fetching report data (to initialize session)")
logger.info("="*80)

data_url = f"{base_url}/smartreport/data"

data_params = {
    'reportId': '474',
    'productId': '2',
    'HQ_DEFA_ROLE_ID': '2',
    'fromdate': today,
    'todate': today
}

data_payload = {
    "reportId": 474,
    "productId": 2,
    "displayLength": 10,
    "displayStart": 0,
    "filters": [],
    "sort": [],
    "needColumns": True,
    "useSessionCache": False
}

response = session.post(
    data_url,
    params=data_params,
    json=data_payload,
    headers={
        'Content-Type': 'application/json',
        'Referer': f'{base_url}/RayMedi_HQ/index.do'
    }
)

logger.info(f"Data fetch response: {response.status_code}")

if response.status_code == 200:
    try:
        data_result = response.json()
        logger.info(f"✓ Got data response")
        logger.info(f"Keys: {list(data_result.keys())}")
        
        if 'aaData' in data_result:
            logger.info(f"Records: {len(data_result['aaData'])}")
        if 'iTotalRecords' in data_result:
            logger.info(f"Total records: {data_result['iTotalRecords']}")
            
    except Exception as e:
        logger.error(f"Error parsing data response: {e}")
else:
    logger.warning(f"Data fetch returned: {response.status_code}")
    logger.info(f"Response: {response.text[:500]}")

time.sleep(2)

# Step 2: Now try export with the session initialized
logger.info("\n" + "="*80)
logger.info("STEP 2: Now trying export (with initialized session)")
logger.info("="*80)

export_url = f"{base_url}/smartreport/export"

export_params = {
    'inline': 'false',
    'exportType': 'csv',
    'reportId': '474',
    'productId': '2',
    'HQ_DEFA_ROLE_ID': '2',
    'fromdate': today,
    'todate': today
}

export_payload = {
    "reportId": 474,
    "productId": 2,
    "displayLength": 50,
    "displayStart": 0,
    "filters": [],
    "sort": [],
    "needColumns": False,
    "useSessionCache": True
}

response = session.post(
    export_url,
    params=export_params,
    json=export_payload,
    headers={
        'Content-Type': 'application/json',
        'Referer': f'{base_url}/RayMedi_HQ/index.do'
    }
)

logger.info(f"Export response: {response.status_code}")
logger.info(f"Response: {response.text[:500]}")

if response.status_code == 200:
    try:
        result = response.json()
        logger.info(f"✓✓✓ EXPORT SUCCESS!")
        logger.info(f"Result: {json.dumps(result, indent=2)}")
        
        file_name = result.get('fileName') or result.get('filename')
        if file_name:
            logger.info(f"\n Downloading: {file_name}")
            
            download_url = f"{base_url}/smartreport/download"
            download_params = {
                'inline': 'false',
                'exportType': 'csv',
                'fileName': file_name,
                'reportId': '474',
                'productId': '2'
            }
            
            download_response = session.get(
                download_url,
                params=download_params,
                headers={'Referer': f'{base_url}/RayMedi_HQ/index.do'}
            )
            
            logger.info(f"Download: {download_response.status_code}, {len(download_response.content)} bytes")
            
            if download_response.status_code == 200:
                save_path = '/app/gofrugal-report-builder/database/downloads/report_474_success.csv'
                with open(save_path, 'wb') as f:
                    f.write(download_response.content)
                logger.info(f"✓✓✓ FILE SAVED: {save_path}")
                
                # Preview
                with open(save_path, 'r') as f:
                    lines = f.readlines()[:3]
                    logger.info(f"\nPreview:")
                    for line in lines:
                        logger.info(f"  {line.strip()}")
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
else:
    logger.error("Export still failed after data fetch")
