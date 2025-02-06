import requests
from bs4 import BeautifulSoup
import time
import sqlite3
import traceback
from tqdm.auto import tqdm

#db
DB = "websites.sqlite3"
TABLE_LIST = "website_list"
TABLE_CONTENT = "website_content"

# 0 for url page only, 1 for links found there (depth of 1)
DEPTH = 1

####################
# Entry point
####################

def get_sites():
    try:
        con = sqlite3.connect(DB)
        urls = parse_db(con)
        for url in urls:
            print(url[0])
            tar = download_page(url[0], DEPTH)
            insert_db(con, tar)
            time.sleep(5)

        finish(con, "Completed scrape")

    # Exceptions
    except KeyboardInterrupt as e:
        finish(con, "\nCtrl+C detected, shuting down...")
    except Exception as e:
        print(traceback.format_exc())
        finish(con, "Fatal error, unknown exception\n" + repr(e))

####################
# Scraping
####################

def download_page(url, depth):
    r = requests.get(url)
    if(r.status_code != requests.codes.ok):
        print(r.status_code)
        return 1
    soup = BeautifulSoup(r.text, "html.parser")
    print(soup.text)

def parse_page():
    pass

####################
# Database
####################
# CREATE TABLE IF NOT EXISTS website_content(url TEXT, website_tar BLOB, time INT, status_code INT, FOREIGN KEY(url) REFERENCES website_list(url));


def parse_db(con):
    try:
        with con:
            cur = con.cursor()
            result = cur.execute("SELECT url FROM " + TABLE_LIST)
            return result.fetchall()

    except sqlite3.Error as e:
        print("Database failure: ", repr(e))

def insert_db(con, website_tar):
    return 1
    try:
        with con:
            cur = con.cursor()
            result = cur.execute("INSERT OR IGNORE INTO " + TABLE_CONTENT + "(url, website_tar, time, status_code)")
            return result.fetchall()

    except sqlite3.Error as e:
        print("Database failure: ", repr(e))

####################
# Utils
####################

def finish(con, message=""):
    con.close()
    print(message)

####################
# Main
####################

if __name__ == "__main__":
    get_sites()