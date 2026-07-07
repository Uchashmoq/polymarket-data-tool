import re
import requests


def claw_wunderground(url, pattern):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
    }

    html = requests.get(url, headers=headers, timeout=15).text
    m = re.search(pattern, html)
    if m:
        temp = int(m.group(1))
        return temp
    else:
        raise RuntimeError("No data")


def wunderground_temperature(url: str) -> int:
    pattern = (
        r'<span\b(?=[^>]*class="[^"]*\bwu-unit-temperature\b[^"]*")[^>]*>'
        r"[\s\S]*?"
        r'<span\b(?=[^>]*class="[^"]*\bwu-value\b[^"]*\bwu-value-to\b[^"]*")[^>]*>'
        r"\s*(-?\d+)\s*</span>"
    )
    return claw_wunderground(url, pattern)


def wunderground_tomorrow_high(url: str) -> int:
    pattern = (
        r'<span\b[^>]*class="[^"]*\bday\b[^"]*"[^>]*>\s*Tomorrow\s*</span>'
        r"[\s\S]*?"
        r'<span\b[^>]*class="[^"]*\bwu-value\b[^"]*\bwu-value-to\b[^"]*"[^>]*>'
        r"\s*(-?\d+)\s*</span>\s*&nbsp;"
    )

    return claw_wunderground(url, pattern)


if __name__ == "__main__":
    url = "https://www.wunderground.com/weather/cn/chongqing/ZUCK"
    # url = "https://www.wunderground.com/weather/kr/incheon/RKSI"
    t1 = wunderground_temperature(url)
    t2 = wunderground_tomorrow_high(url)
    print(f"{url}\nNow: {t1} F\nTomorrow: {t2}F")
