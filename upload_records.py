import requests
import json
import os


def prepare_file_for_storing_records_links(records_path, links_filename):
    file_path = os.path.join(records_path, links_filename)

    if os.path.exists(file_path):
        os.remove(file_path)

    # Create a file for storing records' links
    with open(file_path, 'x') as f:
        json_formatted_text = json.dumps([])
        f.write(json_formatted_text)


def upload_record(url, record_path, record, record_index, request_headers ):
    (record_metadata_filename, record_data_filenames) = record

    # Get title, authors, list of attached files...
    print(os.path.join(record_path, str(record_index), record_metadata_filename))

    with open(os.path.join(record_path, str(record_index), record_metadata_filename)) as f:
        record_metadata = json.load(f)

    # Create a record in the PostgreSQL database
    # Get the url for the record's attached files
    # e.g., 'https://dev1-big-map-archive.materialscloud.org/api/records/cpbc8-ss975/draft/files'
    links = create_record_in_database(url, record_metadata, request_headers)

    data_file_index = 0
    for filename in record_data_filenames:
        upload_data_file(record_path, filename, data_file_index, record_index, links, request_headers)
        data_file_index += 1

    return links


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

    #  Get urls for the record
    #  e.g., 'https://dev1-big-map-archive.materialscloud.org/api/records/h0zrf-17b65/draft/files'
    links = response.json()['links']
    return links


def upload_data_file(record_path, filename, file_index, record_index, links, request_headers):
    (file_content_url, file_commit_url) = start_data_file_upload(filename, file_index, links, request_headers)
    upload_data_file_content(record_path, filename, record_index, request_headers, file_content_url)
    complete_data_file_upload(filename, request_headers, file_commit_url)


def start_data_file_upload(filename, file_index, links, request_headers):
    files_url = links['files']
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


def upload_data_file_content(record_path, filename, record_index, request_headers, file_content_url):
    # Upload the file content by streaming the data
    with open(os.path.join(record_path, str(record_index), filename), 'rb') as f:
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


def publish_record(links, request_headers):
    publish_url = links['publish']

    response = requests.post(
        publish_url,
        headers=request_headers['json'],
        verify=False)

    # Raise an exception if the record could not be published
    if response.status_code != 202:
        raise AssertionError(f"Failed to publish record (code: {response.status_code})")


def save_to_file(record_path, links_filename, links):
    filename = os.path.join(record_path, links_filename)

    with open(filename, "r") as f:
        data = json.load(f)

    data.append(links)

    with open(filename, "w") as f:
        json.dump(data, f)


if __name__ == '__main__':
    url = "https://dev1-big-map-archive.materialscloud.org/"

    # Navigate to 'Applications' > 'Personal access tokens' to create a token if necessary
    token = "VNjlFbSi0NQ5PElPaZMA6mNr5sPvgTh7cVOGqQqRvqt43L2hECu9rHEsrEDr"

    records_path = 'records'
    links_filename = 'records_links.json'

    # Specify records that you want to upload:
    # ('<record metadata json>.json', ['<datafile1>', '<datafile2>'])
    records = [
        ('record_metadata.json', ['scientific_data.json']),
        ('record_metadata.json', ['scientific_data.json', 'a.md']),
        ('record_metadata.json', ['scientific_data.json', 'b.png', 'c.pdf'])
    ]

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
        prepare_file_for_storing_records_links(records_path, links_filename)

        record_index = 0
        for record in records:
            record_links = upload_record(url, records_path, record, record_index, request_headers)

            # [Optional] Publish the draft record
            #publish_record(links, request_headers)

            # Save the record's links to a file
            save_to_file(records_path, links_filename, record_links)

            record_index += 1
    except Exception as e:
        print("Oops!", e.__class__, "occurred.")