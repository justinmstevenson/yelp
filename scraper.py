import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
import csv

# Configure logging
logging.basicConfig(filename='download_log.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

TIMEOUT = 10  # Set your desired wait time in seconds

options = Options()
options.add_argument('--headless')
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

def page_navigation(url):
    # Initialize the WebDriver
    driver = webdriver.Firefox(service=service, options=options)
    business_dict = {}

    try:
        # Navigate to the URL
        driver.get(url)

        # Wait for the "Next Page" button to be present and click it if available
        try:
            next_button = WebDriverWait(driver, TIMEOUT).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Next Page')]"))
            )
            next_button.click()
        except:
            logging.info("Next Page button not found or not clickable")

        # Select every business listing that matches the provided structure
        business_listings = driver.find_elements(By.XPATH, "//div[contains(@class, 'businessName__09f24__HG_pC')]")

        for listing in business_listings:
            business_name = listing.find_element(By.XPATH, ".//h3/a").text
            business_link = listing.find_element(By.XPATH, ".//h3/a").get_attribute("href")
            business_dict[business_link] = {'name': business_name, 'url': business_link}
            logging.info(f"Business Name: {business_name}, Business Link: {business_link}")

    finally:
        # Close the WebDriver
        driver.quit()

    return business_dict

def extract_business_info(html_content, business_info):
    """
    This function extracts business information from a Yelp website snippet
    using BeautifulSoup.

    Args:
        html_content (str): The HTML content of the Yelp website snippet.
        business_info (dict): The dictionary containing business name and URL.

    Returns:
        dict: A dictionary containing the updated business information.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Update business_info dictionary with additional details
    business_info['category'] = soup.find('a', href=lambda href: href and "find_desc" in href).text.strip() if soup.find('a', href=lambda href: href and "find_desc" in href) else None
    business_info['claimed'] = soup.find('span', aria_hidden="true").find_next_sibling('span').text.strip() if soup.find('span', aria_hidden="true") else None
    business_info['closed'] = soup.find('span', text='Closed').find_next_sibling('span').text.strip() if soup.find('span', text='Closed') else None

    # Hours
    hours_table = soup.find('table', text=lambda text: text and "Location & Hours" in text)
    if hours_table:
        days = [th.find('p').text.strip() for th in hours_table.find_all('th')]
        hours = []
        for row in hours_table.find_all('td'):
            hours.extend([li.find('p').text.strip() for li in row.find_all('ul')])
        business_info['hours'] = dict(zip(days, hours))
    else:
        business_info['hours'] = None

    # Photos (assuming image source is in the src attribute)
    business_info['photos'] = [img['src'] for img in soup.find_all('img', aria_label="Photos & videos")]

    # Services Offered
    services_section = soup.find('section', aria_label="Services Offered")
    if services_section:
        business_info['services_offered'] = [a.text.strip() for a in services_section.find_all('a', href=lambda href: href and "find_desc" in href)]
    else:
        business_info['services_offered'] = None

    # Description
    description_section = soup.find('section', aria_label="About the Business")
    business_info['description'] = description_section.find('p').text.strip() if description_section else None

    # Address
    address_section = soup.find('address')
    if address_section:
        paragraphs = address_section.find_all('p')
        business_info['street'] = paragraphs[0].text.strip()
        unit_index = paragraphs.index(paragraphs[0].find('span', text="Main Floor")) if paragraphs[0].find('span', text="Main Floor") else None
        if unit_index:
            business_info['unit'] = paragraphs[unit_index + 1].text.strip()
        else:
            business_info['unit'] = None
        if unit_index:
            business_info['city_state_postal_code'] = paragraphs[unit_index + 2].text.strip()
        else:
            business_info['city_state_postal_code'] = paragraphs[1].text.strip()
        business_info['country'] = paragraphs[-1].text.strip()

    return business_info


def save_to_csv(data, filename='business_info.csv'):
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Name', 'Category', 'Claimed', 'Closed', 'Hours', 'Photos', 'Services Offered', 'Description', 'Street', 'Unit', 'City/State/Postal Code', 'Country'])
        for info in data:
            writer.writerow([
                info.get('name'), info.get('category'), info.get('claimed'), info.get('closed'),
                info.get('hours'), info.get('photos'), info.get('services_offered'), info.get('description'),
                info.get('street'), info.get('unit'), info.get('city_state_postal_code'), info.get('country')
            ])

all_business_info = []
visited_links = set()
for loc in locations:
    url = f"https://www.yelp.com/search?find_desc=Community+Service%2FNon-Profit&find_loc={loc}"
    business_dict = page_navigation(url)
    for link, info in business_dict.items():
        if link not in visited_links:
            driver = webdriver.Firefox(service=service, options=options)
            driver.get(link)
            html_content = driver.page_source
            business_info = extract_business_info(html_content, info)
            all_business_info.append(business_info)
            save_to_csv([business_info])
            visited_links.add(link)
            logging.info(f"Extracted and saved info for {info['name']}")
            driver.quit()


save_to_csv(all_business_info)


#url1 = "https://www.yelp.com/search?find_desc=Community+Service%2FNon-Profit&find_loc=Toronto%2C+ON"
#url2 = "https://www.yelp.com/biz/the-second-chance-foundation-toronto-3?osq=Community+Service%2FNon-Profit&override_cta=Request+information"

