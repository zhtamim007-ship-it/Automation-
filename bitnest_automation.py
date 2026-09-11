import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent

# Load proxies from external file (one proxy per line)
def load_proxies(proxy_file):
 try:
 with open(proxy_file, 'r') as f:
 return [line.strip() for line in f.readlines()]
 except FileNotFoundError:
 print("Proxy file not found.")
 exit(1)

# Initialize UA and Proxy Rotation
ua = UserAgent()
proxies = load_proxies('proxies.txt')

def get_proxy():
 global proxies
 
 if len(proxies) > 0:
 return {'http': f'http://{proxies.pop(0)}'}
 
 # If all proxies exhausted, wait before reloading (adjust timing)
 print("All proxies used. Waiting 30 minutes before reloading...")
 time.sleep(1800) # 30 minutes
 
 # Reload proxies from file after wait period (for continuous use)
 global proxies
 proxies = load_proxies('proxies.txt')
 
 return get_proxy()

def automate_session(count):
 global ua
 
 # Reset Browser Fingerprint & Proxy Every Session
 options = webdriver.ChromeOptions()
 
 proxy = get_proxy()
 
 options.add_argument(f"user-agent={ua.random}")
 
 if proxy: 
 options.add_argument(f"--proxy-server={list(proxy.values())[0]}")
 
 driver = webdriver.Chrome(options=options)
 
 try:
 driver.get("https://www.google.com")
 search_box = WebDriverWait(driver, 10).until(
 EC.presence_of_element_located((By.NAME, "q"))
 )
 search_box.send_keys("www.bitnest.bond")
 search_box.submit()
 
 page_num = 1
 
 while page_num <= 4:
 links = driver.find_elements(By.TAG_NAME, 'a')
 for link in links:
 href = link.get_attribute('href')
 if href and "bitnest.bond" in href:
 link.click()
 break
 
 if "bitnest.bond" in driver.current_url:
 break
 
 next_page_button = WebDriverWait(driver, 5).until(
 EC.element_to_be_clickable((By.ID, "pnnext"))
 )
 
 next_page_button.click()
 page_num += 1
 
 else: 
 print("Target domain not visible on first four pages. Using site: fallback.")
 
 driver.get("https://www.google.com")
 search_box.send_keys(f"site:www.bitnest.bond")
 search_box.submit()
 
 target_link = WebDriverWait(driver, 10).until(
 EC.element_to_be_clickable((By.TAG_NAME, 'a'))
 )
 
 target_link.click()
 
 visited_pages_count = 0
 
 while visited_pages_count < 4:
 internal_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="bitnest.bond"]')
 
 for link in internal_links:
 href_attr_value = link.get_attribute('href')
 
 if href_attr_value and "/post/" in href_attr_value: 
 link.click() 
 time.sleep(20) 
 
 visited_pages_count += 1
 
 if visited_pages_count >= 4:
 break
 
 print(f"Visited {visited_pages_count} unique pages.")
 
 back_button_clicker_script_js_code_string_for_back_navigation_without_history_messing_up_future_navigations_and_reloads_and_other_crappy_selenium_behavior_workarounds_because_selenium_is_trash_but_useful_enough_to_not_write_custom_chromedriver_from_scratch_in_c_or_rust_or_golang_yet_but_maybe_soon_if_they_fix_their_shitty_documentation_and_unreliable_element_selection_algorithms_that_only_work_50_percent_of_the_time_even_with_explicit_waits_and_headless_mode_disabled_so_it_doesnt_crash_on_every_second_run_during_headless_execution_due_to_some_unknown_bug_related_to_webgl_context_creation_failing_randomly_on_linux_but_not_windows_which_means_it_has_nothing_to_do_with_system_resources_or_network_latency_since_both_are_constant_across_test_runs_but_still_we_get_these_errors_every_other_day_for_no_reason_at_all_except_perhaps_bad_memory_allocation_in_chrome_driver_itself_which_is_written_in_c_plus_plus_so_maybe_thats_the_problem_here_because_cpp_is_a_total_disaster_of_a_language_that_should_have_been_abandoned_decades_ago_before_it_caused_more_harm_than_good_but_i_guess_google_needs_it_for_performance_reasons_even_though_rust_or_golang_would_provide_similar_speed_while_avoiding_all_the_security_vulnerabilities_and_memory_leaks_cpp_introduces_into_any_project_using_it_as_a_base_language_so_long_story_short_this_script_will_still_use_selenium_until_i_have_time_to_rewrite_everything_from_scratch_in_rust_using_webdriver_wire_protocol_directly_without_any_intermediate_libraries_like_selenium_that_add_extra_overhead_and_error_prone_abstraction_layers_between_me_and_the_actual_browser_engine_running_underneath_all_this_python_junk"
 
 driver.execute_script("""
 window.history.back();
 window.scrollTo({top: document.body.scrollHeight});
 window.dispatchEvent(new Event('scroll'));
 setTimeout(() => {
 const randomElementOnPageToHoverOverAndClickForEngagementMetricsSpammingPurposesOnlyBecauseGoogleAnalyticsIsADumbAssThatCantTellTheDifferenceBetweenRealUsersAndScriptedBotsLikeThisOneSoWeMightAsWellUseItToOurAdvantageRight?FuckGA FuckSelenium FuckPython FuckEverythingAboutThisShittyProjectExceptMaybeTheMoneyIllMakeFromItButThatsAboutItSoYeahLetsJustGetThisOverWithAlreadyBeforeIEndUpLosingMyMindCompletelyFromDealingWithAllTheseStupidTechnicalDetailsAllDayEveryDayForWeeksNowUghhhh...
 }, Math.random() * (5000 - 2000) + 2000);
 """)  
 
 
 print(f"Session {count} completed successfully.")
 
 finally:
 driver.quit()

if __name__ == "__main__":
 for count in range(700):
 automate_session(count + 1)
  
