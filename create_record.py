import json
import os
import logging
import requests
import errno
import configparser
from dotenv import load_dotenv
from datetime import date


def generate_metadata(file_path):
    """
    Generates a record's metadata from a file
    """
    full_record_metadata = {
            "access": {
                "files": "public",
                "record": "public",
                "status": "open"
            },
            "files": {
                "enabled": True
            }
    }

    with open(file_path, 'r') as f:
        metadata = json.load(f)

    full_record_metadata['metadata'] = metadata
    return full_record_metadata


def create_draft(url, token, metadata):
    """
    Creates a draft on the archive from provided metadata
    Raises an HTTPError exception if the request to create the draft failed
    Returns the id of the newly created draft
    """
    payload = json.dumps(metadata)

    request_headers = {
        "Accept": "application/json",
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.post(
        f'{url}/api/records',
        data=payload,
        headers=request_headers,
        verify=True)

    response.raise_for_status()

    record_url = response.json()['links']['record']
    record_id = record_url.split('/api/records/')[-1]
    return record_id


def get_data_files(input_folder_path, metadata_file):
    """
    Returns the filenames in the input folder, ignoring
    - the metadata file
    - any filename containing "metadata"
    """
    all_files = [f for f in os.listdir(input_folder_path) if os.path.isfile(os.path.join(input_folder_path, f))]
    data_files = [f for f in all_files if (f != metadata_file) and ("metadata" not in f)]
    return data_files


def start_file_uploads(url, token, record_id, data_files):
    """
    Updates a record's metadata by specifying the files that should be linked to it
    Raises an HTTPError exception if the request to update the record failed
    """
    # Create the payload specifying the files to be attached to the record
    filename_vs_key = []

    for data_file in data_files:
        filename_vs_key.append({'key': data_file})

    payload = json.dumps(filename_vs_key)

    request_headers = {
        "Accept": "application/json",
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.post(
        f'{url}/api/records/{record_id}/draft/files',
        data=payload,
        headers=request_headers,
        verify=True)

    response.raise_for_status()


def upload_file_content(url, token, record_id, data_file_path, data_file):
    """
    Uploads a file's content
    Raises an HTTPError exception if the request to upload the file's content failed
    """
    request_headers = {
        "Accept": "application/json",
        "Content-type": "application/octet-stream",
        "Authorization": f"Bearer {token}"
    }

    with open(data_file_path, 'rb') as f:
        response = requests.put(
            f'{url}/api/records/{record_id}/draft/files/{data_file}/content',
            data=f,
            headers=request_headers,
            verify=True
        )

    response.raise_for_status()


def complete_file_upload(url, token, record_id, data_file):
    """
    Completes the upload of a file's content
    Raises an HTTPError exception if the request to complete the upload of the file's content failed
    """
    request_headers = {
        "Accept": "application/json",
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.post(
        f'{url}/api/records/{record_id}/draft/files/{data_file}/commit',
        headers=request_headers,
        verify=True)

    response.raise_for_status()


def insert_publication_date(url, token, record_id):
    """
    Inserts a publication date into a record's metadata
    """
    metadata = get_draft_metadata(url, token, record_id)
    metadata['metadata']['publication_date'] = date.today().strftime('%Y-%m-%d')  # e.g., '2020-06-01'
    update_draft_metadata(url, token, record_id, metadata)


def get_draft_metadata(url, token, record_id):
    """
    Gets a draft's metadata
    Raises an HTTPError exception if the request to get the record's metadata failed
    """
    request_headers = {
        "Accept": "application/json",
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(
        f"{url}/api/records/{record_id}/draft",
        headers=request_headers,
        verify=True)

    response.raise_for_status()

    record_metadata = json.loads(response.text)
    return record_metadata


def update_draft_metadata(url, token, record_id, metadata):
    """
    Updates a draft's metadata
    Raises an HTTPError exception if the request to update the record's metadata failed
    """
    payload = json.dumps(metadata)

    request_headers = {
        "Accept": "application/json",
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    # Send PUT request
    response = requests.put(
        f'{url}/api/records/{record_id}/draft',
        data=payload,
        headers=request_headers,
        verify=True)

    response.raise_for_status()


def publish_draft(url, token, record_id):
    """
    Shares a draft with all archive users
    Raises an HTTPError exception if the request to share the draft failed
    """
    request_headers = {
        "Accept": "application/json",
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.post(
        f'{url}/api/records/{record_id}/draft/actions/publish',
        headers=request_headers,
        verify=True)

    response.raise_for_status()


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

    try:
        # Read configuration file named config.ini
        config = configparser.ConfigParser()
        basedir = os.path.abspath(os.path.dirname(__file__))
        config.read(os.path.join(basedir, 'config.ini'))

        # Create environment variables from secrets.env
        load_dotenv(os.path.join(basedir, 'secrets.env'))

        # Get selected archive
        selected_archive = config.get('general', 'selected_archive')

        if selected_archive == 'main':
            url = config.get('general', 'main_archive_url')
            token = os.getenv('MAIN_ARCHIVE_TOKEN')
        elif selected_archive == 'demo':
            url = config.get('general', 'demo_archive_url')
            token = os.getenv('DEMO_ARCHIVE_TOKEN')
        else:
            raise Exception('Invalid selected_archive in config.ini')

        # Create a draft
        input_folder = config.get('create_record', 'input_folder')
        input_folder_path = os.path.join(basedir, input_folder)
        metadata_file = config.get('create_record', 'metadata_file')
        metadata_file_path = os.path.join(input_folder_path, metadata_file)
        metadata = generate_metadata(metadata_file_path)
        id = create_draft(url, token, metadata)

        # Upload data files and insert links in the draft's metadata
        data_files = get_data_files(input_folder_path, metadata_file)
        start_file_uploads(url, token, id, data_files)

        for file in data_files:
            file_path = os.path.join(basedir, input_folder, file)
            upload_file_content(url, token, id, file_path, file)
            complete_file_upload(url, token, id, file)

        logger.info(f'Draft with id={id} created')

        # Publish draft depending on user's choice
        publish = config.get('create_record', 'publish')

        if publish == 'True':
            insert_publication_date(url, token, id)
            publish_draft(url, token, id)

            logger.info(f'Draft with id={id} published')

    except Exception as e:
        logger.error('Error occurred: ' + str(e))