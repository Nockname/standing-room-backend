import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from pytz import timezone


TKTS_URL = "https://www.tdf.org/discount-ticket-programs/tkts-by-tdf/tkts-live/?tab=TimesSquare"

# Booth container id → display name used in the "currently closed" sentence.
BOOTHS = [
    {"container_id": "tkts-shows-times-square", "name": "Times Square"},
    {"container_id": "tkts-shows-lincoln-center", "name": "Lincoln Center"},
]

# Board class suffix → (is_tomorrow, on_broadway). The site renders past shows
# in these same boards when a booth is closed, so we skip closed booths entirely.
BOARD_VARIANTS = {
    "tkts__board--broadway": (False, True),
    "tkts__board--off": (False, False),
    "tkts__board--tomorrow-broadway": (True, True),
    "tkts__board--tomorrow-off": (True, False),
}


def get_tkts_html():
    response = requests.get(TKTS_URL)
    response.raise_for_status()
    return response.text


def location_is_closed(location_name, html_content):
    # New phrasing as of the 2026 site redesign:
    # "The Lincoln Center booth is currently closed until Tuesday 11:00 AM."
    return f"The {location_name} booth is currently closed" in html_content


def _parse_price(raw):
    """Return (low, high) as strings, or (None, None) if no usable price."""
    price = raw.replace("---", "-").replace("--", "-").replace("$", "").strip()
    if not price:
        return None, None
    if "-" in price:
        low, high = price.split("-", 1)
        low, high = low.strip() or None, high.strip() or None
    else:
        low = high = price
    return low, high


def _parse_item(li, performance_date, on_broadway):
    title_el = li.find(class_="tkts__grid-list-item__title")
    percent_el = li.find(class_="tkts__grid-list-item__percent")
    discount_el = li.find(class_="tkts__grid-list-item__discount")
    time_el = li.find(class_="tkts__grid-list-item__time")

    if not (title_el and percent_el and discount_el and time_el):
        return None

    title = title_el.get_text(strip=True).replace('"', '')
    discount_percent = percent_el.get_text(strip=True).replace("%", "").strip()
    low_price, high_price = _parse_price(discount_el.get_text(strip=True))

    if low_price is None and high_price is None:
        return None

    time_text = time_el.get_text(strip=True)
    performance_time = datetime.strptime(time_text, "%I:%M %p").strftime("%H:%M:%S")

    is_matinee = True
    if "PM" in time_text:
        hour = int(time_text.split(":")[0])
        if hour >= 4:
            is_matinee = False

    return {
        "title": title,
        "discount_percent": discount_percent,
        "low_price": low_price,
        "high_price": high_price,
        "performance_time": performance_time,
        "is_matinee": is_matinee,
        "performance_date": performance_date,
        "on_broadway": on_broadway,
    }


def get_tkts_data():
    html_content = get_tkts_html()
    soup = BeautifulSoup(html_content, "html.parser")

    today = datetime.now(timezone("US/Eastern"))
    today_str = today.strftime("%Y-%m-%d")
    tomorrow_str = (today + timedelta(days=1)).strftime("%Y-%m-%d")

    tkts_data = []

    for booth in BOOTHS:
        if location_is_closed(booth["name"], html_content):
            print(f"{booth['name']} booth is closed.")
            continue

        container = soup.find("div", id=booth["container_id"])
        if not container:
            print(f"No container found for {booth['name']} ({booth['container_id']}).")
            continue

        for board in container.find_all("div", class_="tkts__board"):
            board_classes = set(board.get("class", []))
            variant = next((BOARD_VARIANTS[c] for c in board_classes if c in BOARD_VARIANTS), None)
            if variant is None:
                continue
            is_tomorrow, on_broadway = variant
            performance_date = tomorrow_str if is_tomorrow else today_str

            for li in board.find_all("li", class_="tkts__grid-list-item"):
                record = _parse_item(li, performance_date, on_broadway)
                if record:
                    tkts_data.append(record)

    return tkts_data


if __name__ == "__main__":
    from pprint import pprint
    pprint(get_tkts_data())
