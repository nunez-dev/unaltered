import requests
from bs4 import BeautifulSoup
import re
import numpy as np
import random
import logging
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import time
# Consider selenium_driverless, undetected_geckodriver
import sqlite3
import traceback
from tqdm.auto import tqdm
# pipreqs to regen requirements.txt if you update this!

# Overview:
# Iterate through a list of locations
# Construct queries of "Circumcision clinic in $(location)"
# Use a search engine to find the top RESULTS_PER_PAGE results
# Write to database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
debug = 0

# Can be off by one because google adds "Places" as first result
# Too many and they become irrelevant, but more is probably better
RESULTS_PER_PAGE = 21

# Number of top locations
LOCATIONS=50

# Feel free to experiment. We already wait a good while for the browser to load.
# More so for the first couple pages, then it speeds up. In seconds.
SLEEP_PER_SEARCH_LOWER = 1.6
SLEEP_PER_SEARCH_HIGHER = 2.4

#db
DB = "websites.sqlite3"
TABLE = "websites"

# Disclaimer
"""
Firstly, your location (as given by google) will be added to the database.
This helps reproduce certain searches, diagnose bad searches, and notice if your location is being leaked.

Even if your location was not added to the db, it would be discernable from the results.
It is far better to make it obvious that this information is at risk of leaking by using it in a non-confidential way,
than saying "it might be leaked" and being ambigious.

Despite best efforts google will show results from your location.
If there are a couple clinics from say, Brazil, while the query was for the US,
chances are that user was googling from Brazil. A VPN will improve accuracy of results and protect
your location from being guessable.
"""


####################
# Entry point
####################

def scrape():
    try:
        # First construct our queries
        # Google dork for more accuracy?
        query_base = "location:USA Infant circumcision clinic in "
        location_arr = np.genfromtxt("locations.csv", delimiter=',', dtype=None)
        queries = []

        for location in location_arr[0:LOCATIONS]:
            queries.append(query_base + location[0])

        print("Use a VPN if you care about your location being logged.")
        # Now google, add to db, repeat
        print("Starting selenium driver, may take a moment.")
        driver = get_driver()
        con = sqlite3.connect(DB)
        for i, query in enumerate(tqdm(queries, dynamic_ncols=True)):
            tqdm.write("Searching: " + query)
            serp_arr = query_serp(driver, query, location_arr[i])
            tqdm.write("Found " + str(len(serp_arr)) + " results.")
            tqdm.write("Google location: " + str(serp_arr[0][6]))
            delta = update_db(con, serp_arr)
            tqdm.write("Updated " + str(delta) + " row(s).")
            time.sleep(random.uniform(SLEEP_PER_SEARCH_LOWER, SLEEP_PER_SEARCH_HIGHER))
            
            if(debug):
                exit(1)
        
        finish(driver, con, "Completed scrape")

    # Exceptions
    except KeyboardInterrupt as e:
        finish(driver, con, "\nCtrl+C detected, shuting down...")
    except Exception as e:
        print(traceback.format_exc())
        finish(driver, con, "Fatal error, unknown exception\n" + repr(e))

####################
# Database
####################
# Scratchpad
# CREATE TABLE IF NOT EXISTS websites(rank INT, url TEXT PRIMARY KEY, title TEXT, snippet TEXT, city TEXT, state TEXT, googler_location TEXT, time INT, website_tar BLOB);
# ALTER TABLE websites ADD COLUMN googler_location TEXT
# DELETE FROM websites; SELECT * FROM websites

def update_db(con, serp_arr):
    '''Updates db with a given page of results
    
    Returns:
        Int representing how many rows were added (It will be 0 if no unique entries were given)
    '''
    try:
        # Will auto commit to db at the end of the "with" block
        # Or in the case of an exception (keybord interrupt etc)
        with con:
            cur = con.cursor()
            initial_row_count = cur.execute("SELECT COUNT(*) FROM " + TABLE).fetchone()[0]

            # Will silently fail insert if url is not UNIQUE, i.e already exists in db
            insert = "INSERT OR IGNORE INTO " + TABLE + "(rank, url, title, snippet, city, state, googler_location, time) VALUES (?,?,?,?,?,?,?,?)"
            for result_arr in serp_arr:
                cur.execute(insert, result_arr)

            final_row_count = cur.execute("SELECT COUNT(*) FROM " + TABLE).fetchone()[0]
            return final_row_count - initial_row_count

    except sqlite3.Error as e:
        print("Database failure: ", repr(e))

####################
# Scraping
####################

def get_driver():
        # Reluctantly use chrome for better bot undetectability.
        # i.e experimental options and more discussion and plugins
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        #options.add_argument("start-maximized")
        #options.add_argument("--headless")
        # Disable geolocation, important.
        prefs = {"profile.default_content_setting_values.geolocation" :2}
        options.add_experimental_option("prefs",prefs)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        driver = webdriver.Chrome(options=options)
        
        # Or try firefox
        # options = webdriver.FirefoxOptions()
        # profile = webdriver.FirefoxProfile("l5lhxsk9.selenium")
        # profile.set_preference("dom.webdriver.enabled", False)
        # profile.set_preference("useAutomationExtension", False)
        # profile.update_preferences()
        # options.profile = profile
        # driver = webdriver.Firefox(options=options)
        # driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver

def query_serp(driver, query, l_arr):
    base_url = "https://www.google.com/search?hl=en&num=" + str(RESULTS_PER_PAGE) + "&q="
    if(debug):
        html = open("output.html", 'r')
        soup = BeautifulSoup(html, "html.parser")
    else:
        driver.get(base_url + query)
        # Quite frankly idk what this does but it is meant to wait for document.readyState to be complete
        WebDriverWait(driver, 10).until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
        soup = BeautifulSoup(driver.page_source, "html.parser")
        dump_html(soup.contents)
    try:
        results = parse_serp(soup, str(l_arr[0]), str(l_arr[1]), time.time())
    except AttributeError as e:
        print("Failed to parse serp: ", repr(e), " with query ", query)
        print("Please check your internet connection. Waiting 10s...")
        print(traceback.format_exc())
        time.sleep(10)
    except (KeyError, TypeError) as e:
        print("Failed to parse serp: ", repr(e), " with query ", query)
    return results

def parse_serp(soup, city, state, time):
    '''Will return a 2d array of scraped result values plus relevant args
    
    Returns:
        [rank, url, name, snippet, city, state, googler_location, time (unix timestamp)], []...
    '''
    div = soup.find("div", id="search")
    h3s = div.find_all(h3_search)
    results = []
    # Let's get the location google thinks we are as well, that's useful
    update_location = soup.find_all("update-location")
    googler_location = update_location[-1].parent.find_next("a").find_all("span")[1].text
    for i, h3 in enumerate(h3s):
        rank = i+1
        url = h3.parent["href"]
        heading = h3.string
        parents = h3.find_parents(parent_search)
        snippet = parents[0].find_next_sibling("div").text
        row = [rank, url, heading, snippet, city, state, googler_location, time]
        results.append(row)
    return results

####################
# Utils
####################

def finish(driver, con, message=""):
    driver.quit()
    con.close()
    print(message)

def parent_search(tag):
    return tag.has_attr('class') and tag.has_attr('data-snhf')

def h3_search(tag):
    '''Excludes the junk buried in the collapsable "People also ask"'''
    return tag.name == "h3" and (len(tag.find_parents(parent_search)) > 0)

####################
# Debug
####################

# Expects request object
def dump_requests(r):
    if(debug):
        with open("./request", 'w') as fd:
            info = str(r.request.url) + '\n' + str(r.request.body) + '\n' + str(r.request.headers)
            fd.write(info)
        with open("./response", 'w') as fd:
            info = str(r.status_code) + '\n' + str(r.headers) + '\n' + str(r.cookies)
            fd.write(info)

def dump_html(out):
    with open("./output.html", 'w') as fd:
        fd.write(str(out))


####################
# Main
####################

if __name__ == "__main__":
    scrape()