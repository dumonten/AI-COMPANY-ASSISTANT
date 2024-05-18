import re
import uuid
from urllib.parse import urlparse

from utils import Strings


def generate_uuid():
    """
    Generates a unique identifier (UUID) and returns it as a string.

    Returns:
    str: A UUID string.
    """
    my_uuid = uuid.uuid4()
    uuid_str = str(my_uuid)
    return uuid_str


def check_url(url):
    """
    Validates a given URL against a regular expression pattern and checks its components.

    Parameters:
    - url (str): The URL to validate.

    Returns:
    Tuple[bool, str]: A tuple containing a boolean indicating validity and a message describing the validation result.
    """
    # Checks if the URL is None
    if url is None:
        return False, Strings.NO_URL_MSG

    # Compiles a regular expression pattern for URL validation
    url_pattern = re.compile(
        r"((http|https)://(\w+:{0,1}\w*@)?(\S+)(:[0-9]+)?(/|/\w+)*(\?\S+)?)"
    )

    # Searches the URL against the compiled pattern
    match = url_pattern.search(url)

    # If no match found, indicates an invalid URL format
    if not match:
        return False, Strings.NO_URL_MSG

    # Extracts the matched URL and strips leading/trailing whitespace
    url = match.group(0).strip()

    # Parses the URL into components
    parsed_url = urlparse(url)

    # Checks if the URL has a scheme and netloc (domain part), indicating a valid URL structure
    if not parsed_url.scheme or not parsed_url.netloc:
        return False, Strings.URL_INVALID_MSG

    # If all checks pass, indicates a valid URL
    return True, url


def validate_company_name(name):
    """
    Validates a company name according to specific criteria, including length and character restrictions.

    Parameters:
    - name (str): The company name to validate.

    Returns:
    Tuple[bool, str]: A tuple containing a boolean indicating validity and a message describing the validation result.
    """
    # Strips leading/trailing whitespace from the name
    name = name.strip()

    # Checks if the name length is within acceptable bounds
    if len(name) < 2 or len(name) > 100:
        return False, Strings.SHORT_NAME_MSG

    # Uses a regular expression to ensure the name contains only allowed characters
    if not re.match(r"^[a-zA-Zа-яА-ЯёЁ0-9\s\-\'\"`«»]+$", name):
        return False, Strings.BAD_NAME_MSG

    # If all checks pass, indicates a valid company name
    return True, name
