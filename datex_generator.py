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

    record_text = ET.tostring(record, encoding="unicode")

    if any(term.lower() in record_text.lower() for term in FIFE_TERMS):

        road = "Fife Traffic Alert"
        description = "Traffic incident"

        road_node = record.find(
            ".//d2:ilc/d2:descriptor/d2:values/d2:value",
            ns
        )

        if road_node is not None and road_node.text:
            road = road_node.text

        comment_node = record.find(
            ".//d2:generalPublicComment/d2:comment/d2:values/d2:value",
            ns
        )

        if comment_node is not None and comment_node.text:
            description = comment_node.text

        items.append((road, description))

rss_items = ""

if len(items) == 0:
    rss_items = (
        "<item>"
        "<title>No major incidents reported</title>"
        "<description>No significant delays currently reported on key Fife routes.</description>"
        "<guid>fallback</guid>"
        "</item>"
    )
else:
    for i, (title, description) in enumerate(items[:20], start=1):
        rss_items += (
            f"<item>"
            f"<title>{title}</title>"
            f"<description>{description}</description>"
            f"<guid>{i}</guid>"
            f"</item>"
        )

rss = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<rss version="2.0">'
    '<channel>'
    '<title>K107FM Fife Travel Alerts</title>'
    '<link>https://k107fm.github.io/k107fm-travel-feed/</link>'
    '<description>Live Traffic Scotland updates for Fife</description>'
    + rss_items +
    '</channel>'
    '</rss>'
)

with open("fife-travel.xml", "w", encoding="utf-8") as f:
    f.write(rss)

print("RSS updated")
print("Items found:", len(items))
