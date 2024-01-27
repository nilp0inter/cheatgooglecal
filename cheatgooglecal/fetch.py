import requests
from io import BytesIO

from . import GOOGLE_EXPORT_HEADERS, GOOGLE_EXPORT_URL


def fetch(cookies):
    r = requests.get(GOOGLE_EXPORT_URL, cookies=cookies, allow_redirects=True, headers=GOOGLE_EXPORT_HEADERS)
    r.raise_for_status()
    return BytesIO(r.content)
