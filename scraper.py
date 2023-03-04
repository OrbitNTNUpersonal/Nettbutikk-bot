from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os 
import requests
import pickle

def findNewItems(prev_list, new_list):
    '''
    Both lists are represented by dictionaries where the key is the url to the item
    and the value is the name of the item.
    prev_list : Last pulled list.
    new_list : Currently pulled list from the website. 
    

    Returns items in new_list that are not in prev_list. If there are no new items return None. 
    '''
    new_items = {}
    for i in new_list:
        if i not in prev_list:
            new_items[i] = new_list[i]
    return None if new_items == {} else new_items

# Initialise driver
options = Options()
options.add_argument("--headless=new")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),
                          options=options)

# Log in
load_dotenv()
username = os.environ.get('USERNAME')
password = os.environ.get('PASSWORD')

driver.get("https://www.ntnu.no/nettbutikk/gjenbruk/produktkategori/produkter/")
driver.find_element("name", "feidename").send_keys(username)
driver.find_element("name", "password").send_keys(password)
driver.find_element("xpath", '//button[@type="submit"]').click()

# Get list of items in html format
items_list = driver.find_element("xpath", '//ul[@class="products columns-5"]') 
items_list = items_list.get_attribute("innerHTML") # Get list of postings in html format
soup = BeautifulSoup(items_list, 'html.parser') # Create soup object for easy parsing
items_html = soup.find_all('li') # Get array of items on nettbutikk

# Close web driver
driver.quit()

# Parse html list and store items in dictionary using the link to that items page as the key
curr_items = {}
for item in items_html:
    item_name = item.find('h2').get_text()
    item_link = item.find('a').get('href')
    curr_items[item_link] = item_name
    
# Pull prevopusly checked list of items from pickle database
with open("data.pickle", "rb") as f:
    try:
        prev_items = pickle.load(f)
    except:
        prev_items = {}

# Exctract list of new items by comparing previously pulled list with current list of items
new_items = findNewItems(prev_items, curr_items)

# If curr_list has new items then send slack message and update db with curr_items
if new_items != None:
    # Slack message
    slack_address = os.environ.get('SLACK_ADDRESS')
    for i in new_items:
        payload = '{"text": "A new %s has been posted at %s"}' % (new_items[i], i)
        response = requests.post(
            slack_address,
            data = payload
        )
        print("Message sent to slack with status: ", response.text)

    # Write new list to db
    with open("data.pickle", "wb") as f:
        print("writing to db")
        pickle.dump(curr_items, f)