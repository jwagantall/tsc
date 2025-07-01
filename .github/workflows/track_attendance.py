import os
import re
import csv
import math
from datetime import datetime
from collections import defaultdict

# Constants
TSC_MEMBERS = [
    "Hendrik Ebbers", "Richard Bair", "Leemon Baird", "Stoyan Panayotov",
    "George Spasov", "Alexander Popowycz", "Michael Kantor", "Milan Wiercx van Rhijn"
]
QUORUM_THRESHOLD = math.ceil(2 / 3 * len(TSC_MEMBERS))
MINUTES_DIR = "minutes"
OUTPUT_CSV = "tsc_attendance_tracker.csv"

# Track attendance state
absence_streak = defaultdict(int)
attendance_streak = defaultdict(int)
status = defaultdict(str)

# Results
output_rows = []

def extract_attendees(text):
    match = re.search(r"TSC Attendees\s*[:\-]?\s*(.*?)(?:\n\n|\Z)", text, re.DOTALL | re.IGNORECASE)
    if not match:
        return []
    attendees_section = match.group(1)
    attendees = re.findall(r"-\s*(.*)", attendees_section)
    return [a.strip() for a in attendees if a.strip()]

def parse_minutes():
    files = sorted(os.listdir(MINUTES_DIR))
    for fname in files:
        if not fname.endswith(".md"):
            continue
        date_str = fname.replace(".md", "")
        try:
            meeting_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            continue

        with open(os.path.join(MINUTES_DIR, fname), "r", encoding="utf-8") as f:
            content = f.read()

        attendees = extract_attendees(content)
        absentees = [m for m in TSC_MEMBERS if m not in attendees]
        quorum = "✅" if len(attendees) >= QUORUM_THRESHOLD else "❌"

        row = {
            "Date": str(meeting_date),
            "Quorum": quorum,
            "Suspended": [],
            "Reinstated": []
        }

        for member in TSC_MEMBERS:
            present = member in attendees
            row[member] = "✅" if present else "❌"

            if present:
                attendance_streak[member] += 1
                absence_streak[member] = 0
            else:
                absence_streak[member] += 1
                attendance_streak[member] = 0

            if absence_streak[member] >= 3 and status[member] != "Suspended":
                status[member] = "Suspended"
                row["Suspended"].append(member)

            if status[member] == "Suspended" and attendance_streak[member] >= 2:
                status[member] = "Reinstated"
                row["Reinstated"].append(member)

        row["Suspended"] = ", ".join(row["Suspended"])
        row["Reinstated"] = ", ".join(row["Reinstated"])
        output_rows.append(row)

def write_csv():
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["Date", "Quorum"] + TSC_MEMBERS + ["Suspended", "Reinstated"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in output_rows:
            writer.writerow(row)

def write_markdown():
    fieldnames = ["Date", "Quorum"] + TSC_MEMBERS + ["Suspended", "Reinstated"]
    print("| " + " | ".join(fieldnames) + " |")
    print("|" + "|".join(["---"] * len(fieldnames)) + "|")
    for row in output_rows:
        print("| " + " | ".join(row.get(field, "") for field in fieldnames) + " |")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--markdown", action="store_true", help="Print markdown instead of CSV")
    args = parser.parse_args()

    parse_minutes()

    if args.markdown:
        write_markdown()
    else:
        write_csv()
        print(f"✅ Attendance tracker written to {OUTPUT_CSV}")
