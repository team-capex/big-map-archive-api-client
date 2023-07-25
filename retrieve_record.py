import logging
import requests
import os
import json
import configparser
from dotenv import load_dotenv
import shutil


def get_metadata_of_record(url, token, record_id):
    """
    Returns the metadata of a published record on the archive
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

    records_metadata = json.loads(response.text)
    return records_metadata

def get_metadata_of_all_records(url, token, response_size):
    """
    Returns the metadata of all published records on the archive
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

    records_metadata = json.loads(response.text)
    return records_metadata


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

    records_metadata = json.loads(response.text)
    return records_metadata


def recreate_folder(folder_path):
    """
    Re-creates a folder if it exists, otherwise creates a new one
    """
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)

    os.makedirs(folder_path)


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
        basedir = os.path.abspath(os.path.dirname(__file__))

        # Read configuration file config.ini
        config = configparser.ConfigParser()
        config.read(os.path.join(basedir, 'config.ini'))

        # Create environment variables from secrets.env
        load_dotenv(os.path.join(basedir, 'secrets.env'))
        logger.info('Environment variables created with success')

        select_main_archive = config.get('general', 'select_main_archive')

        if select_main_archive == 'True':
            url = config.get('general', 'main_archive_url')
            token = os.getenv('MAIN_ARCHIVE_TOKEN')
        elif select_main_archive == 'False':
            url = config.get('general', 'demo_archive_url')
            token = os.getenv('DEMO_ARCHIVE_TOKEN')
        else:
            raise Exception('Invalid value for select_main_archive in config.ini')

        # Get the metadata of published record(s)
        requested_records = config.get('get_record_metadata', 'requested_records')

        if requested_records == 'single':
            record_id = config.get('get_record_metadata', 'record_id')
            metadata = get_metadata_of_record(url, token, record_id)
        elif requested_records == 'all':
            metadata = get_metadata_of_all_records(url, token, response_size)
        elif requested_records == 'latest':
            metadata = get_metadata_of_all_latest_versions(url, token, response_size)
        else:
            raise Exception(f'Invalid value for requested_records: {requested_records}')

        logger.info('Metadata of shared record(s) obtained with success')

        # Export the obtained metadata to a file in the output folder
        output_folder = config.get('get_record_metadata', 'output_folder')
        output_folder_path = os.path.join(basedir, output_folder)
        recreate_folder(output_folder_path)
        output_file = config.get('get_record_metadata', 'output_file')
        output_file_path = os.path.join(basedir, output_folder, output_file)
        export_to_file(output_file_path, metadata)
        logger.info(f'Metadata exported to {output_file} with success')

    except requests.exceptions.HTTPError as e:
        logger.error('Error occurred: ' + str(e))

        status_code = e.response.status_code
        reason = e.response.reason

        if status_code == 403 and reason == 'FORBIDDEN':
            logger.error('Check token\'s validity')

    except Exception as e:
        logger.error('Error occurred: ' + str(e))
