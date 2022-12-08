import json
import os
import logging
import requests
from big_map_archive_api.utils import load_token

logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


class BMA:
    """BMA is the API for BIG-MAP archive API.

    Attributes:

    url: str
        url of BIG-MAP Archive.
        Default value: https://archive.big-map.eu/
    token: str
        token of your account.
    ids_filename: str
        file to save the ids of the records.

    Examples:

    >>> from big_map_archive_api.api import BMA
    >>> token = "Your Token"
    >>> bma = BMA(token=token)

    Upload records:

    >>> bma.upload_records("../tests//records")

    Publish records:

    >>> bma.publish()

    """

    def __init__(
        self,
        url="https://archive.big-map.eu/",
        token=None,
        ids_filename="records_ids.json",
    ):
        self.url = url
        token = load_token() if token is None else token
        if token is not None:
            self.token = token
        else:
            raise Exception("token is not provided.")
        self.ids_filename = ids_filename

    def find_records(self):
        """Find all records in the folder."""
        records = {}
        directories = [d for d in os.listdir(self.records_path) if os.path.isdir(d)]
        for folder in os.listdir(self.records_path):
            path = os.path.join(self.records_path, folder)
            if not os.path.isdir(path):
                continue
            files = os.listdir(path)
            if "metadata.json" not in files:
                raise Exception("File metadata.json is required for a record.")
            files.remove("metadata.json")
            records[folder] = files
        self.records = records
        logger.debug(records)

    def upload_records(self, records_path):
        """Upload all records in the records_path."""
        self.records_path = records_path
        self.ids = {}
        self.find_records()
        try:
            self.prepare_output_file()
            record_index = 0
            for folder, files in self.records.items():
                logger.info(
                    "----------Start uploading record " + str(folder) + "----------"
                )
                id = self.upload_record(folder, files)
                self.ids[folder] = id
                record_index += 1
            # Save the record's id to a file
            self.save_to_file()
            logger.info(
                "Uploading was successful. See the file records_ids.json for ids to the created records."
            )
        except Exception as e:
            logger.error("Error occurred: " + str(e))

    def prepare_output_file(self):
        """Prepare output file"""
        file_path = os.path.join(self.records_path, self.ids_filename)

        if os.path.exists(file_path):
            os.remove(file_path)

        # Create a file for storing records' ids
        with open(file_path, "x") as f:
            json_formatted_text = json.dumps([])
            f.write(json_formatted_text)

    def upload_record(self, folder, files):
        """Upload one record

        Args:
            url (str): "https://archive.big-map.eu/" for BIG-MAP archive
            records_path (str): _description_
            record (tuple): _description_
            record_index (int): _description_
            token (str): _description_

        Returns:
            dict: _description_
        """
        # Get title, authors, list of attached files...
        with open(os.path.join(self.records_path, str(folder), "metadata.json")) as f:
            record_metadata = json.load(f)

        # Create a record in the PostgreSQL database
        # Get the url for the record's attached files
        # e.g., 'https://dev1-big-map-archive.materialscloud.org/api/records/cpbc8-ss975/draft/files'
        id = self.create_record_in_database(record_metadata)

        for filename in files:
            self.upload_data_file(id, folder, filename)

        return id

    def create_record_in_database(self, record_metadata):
        """Create one record in the database

        Args:
            record_metadata (dict): metadata for the record

        Raises:
            ValueError: _description_

        Returns:
            dict: _description_
        """
        payload = json.dumps(record_metadata)

        request_headers = {
            "Accept": "application/json",
            "Content-type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }

        # Set "verify=True" in production so that HTTPS requests verify SSL certificates
        response = requests.post(
            f"{self.url}/api/records",
            data=payload,
            headers=request_headers,
            verify=True,
        )

        # Raise an exception if the record could not be created
        if response.status_code != 201:
            raise ValueError(f"Failed to create record (code: {response.status_code})")

        #  Get urls for the record
        # seems we only need to get the uuid of the record, then we can re-build all the links.
        #  e.g., 'https://dev1-big-map-archive.materialscloud.org/api/records/h0zrf-17b65/draft/files'
        data = response.json()
        logger.debug(data)
        id = data["id"]
        return id

    def upload_data_file(self, id, folder, filename):
        """_summary_

        Args:
            folder (str): _description_
            filename (str): _description_
            file_index (int): _description_
            record_index (int): _description_
            links (dict): _description_
            token (str): _description_
        """
        (file_content_url, file_commit_url) = self.start_data_file_upload(id, filename)
        self.upload_data_file_content(folder, filename, file_content_url)
        self.complete_data_file_upload(filename, file_commit_url)

    def start_data_file_upload(self, id, filename):
        """Start upload data file

        Args:
            filename (str): _description_
            file_index (int): _description_
            links (dict): _description_
            token (str): _description_

        Raises:
            ValueError: _description_

        Returns:
            _type_: _description_
        """
        files_url = "{}/api/records/{}/draft/files".format(self.url, id)
        payload = json.dumps([{"key": filename}])

        request_headers = {
            "Accept": "application/json",
            "Content-type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }

        response = requests.post(
            files_url, data=payload, headers=request_headers, verify=True
        )

        # Raise an exception if the file could not be created
        if response.status_code != 201:
            raise ValueError(f"Failed to create record (code: {response.status_code})")

        # Get the file content url and the file commit url
        # Here the name of the datafile should be unique, and is used as the id to build the link.
        # e.g., 'https://dev1-big-map-archive.materialscloud.org/api/records/eqcks-b1q35/draft/files/scientific_data.json/content'
        # e.g, 'https://dev1-big-map-archive.materialscloud.org/api/records/eqcks-b1q35/draft/files/scientific_data.json/commit'
        # it seems the file_index is not needed here, because we can re-build the links by the filename,
        # this need to be varified.
        file_content_url = "{}/api/records/{}/draft/files/{}/content".format(
            self.url, id, filename
        )
        file_commit_url = "{}/api/records/{}/draft/files/{}/commit".format(
            self.url, id, filename
        )
        return (file_content_url, file_commit_url)

    def upload_data_file_content(self, folder, filename, file_content_url):
        """Upload the content of the data file.

        Args:
            records_path (str): _description_
            filename (str): _description_
            record_index (int): _description_
            file_content_url (str): _description_
            token (str): _description_

        Raises:
            ValueError: _description_
        """
        # Upload the file content by streaming the data
        # Does this "b" binary data?
        with open(os.path.join(self.records_path, folder, filename), "rb") as f:
            request_headers = {
                "Accept": "application/json",
                "Content-type": "application/octet-stream",
                "Authorization": f"Bearer {self.token}",
            }

            response = requests.put(
                file_content_url, data=f, headers=request_headers, verify=True
            )

        # Raise an exception if the file content could not be uploaded
        if response.status_code != 200:
            raise ValueError(
                f"Failed to upload file content {filename} (code: {response.status_code})"
            )

    def complete_data_file_upload(self, filename, file_commit_url):
        """Complete the upload by commiting.

        Args:
            filename (str): _description_
            file_commit_url (str): _description_
            token (str): _description_

        Raises:
            ValueError: _description_
        """
        request_headers = {
            "Accept": "application/json",
            "Content-type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }
        # No data is posted here, why?
        response = requests.post(file_commit_url, headers=request_headers, verify=True)

        # Raise an exception if the file content could not be uploaded
        if response.status_code != 200:
            raise ValueError(
                f"Failed to complete file upload {filename} (code: {response.status_code})"
            )

    def publish(self):
        for folder, id in self.ids.items():
            self.publish_record(id)
            logger.info("Publishing data: {} successfully.".format(folder))

    def publish_record(self, id):
        """Publish a record.

        Args:
            links (dict): _description_
            token (str): _description_

        Raises:
            ValueError: _description_
        """
        publish_url = "{}/api/records/{}/draft/actions/publish".format(self.url, id)

        request_headers = {
            "Accept": "application/json",
            "Content-type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }

        response = requests.post(publish_url, headers=request_headers, verify=True)

        # Raise an exception if the record could not be published
        if response.status_code != 202:
            raise ValueError(f"Failed to publish record (code: {response.status_code})")

    def save_to_file(self):
        filename = os.path.join(self.records_path, self.ids_filename)

        with open(filename, "w") as f:
            json.dump(self.ids, f, indent=4)


if __name__ == "__main__":
    url = "https://archive.big-map.eu/"

    # Navigate to 'Applications' > 'Personal access tokens' to create a token if necessary
    token = "qOTqN4fXG4t0fz4bKu3tC1wh0Q5SppafXS5Cm7SJV2Ku4YMQub3jNbjSXxzH"

    records_path = "records"
    ids_filename = "records_ids.json"

    # Specify records that you want to upload:
    # ('<record metadata json>.json', ['<datafile1>', '<datafile2>'])

    publish = True
    bma = BMA(token=token)
    bma.upload_records("./tests/records")
