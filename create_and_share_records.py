import json
import os
import logging
import requests


def prepare_output_file(records_path, filename):
    file_path = os.path.join(records_path, filename)

    if os.path.exists(file_path):
        os.remove(file_path)

    # Create a file for storing records' links
    with open(file_path, 'x') as f:
        json_formatted_text = json.dumps([])
        f.write(json_formatted_text)


def upload_record(url, record_path, record, record_index, token):
    (record_metadata_filename, record_data_filenames) = record

    # Get title, authors, list of attached files...
    with open(os.path.join(record_path, str(record_index), record_metadata_filename)) as f:
        record_metadata = json.load(f)

    # Create a record in the PostgreSQL database
    # Get the url for the record's attached files
    # e.g., '/api/records/cpbc8-ss975/draft/files'
    links = create_record_in_database(url, record_metadata, token)

    data_file_index = 0
    for filename in record_data_filenames:
        upload_data_file(record_path, filename, data_file_index, record_index, links, token)
        data_file_index += 1

    return links


def create_record_in_database(url, record_metadata, token):
    payload = json.dumps(record_metadata)

    request_headers = {
        "Accept": "application/json",
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    # Set "verify=True" in production so that HTTPS requests verify SSL certificates
    response = requests.post(
        f"{url}/api/records",
        data=payload,
        headers=request_headers,
        verify=True)

    # Raise an exception if the record could not be created
    if response.status_code != 201:
        raise ValueError(f"Failed to create record (code: {response.status_code})")

    #  Get urls for the record
    #  e.g., '/api/records/h0zrf-17b65/draft/files'
    links = response.json()['links']
    return links


def upload_data_file(record_path, filename, file_index, record_index, links, token):
    (file_content_url, file_commit_url) = start_data_file_upload(filename, file_index, links, token)
    upload_data_file_content(record_path, filename, record_index, file_content_url, token)
    complete_data_file_upload(filename, file_commit_url, token)


def start_data_file_upload(filename, file_index, links, token):
    files_url = links['files']
    payload = json.dumps([{"key": filename}])

    request_headers = {
        "Accept": "application/json",
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.post(
        files_url,
        data=payload,
        headers=request_headers,
        verify=True)

    # Raise an exception if the file could not be created
    if response.status_code != 201:
        raise ValueError(f"Failed to create record (code: {response.status_code})")

    # Get the file content url and the file commit url
    # e.g., '/api/records/eqcks-b1q35/draft/files/scientific_data.json/content'
    # e.g, '/api/records/eqcks-b1q35/draft/files/scientific_data.json/commit'
    file_links = response.json()['entries'][file_index]['links']
    file_content_url = file_links['content']
    file_commit_url = file_links['commit']
    return (file_content_url, file_commit_url)


def upload_data_file_content(record_path, filename, record_index, file_content_url, token):
    # Upload the file content by streaming the data
    with open(os.path.join(record_path, str(record_index), filename), 'rb') as f:
        request_headers = {
            "Accept": "application/json",
            "Content-type": "application/octet-stream",
            "Authorization": f"Bearer {token}"
        }

        response = requests.put(
            file_content_url,
            data=f,
            headers=request_headers,
            verify=True)

    # Raise an exception if the file content could not be uploaded
    if response.status_code != 200:
        raise ValueError(f"Failed to upload file content {filename} (code: {response.status_code})")


def complete_data_file_upload(filename, file_commit_url, token):
    request_headers = {
        "Accept": "application/json",
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.post(
        file_commit_url,
        headers=request_headers,
        verify=True)

    # Raise an exception if the file content could not be uploaded
    if response.status_code != 200:
        raise ValueError(f"Failed to complete file upload {filename} (code: {response.status_code})")


def publish_record(links, token):
    publish_url = links['publish']

    request_headers = {
        "Accept": "application/json",
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.post(
        publish_url,
        headers=request_headers,
        verify=True)

    # Raise an exception if the record could not be published
    if response.status_code != 202:
        raise ValueError(f"Failed to publish record (code: {response.status_code})")


def save_to_file(record_path, links_filename, links):
    filename = os.path.join(record_path, links_filename)

    with open(filename, "r") as f:
        data = json.load(f)

    data.append(links)

    with open(filename, "w") as f:
        json.dump(data, f)


if __name__ == '__main__':
    #url = "https://archive.big-map.eu/"
    url = "https://big-map-archive-demo.materialscloud.org/"

    # Navigate to 'Applications' > 'Personal access tokens' to create a token if necessary
    token = "<replace by a personal token>"

    records_path = 'records'
    links_filename = 'records_links.json'

    # Specify records that you want to upload:
    # ('<record metadata json>.json', ['<datafile1>', '<datafile2>'])
    records = [
        ('record_metadata.json', ['scientific_data.json']),
        ('record_metadata.json', ['scientific_data.json', 'dummy_data.md'])
    ]

    publish = True

    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

    try:
        prepare_output_file(records_path, links_filename)

        record_index = 0
        for record in records:
            logger.info('----------Start uploading record ' + str(record_index) + '----------')
            record_links = upload_record(url, records_path, record, record_index, token)

            if publish:
                # Publish the draft record
                publish_record(record_links, token)

            # Save the record's links to a file
            save_to_file(records_path, links_filename, record_links)

            record_index += 1
        logger.info('Uploading was successful. See the file records_links.json for links to the created records.')
    except Exception as e:
        logger.error('Error occurred: ' + str(e))
