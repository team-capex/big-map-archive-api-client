import logging
import requests
import os
import json

def get_record(url, token, id):
    """
    Gets the metadata of a shared record
    Raises an exception if the metadata of the record could not be obtained
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

def export_to_file(file_path, data):
    """
    Exports data to file
    """
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4, sort_keys=True)


if __name__ == '__main__':
    # Select an archive
    #url = "https://archive.big-map.eu/"
    url = "https://big-map-archive-demo.materialscloud.org/"

    # Navigate to 'Applications' > 'Personal access tokens' to create a token if necessary
    #token = "<replace by a personal token>"
    token = '1A2GC4qgIRQmEwdFGjNr0jA6EUJ44XOg714MNdFpatmbZqyvqN3Z7soqTLDj'

    # Specify whether you are interested in
    #   - one shared record (single_record = True) or
    #   - all shared records (single_record = False)
    single_record = True

    # If single_record = True, specify the record's id (e.g., 'j6hfj-bsb82')
    # If single_record = False, the value of record_id is ignored by the script
    record_id = 'j6hfj-bsb82'

    # Folders
    output_folder = 'output'

    # Output file
    record_metadata_file = f'record_metadata.json'

    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

    try:
        record_metadata = get_record(url, token, record_id)
        logger.info(f'Metadata of {record_id} obtained with success')

        basedir = os.path.abspath(os.path.dirname(__file__))
        record_metadata_file_path = os.path.join(basedir, output_folder, record_metadata_file)
        export_to_file(record_metadata_file_path, record_metadata)
        logger.info(f'Metadata exported to {record_metadata_file} with success')
    except Exception as e:
        logger.error('Error occurred: ' + str(e))
