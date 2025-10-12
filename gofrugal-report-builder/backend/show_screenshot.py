"""
Login and show screenshot
"""
import asyncio
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv

load_dotenv()

username = os.getenv('GOFRUGAL_USERNAME')
password = os.getenv('GOFRUGAL_PASSWORD')

async def main():
    print("Logging in and taking screenshot...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        # Step 1: Go to login
        print("1. Opening login page...")
        await page.goto('https://bbcohq.gofrugal.com/RayMedi_HQ/index.do')
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)
        await page.screenshot(path='/app/gofrugal-report-builder/logs/current_1_login_page.png', full_page=True)
        print("   Screenshot saved: current_1_login_page.png")
        
        # Step 2: Fill and submit login
        print("2. Filling login form...")
        await page.fill('input[name="j_username"]', username)
        await page.fill('input[name="j_password"]', password)
        await page.screenshot(path='/app/gofrugal-report-builder/logs/current_2_form_filled.png', full_page=True)
        print("   Screenshot saved: current_2_form_filled.png")
        
        print("3. Clicking login...")
        await page.click('button[type="submit"]')
        await asyncio.sleep(5)
        await page.screenshot(path='/app/gofrugal-report-builder/logs/current_3_after_login_5s.png', full_page=True)
        print("   Screenshot saved: current_3_after_login_5s.png")
        
        # Step 3: Wait more and check
        print("4. Waiting more (total 10s)...")
        await asyncio.sleep(5)
        await page.screenshot(path='/app/gofrugal-report-builder/logs/current_4_after_login_10s.png', full_page=True)
        print("   Screenshot saved: current_4_after_login_10s.png")
        
        print(f"   Current URL: {page.url}")
        
        # Step 4: Try navigating to report
        print("5. Navigating to Report 474...")
        await page.goto('https://bbcohq.gofrugal.com/RayMedi_HQ/index.do#/smartreport?reportId=474&productId=2')
        await asyncio.sleep(8)
        await page.screenshot(path='/app/gofrugal-report-builder/logs/current_5_report_page.png', full_page=True)
        print("   Screenshot saved: current_5_report_page.png")
        
        print(f"   Current URL: {page.url}")
        
        await browser.close()
        
        print("\n✓ All screenshots saved to /app/gofrugal-report-builder/logs/")
        print("  Check current_*.png files")

if __name__ == "__main__":
    asyncio.run(main())
