import os
import time
import logging
from urllib.parse import unquote
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

load_dotenv()
logger = logging.getLogger(__name__)

# -----------------------------------------
# Configuration
# -----------------------------------------
VEEX_LOGIN_URL = os.getenv("VEEX_LOGIN_URL", "https://charter.veexinc.net/")
VEEX_DASHBOARD_URL = "https://charter.veexinc.net/home/dashboard"
VEEX_RESULTS_URL = "https://charter.veexinc.net/home/result-and-report/view"
VEEX_USERNAME = os.getenv("VEEX_USERNAME")
# Handle URL-encoded password (e.g., %23 for # character)
VEEX_PASSWORD = unquote(os.getenv("VEEX_PASSWORD", "")) if os.getenv("VEEX_PASSWORD") else None

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# -----------------------------------------
# Main Search Function
# -----------------------------------------
def playwright_search(job_id: str, headless=True, timeout=60000) -> dict:
    """
    Logs in to VeEX portal using Playwright, searches for job ID, and extracts data.
    Returns structured job data dictionary.
    """
    logger.info(f"Searching for Job ID: {job_id}")
    
    with sync_playwright() as p:
        try:
            # Launch browser with anti-detection settings
            browser = p.chromium.launch(
                headless=headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            )
            
            # Create context with realistic browser settings
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={"width": 1920, "height": 1080},
                locale='en-US',
                timezone_id='America/New_York',
                permissions=[],
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                }
            )
            
            # Add JavaScript to make browser look less like a bot
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            page = context.new_page()

            # Go to results page (will redirect to login if needed)
            page.goto(VEEX_RESULTS_URL, timeout=timeout, wait_until="networkidle")
            page.wait_for_timeout(10000)
            
            current_url = page.url
            
            username_selectors = [
                'input[placeholder="Username"]',
                'input[type="text"]',
                'input[name="username"]',
                'input#username',
                'input[formcontrolname="username"]'
            ]
            
            password_selectors = [
                'input[placeholder="Password"]',
                'input[type="password"]',
                'input[name="password"]',
                'input#password',
                'input[formcontrolname="password"]'
            ]
            
            # Try to find username field
            username_field = None
            for selector in username_selectors:
                try:
                    field = page.locator(selector).first
                    if field.is_visible(timeout=5000):
                        username_field = field
                        logger.info(f"✅ Username field found: {selector}")
                        break
                except:
                    continue
            
            # If username field exists, we need to login
            if username_field:
                # Fill username
                username_field.fill(VEEX_USERNAME, timeout=timeout)
                
                # Find and fill password
                password_field = None
                for selector in password_selectors:
                    try:
                        field = page.locator(selector).first
                        if field.is_visible(timeout=5000):
                            password_field = field
                            break
                    except:
                        continue
                
                if not password_field:
                    raise Exception("Could not find password field")
                
                password_field.fill(VEEX_PASSWORD, timeout=timeout)
                password_field.press("Enter")
                page.wait_for_timeout(8000)
                
                current_url = page.url
                page.wait_for_timeout(3000)
                
                # Navigate to Result & Report
                try:
                    page.evaluate('''
                        const element = document.evaluate(
                            "//*[contains(text(), 'Result & Report')]",
                            document,
                            null,
                            XPathResult.FIRST_ORDERED_NODE_TYPE,
                            null
                        ).singleNodeValue;
                        if (element) element.click();
                    ''')
                    page.wait_for_timeout(5000)
                except:
                    page.goto("https://charter.veexinc.net/home/result-and-report", timeout=timeout)
                    page.wait_for_timeout(3000)
                
                # Navigate to Results view
                page.wait_for_timeout(3000)
                try:
                    page.evaluate('''
                        const element = document.evaluate(
                            "//*[text()='Results']",
                            document,
                            null,
                            XPathResult.FIRST_ORDERED_NODE_TYPE,
                            null
                        ).singleNodeValue;
                        if (element) element.click();
                    ''')
                    page.wait_for_timeout(5000)
                except:
                    page.goto(VEEX_RESULTS_URL, timeout=timeout)
                    page.wait_for_timeout(5000)
            
            # Verify we're on the results page
            current_url = page.url
            if "result" not in current_url.lower():
                return {
                    "success": False,
                    "job_id": job_id,
                    "message": "Failed to reach results page"
                }
            
            # Wait for page content to load
            page.wait_for_timeout(15000)
            
            # Search for the Job ID
            search_inputs = page.locator('input[type="text"], input[type="search"], input:not([type])')
            input_count = search_inputs.count()
            
            if input_count > 0:
                for i in range(input_count):
                    try:
                        input_field = search_inputs.nth(i)
                        if input_field.is_visible():
                            input_field.fill(job_id)
                            page.wait_for_timeout(1000)
                            input_field.press("Enter")
                            page.wait_for_timeout(5000)
                            break
                    except:
                        continue
            
            page.wait_for_timeout(10000)
            
            # Extract data from page
            page_text = page.text_content('body')
            
            if job_id in page_text:
                try:
                    job_elements = page.locator(f'text="{job_id}"').all()
                    
                    if len(job_elements) > 0:
                        first_element = job_elements[0]
                        parent_row = first_element.locator('xpath=ancestor::tr').first
                        
                        if parent_row.is_visible():
                            cells = parent_row.locator('td, th').all()
                            cell_values = [cell.text_content().strip() for cell in cells]
                            
                            # Parse component status from result string
                            # Format: "Pass CRF: - |E: P |R: - |B: P |O: P |P: -"
                            component_status = {}
                            overall_status = "UNKNOWN"
                            
                            if len(cell_values) > 24:
                                result_string = cell_values[24]
                                
                                # Extract overall status (Pass/Fail at the beginning)
                                if result_string.startswith("Pass"):
                                    overall_status = "PASS"
                                elif result_string.startswith("Fail"):
                                    overall_status = "FAIL"
                                
                                # Remove the "Pass" or "Fail" prefix from result_string before parsing
                                if result_string.startswith("Pass "):
                                    result_string = result_string[5:]  # Remove "Pass "
                                elif result_string.startswith("Fail "):
                                    result_string = result_string[5:]  # Remove "Fail "
                                
                                # Parse component results
                                # CRF/C: Cable RF/tap, E: EPON/gnb_BI, R: RFoG, B: Bulkhead, O: ONU, P: Pressure
                                parts = result_string.split("|")
                                for part in parts:
                                    part = part.strip()
                                    if ":" in part:
                                        key, value = part.split(":", 1)
                                        key = key.strip()
                                        value = value.strip()
                                        
                                        # Map abbreviations to full names
                                        key_map = {
                                            "CRF": "tap",
                                            "C": "tap",
                                            "E": "gnb_BI",
                                            "R": "RFoG",
                                            "B": "Cpe",  # Changed from gnb_BI to Cpe
                                            "O": "ONU",
                                            "P": "Pressure test"
                                        }
                                        
                                        full_key = key_map.get(key, key)
                                        
                                        # Map values
                                        if value == "P":
                                            component_status[full_key] = "✅ Passed"
                                        elif value == "F":
                                            component_status[full_key] = "❌ Failed"
                                        elif value == "-" or value == "N/A":
                                            component_status[full_key] = "➖ Missing"
                                        else:
                                            component_status[full_key] = value
                            
                            # Add TDR and CPE if not found
                            if "Cpe" not in component_status:
                                # Check if CPE info is in other cells
                                component_status["Cpe"] = "➖ Missing"
                            if "TDR" not in component_status:
                                component_status["TDR"] = "➖ Missing"
                            
                            # Return structured data with correct mapping
                            job_data = {
                                "success": True,
                                "job_id": job_id,
                                "message": f"Job ID {job_id} found successfully",
                                "raw_data": cell_values,
                                "overall_status": overall_status,
                                "account": cell_values[2] if len(cell_values) > 2 else "",  # Account
                                "cable_type": cell_values[7] if len(cell_values) > 7 else "",  # Profile/Cable Type
                                "date_uploaded": cell_values[5] if len(cell_values) > 5 else "",  # Date uploaded ID
                                "test_type": cell_values[6] if len(cell_values) > 6 else "",  # Test type
                                "date_measured": cell_values[10] if len(cell_values) > 10 else "",  # Date measured
                                "test_set": cell_values[11] if len(cell_values) > 11 else "",  # Test set/Company
                                "technician": cell_values[10] if len(cell_values) > 10 else "",  # Technician time
                                "component_status": component_status
                            }
                            
                            return job_data
                            
                except Exception as e:
                    logger.error(f"Extraction error: {e}")
                
                return {
                    "success": True,
                    "job_id": job_id,
                    "message": f"Job ID {job_id} found but extraction incomplete"
                }
            else:
                return {
                    "success": False,
                    "job_id": job_id,
                    "message": f"Job ID {job_id} not found"
                }
                
        except Exception as e:
            logger.error(f"Scraping error: {e}")
            return {
                "success": False,
                "job_id": job_id,
                "message": "Error during scraping",
                "error": str(e)
            }
        finally:
            try:
                browser.close()
            except:
                pass
