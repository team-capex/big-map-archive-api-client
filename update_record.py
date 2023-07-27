import os
import logging
import requests
import hashlib
import configparser
from dotenv import load_dotenv
import sys
import json

from create_record import publish_draft, update_draft_metadata, get_draft_metadata, start_file_uploads, \
    upload_file_content, complete_file_upload, insert_publication_date
from retrieve_record import get_metadata_of_record


def create_draft_with_same_id(url, token, record_id):
    """
    Creates a draft from a published record
    This draft has the same id as the published record
    """
    request_headers = {
        "Accept": "application/json",
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.post(
        f'{url}/api/records/{record_id}/draft',
        headers=request_headers,
        verify=True)

    response.raise_for_status()

    return response.json()


def generate_metadata(full_record_metadata, file_path):
    """
    Updates the original record's metadata with the value provided by the file
    Re-inserts the publication date if the record is published
    """
    with open(file_path, 'r') as f:
        metadata = json.load(f)

    if full_record_metadata['is_published']:
        publication_date = full_record_metadata['metadata']['publication_date']
        full_record_metadata['metadata'] = metadata
        full_record_metadata['metadata']['publication_date'] = publication_date
    else:
        full_record_metadata['metadata'] = metadata

    return full_record_metadata


def create_new_version(url, token, record_id):
    """
    Creates a new version (draft) from a published record (if such a draft does not exist)
    Returns the draft's id
    Raises an HTTPError exception if the request to create the record failed
    """
    request_headers = {
        "Accept": "application/json",
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.post(
        f'{url}/api/records/{record_id}/versions',
        headers=request_headers,
        verify=True)

    response.raise_for_status()

    #  Get record's id
    record_url = response.json()['links']['record']
    record_id = record_url.split('/api/records/')[-1]
    return record_id


def delete_all_links(url, token, id):
    """
    Removes all file links of a draft
    Avoids raising a HTTPError exception when importing file links at a later stage
    """
    checksum_vs_name_for_linked_files = get_checksum_vs_name_for_linked_files(url, token, id)
    for f in checksum_vs_name_for_linked_files:
        delete_link(url, token, id, f['name'])


def get_checksum_vs_name_for_linked_files(url, token, record_id):
    """
    Returns the name and the md5 hash of each linked file in a draft
    Raises an HTTPError exception if the request to get the linked files' metadata failed
    """
    request_headers = {
        "Accept": "application/json",
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(
        f'{url}/api/records/{record_id}/draft/files',
        headers=request_headers,
        verify=True)

    response.raise_for_status()

    #  Return linked files' metadata
    entries = response.json()['entries']

    checksum_vs_name_for_linked_files = [
        {
            'name': entry['key'],
            'checksum': entry['checksum']
        }
        for entry in entries]

    return checksum_vs_name_for_linked_files


def delete_link(url, token, record_id, filename):
    """
    Deletes a file link in a draft
    Raises an HTTPError exception if the request to delete the file link failed
    """
    request_headers = {
        "Accept": "application/json",
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.delete(
        f'{url}/api/records/{record_id}/draft/files/{filename}',
        headers=request_headers,
        verify=True)

    response.raise_for_status()


def import_links(url, token, record_id):
    """
    Imports all file links from a published record into a new version
    This avoids re-uploading files, which would cause duplication on the data store
    Raises an HTTPError exception if the request to import the file links failed
    """
    request_headers = {
        "Accept": "application/json",
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.post(
        f'{url}/api/records/{record_id}/draft/actions/files-import',
        headers=request_headers,
        verify=True)

    response.raise_for_status()


def delete_links_for_updated_files(url, token, id, input_folder_path):
    """
    Removes each link for a file that also appears in the input folder under the same name but storing a different content
    """
    checksum_vs_name_for_linked_files = get_checksum_vs_name_for_linked_files(url, token, id)
    checksum_vs_name_for_input_folder_files = get_checksum_vs_name_for_input_folder_files(input_folder_path)
    updated_files = get_updated_files(checksum_vs_name_for_linked_files, checksum_vs_name_for_input_folder_files)
    for f in updated_files:
        delete_link(url, token, id, f)


def get_checksum_vs_name_for_input_folder_files(input_folder_path):
    """
    Returns the name and the md5 hash of each file in the input folder
    """
    files = [item for item in os.listdir(input_folder_path) if
                 os.path.isfile(os.path.join(input_folder_path, item))]

    checksum_vs_name_for_input_folder_files = []

    for filename in files:
        file_path = os.path.join(input_folder_path, filename)

        with open(file_path, "rb") as f:
            file_hash = hashlib.md5()
            while chunk := f.read(8192):
                file_hash.update(chunk)

        checksum_vs_name_for_input_folder_files.append(
            {
                'name': filename,
                'checksum': 'md5:' + file_hash.hexdigest()
            })

    return checksum_vs_name_for_input_folder_files


def get_updated_files(checksum_vs_name_for_linked_files, checksum_vs_name_for_input_folder_files):
    """
    Returns each linked file that also appears in the input folder under the same name but storing a different content
    """
    updated_files = []

    for linked_file in checksum_vs_name_for_linked_files:
        filename = linked_file['name']
        file_checksum = linked_file['checksum']

        files_in_folder_with_same_name_and_different_content = [ f for f in checksum_vs_name_for_input_folder_files
                         if (f['name'] == filename and f['checksum'] != file_checksum)]

        if len(files_in_folder_with_same_name_and_different_content) == 1:
            # linked file is classified as updated
            updated_files.append(filename)

    return updated_files


def delete_links_for_removed_files(url, token, id, input_folder_path):
    """
    Removes each link for a file that does not appear in the input folder
    """
    checksum_vs_name_for_linked_files = get_checksum_vs_name_for_linked_files(url, token, id)
    checksum_vs_name_for_input_folder_files = get_checksum_vs_name_for_input_folder_files(input_folder_path)
    removed_files = get_removed_files(checksum_vs_name_for_linked_files, checksum_vs_name_for_input_folder_files)
    for f in removed_files:
        delete_link(url, token, id, f)


def get_removed_files(checksum_vs_name_for_linked_files, checksum_vs_name_for_input_folder_files):
    """
    Returns each linked file that does not appear in the input folder
    """
    removed_files = []

    for linked_file in checksum_vs_name_for_linked_files:
        filename = linked_file['name']
        file_checksum = linked_file['checksum']

        files_in_folder_with_same_name_and_same_content = [ f for f in checksum_vs_name_for_input_folder_files
                         if (f['name'] == filename and f['checksum'] == file_checksum)]

        if len(files_in_folder_with_same_name_and_same_content) == 0:
            # linked file is classified as "removed"
            removed_files.append(filename)

    return removed_files


def insert_links_for_added_files(url, token, id, input_metadata_file):
    """
    Uploads each data file in the input folder for which there is currently no link and creates a link
    """
    checksum_vs_name_for_linked_files = get_checksum_vs_name_for_linked_files(url, token, id)
    checksum_vs_name_for_input_folder_files = get_checksum_vs_name_for_input_folder_files(input_folder_path)
    added_files = get_added_files(checksum_vs_name_for_linked_files, checksum_vs_name_for_input_folder_files, input_metadata_file)

    start_file_uploads(url, token, id, added_files)

    for file in added_files:
        file_path = os.path.join(basedir, input_folder, file)
        upload_file_content(url, token, id, file_path, file)
        complete_file_upload(url, token, id, file)


def get_added_files(checksum_vs_name_for_linked_files, checksum_vs_name_for_input_folder_files, metadata_file):
    """
    Returns each data file in the input folder for which there is currently no link
    """
    added_files = [f['name'] for f in checksum_vs_name_for_input_folder_files
                   if (f['name'] != metadata_file) and (f not in checksum_vs_name_for_linked_files)]

    return added_files


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

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

        # Get configuration data
        id = config.get('update_record', 'record_id')
        input_folder = config.get('update_record', 'input_folder')
        input_folder_path = os.path.join(basedir, input_folder)
        metadata_file = config.get('update_record', 'metadata_file')
        metadata_file_path = os.path.join(input_folder_path, metadata_file)
        new_version = config.get('update_record', 'new_version')

        if new_version == 'False':
            # Update metadata of current version
            create_draft_with_same_id(url, token, id)
            current_metadata = get_metadata_of_record(url, token, id)
            metadata = generate_metadata(current_metadata, metadata_file_path)
            update_draft_metadata(url, token, id, metadata)
            publish_draft(url, token, id)

            logger.info(f'Metadata of published record with id={id} updated')

            sys.exit(0)

        # Create a new version (draft) from published record
        id = create_new_version(url, token, id)

        # Update draft's metadata
        current_metadata = get_draft_metadata(url, token, id)
        metadata = generate_metadata(current_metadata, metadata_file_path)
        update_draft_metadata(url, token, id, metadata)

        # Update draft's data file links
        # In this script, we classify data files as:
        # - "kept": linked file that also appears in the input folder (under the same name and storing the same content)
        # - "updated": linked file that also appears in the input folder under the same name but storing a different content
        # - "removed": linked file that does not appear in the input folder
        # - "added": data file in the input folder for which there is currently no link
        delete_all_links(url, token, id)
        import_links(url, token, id)
        delete_links_for_updated_files(url, token, id, input_folder_path)
        delete_removed = config.get('update_record', 'delete_removed')
        if delete_removed == 'True':
            delete_links_for_removed_files(url, token, id, input_folder_path)
        insert_links_for_added_files(url, token, id, metadata_file)

        logger.info(f'Draft with id={id} created')

        # Publish draft depending on user's choice
        publish = config.get('update_record', 'publish')

        if publish == 'True':
            insert_publication_date(url, token, id)
            publish_draft(url, token, id)

            logger.info(f'Draft with id={id} published')

    except Exception as e:
        logger.error('Error occurred: ' + str(e))