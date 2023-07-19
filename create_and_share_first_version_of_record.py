import json
import os
import logging
import requests
import errno


def check_input_folder_exists(input_folder_path):
    """
    Raises an exception if the input folder does not exist
    """
    if not os.path.exists(input_folder_path):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), input_folder_path)

def check_input_file_exists(input_folder_path):
    """
    Raises an exception if the record metadata file is missing from the input folder
    """
    if not os.path.isfile(record_metadata_file_path):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), record_metadata_file_path)

def get_data_files(input_folder_path, record_metadata_file):
    """
    Returns the list of the files in the input folder, except the metadata file
    """
    all_files = [item for item in os.listdir(input_folder_path) if os.path.isfile(os.path.join(input_folder_path, item))]
    data_files = [item for item in all_files if item != record_metadata_file]
    return data_files


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

def start_file_uploads(url, token, record_id, filenames):
    """
    Updates a record's metadata by specifying the files that should be attached to it
    Raises an exception if the record's metadata could not be updated
    """
    # Create the payload specifying the files to be attached to the record
    filename_vs_key = []

    for filename in filenames:
        filename_vs_key.append({'key': filename})

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
    Raises an exception if the file's content could not be uploaded
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
    # -----------------Users: verify the information below-----------------
    # Specify the targeted archive:
    # - the main archive (main = True)
    # - the demo archive (main = False)
    main = False

    # Specify a personal access token for the selected archive
    # If you need a valid token, navigate to 'Applications' > 'Personal access tokens'
    #token = '<replace_with_token>'
    token = '88j0czz2YnArs68xh8xv898h1IpulGCy4T7Dlh55ySkbKg7elBHSWNnpW1Oq'

    # Specify the folder where your input files are located
    input_folder = 'input'

    # Specify the file in the input folder that contains the record's title, the record's authors...
    # Note that all other files in the input folder will automatically be attached to the record
    record_metadata_file = 'record_metadata.json'

    # Specify whether you wish to share the record with all archive's users
    publish = True

    # ---------------Users: do not modify the information below---------------
    # Archives' urls
    main_archive_url = 'https://archive.big-map.eu/'
    demo_archive_url = 'https://big-map-archive-demo.materialscloud.org/'
    url = demo_archive_url

    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

    try:
        basedir = os.path.abspath(os.path.dirname(__file__))
        input_folder_path = os.path.join(basedir, input_folder)
        check_input_folder_exists(input_folder_path)
        logger.info('Input folder exists')

        record_metadata_file_path = os.path.join(basedir, input_folder, record_metadata_file)
        check_input_file_exists(record_metadata_file_path)
        logger.info(f'Input file {record_metadata_file} exists')

        if main:
            url = main_archive_url

        # Create a draft on the archive
        # Get the record's id (e.g., 'cpbc8-ss975')
        record_id = create_draft_record(url, token, record_metadata_file_path)
        logger.info(f'Draft record with id={record_id} created with success')

        # Update the record's metadata with the names of the data files to be attached to the record
        # The data files are the files in the input folder, except for the record metadata file
        data_files = get_data_files(input_folder_path, record_metadata_file)
        data_files_paths = [os.path.join(input_folder_path, f) for f in data_files]
        start_file_uploads(url, token, record_id, data_files)
        logger.info('Data files specified with success')

        # For each data file, upload its content
        for file in data_files:
            upload_file_content(url, token, record_id, basedir, input_folder, file)
            complete_file_upload(url, token, record_id, file)

        logger.info('Data files uploaded with success')

        if publish:
            # Share the draft with all archive's users
            publish_draft_record(url, token, record_id)
            logger.info('Record published with success')

    except FileNotFoundError as exception:
        logger.error('File not found: ' + str(exception.filename))
    except Exception as exception:
        logger.error('Error occurred: ' + str(exception))