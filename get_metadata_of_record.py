import logging
import requests
import os
import json

def get_record_metadata(url, token, id):
    request_headers = {
        "Accept": "application/json",
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    # Set "verify=True" in production so that HTTPS requests verify SSL certificates
    response = requests.get(
        f"{url}/api/records/{id}",
        headers=request_headers,
        verify=True)

    # Raise an exception if HTTP status code is not 200 OK
    if response.status_code != 200:
        raise ValueError(f"Failed request (code: {response.status_code})")

    record_metadata = json.loads(response.text)
    return record_metadata


def save_in_file(folder, filename, data):
    file_path = os.path.join(folder, filename)

    with open(file_path, "w") as f:
        json.dump(data, f, indent=4, sort_keys=True)


if __name__ == '__main__':
    #url = "https://archive.big-map.eu/"
    url = "https://big-map-archive-demo.materialscloud.org/"

    # Navigate to 'Applications' > 'Personal access tokens' to create a token if necessary
    token = "<replace by personal token>"

    # Specify the record that you want to upload
    record_id = "<replace by record id>"

    # Information on where data is saved
    folder = 'shared_records'
    filename = f'{record_id}.json'

    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

    try:
        logger.info(f'Starts getting record\'s metadata for id={record_id}')
        record_metadata = get_record_metadata(url, token, record_id)
        logger.info('Record\'s metadata obtained with success')
        save_in_file(folder, filename, record_metadata)
        logger.info(f'Record\'s metadata saved in {filename}')
    except Exception as e:
        logger.error('Error occurred: ' + str(e))
