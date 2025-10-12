"""
Test GoFrugal WebReporter API for Current Stock
Based on the documentation found
"""
import requests
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

username = os.getenv('GOFRUGAL_USERNAME')
password = os.getenv('GOFRUGAL_PASSWORD')

# Try different base URLs
base_urls = [
    'https://bbcohq.gofrugal.com',
    'http://bbcohq.gofrugal.com',
    'https://bbcohq.gofrugal.com:8482',
]

endpoints = [
    '/WebReporter/api/v1/items',
    '/api/v1/items',
    '/webreporter/items',
]

logger.info("Testing GoFrugal WebReporter API endpoints...")
logger.info("="*80)

session = requests.Session()

for base_url in base_urls:
    logger.info(f"\nTrying base URL: {base_url}")
    
    for endpoint in endpoints:
        full_url = f"{base_url}{endpoint}"
        logger.info(f"  Testing: {full_url}")
        
        # Try with different auth methods
        auth_methods = [
            {"name": "No auth", "headers": {}},
            {"name": "X-Auth-Token", "headers": {"X-Auth-Token": "admin1"}},
            {"name": "Authorization Bearer", "headers": {"Authorization": f"Bearer {username}"}},
            {"name": "Basic Auth", "auth": (username, password)},
        ]
        
        for auth_method in auth_methods:
            try:
                headers = auth_method.get("headers", {})
                auth = auth_method.get("auth")
                
                response = requests.get(
                    full_url,
                    headers=headers,
                    auth=auth,
                    timeout=5,
                    verify=False
                )
                
                logger.info(f"    [{auth_method['name']}] Status: {response.status_code}")
                
                if response.status_code == 200:
                    logger.info(f"    ✓✓✓ SUCCESS! Found working endpoint!")
                    logger.info(f"    URL: {full_url}")
                    logger.info(f"    Auth: {auth_method['name']}")
                    logger.info(f"    Response: {response.text[:500]}")
                    break
                elif response.status_code in [401, 403]:
                    logger.info(f"    Auth required")
                elif response.status_code == 404:
                    logger.info(f"    Not found")
                    
            except requests.exceptions.ConnectionError:
                logger.info(f"    Connection failed")
                break
            except Exception as e:
                logger.info(f"    Error: {str(e)[:50]}")
                
logger.info("\n" + "="*80)
logger.info("WebReporter API test complete")
logger.info("="*80)
