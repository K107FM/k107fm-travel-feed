import os
import requests
import xml.etree.ElementTree as ET
from collections import defaultdict
from requests.auth import HTTPBasicAuth
from datetime import datetime

CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_KEY = os.environ["CLIENT_KEY"]

FIFE_TERMS = [
    "Fife",
    "A92",
    "M90",
    "A985",
    "A921",
    "A915",
    "A916",
    "A909",
    "A823",
    "Kirkcaldy",
    "Dunfermline",
    "Rosyth",
    "Dalgety Bay",
    "Burntisland",
    "Leven",
    "Methil",
    "Glenrothes",
    "Cupar",
    "St Andrews",
    "Inverkeithing",
    "Halbeath",
    "Crossgates",
    "Cowdenbeath",
    "Lochgelly",
    "Kelty",
    "Queensferry",
    "Queensferry Crossing",
    "Forth Road Bridge"
]

LOCATION_MAP = {
    "J1a": "M90 Junction 1A",
    "J1": "M90 Junction 1",
    "J2": "M90 Junction 2",
    "J3": "M90 Junction 3 Halbeath"
}

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

grouped = defaultdict(list)
seen = set()

for record in root.findall(".//d2:situationRecord", ns):

    record_text = ET.tostring(record, encoding="unicode")

    if not any(term.lower() in record_text.lower() for term in FIFE_TERMS):
        continue

    description = "Traffic restriction"

    comment_node = record.find(
        ".//d2:generalPublicComment/d2:comment/d2:values/d2:value",
        ns
    )

    if comment_node is not None and comment_node.text:
        description = comment_node.text.strip()

    version_node = record.find(
        ".//d2:situationRecordVersionTime",
        ns
    )

    updated_time = ""

    if version_node is not None and version_node.text:
        try:
            dt = datetime.fromisoformat(
                version_node.text.replace("Z", "+00:00")
            )
            updated_time = dt.strftime("%H:%M")
        except Exception:
            pass

    lanes_node = record.find(
        ".//d2:numberOfLanesRestricted",
        ns
    )

    lanes = 0

    if lanes_node is not None and lanes_node.text:
        try:
            lanes = int(lanes_node.text)
        except Exception:
            lanes = 0

    locations = []

    # Existing location extraction
    for value in record.findall(
        ".//d2:name/d2:descriptor/d2:values/d2:value",
        ns
    ):
        if value.text:
            locations.append(value.text.strip())

    # Additional DATEX location extraction
    for value in record.findall(
        ".//d2:otherName/d2:descriptor/d2:values/d2:value",
        ns
    ):
        if value.text:
            locations.append(value.text.strip())

    title = "Fife Traffic Alert"

    # Ferrytoll
    for location in locations:
        if "Ferrytoll" in location:
            title = "M90 Ferrytoll"
            break

    # Scotstoun
    if title == "Fife Traffic Alert":
        for location in locations:
            if "Scotstoun" in location:
                title = "M90 Scotstoun"
                break

    # B800 underpass
    if title == "Fife Traffic Alert":
        for location in locations:
            if "B800" in location:
                title = "M90 B800 Underpass"
                break

    # Standard mappings
    if title == "Fife Traffic Alert":

        for location in locations:

            clean_location = location.split(" (")[0]

            if clean_location in LOCATION_MAP:
                title = LOCATION_MAP[clean_location]
                break

            if "(" in location:
                title = clean_location
                break

    # Final fallback
    if title == "Fife Traffic Alert" and locations:
        title = locations[0]

    direction = "General"

    description_lower = description.lower()

    if "southbound" in description_lower:
        direction = "Southbound"
    elif "northbound" in description_lower:
        direction = "Northbound"
    elif "eastbound" in description_lower:
        direction = "Eastbound"
    elif "westbound" in description_lower:
        direction = "Westbound"

    group_key = f"{title} ({direction})"

    dedupe_key = (group_key, description)

    if dedupe_key in seen:
        continue

    seen.add(dedupe_key)

    grouped[group_key].append({
        "description": description,
        "lanes": lanes,
        "updated": updated_time
    })

rss_items = ""

if not grouped:

    rss_items = """
<item>
<title>No major incidents reported</title>
<description>No significant delays currently reported on key Fife routes.</description>
<guid>fallback</guid>
</item>
"""

else:

    counter = 1

    for location, incidents in grouped.items():

        max_lanes = max(
            incident["lanes"]
            for incident in incidents
        )

        if max_lanes >= 3:
            severity = "🔴 Major traffic restrictions"
        elif max_lanes >= 2:
            severity = "🟠 Traffic restrictions"
        elif max_lanes == 1:
            severity = "🟢 Minor traffic restriction"
        else:
            severity = "🟠 Traffic restriction"

        descriptions = []
        latest_update = ""

        for incident in incidents:

            descriptions.append(
                f"• {incident['description']}"
            )

            if incident["updated"]:
                latest_update = incident["updated"]

        full_description = severity + "\n\n"
        full_description += "\n".join(descriptions)

        if latest_update:
            full_description += f"\n\nUpdated: {latest_update}"

        rss_items += f"""
<item>
<title>{location}</title>
<description><![CDATA[{full_description}]]></description>
<guid>{counter}</guid>
</item>
"""

        counter += 1

rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>

<title>K107FM Fife Travel Alerts</title>
<link>https://k107fm.github.io/k107fm-travel-feed/</link>
<description>Live Traffic Scotland updates for Fife</description>

{rss_items}

</channel>
</rss>
"""

with open("fife-travel.xml", "w", encoding="utf-8") as f:
    f.write(rss)

print("RSS updated")
print("Locations found:", len(grouped))

print("\nGenerated groups:")

for group_name in grouped.keys():
    print(" -", group_name)
