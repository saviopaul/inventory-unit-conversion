"""
Try different variations of the export API call
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

logger.info(f"✓ Login successful")
time.sleep(1)

today = datetime.now().strftime('%d-%m-%Y')

# Try different variations
variations = [
    {
        "name": "Variation 1: Full payload from original code",
        "method": "POST",
        "params": {
            'inline': 'false',
            'exportType': 'csv',
            'reportId': '474',
            'productId': '2',
            'HQ_DEFA_ROLE_ID': '2',
            'popup': 'false',
            'fromdate': today,
            'todate': today,
            'gst_company': '-1',
            'areaCode': '-1',
            'retail': '-1'
        },
        "payload": {
            "groupby": None,
            "reportId": 474,
            "productId": 2,
            "displayLength": 50,
            "displayStart": 0,
            "filters": [],
            "sort": [],
            "isProcedureReport": False,
            "invtype": 1,
            "currencyPattern": "##,##,##,##0.00",
            "dateFormat": "DD-MM-YYYY",
            "useSessionCache": True,
            "groupBy": "-1"
        }
    },
    {
        "name": "Variation 2: Minimal payload",
        "method": "POST",
        "params": {
            'reportId': '474',
            'exportType': 'csv'
        },
        "payload": {
            "reportId": 474
        }
    },
    {
        "name": "Variation 3: GET request with params only",
        "method": "GET",
        "params": {
            'reportId': '474',
            'exportType': 'csv',
            'productId': '2'
        },
        "payload": None
    },
    {
        "name": "Variation 4: POST without params, all in payload",
        "method": "POST",
        "params": {},
        "payload": {
            "reportId": 474,
            "productId": 2,
            "exportType": "csv",
            "inline": False,
            "fromdate": today,
            "todate": today
        }
    },
    {
        "name": "Variation 5: Try /smartreport/csvexport endpoint",
        "method": "POST",
        "url_suffix": "/smartreport/csvexport",
        "params": {
            'reportId': '474',
            'productId': '2'
        },
        "payload": {
            "reportId": 474
        }
    },
    {
        "name": "Variation 6: Try form data instead of JSON",
        "method": "POST",
        "params": {},
        "payload": None,
        "form_data": {
            'reportId': '474',
            'exportType': 'csv',
            'productId': '2',
            'inline': 'false'
        }
    }
]

for i, variation in enumerate(variations, 1):
    logger.info(f"\n{'='*80}")
    logger.info(f"TESTING: {variation['name']}")
    logger.info(f"{'='*80}")
    
    export_url = f"{base_url}{variation.get('url_suffix', '/smartreport/export')}"
    method = variation['method']
    params = variation.get('params', {})
    payload = variation.get('payload')
    form_data = variation.get('form_data')
    
    try:
        if method == 'GET':
            response = session.get(
                export_url,
                params=params,
                headers={'Referer': f'{base_url}/RayMedi_HQ/index.do'}
            )
        elif form_data:
            response = session.post(
                export_url,
                params=params,
                data=form_data,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Referer': f'{base_url}/RayMedi_HQ/index.do'
                }
            )
        else:
            response = session.post(
                export_url,
                params=params,
                json=payload,
                headers={
                    'Content-Type': 'application/json',
                    'Referer': f'{base_url}/RayMedi_HQ/index.do'
                }
            )
        
        logger.info(f"Response: {response.status_code}")
        logger.info(f"Body: {response.text[:500]}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                logger.info(f"✓✓✓ SUCCESS with {variation['name']}!")
                logger.info(f"Result: {json.dumps(result, indent=2)}")
                
                # If we got a fileName, try to download
                file_name = result.get('fileName') or result.get('filename')
                if file_name:
                    logger.info(f"\nAttempting download of: {file_name}")
                    download_url = f"{base_url}/smartreport/download"
                    download_response = session.get(
                        download_url,
                        params={'fileName': file_name, 'exportType': 'csv'},
                        headers={'Referer': f'{base_url}/RayMedi_HQ/index.do'}
                    )
                    logger.info(f"Download: {download_response.status_code}, {len(download_response.content)} bytes")
                    
                    if download_response.status_code == 200:
                        save_path = f'/app/gofrugal-report-builder/database/downloads/report_474_v{i}.csv'
                        with open(save_path, 'wb') as f:
                            f.write(download_response.content)
                        logger.info(f"✓✓✓ SAVED: {save_path}")
                        break
            except:
                pass
        
        time.sleep(0.5)
        
    except Exception as e:
        logger.error(f"Error: {e}")

logger.info(f"\n{'='*80}")
logger.info("TEST COMPLETE")
logger.info(f"{'='*80}")
