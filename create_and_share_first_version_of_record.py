import json
import os
import logging
import requests
import errno


def check_input_files_exist(record_metadata_file_path, data_files_paths):
    """
    Raises an exception if a file specified by an argument is missing from the input folder
    """
    if not os.path.isfile(record_metadata_file_path):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), record_metadata_file_path)

    for p in data_files_paths:
        if not os.path.isfile(p):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), p)

def create_draft_record(url, token, record_metadata_file_path):
    """
    Creates a record, which remains private to its owner, from a file
    Raises an exception if the record could not be created
    """
    # Create the payload from the record's metadata file (title, authors...)
    with open(record_metadata_file_path, 'r') as f:
        record_metadata = json.load(f)

    payload = json.dumps(record_metadata)

    request_headers = {
        "Accept": "application/json",
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    # Send POST request
    # with "verify=True" in production so that HTTPS requests verify SSL certificates
    response = requests.post(
        f'{url}/api/records',
        data=payload,
        headers=request_headers,
        verify=True)

    # Raise an exception if the record could not be created
    if response.status_code != 201:
        raise ValueError(f"Failed to create record (code: {response.status_code})")

    #  Get record's id
    record_url = response.json()['links']['record']
    record_id = record_url.split('/api/records/')[-1]
    return record_id

def start_file_uploads(url, token, record_id, data_files):
    """
    Updates a record's metadata by specifying the files that should be attached to it
    Raises an exception if the record's metadata could not be updated
    """
    # Create the payload specifying the files to be attached to the record
    filename_vs_key = []
    for f in data_files:
        filename_vs_key.append({'key': f})

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

    # Raise an exception if the record could not be updated
    if response.status_code != 201:
        raise ValueError(f"Failed to update the record (code: {response.status_code})")

def upload_file_content(url, token, record_id, basedir, input_folder, filename):
    """
    Uploads a file's content
    Raise an exception if the file's content could not be uploaded
    """
    request_headers = {
        "Accept": "application/json",
        "Content-type": "application/octet-stream",
        "Authorization": f"Bearer {token}"
    }

    with open(os.path.join(basedir, input_folder, filename), 'rb') as f:
        response = requests.put(
            f'{url}/api/records/{record_id}/draft/files/{filename}/content',
            data=f,
            headers=request_headers,
            verify=True
        )

    # Raise an exception if the file's content could not be uploaded
    if response.status_code != 200:
        raise ValueError(f"Upload of {filename}'s content failed (code: {response.status_code})")


def complete_file_upload(url, token, record_id, filename):
    """
    Completes the upload of a file's content
    Raises an exception if the upload of the file's content could not be completed
    """
    request_headers = {
        "Accept": "application/json",
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.post(
        f'{url}/api/records/{record_id}/draft/files/{filename}/commit',
        headers=request_headers,
        verify=True)

    # Raise an exception if the upload of the file's content could not be completed
    if response.status_code != 200:
        raise ValueError(f"Completing the upload of {filename}'s content failed (code: {response.status_code})")

def publish_draft_record(url, token, record_id):
    """
    Shares a draft with all users of the archive
    Raises an exception if the draft could not be shared
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

    # Raise an exception if the draft could not be shared
    if response.status_code != 202:
        raise ValueError(f"Failed to publish record (code: {response.status_code})")

if __name__ == '__main__':
    # Select an archive
    #url = 'https://archive.big-map.eu/'
    url = 'https://big-map-archive-demo.materialscloud.org/'

    # Navigate to 'Applications' > 'Personal access tokens' to create a token if necessary
    token = '<replace by a personal token>'

    # Specify whether to share the record and its files with other users
    publish = True

    # Folder
    input_folder = 'input'

    # Input files
    record_metadata_file = 'record_metadata.json' # Contains the title, the list of authors...
    data_files = ['a.json', 'b.png', 'c.pdf'] # Files to attach to the record

    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

    try:
        # Determine files' absolute paths
        basedir = os.path.abspath(os.path.dirname(__file__))
        record_metadata_file_path = os.path.join(basedir, input_folder, record_metadata_file)
        data_files_paths = [os.path.join(basedir, input_folder, f) for f in data_files]

        check_input_files_exist(record_metadata_file_path, data_files_paths)
        logger.info('Input files exist')

        # Create a draft on the archive
        # Get the record's id (e.g., 'cpbc8-ss975')
        record_id = create_draft_record(url, token, record_metadata_file_path)
        logger.info(f'Draft record with id={record_id} created with success')

        # Update the record's metadata with the names of the data files to be attached to the record
        start_file_uploads(url, token, record_id, data_files)
        logger.info('Data files specified with success')

        # For each data file, upload its content
        for file in data_files:
            upload_file_content(url, token, record_id, basedir, input_folder, file)
            complete_file_upload(url, token, record_id, file)

        logger.info('Data files uploaded with success')

        # Share the draft with all archive's users
        if publish:
            publish_draft_record(url, token, record_id)

        logger.info('Record published with success')
    except FileNotFoundError as exception:
        logger.error('File not found: ' + str(exception.filename))
    except Exception as exception:
        logger.error('Error occurred: ' + str(exception))