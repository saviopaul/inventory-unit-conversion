"""
Test fetching Report 474 with session setup
"""
import requests
import os
from dotenv import load_dotenv
import logging
import json
import time

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

base_url = "https://bbcohq.gofrugal.com"
username = os.getenv('GOFRUGAL_USERNAME')
password = os.getenv('GOFRUGAL_PASSWORD')

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
})

logger.info("="*80)
logger.info("STEP 1: LOGIN")
logger.info("="*80)

# Get login page
login_url = f"{base_url}/RayMedi_HQ/index.do"
response = session.get(login_url)
logger.info(f"✓ GET login page: {response.status_code}")

# Submit login
login_post_url = f"{base_url}/RayMedi_HQ/j_security_check"
data = {
    'j_username': username,
    'j_password': password
}

response = session.post(
    login_post_url,
    data=data,
    headers={
        'Content-Type': 'application/x-www-form-urlencoded',
        'Referer': login_url
    },
    allow_redirects=True
)

logger.info(f"✓ POST login: {response.status_code}")
cookies = session.cookies.get_dict()
logger.info(f"  Cookies: {list(cookies.keys())}")

if 'JSESSIONID' not in cookies:
    logger.error("Login failed!")
    exit(1)

logger.info(f"✓✓ Login successful! JSESSIONID: {cookies['JSESSIONID'][:20]}...")

# Wait a moment
time.sleep(1)

logger.info("\n" + "="*80)
logger.info("STEP 2: NAVIGATE TO REPORT PAGE (to set up session)")
logger.info("="*80)

# Navigate to the report page first
report_page_url = f"{base_url}/RayMedi_HQ/index.do#/smartreport?reportId=474&productId=2&HQ_DEFA_ROLE_ID=2&popup=false"
response = session.get(f"{base_url}/RayMedi_HQ/index.do")
logger.info(f"✓ Accessed dashboard: {response.status_code}")

time.sleep(1)

logger.info("\n" + "="*80)
logger.info("STEP 3: TRY SIMPLE EXPORT (CSV)")
logger.info("="*80)

# Try a simpler export call
export_url = f"{base_url}/smartreport/export"

# Simplified params based on the URL pattern
params = {
    'inline': 'false',
    'exportType': 'csv',
    'reportId': '474',
    'productId': '2',
    'HQ_DEFA_ROLE_ID': '2'
}

# Minimal payload
payload = {
    "reportId": 474,
    "productId": 2,
    "exportType": "csv"
}

logger.info(f"Calling: {export_url}")
logger.info(f"Params: {params}")
logger.info(f"Payload: {json.dumps(payload, indent=2)}")

response = session.post(
    export_url,
    params=params,
    json=payload,
    headers={
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/plain, */*',
        'Referer': f'{base_url}/RayMedi_HQ/index.do',
        'Origin': base_url
    }
)

logger.info(f"\nExport response: {response.status_code}")
logger.info(f"Response headers: {dict(response.headers)}")
logger.info(f"Response body: {response.text[:1000]}")

if response.status_code == 200:
    try:
        result = response.json()
        logger.info(f"\n✓✓✓ SUCCESS!")
        logger.info(f"Result: {json.dumps(result, indent=2)}")
        
        file_name = result.get('fileName') or result.get('filename')
        if file_name:
            logger.info(f"\nFile generated: {file_name}")
            
            # Try to download
            logger.info("\n" + "="*80)
            logger.info("STEP 4: DOWNLOAD FILE")
            logger.info("="*80)
            
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
            
            logger.info(f"Download response: {download_response.status_code}")
            logger.info(f"Content length: {len(download_response.content)} bytes")
            
            if download_response.status_code == 200:
                save_path = '/app/gofrugal-report-builder/database/downloads/test_report_474.csv'
                with open(save_path, 'wb') as f:
                    f.write(download_response.content)
                logger.info(f"✓✓✓ File saved: {save_path}")
                
                # Show preview
                with open(save_path, 'r') as f:
                    lines = f.readlines()[:5]
                    logger.info(f"\nFile preview (first 5 lines):")
                    for line in lines:
                        logger.info(f"  {line.strip()}")
            else:
                logger.error(f"Download failed: {download_response.text[:500]}")
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
else:
    logger.error(f"Export failed: {response.status_code}")
    logger.error(f"Error: {response.text[:1000]}")
