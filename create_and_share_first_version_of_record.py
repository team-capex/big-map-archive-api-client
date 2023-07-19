import json
import os
import logging
import requests
import errno


def check_api_access(url, token):
    """
    Sends a GET request to test access to an api's endpoint
    If the token is invalid, an HTTPError exception with the status code 403 and the reason 'FORBIDDEN' is raised
    """
    request_headers = {
        "Accept": "application/json",
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(
        f'{url}/api/records?size=1',
        headers=request_headers,
        verify=True)

    # Raise an exception if there is an HTTP error
    response.raise_for_status()

def check_input_folder_exists(input_folder_path):
    """
    Raises an exception if the input folder does not exist
    """
    if not os.path.exists(input_folder_path):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), input_folder_path)

def check_input_file_exists(initial_metadata_file_path):
    """
    Raises an exception if the initial metadata file is missing from the input folder
    """
    if not os.path.isfile(initial_metadata_file_path):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), initial_metadata_file_path)

def create_draft_record(url, token, input_metadata_file_path):
    """
    Creates a record, which remains private to its owner, from the initial metadata file
    Raises an HTTPError exception if the request to create the record fails
    """
    # Create the payload from the record's metadata file (title, authors...)
    with open(input_metadata_file_path, 'r') as f:
        input_metadata = json.load(f)

    payload = json.dumps(input_metadata)

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

    # Raise an exception if there is an HTTP error
    response.raise_for_status()

    #  Get record's id
    record_url = response.json()['links']['record']
    record_id = record_url.split('/api/records/')[-1]
    return record_id

def get_data_files(input_folder_path, record_metadata_file):
    """
    Returns the filenames in the input folder, except for the metadata file
    """
    all_files = [item for item in os.listdir(input_folder_path) if os.path.isfile(os.path.join(input_folder_path, item))]
    data_files = [item for item in all_files if item != record_metadata_file]
    return data_files

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

    # Raise an exception if there is an HTTP error
    response.raise_for_status()

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

    # Raise an exception if there is an HTTP error
    response.raise_for_status()


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

    # Raise an exception if there is an HTTP error
    response.raise_for_status()

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

    # Raise an exception if there is an HTTP error
    response.raise_for_status()


if __name__ == '__main__':
    # -----------------Users: verify the information below-----------------
    # Specify the targeted archive:
    # - the main archive (main = True)
    # - the demo archive (main = False)
    main = False

    # Specify a valid token for the selected archive
    # If you need a new token, navigate to 'Applications' > 'Personal access tokens'
    token = '<replace_with_token>'

    # Specify the folder where your input files are located
    input_folder = 'input'

    # Specify the file in the input folder that contains the title, the authors... for the record
    # Note that all other files in the input folder will automatically be attached to the record
    initial_metadata_file = 'initial_metadata.json'

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
        if main:
            url = main_archive_url

        check_api_access(url, token)

        basedir = os.path.abspath(os.path.dirname(__file__))
        input_folder_path = os.path.join(basedir, input_folder)
        check_input_folder_exists(input_folder_path)
        logger.info('Input folder exists')

        initial_metadata_file_path = os.path.join(basedir, input_folder, initial_metadata_file)
        check_input_file_exists(initial_metadata_file_path)
        logger.info(f'Input file {initial_metadata_file} exists')

        # Create a draft on the archive from the content of initial_metadata_file
        # Get the id of the newly created record (e.g., 'cpbc8-ss975')
        record_id = create_draft_record(url, token, initial_metadata_file_path)
        logger.info(f'Draft record with id={record_id} created with success')

        # Update the record's metadata with the names of the data files that will be attached to the record
        # The data files are the files in the input folder, except for the initial metadata file
        data_files = get_data_files(input_folder_path, initial_metadata_file)
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

    except requests.exceptions.HTTPError as e:
        logger.error('Error occurred: ' + str(e))

        status_code = e.response.status_code
        reason = e.response.reason

        if status_code == 403 and reason == 'FORBIDDEN':
            logger.error('Check token\'s validity')

    except FileNotFoundError as e:
        logger.error('File not found: ' + str(e.filename))

    except Exception as e:
        logger.error('Error occurred: ' + str(e))