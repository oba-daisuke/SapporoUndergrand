import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import re

TARGETS = [
    {
        "station": "麻生",
        "url": "https://www.city.sapporo.jp/st/subway/route_time/h26/n01.html",
        "csv_files": {
            "真駒内方面": "timetables/南北線_麻生_真駒内方面.csv"
        }
    },
    {
        "station": "さっぽろ",
        "url": "https://www.city.sapporo.jp/st/subway/route_time/h26/n06.html",
        "csv_files": {
            "麻生方面": "timetables/南北線_さっぽろ_麻生方面.csv"
        }
    },
    {
        "station": "大通",
        "url": "https://www.city.sapporo.jp/st/subway/route_time/h26/n07.html",
        "csv_files": {
            "麻生方面": "timetables/南北線_大通_麻生方面.csv"
        }
    },
    {
        "station": "すすきの",
        "url": "https://www.city.sapporo.jp/st/subway/route_time/h26/n08.html",
        "csv_files": {
            "麻生方面": "timetables/南北線_すすきの_麻生方面.csv"
        }
    }
]

def fetch_and_parse(url):
    print(f"Fetching {url}...")
    try:
        response = requests.get(url)
        response.encoding = response.apparent_encoding
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching URL: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    return soup

def extract_times_from_text_block(soup, direction_key, day_key):
    """
    Extract times assuming standard Sapporo City layout:
    - Direction Header (H2)
    - Day Type Header (H3/H4 containing "平日" or "土")
    - Text block with one line per hour, starting at 6am.
    """
    
    times = set()
    
    # 1. Find Direction Header
    h2s = soup.find_all("h2")
    target_h2 = None
    for h2 in h2s:
        if direction_key in h2.get_text():
            target_h2 = h2
            break
            
    if not target_h2:
        print(f"  [WARN] Header for {direction_key} not found.")
        return times
        
    # 2. Find Day Type Section after Direction Header
    curr = target_h2.next_sibling
    in_target_section = False
    
    target_day_text = "平日" if day_key == "weekday" else "土"
    
    collected_lines = []
    
    while curr:
        if curr.name == "h2":
            # Reached next direction
            break
            
        if curr.name in ["h3", "h4"]:
            text = curr.get_text(strip=True)
            if target_day_text in text:
                in_target_section = True
                curr = curr.next_sibling
                continue
            else:
                if in_target_section:
                    # We were in target, now hit another header -> end
                    break
                    
        if in_target_section:
             # Identify content
            text = ""
            if isinstance(curr, str):
                text = curr
            elif curr.name not in ["h3", "h4"]: # content element
                text = curr.get_text(separator="\n")
            
            if text.strip():
                # Split and collect
                raw_lines = text.splitlines()
                for line in raw_lines:
                    # Basic cleanup
                    l = line.strip()
                    # Filter out garbage or urls
                    if l and (any(c.isdigit() for c in l)) and "http" not in l:
                         collected_lines.append(l)
                         
        curr = curr.next_sibling
        
    # 3. Parse Lines
    # Expected: 6, 7, ..., 23, 0 (19 lines)
    # If lines count is distinctively different, warn.
    
    # Debug
    # print(f"DEBUG {direction_key} {day_key}: Collected {len(collected_lines)} lines.")
    # for i, l in enumerate(collected_lines[:3]):
    #     print(f"  Line {i}: {l}")

    # Sometimes header lines or remarks sneak in.
    # Filter to lines that look like sequences of numbers.
    valid_lines = []
    for l in collected_lines:
        nums = re.findall(r"\d+", l)
        if nums:
            # Heuristic: If line has only 1 number, it's likely the hour header found in th/td
            # Sapporo subway has many trains per hour, 1 train is unlikely except maybe 0 or 23, but usually more.
            # 0 hour has 2 trains.
            if len(nums) == 1:
                continue
            valid_lines.append(nums)
            
    print(f"DEBUG {direction_key} {day_key}: Valid {len(valid_lines)} lines.")
    for i, vl in enumerate(valid_lines):
        print(f"  Valid Line {i} (Hour {6+i if 6+i < 24 else 6+i-24}): {vl}")
    
    # Logic: Start at 6.
    hour = 6
    processed_count = 0
    
    for nums in valid_lines:
        # Check if row seems valid (minutes)
        # Convert all to int
        mins = [int(x) for x in nums]
        
        # Heuristic: If first number is exactly the hour we expect, remove it (e.g. "6 12 24")
        # But only if it's < 24.
        if mins and mins[0] == hour:
            mins.pop(0)

        # Double check: if explicit hour header filtering missed something, and we have one number equals hour?
        # But we filtered len(nums)==1 above.
            
        # Add times
        for m in mins:
            if 0 <= m < 60:
                t_str = f"{hour:02d}:{m:02d}"
                times.add(t_str)
        
        # Advance hour
        if hour == 23:
            hour = 0
        elif hour == 0:
            hour = -1 # Stop
        else:
            hour += 1
        
        processed_count += 1
        if hour == -1:
            break
            
    return times

def verify_station(target):
    print(f"=== Verifying {target['station']} ===")
    soup = fetch_and_parse(target['url'])
    if not soup:
        return

    for direction, csv_path in target['csv_files'].items():
        print(f"Checking {direction}...")
        
        df = pd.read_csv(csv_path)
        
        dir_key = "麻生" if "麻生" in direction else "真駒内"
        
        for day_type in ["weekday", "weekend_holiday"]:
            web_times = extract_times_from_text_block(soup, dir_key, day_type)
            
            if not web_times:
                print(f"  [{day_type}] Skip (No web data extracted)")
                continue

            csv_times = set(df[df["day_type"] == day_type]["time"].tolist())
            
            missing_in_csv = web_times - csv_times
            extra_in_csv = csv_times - web_times
            
            if not missing_in_csv and not extra_in_csv:
                print(f"  [{day_type}] OK ({len(csv_times)} trains)")
            else:
                print(f"  [{day_type}] MISMATCH")
                print(f"    Web count: {len(web_times)}, CSV count: {len(csv_times)}")
                if missing_in_csv:
                    sample = sorted(list(missing_in_csv))[:5]
                    print(f"    Missing in CSV (Sample): {sample}")
                if extra_in_csv:
                    sample = sorted(list(extra_in_csv))[:5]
                    print(f"    Extra in CSV (Sample):   {sample}")

if __name__ == "__main__":
    for t in TARGETS:
        verify_station(t)
