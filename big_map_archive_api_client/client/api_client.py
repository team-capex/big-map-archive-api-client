import json
import os
from datetime import date

from big_map_archive_api_client.client.rest_api_connection import RestAPIConnection
from big_map_archive_api_client.utils import generate_full_metadata


class APIClient:
    """
    Class to interact with BMA's API
    """

    def __init__(self, domain_name, port, token):
        """
        Initialize internal variables
        """
        self._connection = RestAPIConnection(domain_name, port, token)

    def post_record(self, base_dir, input_dir, metadata_filename):
        """
        Creates a draft on the archive from provided metadata
        Raises an HTTPError exception if the request fails
        Returns the newly created draft's id
        """
        resource_path = '/api/records'
        metadata_file_path = os.path.join(base_dir, input_dir, metadata_filename)
        full_metadata = generate_full_metadata(metadata_file_path)
        payload = json.dumps(full_metadata)
        response = self._connection.post(resource_path, payload)
        response.raise_for_status()
        return response.json()

    def post_files(self, record_id, filenames):
        """
        Updates a record's metadata by specifying the files that should be linked to it
        Raises an HTTPError exception if the request fails
        """
        resource_path = f'/api/records/{record_id}/draft/files'

        # Create the payload specifying the files to be attached to the record
        key_to_filename = []
        for filename in filenames:
            key_to_filename.append({'key': filename})

        payload = json.dumps(key_to_filename)
        response = self._connection.post(resource_path, payload)
        response.raise_for_status()
        return response.json()

    def put_content(self, record_id, base_dir, input_dir, filename):
        """
        Uploads a file's content
        Raises an HTTPError exception if the request fails
        """
        resource_path = f'/api/records/{record_id}/draft/files/{filename}/content'
        file_path = os.path.join(base_dir, input_dir, filename)

        with open(file_path, 'rb') as f:
            payload = f
            response = self._connection.put(resource_path, payload, 'application/octet-stream')

        response.raise_for_status()
        return response.json()

    def post_commit(self, record_id, filename):
        """
        Completes the upload of a file's content
        Raises an HTTPError exception if the request fails
        """
        resource_path = f'/api/records/{record_id}/draft/files/{filename}/commit'
        response = self._connection.post(resource_path)
        response.raise_for_status()
        return response.json()

    def get_draft(self, record_id):
        """
        Gets a draft's metadata
        Raises an HTTPError exception if the request fails
        """
        resource_path = f'/api/records/{record_id}/draft'
        response = self._connection.get(resource_path)
        response.raise_for_status()
        return response.json()

    def put_draft(self, record_id, metadata):
        """
        Updates a draft's metadata
        Raises an HTTPError exception if the request fails
        """
        resource_path = f'/api/records/{record_id}/draft'
        payload = json.dumps(metadata)
        response = self._connection.put(resource_path, payload)
        response.raise_for_status()
        return response.json()

    def insert_publication_date(self, record_id):
        """
        Inserts a publication date into a record's metadata
        """
        response = self.get_draft(record_id)
        response['metadata']['publication_date'] = date.today().strftime('%Y-%m-%d')  # e.g., '2020-06-01'
        self.put_draft(record_id, response)

    def post_publish(self, record_id):
        """
        Publishes a draft to the archive (i.e., shares a record with all archive users)
        Raises an HTTPError exception if the request fails
        """
        resource_path = f'/api/records/{record_id}/draft/actions/publish'
        response = self._connection.post(resource_path)
        response.raise_for_status()
        return response.json()

    def get_record(self, record_id):
        """
        Gets a published record's metadata
        Raises an HTTPError exception if the request fails
        """
        resource_path = f'/api/records/{record_id}'
        response = self._connection.get(resource_path)
        response.raise_for_status()
        return response.json()

    def get_records(self, all_versions, response_size):
        """
        Gets published records' metadata
        Raises an HTTPError exception if the request fails
        """
        resource_path = f'/api/records?allversions={all_versions}&size={response_size}'
        response = self._connection.get(resource_path)
        response.raise_for_status()
        return response.json()