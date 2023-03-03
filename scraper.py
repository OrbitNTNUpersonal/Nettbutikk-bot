from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os 
import csv
import time # to be deleted
import requests
import pickle

def findNewItems(prev_list, new_list):
    '''
    prev_list : Last pulled list.
    new_list : Currently pulled list from the website.
    Items in both lists are represented by strings of the items url. 

    Returns items in new_list that are not in prev_list. If there are no new items return None. 
    '''
    new_items = {}
    for i in new_list:
        if i not in prev_list:
            new_items[i] = new_list[i]
    return None if new_items == [] else new_items

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

# Parse html list and store items in dictionary
curr_items = {}
for item in items_html:
    item_name = item.find('h2').get_text()
    item_link = item.find('a').get('href')
    curr_items[item_link] = item_name
    
# pull prev list from database
with open("data.pickle", "rb") as f:
    try:
        prev_items = pickle.load(f)
        print("Recieved prev list successfully")
    except:
        prev_items = {}
        print("Prev list reset to empty")

# Exctract list of new items
new_items = findNewItems(prev_items, curr_items)

# if curr_list has new items then 1. send slack message 2. update llist in db
if new_items != None:
    # Slack message
    slack_address = 'https://hooks.slack.com/services/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'
    for i in new_items:
        payload = '{"text": "A new %s has been posted at %s!"}' % (i ,new_items[i])
        response = requests.post(
            slack_address,
            data = payload
        )
        print("Message sent to slack with status: ", response.text)

    # Write new list to db
    with open("data.pickle", "wb") as f:
        pickle.dump(curr_items, f)