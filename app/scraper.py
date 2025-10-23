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
            
            # Look for search/filter controls
            logger.info("Looking for search controls and filters...")
            
            # First, scroll down to see the search controls at the bottom
            logger.info("Scrolling to bottom to find search controls...")
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            page.wait_for_timeout(2000)
            
            # Take screenshot before search
            if not headless:
                try:
                    page.screenshot(path="before_search.png")
                    logger.info("Screenshot saved: before_search.png")
                except:
                    pass
            
            # First, find and select "Job ID" from the "Search By" dropdown
            try:
                logger.info("Looking for 'Search By' dropdown...")
                # The search by dropdown should be near the bottom of the page
                search_by_select = page.locator('select').first
                if search_by_select.is_visible():
                    # Select "Job ID" option
                    search_by_select.select_option(label="Job ID")
                    logger.info("Selected 'Job ID' from Search By dropdown")
                    page.wait_for_timeout(1000)
                else:
                    logger.warning("Search By dropdown not visible")
            except Exception as e:
                logger.error(f"Error selecting Job ID filter: {e}")
            
            # Find the search input field (should be visible after selecting Job ID)
            logger.info("Looking for search input field...")
            try:
                # Look for all text inputs and find enabled ones
                all_inputs = page.locator('input[type="text"]').all()
                logger.info(f"Found {len(all_inputs)} text input fields")
                
                # Try the last visible AND enabled input (likely the search field)
                search_input = None
                for idx, inp in enumerate(reversed(all_inputs)):
                    try:
                        if inp.is_visible() and inp.is_enabled():
                            search_input = inp
                            logger.info(f"Found enabled input at reverse index {idx}")
                            break
                    except:
                        continue
                
                if search_input:
                    # Click to focus
                    search_input.click()
                    page.wait_for_timeout(500)
                    # Clear any existing value
                    search_input.fill("")
                    page.wait_for_timeout(500)
                    # Fill with Job ID
                    search_input.fill(job_id)
                    logger.info(f"Filled Job ID '{job_id}' into search field")
                    page.wait_for_timeout(2000)
                else:
                    logger.warning("No enabled search input found")
            except Exception as e:
                logger.error(f"Error filling search input: {e}")
            
            # Click the Search button
            logger.info("Looking for Search button...")
            try:
                search_button = page.locator('button:has-text("Search")').first
                if search_button.is_visible():
                    search_button.click()
                    logger.info("Clicked Search button")
                    page.wait_for_timeout(10000)  # Wait for search results to load
                    
                    # Check if we got results
                    current_url = page.url
                    logger.info(f"Current URL after search: {current_url}")
                    
                    # Take screenshot for debugging
                    if not headless:
                        try:
                            page.screenshot(path="after_search.png")
                            logger.info("Screenshot saved: after_search.png")
                        except:
                            pass
                else:
                    logger.warning("Search button not visible")
            except Exception as e:
                logger.error(f"Error clicking search button: {e}")
            
            page.wait_for_timeout(3000)
            
            # Scroll to load all content
            logger.info("Scrolling page to load all results...")
            for _ in range(5):  # Scroll 5 times to load more content
                page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                page.wait_for_timeout(2000)
            
            # Scroll back to top
            page.evaluate('window.scrollTo(0, 0)')
            page.wait_for_timeout(2000)
            
            # Try to find Job ID in table rows directly
            logger.info(f"Looking for Job ID {job_id} in table rows...")
            all_rows = page.locator('table tr').all()
            logger.info(f"Found {len(all_rows)} table rows")
            
            # Print first 3 data rows to see what's in the table
            for idx in range(min(5, len(all_rows))):
                row_text = all_rows[idx].text_content()
                logger.info(f"Row {idx}: {row_text[:150]}")
            
            found_in_row = False
            for idx, row in enumerate(all_rows):
                row_text = row.text_content()
                if job_id in row_text:
                    logger.info(f"✅ Found Job ID in row {idx}: {row_text[:100]}")
                    found_in_row = True
                    break
            
            if not found_in_row:
                logger.warning(f"Job ID {job_id} not found in any of {len(all_rows)} table rows")
                logger.info("Checking if search field worked - looking at visible Job IDs...")
                # Get all text content from first 10 data rows
                sample_ids = []
                for idx in range(min(10, len(all_rows))):
                    cells = all_rows[idx].locator('td').all()
                    if len(cells) > 0:
                        first_cell = cells[0].text_content().strip()
                        if first_cell and len(first_cell) > 10:
                            sample_ids.append(first_cell)
                logger.info(f"Sample Job IDs on page: {sample_ids[:5]}")
            
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
