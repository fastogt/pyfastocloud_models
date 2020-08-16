import os
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests


def date_to_utc_msec(date: datetime):
    date = date.replace(tzinfo=timezone.utc)
    seconds = date.timestamp()
    return int(seconds * 1000)


def remove_port_from_url(url: str) -> str:
    parsed_url = urlparse(url)
    if parsed_url:
        parsed_url = parsed_url._replace(netloc=parsed_url.hostname)
        return parsed_url.geturl()

    return url


def download_file(url: str, path: str, extension: str, timeout=1):
    get_response = requests.get(url, stream=True, timeout=timeout)
    parsed_url = urlparse(url)
    file_name = parsed_url.path.split('/')[-1]
    if not file_name:
        ts = datetime.now()
        # msec = int(ts.timestamp() * 1000)
        unique_filename = str(uuid.uuid4())
        file_name = '{0}{1}'.format(unique_filename, extension)
    full_path = os.path.join(path, file_name)
    with open(full_path, 'wb') as f:
        for chunk in get_response.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)

    return full_path, file_name


def is_valid_http_url(url: str, timeout=1) -> bool:
    if not url or len(url) == 0:
        return False

    try:
        response = requests.head(url, timeout=timeout)
        return response.status_code == 200
    except:
        return False


def is_valid_url(url):
    try:
        parsed_url = urlparse(url)
        return all([parsed_url.scheme])
    except TypeError as ex:
        return False


def get_country_code_by_remote_addr(remote_addr: str):
    url = 'http://ipinfo.io/' + remote_addr
    response = requests.get(url)
    data = response.json()
    return data.get('country', None)
