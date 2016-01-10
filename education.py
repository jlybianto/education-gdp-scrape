# ----------------
# IMPORT PACKAGES
# ----------------

# Beautiful Soup is a Python package designed for navigating, searching and modifying parse tree.
# Requests is a package that allows download of data from any online resource.
from bs4 import BeautifulSoup
import requests

# ----------------
# OBTAIN DATA
# ----------------

# Import the page that contains the data to be scraped through requesting its URL
url = "http://web.archive.org/web/20110514112442/http://unstats.un.org/unsd/demographic/products/socind/education.htm"
r = requests.get(url)

soup = BeautifulSoup(r.content)

# Parse through content tables for relevant data.
# Data is in table 7 (index 6) from 14 tables. Find all table rows ("tr").
data = soup("table")[6].find_all("tr")
# Data is in row 4 or index 3 // len(soup("table")[6].find_all("tr")) = 202
data = data[3]
# Data is in table 1 or index 0 // len(data("table")) = 2
data = data("table")[0]
# Filter all table rows ("tr") // len(data("table")[0]) = 375
data = data("tr")