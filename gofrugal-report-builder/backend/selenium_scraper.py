"""
Selenium-based scraper for GoFrugal portal
"""
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_selenium_login():
    """Test login and dashboard access with Selenium"""
    
    username = os.getenv('GOFRUGAL_USERNAME')
    password = os.getenv('GOFRUGAL_PASSWORD')
    
    # Setup Chrome options - make it look like a real browser
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Anti-detection measures
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Enable JavaScript
    chrome_options.add_argument('--enable-javascript')
    
    # Use system chromium-driver
    service = Service('/usr/bin/chromedriver')
    
    logger.info("="*80)
    logger.info("TESTING WITH SELENIUM")
    logger.info("="*80)
    
    driver = None
    try:
        # Initialize driver
        logger.info("\nInitializing Chrome driver...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(10)
        
        logger.info("✓ Chrome driver initialized")
        
        # Step 1: Login
        logger.info("\nSTEP 1: Navigating to login page")
        login_url = "https://bbcohq.gofrugal.com/RayMedi_HQ/index.do"
        driver.get(login_url)
        
        time.sleep(3)
        logger.info(f"Current URL: {driver.current_url}")
        
        # Take screenshot
        driver.save_screenshot('/app/gofrugal-report-builder/logs/selenium_login_page.png')
        logger.info("✓ Login page screenshot saved")
        
        # Fill credentials
        logger.info("\nSTEP 2: Filling credentials")
        
        username_field = driver.find_element(By.NAME, 'j_username')
        password_field = driver.find_element(By.NAME, 'j_password')
        
        username_field.clear()
        username_field.send_keys(username)
        
        password_field.clear()
        password_field.send_keys(password)
        
        logger.info("✓ Credentials filled")
        
        # Submit
        logger.info("\nSTEP 3: Submitting login")
        submit_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_button.click()
        
        # Wait for navigation
        logger.info("Waiting for post-login redirect...")
        time.sleep(10)
        
        logger.info(f"URL after login: {driver.current_url}")
        driver.save_screenshot('/app/gofrugal-report-builder/logs/selenium_after_login.png')
        
        # Step 4: Navigate to dashboard
        logger.info("\nSTEP 4: Navigating to main dashboard")
        
        if 'mainIndex.do' not in driver.current_url:
            driver.get("https://bbcohq.gofrugal.com/RayMedi_HQ/mainIndex.do")
            time.sleep(10)
        
        logger.info(f"Dashboard URL: {driver.current_url}")
        driver.save_screenshot('/app/gofrugal-report-builder/logs/selenium_dashboard.png')
        
        # Step 5: Check for dashboard tabs
        logger.info("\nSTEP 5: Looking for dashboard tabs")
        
        tabs_found = []
        tab_names = ['Home', 'MDM', 'BPM', 'Reports', 'Accounts', 'Admin']
        
        for tab_name in tab_names:
            try:
                elements = driver.find_elements(By.XPATH, f"//*[text()='{tab_name}']")
                if elements:
                    tabs_found.append(tab_name)
                    logger.info(f"  ✓ Found tab: {tab_name}")
            except:
                pass
        
        if tabs_found:
            logger.info(f"\n✓✓✓ SUCCESS! Dashboard tabs visible: {tabs_found}")
        else:
            logger.info(f"\n✗ No dashboard tabs found")
            
            # Show what we do see
            logger.info("\nButtons on page:")
            buttons = driver.find_elements(By.TAG_NAME, 'button')
            for i, btn in enumerate(buttons[:10]):
                try:
                    text = btn.text
                    if text.strip():
                        logger.info(f"  Button {i+1}: {text.strip()}")
                except:
                    pass
        
        # Step 6: Try to navigate to Report 474
        if tabs_found:
            logger.info("\n✓ Dashboard loaded! Now trying to access Report 474...")
            
            report_url = "https://bbcohq.gofrugal.com/RayMedi_HQ/mainIndex.do?page=%2Fsmartreport%2Findex.html%23%2Freports%3FreportId%3D474%26productId%3D2"
            driver.get(report_url)
            
            logger.info("Waiting for report page to load...")
            time.sleep(20)  # Wait for SPA to load
            
            driver.save_screenshot('/app/gofrugal-report-builder/logs/selenium_report_474.png')
            logger.info(f"Report 474 URL: {driver.current_url}")
            
            # Look for Apply button
            try:
                apply_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'Apply')]")
                if apply_buttons:
                    logger.info(f"✓✓✓ Found {len(apply_buttons)} Apply button(s)!")
                    
                    # Try to click it
                    logger.info("Clicking Apply button...")
                    apply_buttons[0].click()
                    
                    time.sleep(15)  # Wait for report to generate
                    
                    driver.save_screenshot('/app/gofrugal-report-builder/logs/selenium_report_generated.png')
                    
                    # Look for Export button
                    export_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'Export') or contains(text(), 'CSV')]")
                    if export_buttons:
                        logger.info(f"✓✓✓ Found {len(export_buttons)} Export button(s)!")
                        for btn in export_buttons:
                            logger.info(f"  Button text: {btn.text}")
                    else:
                        logger.info("✗ Export button not found")
                else:
                    logger.info("✗ Apply button not found")
            except Exception as e:
                logger.error(f"Error accessing report: {e}")
        
        # Save page source for debugging
        with open('/app/gofrugal-report-builder/logs/selenium_page_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        logger.info("\n✓ Page source saved")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        if driver:
            try:
                driver.save_screenshot('/app/gofrugal-report-builder/logs/selenium_error.png')
            except:
                pass
    finally:
        if driver:
            driver.quit()
            logger.info("\n✓ Browser closed")


if __name__ == "__main__":
    test_selenium_login()
