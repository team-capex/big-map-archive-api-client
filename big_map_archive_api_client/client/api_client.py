import json
import os
from datetime import date

from big_map_archive_api_client.client.rest_api_connection import RestAPIConnection
from big_map_archive_api_client.utils import (generate_full_metadata,
                                              change_metadata,
                                              get_name_to_checksum_for_input_folder_files)


class APIClient:
    """
    Class to interact with BMA's API
    """

    def __init__(self, domain_name, port, token):
        """
        Initialize internal variables
        """
        self._connection = RestAPIConnection(domain_name, port, token)

    def post_records(self, base_dir, input_dir, metadata_filename):
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
        response = self.put_draft(record_id, response)
        return response.json()

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

    def post_draft(self, record_id):
        """
        Creates a draft from a published record: same version with same record id
        Raises an HTTPError exception if the request fails
        """
        resource_path = f'/api/records/{record_id}/draft'
        response = self._connection.post(resource_path)
        response.raise_for_status()
        return response.json()

    def post_versions(self, record_id):
        """
        Creates a draft from a published record: a new version with a different record id
        Raises an HTTPError exception if the request fails
        """
        resource_path = f'/api/records/{record_id}/versions'
        response = self._connection.post(resource_path)
        response.raise_for_status()
        return response.json()

    def get_files(self, record_id):
        """
        Gets a draft's linked files (with their names and their md5 hashes)
        Raises an HTTPError exception if the request fails
        """
        resource_path = f'/api/records/{record_id}/draft/files'
        response = self._connection.get(resource_path)
        response.raise_for_status()
        return response.json()

    def delete_filename(self, record_id, filename):
        """
        Removes a link to a file from a draft
        Raises an HTTPError exception if the request fails
        """
        resource_path = f'/api/records/{record_id}/draft/files/{filename}'
        response = self._connection.delete(resource_path)
        response.raise_for_status()

    def post_file_import(self, record_id):
        """
        Imports all file links from a published record into a draft (new version)
        This avoids re-uploading files, which would cause duplication on the data store
        Raises an HTTPError exception if the request fails
        """
        resource_path = f'/api/records/{record_id}/draft/actions/files-import'
        response = self._connection.post(resource_path)
        response.raise_for_status()
        return response.json()

    def update_metadata(self, record_id, base_dir, input_dir, metadata_filename):
        """
        Updates the metadata of a draft using a file's content
        """
        metadata = self.get_draft(record_id)
        metadata = change_metadata(metadata, base_dir, input_dir, metadata_filename)
        self.put_draft(record_id, metadata)

    def get_name_to_checksum_for_linked_files(self, record_id):
        """
        Gets the names and md5 hashes of a draft's linked files
        """
        response = self.get_files(record_id)
        entries = response['entries']

        name_to_checksum_for_linked_files = [
            {
                'name': entry['key'],
                'checksum': entry['checksum']
            } for entry in entries]

        return name_to_checksum_for_linked_files

    def get_links(self, record_id):
        """
        Gets the names of a draft's linked files
        """
        name_to_checksum_for_linked_files = self.get_name_to_checksum_for_linked_files(record_id)
        filenames = [file['name'] for file in name_to_checksum_for_linked_files]
        return filenames

    def delete_links(self, record_id, filenames):
        """
        Deletes file links from a draft
        """
        for filename in filenames:
            self.delete_filename(record_id, filename)

    def get_changed_content_links(self, record_id, base_dir, input_dir):
        """
        Gets the links in a draft for which there is a file in the input folder with the same name but a different content
        """
        name_to_checksum_for_linked_files = self.get_name_to_checksum_for_linked_files(record_id)
        name_to_checksum_for_input_folder_files = get_name_to_checksum_for_input_folder_files(base_dir, input_dir)

        filenames = []

        for file in name_to_checksum_for_linked_files:
            name = file['name']
            checksum = file['checksum']

            files_in_folder_with_same_name_and_different_content = [f for f in name_to_checksum_for_input_folder_files
                                                                    if (f['name'] == name and f[
                    'checksum'] != checksum)]

            if len(files_in_folder_with_same_name_and_different_content) == 1:
                # linked file is classified as updated
                filenames.append(name)

        return filenames

    def get_links_to_delete(self, record_id, delete_missing, base_dir, input_dir):
        """
        Two possible reasons for deleting a link that was imported from the previous version into a new version:
        - file has changed content (i.e., it appears in the input folder but with a different md5 hash)
        - file has been removed (i.e., it does not appear in the input folder) and delete_removed is set to True
        """
        filenames = self.get_changed_content_links(record_id, base_dir, input_dir)

        #if delete_missing:
        #    filenames += self.get_missing_links()

        return filenames

    def get_files_to_upload_and_link(self, record_id, base_dir, input_dir, metadata_filename):
        """
        TODO
        """
        filenames = []
        return filenames

    def upload_and_link(self, record_id, filenames):
        """
        TODO
        """
        pass




        """
        Updates the file links for a draft
        File links from the previous version are classified into 3 categories:
            - 'updated': is linked to the previous version and also appears in the input folder but with a different md5 hash (i.e., with an updated content)
            - 'former': is linked to the previous version but does not appear in the input folder
            - 'new': appears in the input folder but there is no file linked to the previous version carrying this name
        """



