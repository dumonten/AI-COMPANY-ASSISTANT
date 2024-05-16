import re
import uuid
from urllib.parse import urlparse

import requests

from utils import Strings


def generate_uuid():
    my_uuid = uuid.uuid4()
    uuid_str = str(my_uuid)
    return uuid_str


def check_url(url):
    url_pattern = re.compile(
        r"((http|https)://(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(/|/\w+)*(\?\S+)?)"
    )
    match = url_pattern.search(url)
    if not match:
        return False, Strings.NO_URL
    url = match.group(0).strip()
    parsed_url = urlparse(url)
    if not parsed_url.scheme or not parsed_url.netloc:
        return False, Strings.URL_INVALID
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        if response.status_code == 200:
            return True, url
        else:
            return False, Strings.URL_CONNECTION_ERROR
    except requests.RequestException:
        return False, Strings.URL_CONNECTION_ERROR


def validate_company_name(name):
    name = name.strip()
    if len(name) < 2 or len(name) > 100:
        return False, Strings.SHORT_NAME
    if not re.match(r"^[a-zA-Zа-яА-ЯёЁ0-9\s\-\'\"`«»]+$", name):
        return (False, Strings.BAD_NAME)
    return True, name
