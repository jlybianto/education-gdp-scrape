# ----------------
# IMPORT PACKAGES
# ----------------

# Beautiful Soup is a Python package designed for navigating, searching and modifying parse tree.
# Requests is a package that allows download of data from any online resource.
# The sqlite3 model is used to work with the SQLite database.
# The pandas package is used to fetch and store data in a DataFrame.
# The csv (comma separated values) module implements classes to read and write tabular data.
# The matplotlib package is for graphical outputs (eg. box-plot, histogram, QQ-plot).
# The numpy package is for scientific computing and container of generic data (used for generating a continuous distribution)
# The statsmodels is used to find the model coefficients. Formula holds lower case models.
from bs4 import BeautifulSoup
import requests
import sqlite3 as lite
import pandas as pd
import csv
import matplotlib.pyplot as plt
import numpy as np
import statsmodels.api as sm

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

# Import country GDP data from CSV file.
# Data columns start in Row 5
df_gdp = pd.read_csv("country-gdp-1960-2014.csv", skiprows=4)
# Filter columns with years of interest (UN Data 1999-2010)
period = pd.period_range("1999", "2010", freq="A-DEC")
period = list(str(t) for t in period)
col = ["Country Name"] + period
df_gdp = df_gdp[col]

# ----------------
# STORE DATA
# ----------------

# Connect to the database. The "connect()" method returns a connection object.
con = lite.connect("education.db")
cur = con.cursor()

# Create the table specifying the name of columns and their data types for country, years of education and gender.
with con:
	# Drop currently existing table.
	cur.execute("DROP TABLE IF EXISTS un_education")
	# Construct the table and add the listed and ordered data.
	cur.execute("CREATE TABLE un_education (Country TEXT, Year INT, Men INT, Women INT);")
	cur.executemany("INSERT INTO un_education (country, year, men, women) VALUES (?, ?, ?, ?)", rows)

# Create the table specifying the name of columns and their data types.
with con:
	# Drop currently existing table
	cur.execute("DROP TABLE IF EXISTS gdp")
	# Construct the table
	cur.execute("CREATE TABLE gdp (Country TEXT, Year INT, GDP NUMERIC);")
	for row in df_gdp.index:
		values = []
		for year in period:
			values = values + [(df_gdp.ix[row]["Country Name"], year, df_gdp.ix[row][year])]
		cur.executemany("INSERT INTO gdp (Country, Year, GDP) VALUES (?, ?, ?)", values)

# Load the data from two separate tables into a single DataFrame.
# Table columns are "Country, Year, Men, Women, GDP"
load = ("SELECT T1.Country, T1.Year, Men, Women, GDP "
		"FROM un_education T1 "
		"INNER JOIN gdp T2 ON T1.Country = T2.Country "
		"AND T1.Year = T2.Year")

df = pd.read_sql_query(load, con)
df.dropna(inplace=True)

# ----------------
# ANALYZE DATA
# ----------------

# Load collected data into a DataFrame
df_un = pd.DataFrame(rows, columns=["Country", "Year", "Men", "Women"])
# Set "Year" column to be the index
df_un = df_un.set_index("Year")
# Convert the values under the "Men" and "Women" column
df_un[["Men", "Women"]] = df_un[["Men", "Women"]].astype(int)

# Determine the average and standard deviation (variation) of the number of years each gender goes for education.
print("")
print("The international average number of years " + str(df_un.columns[1]).lower() + " are likely to stay in school is " 
	+ str(round(df_un["Men"].mean(), 2)) + " with a variation of approximately " + str(round(df_un["Men"].std(), 2)) + " years.")
print("The international average number of years " + str(df_un.columns[2]).lower() + " are likely to stay in school is " 
	+ str(round(df_un["Women"].mean(), 2)) + " with a variation of approximately " + str(round(df_un["Women"].std(), 2)) + " years.")

# ----------------
# VISUALIZE DATA
# ----------------

# Scatter Plot GDP and School Life Expectancy for Male and Female
plt.figure(figsize=(10, 10))
plt.scatter(df["GDP"], df["Men"], alpha=0.5)
plt.gca().grid(True)
plt.xlabel("Gross Domestic Product (GDP)", fontsize=14)
plt.ylabel("School Life Expectancy (Years)", fontsize=14)
plt.title("Male International School Life Expectancy and GDP", fontsize=18)
plt.savefig("male_GDP.png")

plt.figure(figsize=(10, 10))
plt.scatter(df["GDP"], df["Women"], alpha=0.5)
plt.gca().grid(True)
plt.xlabel("Gross Domestic Product (GDP)", fontsize=14)
plt.ylabel("School Life Expectancy (Years)", fontsize=14)
plt.title("Female International School Life Expectancy and GDP", fontsize=18)
plt.savefig("female_GDP.png")

# No trend due to extremely wide distribution of GDP values.
# Attempt with logarithmic transformation.
df["log_GDP"] = [np.log10(n) for n in df["GDP"]]

plt.figure(figsize=(10, 10))
plt.scatter(df["log_GDP"], df["Men"], alpha=0.5)
plt.gca().grid(True)
plt.xlabel("Gross Domestic Product (Log GDP)", fontsize=14)
plt.ylabel("School Life Expectancy (Years)", fontsize=14)
plt.title("Male International School Life Expectancy and Log GDP", fontsize=18)
plt.savefig("male_logGDP.png")

plt.figure(figsize=(10, 10))
plt.scatter(df["log_GDP"], df["Women"], alpha=0.5)
plt.gca().grid(True)
plt.xlabel("Gross Domestic Product (Log GDP)", fontsize=14)
plt.ylabel("School Life Expectancy (Years)", fontsize=14)
plt.title("Female International School Life Expectancy and Log GDP", fontsize=18)
plt.savefig("female_logGDP.png")

# ----------------
# MODEL DATA
# ----------------

# Model logarithm of GDP and school life expectancy
logGDP = df["log_GDP"]
men = df["Men"]
women = df["Women"]

# Extraction of a column from a DataFrame is returned as a Series data type.
z = np.matrix(logGDP).transpose()
y = np.matrix(men).transpose()
x = np.matrix(women).transpose()
w = sm.add_constant(z)

# Create the linear model and summarized evaluation of data.
model_men = sm.OLS(y, w).fit()
print ""
print model_men.summary()
print "Intercept: ", model_men.params[0]
print "Coefficient: ", model_men.params[1]
print "P-Value: ", model_men.pvalues[0]
print "R-Squared: ", model_men.rsquared

model_women = sm.OLS(x, w).fit()
print ""
print model_women.summary()
print "Intercept: ", model_women.params[0]
print "Coefficient: ", model_women.params[1]
print "P-Value: ", model_women.pvalues[0]
print "R-Squared: ", model_women.rsquared

# Plot scatter together with linear regression
logspace = np.arange(min(df["log_GDP"]), max(df["log_GDP"]), 0.5)
plt.figure(figsize=(10, 10))
plt.scatter(df["log_GDP"], df["Men"], alpha=0.5, color="r")
plt.scatter(df["log_GDP"], df["Women"], alpha=0.5, color="b")
plot1, = plt.plot(model_men.params[0] + model_men.params[1] * logspace, "r", label="Men")
plot2, = plt.plot(model_women.params[0] + model_women.params[1] * logspace, "b", label="Women")
plt.gca().grid(True)
plt.legend(handles=[plot1, plot2], loc=2, fontsize=14)
plt.xlabel("log(Gross Domestic Product)", fontsize=14)
plt.ylabel("School Life Expectancy (Years)", fontsize=14)
plt.title("International School Life Expectancy vs Gross Domestic Product", fontsize=16)
plt.savefig("SLE_GDP.png")