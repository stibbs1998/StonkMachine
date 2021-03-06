# -*- coding: utf-8 -*-
"""STONK-MACHINE.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1omCiG-8rHGchiHO6PBlekUuWtQK0-mZW

## Stonks only Go Up
Use this to get data from hedge fund holdings
"""

# Libraries
import requests
import re
import csv
import lxml
from bs4 import BeautifulSoup
import xmltodict
import json
import pandas as pd

"""### Functions"""

sec_url = 'https://www.sec.gov'

def get_request(url):
    return requests.get(url)

def create_url(cik):
    return 'https://www.sec.gov/cgi-bin/browse-edgar?CIK={}&owner=exclude&action=getcompany&type=13F-HR'.format(cik)

def get_user_input():
    cik = input("Enter 10-digit CIK number: ")
    return cik


hedgeFundMapper = pd.read_csv("data/CIK-Number-Lookup.csv")

"""Input a CIK number and get the XML data"""

hedgeFundMapper['CIKNBR'] = hedgeFundMapper['CIKNBR'].apply(lambda x: "0"*(10-len(str(x))) + str(x))

masterDF = pd.DataFrame()

for date, companyNM, requested_cik in hedgeFundMapper.values:

    print(requested_cik)

    # Find mutual fund by CIK number on EDGAR
    response = get_request(create_url(requested_cik))
    soup = BeautifulSoup(response.text, "html.parser")
    tags = soup.findAll('a', id="documentsbutton")

    # Find latest 13F report for mutual fund
    try:
        response_two = get_request(sec_url + tags[0]['href'])
        soup_two = BeautifulSoup(response_two.text, "html.parser")
        tags_two = soup_two.findAll('a', attrs={'href': re.compile('xml')})
        xml_url = tags_two[3].get('href')

        response_xml = get_request(sec_url + xml_url)
        soup_xml = BeautifulSoup(response_xml.content, "lxml")

        hedgefundJSON = xmltodict.parse(str(soup_xml.body))
        secondKey = list(hedgefundJSON['body'].keys())[0]
        infoTableKey =  list(hedgefundJSON['body'][secondKey].keys())[-1]
        infoTable = hedgefundJSON['body'][secondKey][infoTableKey]

        json_data = json.dumps(infoTable)

        with open(f"data/{requested_cik}.json", "w") as json_file:
            json_file.write(json_data)

        cikDF = pd.read_json(f"data/{requested_cik}.json")

        if cikDF.columns.values[0][:4] == "ns1:":
            cikDF.columns = [name[4:] for name in cikDF.columns.values]

        cikDF['CIK'] = requested_cik
        cikDF['HedgeFundNM'] = companyNM.strip()

        try:
            totalValue = sum(cikDF['value'])
            cikDF['PercentOfPortfolio'] = cikDF['value']/totalValue

            cikDF.to_csv(f"data/{requested_cik}.csv")

            masterDF = pd.concat([masterDF, cikDF], sort = False)
        except KeyError:
            continue
    except IndexError:
        continue


masterDF.to_csv("data/last300Filings.csv")
