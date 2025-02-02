import requests
from bs4 import BeautifulSoup
import re
import numpy as np

if __name__ == "__main__":
    response = requests.get("https://en.wikipedia.org/wiki/List_of_United_States_cities_by_population")
    soup = BeautifulSoup(response.text, "html.parser")
    #fd = open("~/Downloads/List of United States cities by population - Wikipedia.html", encoding='utf-8-sig')
    #soup = BeautifulSoup(fd, "html.parser")
    table = soup.find_all(class_=re.compile("sortable wikitable .*"))[0]
    table_arr = []
    for row in table.find_all("tr"):
        row_arr = []
        for column in row.find_all("td"):
            if(column.a != None):
                if(column.a.string != None):
                    row_arr.append(column.a.string)
                else:
                    row_arr.append(column.find(class_="geo-dec").string)
            else:
                row_arr.append(column.text.replace('\n',''))
        if(len(row_arr) != 0):
            table_arr.append(row_arr)

# City, State, 2023 est, 2020 census, change, (area) mi^2, (area) km^2, (density) mi^2, (density) km^2, location
a = np.asarray(table_arr)
a = np.strings.replace(a, ',', '')
np.savetxt("locations.csv", a, delimiter=',', fmt='%s')
