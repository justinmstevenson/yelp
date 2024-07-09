from pprint import pprint
import os
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import logging

categories = ['Community+Service%2FNon-Profit']
locations = [
    'Toronto%2C+ON',        # 2,731,571
    'Montreal%2C+QC',       # 1,704,694
    'Calgary%2C+AB',        # 1,239,220
    'Ottawa%2C+ON',         # 934,243
    'Edmonton%2C+AB',       # 932,546
    'Mississauga%2C+ON',    # 721,599
    'Winnipeg%2C+MB',       # 705,244
    'Vancouver%2C+BC',      # 631,486
    'Brampton%2C+ON',       # 593,638
    'Hamilton%2C+ON',       # 536,917
    'Quebec+City%2C+QC',    # 531,902
    'Surrey%2C+BC',         # 517,887
    'Laval%2C+QC',          # 422,993
    'Halifax%2C+NS',        # 403,131
    'London%2C+ON',         # 383,822
    'Markham%2C+ON',        # 328,966
    'Vaughan%2C+ON',        # 306,233
    'Gatineau%2C+QC',       # 276,245
    'Saskatoon%2C+SK',      # 246,376
    'Longueuil%2C+QC',      # 239,700
    'Kitchener%2C+ON',      # 233,222
    'Burnaby%2C+BC',        # 232,755
    'Windsor%2C+ON',        # 217,188
    'Regina%2C+SK',         # 215,106
    'Richmond%2C+BC',       # 198,309
    'Richmond+Hill%2C+ON',  # 195,022
    'Oakville%2C+ON',       # 193,832
    'Burlington%2C+ON',     # 183,314
    'Greater+Sudbury%2C+ON',# 161,531
    'Sherbrooke%2C+QC',     # 161,323
    'Oshawa%2C+ON',         # 159,458
    'Saguenay%2C+QC',       # 144,746
    'Levis%2C+QC',          # 143,414
    'Barrie%2C+ON',         # 141,434
    'Abbotsford%2C+BC',     # 141,397
    'Coquitlam%2C+BC',      # 139,284
    'Trois-Rivieres%2C+QC', # 134,413
    'St.+Catharines%2C+ON', # 133,113
    'Guelph%2C+ON',         # 131,794
    'Cambridge%2C+ON',      # 129,920
    'Whitby%2C+ON',         # 128,377
    'Kelowna%2C+BC',        # 127,380
    'Kingston%2C+ON'        # 123,798
]

for loc in locations:
    URL = f"https://www.yelp.com/search?find_desc=Community+Service%2FNon-Profit&find_loc={locations}"


# Configure logging
logging.basicConfig(filename='download_log.log', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

TIMEOUT = 10  # Set your desired wait time in seconds

def extract_business_info(html_content):
  """
  This function extracts business information from a Google Maps website snippet
  using BeautifulSoup.

  Args:
      html_content (str): The HTML content of the Google Maps website snippet.

  Returns:
      dict: A dictionary containing the extracted business information.
  """
  soup = BeautifulSoup(html_content, 'html.parser')

  info = {}

  # Business Name
  info['name'] = WebDriverWait(soup, TIMEOUT).until(EC.presence_of_element_located((By.TAG_NAME, 'h1'))).text.strip()

  # Category
  category_link = soup.find('a', href=lambda href: href and "find_desc" in href)
  info['category'] = category_link.text.strip() if category_link else None

  # Claimed Status
  claimed_span = soup.find('span', aria_hidden="true")
  info['claimed'] = claimed_span.find_next_sibling('span').text.strip() if claimed_span else None

  # Closed Status
  closed_span = WebDriverWait(soup, TIMEOUT).until(EC.presence_of_element_located((By.XPATH, "//span[text()='Closed' and @data-font-weight='semibold']"))).find_next_sibling('span').text.strip()

  # Hours
  hours_table = soup.find('table', text=lambda text: text and "Location & Hours" in text)
  if hours_table:
    days = [th.find('p').text.strip() for th in hours_table.find_all('th')]
    hours = []
    for row in hours_table.find_all('td'):
      hours.extend([li.find('p').text.strip() for li in row.find_all('ul')])
    info['hours'] = dict(zip(days, hours))
  else:
    info['hours'] = None

  # Photos (assuming image source is in the src attribute)
  photos = [img['src'] for img in soup.find_all('img', aria_label="Photos & videos")]
  info['photos'] = photos

  # Services Offered
  services_section = soup.find('section', aria_label="Services Offered")
  if services_section:
    services = [a.text.strip() for a in services_section.find_all('a', href=lambda href: href and "find_desc" in href)]
    info['services_offered'] = services
  else:
    info['services_offered'] = None

  # Description
  description_section = soup.find('section', aria_label="About the Business")
  info['description'] = description_section.find('p').text.strip() if description_section else None

  # Address
  address_section = soup.find('address')
  if address_section:
    paragraphs = address_section.find_all('p')
    info['street'] = paragraphs[0].text.strip().split('>')[1]
    unit_index = paragraphs.index(paragraphs[0].find('span', text="Main Floor")) if paragraphs[0].find('span', text="Main Floor") else None
    if unit_index:
      info['unit'] = paragraphs[unit_index + 1].text.strip()
    else:
      info['unit'] = None
    if unit_index:
      info['city_state_postal_code'] = paragraphs[unit_index + 2].text.strip().split('>')[1]
    else:
      info['city_state_postal_code'] = paragraphs[1].text.strip().split('>')[1]
    info['country'] = paragraphs[-1].text.



# Replace these with the URLs you want to fetch
url1 = "https://www.yelp.com/search?find_desc=Community+Service%2FNon-Profit&find_loc=Toronto%2C+ON"
url2 = "https://www.yelp.com/biz/the-second-chance-foundation-toronto-3?osq=Community+Service%2FNon-Profit&override_cta=Request+information"
