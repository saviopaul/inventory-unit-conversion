"""
Use Playwright to capture the actual API call made when exporting Report 474
"""
import asyncio
from playwright.async_api import async_playwright
import json
import os
from dotenv import load_dotenv

load_dotenv()

username = os.getenv('GOFRUGAL_USERNAME')
password = os.getenv('GOFRUGAL_PASSWORD')

captured_requests = []

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        page = await context.new_page()
        
        # Capture network requests
        async def log_request(request):
            if 'smartreport' in request.url and ('export' in request.url or 'download' in request.url):
                print(f"\n{'='*80}")
                print(f"🎯 CAPTURED: {request.method} {request.url}")
                print(f"{'='*80}")
                print(f"Headers:")
                for key, value in request.headers.items():
                    if key.lower() not in ['user-agent', 'host']:
                        print(f"  {key}: {value}")
                
                if request.post_data:
                    print(f"\nPost Data:")
                    try:
                        post_json = json.loads(request.post_data)
                        print(json.dumps(post_json, indent=2))
                    except:
                        print(f"  {request.post_data[:500]}")
                
                captured_requests.append({
                    'method': request.method,
                    'url': request.url,
                    'headers': dict(request.headers),
                    'post_data': request.post_data
                })
        
        page.on('request', log_request)
        
        print("Step 1: Navigating to login page...")
        await page.goto('https://bbcohq.gofrugal.com/RayMedi_HQ/index.do')
        await page.wait_for_load_state('networkidle')
        
        print("Step 2: Entering credentials...")
        await page.fill('input[name="j_username"]', username)
        await page.fill('input[name="j_password"]', password)
        
        print("Step 3: Clicking login...")
        await page.click('button[type="submit"]')
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)
        
        print("\nStep 4: Navigating to Report 474...")
        # Try to navigate to the report
        await page.goto('https://bbcohq.gofrugal.com/RayMedi_HQ/index.do#/smartreport?reportId=474&productId=2')
        await asyncio.sleep(5)
        
        print("\nStep 5: Looking for export button...")
        await page.screenshot(path='/app/gofrugal-report-builder/logs/report_page.png')
        
        # Wait for user to manually trigger export
        print("\n" + "="*80)
        print("MANUAL ACTION REQUIRED:")
        print("1. The browser window should be open")
        print("2. Navigate to Report 474 if needed")
        print("3. Click the EXPORT button")
        print("4. We will capture the API call")
        print("="*80)
        print("\nWaiting 60 seconds for manual export action...")
        
        await asyncio.sleep(60)
        
        await browser.close()
        
        # Save captured requests
        if captured_requests:
            print("\n" + "="*80)
            print("CAPTURED REQUESTS:")
            print("="*80)
            for req in captured_requests:
                print(f"\n{req['method']} {req['url']}")
                if req['post_data']:
                    print(f"Data: {req['post_data'][:200]}")
            
            with open('/app/gofrugal-report-builder/logs/captured_api_calls.json', 'w') as f:
                json.dump(captured_requests, f, indent=2)
            print("\n✓ Saved to: /app/gofrugal-report-builder/logs/captured_api_calls.json")
        else:
            print("\n❌ No export API calls captured")

if __name__ == '__main__':
    asyncio.run(main())
