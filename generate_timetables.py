import pandas as pd
from datetime import datetime, timedelta
import os

TIMETABLE_DIR = "timetables"
os.makedirs(TIMETABLE_DIR, exist_ok=True)

# Odori Data (Source: Search Step 40)
# Structure: { direction: { day_type: { hour: [mins...] } } }
# Directions: "Makomanai" (South), "Asabu" (North)
# Day types: "weekday", "weekend_holiday"

# NOTE: Exceptions (Jieitai-mae) are marked in remarks logic later.
# List valid lists.
odori_data = {
    "真駒内方面": {
        "weekday": {
            6: [11, 21, 31, 41, 50, 59],
            7: [8, 17, 25, 32, 36, 40, 44, 48, 52, 56],
            8: [1, 5, 9, 13, 18, 22, 26, 30, 34, 38, 42, 47, 51, 55, 59], # 59 is J
            9: [3, 7, 11, 16, 20, 24, 28, 32, 36, 40, 44, 48, 53], # 11, 20, 36, 44 are J
            10: [0, 7, 14, 21, 28, 35, 42, 49, 56],
            11: [3, 10, 17, 24, 31, 38, 45, 52, 59],
            12: [6, 13, 20, 27, 34, 41, 48, 55],
            13: [2, 9, 16, 23, 30, 37, 44, 51, 58],
            14: [5, 12, 19, 26, 33, 40, 47, 54],
            15: [1, 8, 15, 22, 29, 36, 43, 50, 57],
            16: [4, 12, 19, 26, 33, 40, 46, 51, 56],
            17: [1, 6, 11, 17, 22, 27, 32, 37, 42, 47, 53, 58],
            18: [3, 8, 13, 18, 24, 29, 34, 39, 44, 49, 54, 59],
            19: [4, 10, 15, 20, 25, 31, 36, 41, 47, 52, 57],
            20: [4, 13, 21, 29, 37, 45, 53],
            21: [1, 9, 17, 25, 33, 41, 49, 57],
            22: [5, 13, 21, 29, 38, 46, 54],
            23: [2, 10, 19, 28, 37, 46, 54],
            0: [2, 11]
        },
        "weekend_holiday": {
            6: [11, 21, 31, 41, 51],
            7: [0, 8, 16, 23, 27, 31, 37, 44, 50, 56],
            8: [2, 8, 14, 20, 26, 32, 38, 43, 49, 55],
            9: [1, 7, 14, 21, 26, 32, 39, 46, 53],
            10: [0, 7, 14, 21, 28, 35, 42, 49, 56],
            11: [3, 10, 17, 24, 31, 38, 45, 52, 59],
            12: [6, 13, 20, 27, 34, 41, 48, 55],
            13: [2, 9, 16, 23, 30, 37, 44, 51, 58],
            14: [5, 12, 19, 26, 33, 40, 47, 54],
            15: [1, 8, 15, 22, 29, 36, 43, 50, 57],
            16: [4, 11, 18, 25, 32, 39, 46, 53],
            17: [0, 7, 14, 21, 28, 35, 42, 49, 56],
            18: [3, 10, 17, 24, 31, 38, 45, 52, 59],
            19: [6, 13, 20, 27, 34, 41, 48, 55],
            20: [2, 10, 18, 26, 34, 42, 50, 58],
            21: [6, 14, 22, 30, 38, 46, 54],
            22: [2, 10, 18, 26, 35, 43, 51, 59],
            23: [7, 16, 25, 34, 43, 52],
            0: [0, 9]
        }
    },
    "麻生方面": {
        "weekday": {
            6: [16, 26, 36, 46, 54],
            7: [1, 7, 14, 20, 26, 31, 36, 40, 44, 48, 52, 56],
            8: [0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56],
            9: [0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56],
            10: [0, 7, 14, 21, 28, 35, 42, 49, 56],
            11: [3, 10, 17, 24, 31, 38, 45, 52, 59],
            12: [6, 13, 20, 27, 34, 41, 48, 55],
            13: [2, 9, 16, 23, 30, 37, 44, 51, 58],
            14: [5, 12, 19, 26, 33, 40, 47, 54],
            15: [1, 8, 15, 22, 29, 36, 43, 50, 57],
            16: [4, 11, 18, 25, 32, 39, 46, 53],
            17: [0, 7, 14, 21, 28, 35, 42, 49, 56],
            18: [3, 10, 17, 24, 31, 38, 45, 52, 59],
            19: [6, 13, 20, 27, 34, 41, 48, 55],
            20: [2, 10, 18, 26, 34, 42, 50, 58],
            21: [6, 14, 22, 30, 38, 46, 54],
            22: [2, 10, 18, 26, 35, 43, 51, 59],
            23: [7, 16, 25, 34, 43, 52],
            0: [0, 9]
        },
        "weekend_holiday": {
            6: [16, 26, 36, 46, 54],
            7: [1, 7, 14, 20, 26, 31, 36, 40, 44, 48, 52, 56],
            8: [0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56],
            9: [0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56],
            10: [0, 7, 14, 21, 28, 35, 42, 49, 56],
            11: [3, 10, 17, 24, 31, 38, 45, 52, 59],
            12: [6, 13, 20, 27, 34, 41, 48, 55],
            13: [2, 9, 16, 23, 30, 37, 44, 51, 58],
            14: [5, 12, 19, 26, 33, 40, 47, 54],
            15: [1, 8, 15, 22, 29, 36, 43, 50, 57],
            16: [4, 11, 18, 25, 32, 39, 46, 53],
            17: [0, 7, 14, 21, 28, 35, 42, 49, 56],
            18: [3, 10, 17, 24, 31, 38, 45, 52, 59],
            19: [6, 13, 20, 27, 34, 41, 48, 55],
            20: [2, 10, 18, 26, 34, 42, 50, 58],
            21: [6, 14, 22, 30, 38, 46, 54],
            22: [2, 10, 18, 26, 35, 43, 51, 59],
            23: [7, 16, 25, 34, 43, 52],
            0: [0, 9]
        }
    }
}

# Jieitai-mae exceptions for Odori Weekday Makomanai-bound
jieitai_mae_exceptions = {
    8: {59},
    9: {11, 20, 36, 44}
}
# Based on search result: "※1は自衛隊前行き"
# "8時...59※1"
# "9時...11※1, ... 20※1 ... 36※1 ... 44※1"

def get_destination(direction, hour, minute, is_weekday):
    if direction == "真駒内方面":
        if is_weekday and hour in jieitai_mae_exceptions and minute in jieitai_mae_exceptions[hour]:
            return "自衛隊前行き"
        return "真駒内行き"
    else:
        # Assuming all Asabu bound for now as no exceptions listed
        return "麻生行き"

def generate_csv(station, data_dict, offset_minutes=0):
    rows = []
    # Header: line,station,direction,day_type,time,dest,remark
    # offset_minutes: Add to time.
    
    for direction, day_map in data_dict.items():
        for day_type, hour_map in day_map.items():
            for h, mins in hour_map.items():
                for m in mins:
                    # Calculate new time with offset
                    # Using arbitrary date to handle rollover
                    base_dt = datetime(2024, 1, 1, h, m)
                    new_dt = base_dt + timedelta(minutes=offset_minutes)
                    
                    new_h = new_dt.hour
                    new_m = new_dt.minute
                    
                    # Formatting time string "HH:MM". 
                    # If it crosses midnight (e.g. 24:00, 25:00), we stick to 00:xx formats usually,
                    # but original CSV uses "00:00" for midnight. 
                    # app.py handles 0-4h as "next day" or "late night of curr day"?
                    # original CSV uses "00:09".
                    
                    time_str = f"{new_h:02d}:{new_m:02d}"
                    
                    dest = get_destination(direction, h, m, day_type == "weekday")
                    
                    # Remark currently empty except possibly for Jieitai-mae handling if we wanted to put it in remark
                    remark = ""
                    
                    rows.append({
                        "line": "南北線",
                        "station": station,
                        "direction": direction,
                        "day_type": day_type,
                        "time": time_str,
                        "dest": dest,
                        "remark": remark
                    })
    
    # Sort by day_type, then time
    # But time is string, so 00:00 comes before 06:00.
    # We should sort logically. 
    # Logic: 05:00 is start, 04:59 is end. 
    # Helper to sort time
    def time_sort_key(t_str):
        hh, mm = map(int, t_str.split(":"))
        if hh < 5:
            hh += 24
        return hh * 60 + mm

    df = pd.DataFrame(rows)
    # Sort
    df["sort_key"] = df["time"].apply(time_sort_key)
    # also sort day_type (weekday first)
    df = df.sort_values(["direction", "day_type", "sort_key"], ascending=[True, True, True])
    df = df.drop(columns=["sort_key"])
    
    # Write to files
    # One file per station/direction as per existing pattern
    for direc in ["麻生方面", "真駒内方面"]:
        subdir_df = df[df["direction"] == direc]
        filename = f"南北線_{station}_{direc}.csv"
        path = os.path.join(TIMETABLE_DIR, filename)
        subdir_df.to_csv(path, index=False)
        print(f"Generated {path}")

# Generate Odori
generate_csv("大通", odori_data, offset_minutes=0)

# Susukino Data (Source: sapporo.jp)
susukino_data = {
    "麻生方面": {
        "weekday": {
            6: [14, 24, 34, 44, 52, 59],
            7: [6, 12, 18, 23, 27, 31, 36, 40, 44, 48, 53, 57],
            8: [1, 5, 9, 13, 17, 22, 26, 30, 34, 38, 42, 46, 51, 55, 59],
            9: [3, 7, 11, 15, 19, 23, 28, 35, 41, 48, 56],
            10: [3, 11, 17, 24, 32, 39, 46, 53],
            11: [0, 7, 14, 21, 28, 35, 42, 49, 56],
            12: [3, 10, 17, 24, 31, 38, 45, 52, 59],
            13: [6, 13, 20, 27, 34, 41, 48, 55],
            14: [2, 9, 16, 23, 30, 37, 44, 51, 58],
            15: [5, 12, 19, 26, 33, 40, 47, 54],
            16: [1, 8, 15, 21, 26, 30, 35, 40, 46, 51, 57],
            17: [2, 7, 12, 17, 23, 28, 33, 38, 43, 48, 53, 59],
            18: [4, 9, 14, 19, 24, 30, 35, 40, 45, 50, 55],
            19: [0, 5, 10, 16, 21, 28, 32, 36, 43, 51, 59],
            20: [7, 15, 23, 31, 40, 48, 56],
            21: [4, 12, 20, 28, 36, 44, 52],
            22: [0, 8, 16, 24, 32, 41, 49, 58],
            23: [6, 13, 21, 29, 38, 47, 56],
            0: [5, 14]
        },
        "weekend_holiday": {
            6: [14, 24, 34, 44, 52, 59],
            7: [6, 13, 19, 25, 31, 37, 43, 49, 54, 59],
            8: [5, 11, 17, 23, 29, 35, 41, 47, 53],
            9: [0, 6, 14, 21, 28, 35, 42, 49, 57],
            10: [3, 10, 17, 24, 31, 38, 45, 52, 59],
            11: [6, 13, 20, 27, 34, 41, 48, 55],
            12: [2, 9, 16, 23, 30, 37, 44, 51, 58],
            13: [5, 12, 19, 26, 33, 40, 47, 54],
            14: [1, 8, 15, 22, 29, 36, 43, 50, 57],
            15: [4, 11, 18, 25, 32, 39, 46, 53],
            16: [0, 7, 14, 21, 28, 35, 42, 49, 56],
            17: [3, 10, 17, 24, 31, 38, 45, 52, 59],
            18: [6, 13, 20, 27, 34, 41, 48, 55],
            19: [2, 10, 18, 26, 30, 35, 43, 51],
            20: [0, 8, 16, 23, 32, 40, 48, 56],
            21: [4, 12, 20, 28, 36, 44, 52],
            22: [0, 8, 16, 24, 32, 41, 49, 58],
            23: [6, 13, 21, 29, 38, 47, 56],
            0: [5, 14]
        }
    }
}

# Generate Susukino
# Uses specific data for Asabu. Makomanai is ignored as per instructions.
generate_csv("すすきの", susukino_data, offset_minutes=0)
