from pprint import pprint
import logging
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
import csv
from time import sleep

# Configure logging
logging.basicConfig(filename='download_log.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

TIMEOUT = 10  # Set your desired wait time in seconds

options = Options()
#options.add_argument('--headless')
service = FirefoxService('./geckodriver')
options.set_preference('permissions.default.image', 2)

categories = ['Community+Service%2FNon-Profit']
locations = [
    'Toronto%2C+ON', 'Montreal%2C+QC', 'Calgary%2C+AB', 'Ottawa%2C+ON', 'Edmonton%2C+AB',
    'Mississauga%2C+ON', 'Winnipeg%2C+MB', 'Vancouver%2C+BC', 'Brampton%2C+ON', 'Hamilton%2C+ON',
    'Quebec+City%2C+QC', 'Surrey%2C+BC', 'Laval%2C+QC', 'Halifax%2C+NS', 'London%2C+ON',
    'Markham%2C+ON', 'Vaughan%2C+ON', 'Gatineau%2C+QC', 'Saskatoon%2C+SK', 'Longueuil%2C+QC',
    'Kitchener%2C+ON', 'Burnaby%2C+BC', 'Windsor%2C+ON', 'Regina%2C+SK', 'Richmond%2C+BC',
    'Richmond+Hill%2C+ON', 'Oakville%2C+ON', 'Burlington%2C+ON', 'Greater+Sudbury%2C+ON', 'Sherbrooke%2C+QC',
    'Oshawa%2C+ON', 'Saguenay%2C+QC', 'Levis%2C+QC', 'Barrie%2C+ON', 'Abbotsford%2C+BC',
    'Coquitlam%2C+BC', 'Trois-Rivieres%2C+QC', 'St.+Catharines%2C+ON', 'Guelph%2C+ON', 'Cambridge%2C+ON',
    'Whitby%2C+ON', 'Kelowna%2C+BC', 'Kingston%2C+ON'
]

import time

def page_navigation(driver, url):
    business_links = []

    try:
        # Navigate to the URL
        driver.get(url)
        logging.info(f"Navigated to {url}")

        while True:
            # Select every business listing that matches the provided structure
            business_listings = driver.find_elements(By.XPATH, "//div[contains(@class, 'businessName__09f24__HG_pC')]")

            for listing in business_listings:
                business_link = listing.find_element(By.XPATH, ".//h3/a").get_attribute("href")
                business_links.append(business_link)
                logging.info(f"Business Link: {business_link}")

            # Wait for the "Next Page" button to be present and click it if available
            try:
                next_button_span = WebDriverWait(driver, TIMEOUT).until(
                    EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Next Page')]"))
                )
                logging.info("Next Page span found")

                # Gradually scroll to the bottom of the page over 1 second
                #total_height = driver.execute_script("return document.body.scrollHeight")
                #for _ in range(10):
                #    driver.execute_script(f"window.scrollBy(0, {total_height / 10});")
                #    time.sleep(0.1)
                #logging.info("Gradually scrolled to the bottom of the page")

                # Sleep for 1 second
                #time.sleep(1)

                # Find the parent button element
                next_button = next_button_span.find_element(By.XPATH, "./ancestor::button")
                if next_button.is_displayed() and next_button.is_enabled():
                    # Perform a JavaScript click on the button
                    driver.execute_script("arguments[0].click();", next_button)
                    logging.info("Next Page button clicked via JavaScript")

                    # Wait for the next page to load
                    time.sleep(2)
                else:
                    logging.info("Next Page button is not clickable")
                    break
            except Exception as e:
                logging.info("No more pages to navigate")
                break

    except Exception as e:
        logging.error(f"Error in page_navigation: {e}")

    return business_links

def extract_business_info(driver, url):
    """
    This function extracts business information from a Yelp website using Selenium.

    Args:
        driver (WebDriver): The Selenium WebDriver instance.
        url (str): The URL of the business page.

    Returns:
        dict: A dictionary containing the extracted business information.
    """
    driver.get(url)
    WebDriverWait(driver, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'body')))
    sleep(1)
    info = {'url': url}

    # Business Name
    try:
        info['name'] = driver.find_element(By.TAG_NAME, 'h1').text.strip()
    except Exception as e:
        info['name'] = None

    # Category
    try:
        category_link = driver.find_element(By.XPATH, "//a[contains(@href, 'find_desc')]")
        info['category'] = category_link.text.strip()
    except Exception as e:
        info['category'] = None

    # Claimed Status
    try:
        claimed_span = driver.find_element(By.XPATH, "//span[@aria-hidden='true']")
        info['claimed'] = claimed_span.find_element(By.XPATH, "following-sibling::span").text.strip()
    except Exception as e:
        info['claimed'] = None

    # Closed Status
    try:
        closed_span = driver.find_element(By.XPATH, "//span[contains(text(), 'Closed')]")
        info['closed'] = closed_span.find_element(By.XPATH, "following-sibling::span").text.strip()
    except Exception as e:
        info['closed'] = None

    # Hours
    try:
        hours_table = driver.find_element(By.XPATH, "//table[contains(text(), 'Location & Hours')]")
        days = [th.find_element(By.TAG_NAME, 'p').text.strip() for th in hours_table.find_elements(By.TAG_NAME, 'th')]
        hours = []
        for row in hours_table.find_elements(By.TAG_NAME, 'td'):
            hours.extend([li.find_element(By.TAG_NAME, 'p').text.strip() for li in row.find_elements(By.TAG_NAME, 'ul')])
        info['hours'] = dict(zip(days, hours))
    except Exception as e:
        info['hours'] = None

    # Photos
    try:
        photos = [img.get_attribute('src') for img in driver.find_elements(By.XPATH, "//img[@aria-label='Photos & videos']")]
        info['photos'] = photos
    except Exception as e:
        info['photos'] = None

    # Services Offered
    try:
        services_section = driver.find_element(By.XPATH, "//section[@aria-label='Services Offered']")
        services = [a.text.strip() for a in services_section.find_elements(By.XPATH, ".//a[contains(@href, 'find_desc')]")]
        info['services_offered'] = services
    except Exception as e:
        info['services_offered'] = None

    # Description
    try:
        description_section = driver.find_element(By.XPATH, "//section[@aria-label='About the Business']")
        info['description'] = description_section.find_element(By.TAG_NAME, 'p').text.strip()
    except Exception as e:
        info['description'] = None
    # Reviews
    try:
        reviews_tag = driver.find_element(By.XPATH, "//a[contains(@href, '#reviews')]")
        reviews_rating = reviews_tag.find_element(By.XPATH, "preceding-sibling::span").text.strip()
        info['reviews'] = float(reviews_rating)
    except Exception as e:
        info['reviews'] = None
    # Address
    try:
        address_section = driver.find_element(By.TAG_NAME, 'address')
        paragraphs = address_section.find_elements(By.TAG_NAME, 'p')
        info['street'] = paragraphs[0].text.strip()
        unit_index = next((i for i, p in enumerate(paragraphs) if "Main Floor" in p.text), None)
        if unit_index is not None:
            info['unit'] = paragraphs[unit_index + 1].text.strip()
            info['city_state_postal_code'] = paragraphs[unit_index + 2].text.strip()
        else:
            info['unit'] = None
            info['city_state_postal_code'] = paragraphs[1].text.strip()
    except Exception as e:
        info['street'] = None
        info['unit'] = None
        info['city_state_postal_code'] = None

    # Business Website
    try:
        # Find all 'a' tags
        print("Finding all 'a' tags...")
        all_links = driver.find_elements(By.TAG_NAME, 'a')
        print(f"Total 'a' tags found: {len(all_links)}")
        
        # Filter for the first occurring '/biz_redir' URL
        print("Filtering for the first occurring '/biz_redir' URL...")
        website_link = next((link.get_attribute('href') for link in all_links if link.get_attribute('href') and '/biz_redir?url=' in link.get_attribute('href')), None)
        
        if website_link:
            print(f"Website link found: {website_link}")
            # Extract the actual URL from the href attribute
            website_url = website_link.split('url=')[1].split('&')[0]
            website_url = website_url.replace('%3A', ':').replace('%2F', '/')
            info['website'] = website_url
            print(f"Extracted website URL: {website_url}")
        else:
            info['website'] = None
            print("No website link found.")
    except Exception as e:
        info['website'] = None
        print(f"Error extracting website: {e}")
        logging.error(f"Error extracting website: {e}")


    # Phone Number
    try:
        phone_tag = driver.find_element(By.XPATH, "//p[contains(text(), 'Phone number')]")
        phone_number = phone_tag.find_element(By.XPATH, "following-sibling::p").text.strip()
        info['phone_number'] = phone_number
    except Exception as e:
        info['phone_number'] = None

    return info

def save_to_csv(data, filename='business_info.csv'):
    file_exists = os.path.isfile(filename)
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow([
                'Name', 'Category', 'Claimed', 'Closed', 'Hours', 'Photos', 'Services Offered', 
                'Description', 'Street', 'Unit', 'City/State/Postal Code', 'Country', 
                'Website', 'Phone Number', 'Reviews'
            ])
        for info in data:
            writer.writerow([
                info.get('name'), info.get('category'), info.get('claimed'), info.get('closed'),
                info.get('hours'), info.get('photos'), info.get('services_offered'), info.get('description'),
                info.get('street'), info.get('unit'), info.get('city_state_postal_code'), info.get('country'),
                info.get('website'), info.get('phone_number'), info.get('reviews')
            ])

# Example usage
all_business_info = []
visited_links = set()
driver = webdriver.Firefox(service=service, options=options)

try:
    # Step 1: Extract all business URLs
    #all_business_links = []
    with open('biz_urls.txt', 'r') as file:
      all_business_links = [line.strip() for line in file]
    #for loc in locations:
    #    url = f"https://www.yelp.com/search?find_desc=Community+Service%2FNon-Profit&find_loc={loc}"
    #    business_links = page_navigation(driver, url)
    #    all_business_links.extend(business_links)

    # Step 2: Extract detailed information for each business
    for link in all_business_links:
        if link not in visited_links:
            business_info = extract_business_info(driver, link)
            pprint(business_info)
            all_business_info.append(business_info)
            save_to_csv([business_info])
            visited_links.add(link)
            logging.info(f"Extracted and saved info for {business_info['name']}")
finally:
    driver.quit()

save_to_csv(all_business_info)

#url1 = "https://www.yelp.com/search?find_desc=Community+Service%2FNon-Profit&find_loc=Toronto%2C+ON"
#url2 = "https://www.yelp.com/biz/the-second-chance-foundation-toronto-3?osq=Community+Service%2FNon-Profit&override_cta=Request+information"

