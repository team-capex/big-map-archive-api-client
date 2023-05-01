import logging
import requests
import os
import json

def get_records_metadata(url, token, response_size):
    request_headers = {
        "Accept": "application/json",
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    # Set "verify=True" in production so that HTTPS requests verify SSL certificates
    response = requests.get(
        f"{url}/api/records?size={response_size}",
        headers=request_headers,
        verify=True)

    # Raise an exception if HTTP status code is not 200 OK
    if response.status_code != 200:
        raise ValueError(f"Failed request (code: {response.status_code})")

    records_metadata = json.loads(response.text)
    return records_metadata


def save_in_file(folder, filename, data):
    file_path = os.path.join(folder, filename)

    with open(file_path, "w") as f:
        json.dump(data, f, indent=4, sort_keys=True)




if __name__ == '__main__':
    #url = "https://archive.big-map.eu/"
    url = "https://big-map-archive-demo.materialscloud.org/"

    # Navigate to 'Applications' > 'Personal access tokens' to create a token if necessary
    token = "<replace by personal token>"

    # Information on where data is saved
    folder = 'shared_records'
    filename = 'all.json'

    # Max number of items in the response
    response_size = int(1e6)

    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

    try:
        logger.info('Starts getting records\' metadata')
        records_metadata = get_records_metadata(url, token, response_size)
        logger.info('Records\' metadata obtained with success')
        save_in_file(folder, filename, records_metadata)
        logger.info(f'Records\' metadata saved in {filename}')
    except Exception as e:
        logger.error('Error occurred: ' + str(e))