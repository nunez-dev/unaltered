# unaltered

## ClinicScraper.py:
This is an intactivist web scraper which will search google for circumcision clinics in each city provided in locations.csv (top 100 US cities).
Timing and results per search can be found in the python file.
Each successful search will update websites.sqlite3 with the urls found. You can use sqlitebrowser to view this.
The end goal is to detect unlawful usage of expired health policy and harmful rhetoric about circumcision.
<br>
<br>

__First time running:__
```bash
# Install python :)
# Open a terminal where you want the project to be (cmd/bash/etc)
git clone https://github.com/nunez-dev/unaltered.git
cd unaltered
# Create a virtual environment to install the required dependencies
python3 -m venv venv
# Windows
.\venv\Scripts\activate.bat
# Linux
source ./venv/bin/activate
# Install reqs
pip3 install -r requirements.txt
# Now your requirements are installed in this temporary environment 'venv'

python3 ./ClinicScraper.py
# Expect a chrome window popup to perform the searches
# Close at any time (ctrl+c in terminal) and previous searches will be saved
```
<br>

__Subsequent runs:__
```bash
# If you have launched a new terminal or exited out of the environment,
# you will need to re-initialise the venv before running
# Windows
.\venv\Scripts\activate.bat
# Linux
source ./venv/bin/activate

python3 ./ClinicScraper.py
```
