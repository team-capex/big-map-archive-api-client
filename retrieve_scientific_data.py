import json
import os
import logging
import requests


def get_records_links_from_file(records_path, links_filename):
    input_file_path = os.path.join(records_path, links_filename)

    if not os.path.exists(input_file_path):
        raise FileNotFoundError('The file records_links.json could not be found')

    with open(input_file_path, 'r') as f:
        records_links = json.load(f)

    if len(records_links) == 0:
        raise ValueError('No links in records_links.json')

    return records_links


def get_records_scientific_data(records_links, token):
    records_scientific_data = []

    for record_links in records_links:
        data = get_content_of_record_scientific_data_files(record_links, token)
        records_scientific_data.append(data)

    # Flatten list of lists
    records_scientific_data = [item for sublist in records_scientific_data for item in sublist]

    return records_scientific_data


def get_content_of_record_scientific_data_files(record_links, token):
    data_files = get_record_data_files(record_links, token)

    scientific_data = []
    # Collect the content of 'scientific-data.json' files
    for file in data_files:
        if file['key'] == 'scientific_data.json':
            file_content = get_content_of_data_file(file, token)
            scientific_data.append(file_content)

    return scientific_data


def get_record_data_files(record_links, token):
    data_files_url = record_links['files']

    request_headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(
        data_files_url,
        headers=request_headers,
        verify=False)

    if response.status_code != 200:
        raise ValueError(f"Failed to find the list of files for the record (code: {response.status_code})")

    data_files = response.json()['entries']
    return data_files


def get_content_of_data_file(file, token):
    file_content_url = file['links']['content']

    request_headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }

    # Get the link to the file at CSCS
    response = requests.get(
        file_content_url,
        headers=request_headers,
        verify=False)

    if response.status_code != 200:
        raise ValueError(
            f"Failed to get the file's link {file_content_url} (code: {response.status_code})")

    request_headers = {
        "Accept": "application/octet-stream",
        "Content-type": "text/plain",
        "Authorization": f"Bearer {token}"
    }

    # Download the content of the file
    response = requests.get(
        response.text,
        headers=request_headers,
        verify=False)

    if response.status_code != 200:
        raise ValueError(
            f"Failed to download the content of the file {file_content_url} (code: {response.status_code})")

    # Decode a bytes into a str
    content = response.content.decode('utf-8')
    # Create a json from a str
    file_content = json.loads(content)
    return file_content


def save_to_file(records_path, filename, records_scientific_data):
    file_path = os.path.join(records_path, filename)

    if os.path.exists(file_path):
        os.remove(file_path)

    with open(file_path, 'x', encoding='utf-8') as f:
        json.dump(records_scientific_data, f, ensure_ascii=False)


if __name__ == '__main__':
    url = "https://dev1-big-map-archive.materialscloud.org/"

    # Navigate to 'Applications' > 'Personal access tokens' to create a token if necessary
    token = "<replace by a personal token>"

    records_path = 'records'
    links_filename = 'records_links.json'
    records_scientific_data_filename = 'records_scientific_data.json'

    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

    try:
        records_links = get_records_links_from_file(records_path, links_filename)
        records_scientific_data = get_records_scientific_data(records_links, token)
        save_to_file(records_path, records_scientific_data_filename, records_scientific_data)
    except Exception as e:
        logger.error("Error occurred: " + str(e))
