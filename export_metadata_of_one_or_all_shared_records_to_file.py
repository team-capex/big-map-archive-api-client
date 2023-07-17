import logging
import requests
import os
import json

def get_record_metadata(url, token, id):
    """
    Gets the metadata of a shared record
    Raises an exception if the metadata could not be obtained
    """
    request_headers = {
        "Accept": "application/json",
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(
        f"{url}/api/records/{id}",
        headers=request_headers,
        verify=True)

    # Raise an exception if the metadata of the record could not be obtained
    if response.status_code != 200:
        raise ValueError(f"Failed request (code: {response.status_code})")

    record_metadata = json.loads(response.text)
    return record_metadata

def get_records_metadata(url, token, response_size):
    """
    Gets the metadata of all shared records
    Raises an exception if the metadata could not be obtained
    """
    request_headers = {
        "Accept": "application/json",
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(
        f"{url}/api/records?allversions=true&size={response_size}",
        headers=request_headers,
        verify=True)

    # Raise an exception if the metadata could not be obtained
    if response.status_code != 200:
        raise ValueError(f"Failed request (code: {response.status_code})")

    records_metadata = json.loads(response.text)
    return records_metadata

def create_folder(folder_path):
    """
    Creates a folder if it does not exist
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

def export_to_file(file_path, data):
    """
    Exports data to file
    """
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4, sort_keys=True)


if __name__ == '__main__':
    # -----------------Users: verify the information below-----------------
    # Specify the targeted archive:
    # - the main archive (main = True)
    # - the demo archive (main = False)
    main = False

    # Specify a personal access token for the selected archive
    # If you need a valid token, navigate to 'Applications' > 'Personal access tokens'
    token = '<replace_with_token>'

    # Specify the folder where your output files are located
    output_folder = 'output'

    # Specify whether you wish to retrieve the metadata of
    # - a single record that is shared on the archive (single_record = True) or
    # - all records that are shared on the archive (single_record = False)
    single_record = False

    # If you wish to retrieve the metadata of a single record, specify its id
    # e.g., jenf1-ng292
    record_id = '<replace_with_id>'

    # ---------------Users: do not modify the information below---------------
    # Archives' urls
    main_archive_url = 'https://archive.big-map.eu/'
    demo_archive_url = 'https://big-map-archive-demo.materialscloud.org/'
    url = demo_archive_url

    # Max number of items in requests' responses
    response_size = int(1e6)

    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

    try:
        basedir = os.path.abspath(os.path.dirname(__file__))

        if main:
            url = main_archive_url

        if single_record:
            metadata = get_record_metadata(url, token, record_id)
            logger.info(f'Metadata of {record_id} obtained with success')
            output_file = f'{record_id}.json'
        else:
            metadata = get_records_metadata(url, token, response_size)
            logger.info(f'Metadata of all records obtained with success')
            output_file = 'all_shared_records.json'

        output_folder_path = os.path.join(basedir, output_folder)
        create_folder(output_folder_path)

        output_file_path = os.path.join(basedir, output_folder, output_file)
        export_to_file(output_file_path, metadata)
        logger.info(f'Metadata exported to {output_file} with success')

    except Exception as e:
        logger.error('Error occurred: ' + str(e))
