import os
import requests
import xml.etree.ElementTree as ET
from requests.auth import HTTPBasicAuth

CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_KEY = os.environ["CLIENT_KEY"]

FIFE_TERMS = [
    "A92",
    "M90",
    "A985",
    "A921",
    "Kirkcaldy",
    "Dunfermline",
    "Rosyth",
    "Dalgety Bay",
    "Burntisland",
    "Leven",
    "Glenrothes",
    "Cupar",
    "Inverkeithing",
    "Halbeath",
    "Queensferry",
    "Forth Road Bridge"
]

url = "https://datex2.trafficscotland.org/rest/2.3/publications/UnplannedEvents/Content.xml"

response = requests.get(
    url,
    auth=HTTPBasicAuth(CLIENT_ID, CLIENT_KEY),
    timeout=30
)

response.raise_for_status()

ns = {
    "d2": "http://datex2.eu/schema/2/2_0"
}

root = ET.fromstring(response.text)

items = []

for record in root.findall(".//d2:situationRecord", ns):

    xml_text = ET.tostring(record, encoding="unicode")

    if any(term.lower() in xml_text.lower() for term in FIFE_TERMS):
        items.append(("Fife Traffic Alert", "Traffic incident"))

rss = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>K107FM Fife Travel Alerts</title>
<link>https://k107fm.github.io/k107fm-travel-feed/</link>
<description>Live Traffic Scotland updates for Fife</description>
<item>
<title>No major incidents reported</title>
<description>No significant delays currently reported on key Fife routes.</description>
<guid>fallback</guid>
</item>
</channel>
</rss>
"""

with open("fife-travel.xml", "w", encoding="utf-8") as f:
    f.write(rss)

print("RSS file written")
print("Items 
