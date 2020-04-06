import json
import os
import ssl
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse
from urllib.request import urlopen

import requests
from validate_email import validate_email


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


def is_valid_email(email: str, check_mx: bool) -> bool:
    dns_valid = validate_email(email, check_mx=check_mx)
    if not dns_valid:
        return False

    validate_url = 'https://open.kickbox.com/v1/disposable/' + email
    context = ssl._create_unverified_context()
    response = urlopen(validate_url, context=context)
    if response.status != 200:
        return False

    data = response.read()
    json_object = json.loads(data.decode('utf-8'))
    is_disposable = json_object['disposable']
    return not is_disposable


def get_country_code_by_remote_addr(remote_addr: str):
    url = 'http://ipinfo.io/' + remote_addr
    response = requests.get(url)
    data = response.json()
    return data.get('country', None)
