# ----------------
# IMPORT PACKAGES
# ----------------

# Beautiful Soup is a Python package designed for navigating, searching and modifying parse tree.
# Requests is a package that allows download of data from any online resource.
# The sqlite3 model is used to work with the SQLite database.
# The pandas package is used to fetch and store data in a DataFrame.
from bs4 import BeautifulSoup
import requests
import sqlite3 as lite
import pandas as pd

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

# Obtain values parsed data
rows = []
for i in range(4, len(data)):
	# Data from data[0] to data[3] are not ones with desired data
	tr = data[i]
	# Use .string to pull strings of the object
	value = [td.string for td in tr("td")]
	# Data of country, year, men years and women years are in 'data[i]("td")[x].string' where x are 0, 1, 7, 10.
	rows.append(list(value[i] for i in [0, 1, 7, 10]))

# ----------------
# STORE DATA
# ----------------

# Connect to the database. The "connect()" method returns a connection object.
con = lite.connect("education.db")
cur = con.cursor()

# Create the table specifying the name of columns and their data types.
with con:
	# Drop currently existing tables.
	cur.execute("DROP TABLE IF EXISTS un_education")
	# Construct the table and add the listed and ordered data.
	cur.execute("CREATE TABLE un_education (country TEXT, year INT, men INT, women INT);")
	cur.executemany("INSERT INTO un_education (country, year, men, women) VALUES (?, ?, ?, ?)", rows)

# ----------------
# ANALYZE DATA
# ----------------

# Load collected data into a DataFrame
df = pd.DataFrame(rows, columns=["Country", "Year", "Men", "Women"])
# Set "Year" column to be the index
df = df.set_index("Year")
# Convert the values under the "Men" and "Women" column
df[["Men", "Women"]] = df[["Men", "Women"]].astype(int)

# Determine the average and standard deviation (variation) of the number of years each gender goes for education.
print("")
print("The international average number of years " + str(df.columns[1]).lower() + " are likely to stay in school is " 
	+ str(round(df["Men"].mean(), 2)) + " with a variation of approximately " + str(round(df["Men"].std(), 2)) + " years.")
print("The international average number of years " + str(df.columns[2]).lower() + " are likely to stay in school is " 
	+ str(round(df["Women"].mean(), 2)) + " with a variation of approximately " + str(round(df["Women"].std(), 2)) + " years.")