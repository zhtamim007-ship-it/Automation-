import os
import sys
import time
import random
import json
import logging
import re
from urllib.parse import urljoin

# Playwright imports
from playwright.sync_api import sync_playwright

# --- Configuration ---
TARGET_URL = "https://www.bitnest.bond/"
ITERATIONS = 700
MIN_DWELL = 20  # seconds
MAX_DWELL = 30  # seconds

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# User-Agent Pool for fingerprint rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
]

def load_proxies(filename="proxies.json"):
    """Load proxies from the JSON file."""
    if not os.path.exists(filename):
        logger.warning(f"{filename} not found. Running without proxy rotation.")
        return []
    
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            # Handle both list format and object format
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "proxies" in data:
                return data["proxies"]
    except Exception as e:
        logger.error(f"Error loading proxies: {e}")
    return []

def get_random_proxy(proxies):
    """Select a random proxy from the list."""
    if not proxies:
        return None
    return random.choice(proxies)

def get_random_ua():
    """Select a random User-Agent string."""
    return random.choice(USER_AGENTS)

def find_bitnest_link_from_google(query_term):
    """
    Simulates opening Google, searching, and finding the BitNest link.
    Uses Playwright to render the page and extract the link, ensuring we get 
    a realistic SERP experience without relying on external APIs that might block.
    """
    logger.info(f"Opening Google and searching for '{query_term}'...")
    
    with sync_playwright() as p:
        # We use a fresh browser instance for the search to keep it clean
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Navigate to Google
            page.goto("https://www.google.com", wait_until="domcontentloaded", timeout=15000)
            
            # Find the search box and enter query
            search_box = page.wait_for_selector("textarea[name='q']", timeout=10000)
            search_box.fill(query_term)
            
            # Submit the form
            page.keyboard.press("Enter")
            
            # Wait for search results to load
            page.wait_for_selector("#search", timeout=15000)
            
            # Scroll through the first few pages of results to simulate human behavior
            # Google usually loads more results as you scroll
            for _ in range(3): # Scroll 3 times
                page.mouse.wheel(0, 1000)
                time.sleep(random.uniform(1, 2))
            
            # Extract all links that contain 'bitnest.bond'
            # We look for links in the search results area
            links = page.query_selector_all("a[href]")
            
            found_links = []
            for link in links:
                href = link.get_attribute("href")
                if href and "bitnest.bond" in href:
                    # Clean up the URL (Google sometimes adds tracking params)
                    if href.startswith("http"):
                        found_links.append(href)
                    else:
                        # Relative link
                        found_links.append(urljoin("https://www.google.com", href))
            
            if found_links:
                logger.info(f"Found {len(found_links)} BitNest links in search results.")
                # Return the first one that looks like a main page or post
                for link in found_links:
                    if "/p/" not in link and "/blog/" not in link:
                        return link
                return found_links[0]
            else:
                logger.warning("No BitNest link found in top results.")
                return None
                
        except Exception as e:
            logger.error(f"Error during Google search simulation: {e}")
            return None
        finally:
            context.close()
            browser.close()

def simulate_human_scroll(page):
    """Simulate natural scrolling behavior."""
    page.evaluate("""() => {
        // Scroll down a bit, then up a bit, then down more
        window.scrollBy({ top: 400, behavior: 'auto' });
        window.scrollBy({ top: -200, behavior: 'auto' });
        window.scrollBy({ top: 600, behavior: 'auto' });
    }""")
    time.sleep(random.uniform(1.5, 3))

def simulate_hover(page):
    """Simulate hovering over elements."""
    try:
        # Try to hover over a random link or button
        elements = page.query_selector_all("a, button, .post-card, .btn")
        if elements:
            target = random.choice(elements)
            target.hover()
            time.sleep(random.uniform(0.5, 1.5))
    except Exception:
        pass

def get_random_post_links(page, count=4):
    """Extract random post links from the current page."""
    links = page.query_selector_all("a[href]")
    unique_links = []
    seen_urls = set()
    
    for link in links:
        href = link.get_attribute("href")
        if href:
            # Ensure it's a valid BitNest URL and not already seen
            if "bitnest.bond" in href and href not in seen_urls:
                # Avoid main homepage if possible, prefer posts
                if "/p/" in href or "/blog/" in href:
                    seen_urls.add(href)
                    unique_links.append(href)
                elif len(unique_links) < count and "/p/" not in href and "/blog/" not in href:
                    # If we don't have enough posts, include homepage or other pages
                    seen_urls.add(href)
                    unique_links.append(href)
        
        if len(unique_links) >= count:
            break
            
    return unique_links

def run_session(session_id, proxies):
    logger.info(f"[Session {session_id}] Starting new isolated session.")
    
    proxy = get_random_proxy(proxies)
    ua = get_random_ua()
    
    try:
        with sync_playwright() as p:
            # Create a new isolated context (fingerprint rotation)
            context_options = {
                "user_agent": ua,
                "viewport": {"width": 1920, "height": 1080},
                "locale": "en-US",
                "timezone_id": "America/New_York",
                "hardware_concurrency": 4,
                "device_scale_factor": 1,
                "storage_state": None, # Fresh storage
            }
            
            if proxy:
                context_options["proxy"] = {"server": proxy}

            browser = p.chromium.launch(
                headless=True, 
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            context = browser.new_context(**context_options)
            page = context.new_page()

            # 1. Organic Search Acquisition
            target_link = None
            # Try multiple queries to find the site
            queries = ["site:www.bitnest.bond", "bitnest bond", "www.bitnest.bond"]
            
            for q in queries:
                target_link = find_bitnest_link_from_google(q)
                if target_link:
                    break
            
            if not target_link:
                logger.warning(f"[Session {session_id}] Could not find organic link via Google search. Using direct URL.")
                target_link = TARGET_URL
            
            logger.info(f"[Session {session_id}] Navigating to: {target_link}")
            
            # Navigate to the link (simulating click from SERP)
            page.goto(target_link, wait_until="domcontentloaded", timeout=30000)
            
            # 2. Active User Engagement
            posts_visited = []
            
            # Get initial list of posts from the landing page
            current_posts = get_random_post_links(page, 4)
            
            # If no posts found, refresh and try again
            if not current_posts:
                logger.info(f"[Session {session_id}] No posts found on home, scrolling and refreshing.")
                simulate_human_scroll(page)
                page.reload()
                current_posts = get_random_post_links(page, 4)

            # Visit each post
            # We aim for at least 4 distinct pages
            pages_to_visit = current_posts if len(current_posts) >= 4 else current_posts + [TARGET_URL] * (4 - len(current_posts))
            
            # Ensure we visit unique pages if possible
            visited_urls = set()
            
            for i in range(len(pages_to_visit)):
                post_url = pages_to_visit[i]
                
                # Skip if already visited
                if post_url in visited_urls:
                    continue
                    
                page.goto(post_url, wait_until="domcontentloaded", timeout=30000)
                visited_urls.add(post_url)
                
                # Simulate human behavior on the page
                simulate_human_scroll(page)
                simulate_hover(page)
                
                # Dwell time
                dwell_time = random.uniform(MIN_DWELL, MAX_DWELL)
                logger.debug(f"[Session {session_id}] Dwell time: {dwell_time:.2f}s on {post_url}")
                time.sleep(dwell_time)

            logger.info(f"[Session {session_id}] Completed. Visited: {len(visited_urls)} pages.")
            
            # Cleanup
            context.close()
            browser.close()
            
            return True

    except Exception as e:
        logger.error(f"[Session {session_id}] Error: {e}")
        return False

def main():
    logger.info(f"Starting BitNest Agent for {ITERATIONS} sessions.")
    
    # Load proxies
    proxies = load_proxies("proxies.json")
    if proxies:
        logger.info(f"Loaded {len(proxies)} proxies.")
    else:
        logger.warning("No proxies loaded. All sessions will use the same IP.")

    successful_sessions = 0
    failed_sessions = 0
    
    for i in range(1, ITERATIONS + 1):
        logger.info(f"--- Processing Session {i}/{ITERATIONS} ---")
        success = run_session(i, proxies)
        if success:
            successful_sessions += 1
        else:
            failed_sessions += 1
        
        # Small pause between sessions to avoid local rate limits
        time.sleep(random.uniform(2, 5))
        
    logger.info(f"Finished. Success: {successful_sessions}, Failed: {failed_sessions}")

if __name__ == "__main__":
    main()
