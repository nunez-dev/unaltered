import time
import sqlite3
import json

DB = "websites.sqlite3"
TABLE_LIST = "website_list"
TABLE_CONTENT = "website_content"


####################
# Database
####################

def get_db():
    try:
        con = sqlite3.connect(DB)
        with con:
            cur = con.cursor()
            result = cur.execute("SELECT rank,url,title,city,state FROM " + TABLE_LIST)
            return result.fetchall()

    except sqlite3.Error as e:
        print("Database failure: ", repr(e))
        con.close()
    con.close()
####################
# Main
####################

# Rank, Url, Title, City, State, Offending Statement (Automatic), Offending Statement (Manual),
# Wayback Machine (Manual), Contacted By, First Contact Date, Status, Expired Health Policy,
# Scientifically Unsupported Claims, Religious Freedoms, Parental Freedoms, Appeal To Tradition,
# Clinic, Hospital, Blog, Aggregator, Other.

if __name__ == "__main__":
    dict_array = []
    rows = get_db()
    for row in rows:
        row_dict = {
            "Rank": row[0],
            "Url": row[1],
            "Title": row[2],
            "City": row[3],
            "State": row[4],
            "Offending Statement (Automatic)": "",
            "Offending Statement (Manual)": "",
            "Wayback Machine (Manual)": "",
            "Contacted By": "",
            "First Contact Date": "",
            "Status": "",
            "Expired Health Policy": "",
            "Scientifically Unsupported Claims": "",
            "Religious Freedoms": "",
            "Parental Freedoms": "",
            "Appeal To Tradition": "",
            "Clinic": "",
            "Hospital": "",
            "Blog": "",
            "Aggregator": "",
            "Other": ""
        }
        dict_array.append(row_dict)
    print(json.dumps(dict_array, indent=4))