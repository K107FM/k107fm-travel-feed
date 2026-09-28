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

    text = ET.tostring(record, encoding="unicode")

    if any(term.lower() in text.lower() for term in FIFE_TERMS):

        comment = "Traffic incident"

        comment
