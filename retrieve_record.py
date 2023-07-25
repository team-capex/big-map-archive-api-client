import logging
import requests
import os
import json
import configparser
from dotenv import load_dotenv


def get_metadata_of_record(url, token, record_id):
    """
    Returns the metadata of a published record
    Raises an HTTPError exception if the request to get the metadata failed
    """
    request_headers = {
        "Accept": "application/json",
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(
        f'{url}/api/records/{record_id}',
        headers=request_headers,
        verify=True)

    response.raise_for_status()

    metadata = json.loads(response.text)
    return metadata


def get_metadata_of_all_records(url, token, response_size):
    """
    Returns the metadata of all published records
    Raises an HTTPError exception if the request to get the metadata failed
    """
    request_headers = {
        "Accept": "application/json",
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(
        f'{url}/api/records?allversions=true&size={response_size}',
        headers=request_headers,
        verify=True)

    response.raise_for_status()

    metadata = json.loads(response.text)
    return metadata


def get_metadata_of_all_latest_versions(url, token, response_size):
    """
    Returns the metadata of all published latest versions
    Raises an HTTPError exception if the request to get the metadata failed
    """
    request_headers = {
        "Accept": "application/json",
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(
        f'{url}/api/records?size={response_size}',
        headers=request_headers,
        verify=True)

    response.raise_for_status()

    metadata = json.loads(response.text)
    return metadata


def export_to_file(file_path, data):
    """
    Exports data to file
    """
    with open(file_path, "a") as f:
        json.dump(data, f, indent=4, sort_keys=True)


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

    # Max number of items in requests' responses
    response_size = int(1e6)

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

        # Get metadata of requested records
        requested_records = config.get('retrieve_record', 'requested_records')

        if requested_records == 'single':
            id = config.get('retrieve_record', 'record_id')
            metadata = get_metadata_of_record(url, token, id)
        elif requested_records == 'all':
            metadata = get_metadata_of_all_records(url, token, response_size)
        elif requested_records == 'latest':
            metadata = get_metadata_of_all_latest_versions(url, token, response_size)
        else:
            raise Exception(f'Invalid requested_records in config.ini')

        # Export obtained metadata to file
        output_folder = config.get('retrieve_record', 'output_folder')
        output_file = config.get('retrieve_record', 'output_file')
        output_file_path = os.path.join(basedir, output_folder, output_file)
        export_to_file(output_file_path, metadata)

        logger.info(f'Metadata obtained and exported to {output_file}')

    except Exception as e:
        logger.error('Error occurred: ' + str(e))
