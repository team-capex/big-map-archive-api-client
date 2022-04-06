import requests
import json
import os


def upload_record(url, record_path, record, request_headers ):
    (record_metadata_filename, record_data_filenames) = record

    # Get title, authors, list of attached files...
    with open(os.path.join(record_path, record_metadata_filename)) as f:
        record_metadata = json.load(f)

    # Create a record in the PostgreSQL database
    # Get the url for the record's attached files
    # e.g., 'https://dev1-big-map-archive.materialscloud.org/api/records/cpbc8-ss975/draft/files'
    data_files_url = create_record_in_database(url, record_metadata, request_headers)

    data_file_index = 0
    for filename in record_data_filenames:
        upload_data_file(record_path, filename, data_file_index, data_files_url, request_headers)
        data_file_index += 1


def create_record_in_database(url, record_metadata, request_headers):
    payload = json.dumps(record_metadata)

    # Set "verify=True" in production so that HTTPS requests verify SSL certificates
    response = requests.post(
        f"{url}/api/records",
        data=payload,
        headers=request_headers['json'],
        verify=False)

    # Raise an exception if the record could not be created
    if response.status_code != 201:
        raise AssertionError(f"Failed to create record (code: {response.status_code})")

    #  Get the files url for the record
    #  e.g., 'https://dev1-big-map-archive.materialscloud.org/api/records/h0zrf-17b65/draft/files'
    data_files_url = response.json()['links']['files']
    return data_files_url


def upload_data_file(record_path, filename, file_index, files_url, request_headers):
    (file_content_url, file_commit_url) = start_data_file_upload(filename, file_index, files_url, request_headers)
    upload_data_file_content(record_path, filename, request_headers, file_content_url)
    complete_data_file_upload(filename, request_headers, file_commit_url)


def start_data_file_upload(filename, file_index, files_url, request_headers):
    payload = json.dumps([{"key": filename}])

    response = requests.post(
        files_url,
        data=payload,
        headers=request_headers['json'],
        verify=False)

    # Raise an exception if the file could not be created
    if response.status_code != 201:
        raise AssertionError(f"Failed to create record (code: {response.status_code})")

    # Get the file content url and the file commit url
    # e.g., 'https://dev1-big-map-archive.materialscloud.org/api/records/eqcks-b1q35/draft/files/scientific_data.json/content'
    # e.g, 'https://dev1-big-map-archive.materialscloud.org/api/records/eqcks-b1q35/draft/files/scientific_data.json/commit'
    file_links = response.json()['entries'][file_index]['links']
    file_content_url = file_links['content']
    file_commit_url = file_links['commit']
    return (file_content_url, file_commit_url)


def upload_data_file_content(record_path, filename, request_headers, file_content_url):
    # Upload the file content by streaming the data
    with open(os.path.join(record_path, filename), 'rb') as f:
        response = requests.put(
            file_content_url,
            data=f,
            headers=request_headers['binary'],
            verify=False)

    # Raise an exception if the file content could not be uploaded
    if response.status_code != 200:
        raise AssertionError(f"Failed to upload file content {filename} (code: {response.status_code})")


def complete_data_file_upload(filename, request_headers, file_commit_url):
    response = requests.post(
        file_commit_url,
        headers=request_headers['json'],
        verify=False)

    # Raise an exception if the file content could not be uploaded
    if response.status_code != 200:
        raise AssertionError(f"Failed to complete file upload {filename} (code: {response.status_code})")


if __name__ == '__main__':
    url = "https://dev1-big-map-archive.materialscloud.org/"

    # Navigate to 'Applications' > 'Personal access tokens' to create a token if necessary
    token = "vHeuWbNDspNH0UGUMrmxzQTENpv6996H3GyeVFCOLVVcAudJZBkrMKRnJAWH"

    record_path = 'record'

    # Define a record that you want to upload:
    # ('<record metadata json>.json', ['<datafile1>', '<datafile2>'])
    record = (
        'record_metadata.json',
        ['scientific_data.json', 'a.md', 'b.png', 'c.pdf']
    )

    # HTTP Headers used during requests
    request_headers_json = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    request_headers_binary = {
        "Accept": "application/json",
        "Content-Type": "application/octet-stream",
        "Authorization": f"Bearer {token}"
    }

    request_headers = {
        "json": request_headers_json,
        "binary": request_headers_binary
    }

    try:
        upload_record(url, record_path, record, request_headers)
    except Exception as e:
        print("Oops!", e.__class__, "occurred.")
