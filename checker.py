import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

URL = "https://halifaxregionalmunicipality.perfectmind.com/36011/Clients/BookMe4BookingPagesV2/ClassesV2"

# Add more sports here anytime
SPORTS = {
    "Badminton": "fee5a20c-f5c3-466d-9c83-e15fb01f2a50",
    "Pickleball": "3dd563f5-8b1e-4afc-aee3-cd7b9ee9ebdb"
}


def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        print(message)
        return

    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=30
    )


def get_dates():
    today = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    future = today + timedelta(days=5)

    return (
        today.isoformat().replace("+00:00", ".000Z"),
        future.isoformat().replace("+00:00", ".000Z")
    )


def fetch_classes(calendar_id):
    start_date, end_date = get_dates()

    cookies = {
        "ClusterId": "default",
        "perfectmindmobilefeature": "0"
    }

    data = {
        "calendarId": calendar_id,
        "widgetId": "d177de04-d238-4ab9-ab96-c7e183be7ed0",
        "values[1][Name]": "Canada Games Centre",
        "values[1][Value]": "2c3ada6c-1642-45a2-b168-36df96188aee",
        "values[2][Name]": "Date Range",
        "values[2][Value]": start_date,
        "values[2][Value2]": end_date,
        "values[2][ValueKind]": 6,
        "values[3][ValueKind]": 7,
        "values[0][ValueKind]": 9
    }

    r = requests.post(URL, cookies=cookies, data=data, timeout=60)
    r.raise_for_status()
    return r.json()


def get_available(classes):
    available = []

    for c in classes:
        spots = str(c.get("Spots", "")).strip()

        if spots.lower() == "full":
            continue

        available.append({
            "name": c.get("EventName"),
            "date": c.get("FormattedStartDate"),
            "time": c.get("EventTimeDescription"),
            "facility": c.get("Facility"),
            "spots": spots if spots else "Available"
        })

    return available


def main():
    all_results = []

    for sport_name, calendar_id in SPORTS.items():
        try:
            data = fetch_classes(calendar_id)
            classes = data.get("classes", [])
            available = get_available(classes)

            if available:
                all_results.append((sport_name, available))

        except Exception as e:
            print(f"{sport_name} failed: {e}")

    if not all_results:
        print("No spots available.")
        return

    msg = "🏟 Canada Games Centre Spots Available!\n\n"

    for sport, items in all_results:
        msg += f"=== {sport} ===\n"

        for item in items[:8]:
            msg += (
                f"{item['name']}\n"
                f"{item['date']}\n"
                f"{item['time']}\n"
                f"{item['facility']}\n"
                f"Status: {item['spots']}\n\n"
            )

    send_telegram(msg)
    print("Alert sent.")


if __name__ == "__main__":
    main()