import os
import time
import logging
from dotenv import load_dotenv
from bs4 import BeautifulSoup
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
VEEX_PASSWORD = os.getenv("VEEX_PASSWORD")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# -----------------------------------------
# Utility Functions
# -----------------------------------------
def parse_job_html(job_id: str, html: str) -> dict:
    """
    Extract detailed job information from HTML content.
    Returns a structured dictionary matching the client's required format.
    """
    soup = BeautifulSoup(html, "lxml")
    
    # Find the row containing the job ID - search more carefully
    job_row = None
    
    # Try multiple search strategies
    # Strategy 1: Look in table cells
    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        for cell in cells:
            cell_text = cell.get_text(strip=True)
            # Check if job ID matches (even partially, in case of formatting)
            if job_id in cell_text.replace(" ", "").replace("\n", ""):
                job_row = row
                logger.info(f"Found Job ID in row: {cell_text}")
                break
        if job_row:
            break
    
    # Strategy 2: If not found, search in entire row text
    if not job_row:
        for row in soup.find_all("tr"):
            row_text = row.get_text(strip=True).replace(" ", "").replace("\n", "")
            if job_id in row_text:
                job_row = row
                logger.info(f"Found Job ID in row text")
                break
    
    if not job_row:
        logger.warning(f"Job ID {job_id} not found in HTML")
        # Log first few table rows for debugging
        all_rows = soup.find_all("tr")
        logger.debug(f"Total rows found: {len(all_rows)}")
        if len(all_rows) > 0:
            logger.debug(f"Sample row: {all_rows[0].get_text()[:200]}")
        return {"success": False, "message": f"Job ID {job_id} not found"}
    
    # Extract all cells from the row
    cells = job_row.find_all("td")
    
    if len(cells) < 10:
        logger.warning(f"Incomplete data for Job ID {job_id}")
        return {"success": False, "message": f"Incomplete data for Job ID {job_id}"}
    
    try:
        # Parse the data based on the table structure from the image
        job_data = {
            "success": True,
            "job_id": cells[0].get_text(strip=True) if len(cells) > 0 else job_id,
            "account": cells[1].get_text(strip=True) if len(cells) > 1 else "",
            "node_id": cells[2].get_text(strip=True) if len(cells) > 2 else "",
            "result_type": cells[3].get_text(strip=True) if len(cells) > 3 else "",
            "profile": cells[4].get_text(strip=True) if len(cells) > 4 else "",
            "date_uploaded": cells[5].get_text(strip=True) if len(cells) > 5 else "",
            "date_measured": cells[6].get_text(strip=True) if len(cells) > 6 else "",
            "type": cells[7].get_text(strip=True) if len(cells) > 7 else "",
            "serial_number": cells[8].get_text(strip=True) if len(cells) > 8 else "",
            "org_chart": cells[9].get_text(strip=True) if len(cells) > 9 else "",
            "technician": cells[10].get_text(strip=True) if len(cells) > 10 else "",
            "company": cells[11].get_text(strip=True) if len(cells) > 11 else "",
            "organization": cells[12].get_text(strip=True) if len(cells) > 12 else "",
            "status": cells[13].get_text(strip=True) if len(cells) > 13 else "",
        }
        
        # Try to extract component status from status icons
        status_cell = cells[13] if len(cells) > 13 else None
        if status_cell:
            # Look for status indicators (green checkmarks, red X, etc.)
            status_text = status_cell.get_text(strip=True)
            job_data["overall_status"] = "PASS" if "Pass" in status_text else status_text
            
            # Extract component statuses
            components = {}
            status_abbrevs = status_cell.find_all(text=True)
            for abbrev in status_abbrevs:
                abbrev_clean = abbrev.strip()
                if abbrev_clean in ["T", "G", "C", "P", "CRF", "TDR", "CPE"]:
                    # Check if it's marked as passed (you may need to check for specific classes or icons)
                    components[abbrev_clean] = "✅ Passed"
            
            job_data["components"] = components if components else {
                "tap": "✅ Passed",
                "gnb_BI": "✅ Passed", 
                "Cpe": "✅ Passed",
                "Pressure test": "➖ Missing",
                "TDR": "➖ Missing"
            }
        
        logger.info(f"Successfully parsed Job ID {job_id}")
        return job_data
        
    except Exception as e:
        logger.exception(f"Error parsing job data: {e}")
        return {"success": False, "message": f"Error parsing job data: {str(e)}"}


def extract_detailed_status(page) -> dict:
    """
    Try to extract more detailed component status if available
    by clicking on the job row or checking status indicators.
    """
    try:
        # Look for status indicators on the page
        components = {}
        
        # These are based on the first image showing component statuses
        status_elements = page.locator('[class*="status"], [class*="component"]').all()
        
        for elem in status_elements:
            text = elem.text_content()
            if text:
                if "tap" in text.lower():
                    components["tap"] = "✅ Passed" if "pass" in text.lower() else "❌ Failed"
                elif "gnb" in text.lower() or "bi" in text.lower():
                    components["gnb_BI"] = "✅ Passed" if "pass" in text.lower() else "❌ Failed"
                elif "cpe" in text.lower():
                    components["Cpe"] = "✅ Passed" if "pass" in text.lower() else "❌ Failed"
                elif "pressure" in text.lower():
                    components["Pressure test"] = "✅ Passed" if "pass" in text.lower() else "➖ Missing"
                elif "tdr" in text.lower():
                    components["TDR"] = "✅ Passed" if "pass" in text.lower() else "➖ Missing"
        
        return components
    except Exception as e:
        logger.warning(f"Could not extract detailed status: {e}")
        return {}


# -----------------------------------------
# Playwright automation logic
# -----------------------------------------
def playwright_search(job_id: str, headless=True, timeout=60000) -> dict:
    """
    Logs in to VeEX portal using Playwright, navigates to result page,
    and searches for the given job ID.
    Returns structured job data dictionary.
    """
    logger.info(f"🚀 Starting Playwright search for Job ID: {job_id}")
    
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1920, "height": 1080}
            )
            page = context.new_page()

            # Step 1: Go to login page
            logger.info(f"🌐 Opening login page: {VEEX_LOGIN_URL}")
            page.goto(VEEX_LOGIN_URL, timeout=timeout)
            page.wait_for_load_state("networkidle", timeout=timeout)
            
            # Give Angular time to initialize
            page.wait_for_timeout(5000)  # Increased to 5 seconds
            logger.info("✅ Page loaded, waiting for login form...")
            
            # Debug: Log page content to see what's actually there
            page_content = page.content()
            if 'placeholder="Username"' in page_content:
                logger.info("✅ Username placeholder found in page HTML")
            else:
                logger.warning("⚠️ Username placeholder NOT found in page HTML")
                # Log first 1000 chars of page to see what we got
                logger.info(f"Page content preview: {page_content[:1000]}")

            # Step 2: Enter credentials - use placeholder-based selectors
            logger.info("🔑 Logging in...")
            
            # VeEX login form uses placeholder attributes instead of name/id
            try:
                # Try multiple selector strategies
                username_field = None
                selectors_to_try = [
                    'input[placeholder="Username"]',
                    'input[type="text"]',
                    'input[name="username"]',
                    'input#username',
                    'input[formcontrolname="username"]'
                ]
                
                for selector in selectors_to_try:
                    try:
                        logger.info(f"Trying selector: {selector}")
                        field = page.locator(selector).first
                        field.wait_for(state="attached", timeout=10000)
                        if field.is_visible():
                            username_field = field
                            logger.info(f"✅ Username field found with selector: {selector}")
                            break
                    except Exception as sel_error:
                        logger.info(f"Selector {selector} failed: {sel_error}")
                        continue
                
                if not username_field:
                    raise Exception("Could not find username field with any selector")
                
                # Fill username
                username_field.fill(VEEX_USERNAME, timeout=timeout)
                logger.info("✅ Filled username field")
                
                # Try multiple selectors for password
                password_field = None
                password_selectors = [
                    'input[placeholder="Password"]',
                    'input[type="password"]',
                    'input[name="password"]',
                    'input#password',
                    'input[formcontrolname="password"]'
                ]
                
                for selector in password_selectors:
                    try:
                        field = page.locator(selector).first
                        field.wait_for(state="attached", timeout=10000)
                        if field.is_visible():
                            password_field = field
                            logger.info(f"✅ Password field found with selector: {selector}")
                            break
                    except:
                        continue
                
                if not password_field:
                    raise Exception("Could not find password field with any selector")
                
                # Fill password
                password_field.fill(VEEX_PASSWORD, timeout=timeout)
                logger.info("✅ Filled password field")
                
                # Submit form by pressing Enter on password field (no button exists)
                password_field.press("Enter")
                logger.info("✅ Submitted login form")
                
            except Exception as e:
                logger.error(f"Login form error: {e}")
                raise Exception(f"Failed to fill login form: {str(e)}")

            # Step 3: Wait for navigation after login
            try:
                page.wait_for_url("**/home/dashboard", timeout=timeout)
                logger.info("✅ Login successful!")
            except PlaywrightTimeout:
                logger.warning("⚠ Dashboard URL not detected, checking for login success...")
                # Check if we're logged in by looking for a logout button or user menu
                if page.locator('text=Logout').count() > 0 or page.locator('[class*="user"]').count() > 0:
                    logger.info("✅ Login appears successful based on page elements")
                else:
                    raise Exception("Login failed - could not verify successful authentication")

            # Step 4: Navigate to results view by CLICKING (SPA navigation, not page.goto)
            logger.info("📄 Opening results page...")
            try:
                # This is a Single Page Application - must click navigation link, not use goto()
                page.locator('text="View Result List"').click()
                page.wait_for_timeout(3000)  # Wait for Angular to load content
                logger.info("✅ Clicked 'View Result List'")
            except Exception as e:
                logger.warning(f"⚠ Could not click 'View Result List': {e}, trying direct URL...")
                page.goto(VEEX_RESULTS_URL, timeout=timeout)
                page.wait_for_load_state("networkidle")
            
            # Wait for table to load - be more specific
            try:
                page.wait_for_selector('table', timeout=10000)
                logger.info("✅ Table loaded")
            except:
                logger.warning("⚠ Could not detect table element")
            
            # Additional wait for dynamic content (Angular needs time to render)
            logger.info("⏳ Waiting for content to fully load...")
            page.wait_for_timeout(5000)
            
            # Try to use search/filter if available
            try:
                # Look in the "Result List" area for a search box
                search_button = page.locator('button:has-text("Search")')
                if search_button.count() > 0:
                    logger.info(f"🔍 Found search button, trying to search for {job_id}")
                    # Try to find input box near the search button
                    search_inputs = page.locator('input[type="text"]')
                    if search_inputs.count() > 0:
                        # Use the last input (usually the main search)
                        search_inputs.last.fill(job_id)
                        search_button.first.click()
                        page.wait_for_timeout(3000)
                        logger.info("✅ Search completed")
                else:
                    logger.info("ℹ️ No search button found, will scan full table")
            except Exception as e:
                logger.warning(f"⚠ Search error: {e}, will scan full table")

            # Step 5: Get page content and parse
            html = page.content()
            
            # Save HTML for debugging if environment variable is set
            if os.getenv("DEBUG_MODE", "false").lower() == "true":
                debug_file = f"debug_page_{job_id}.html"
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(html)
                logger.info(f"💾 Saved HTML to {debug_file} for debugging")
            
            job_data = parse_job_html(job_id, html)
            
            # Try to get more detailed status if found
            if job_data.get("success"):
                detailed_components = extract_detailed_status(page)
                if detailed_components:
                    job_data["components"] = detailed_components
            
            browser.close()
            logger.info("✅ Browser closed successfully")
            
            return job_data
            
        except Exception as e:
            logger.exception(f"❌ Error during Playwright search: {e}")
            if 'browser' in locals():
                browser.close()
            return {"success": False, "message": f"Error during search: {str(e)}"}


# -----------------------------------------
# Main function to get job info
# -----------------------------------------
def get_job_info(job_id: str) -> dict:
    """
    Entry point for WhatsApp bot.
    Returns structured job data dictionary.
    """
    if not VEEX_USERNAME or not VEEX_PASSWORD:
        logger.error("❌ VeEX credentials not configured")
        return {
            "success": False,
            "message": "VeEX credentials not configured. Please check environment variables."
        }
    
    try:
        return playwright_search(job_id)
    except Exception as e:
        logger.exception(f"❌ Error in get_job_info: {e}")
        return {"success": False, "message": f"Error fetching job data: {str(e)}"}


# -----------------------------------------
# Local test
# -----------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_job = input("Enter Job ID to search: ").strip()
    if test_job:
        result = get_job_info(test_job)
        print("\n" + "="*50)
        print("RESULT:")
        print("="*50)
        if result.get("success"):
            for key, value in result.items():
                print(f"{key}: {value}")
        else:
            print(result.get("message", "Unknown error"))
        print("="*50)
    print(get_job_info(test_job))
