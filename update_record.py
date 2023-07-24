import os
import logging
import requests
import hashlib
import configparser
from dotenv import load_dotenv

from create_and_share_first_version_of_record import (start_file_uploads,
                                                      upload_file_content,
                                                      complete_file_upload,
                                                      publish_draft,
                                                      set_publication_date)


def create_draft(url, token, shared_record_id):
    """
    Creates a draft, which remains private to its owner, from a shared record, if such a draft does not exist
    Returns the id of the newly created draft
    Raises an HTTPError exception if the request to create the record failed
    """
    request_headers = {
        "Accept": "application/json",
        "Content-type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.post(
        f'{url}/api/records/{shared_record_id}/versions',
        headers=request_headers,
        verify=True)

    response.raise_for_status()

    #  Get record's id
    record_url = response.json()['links']['record']
    record_id = record_url.split('/api/records/')[-1]
    return record_id


def delete_file_links(url, token, record_id, filenames):
    """
    Deletes file links in a draft
    """
    for filename in filenames:
        delete_file_link(url, token, record_id, filename)


def delete_file_link(url, token, record_id, filename):
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


def import_file_links(url, token, record_id):
    """
    Imports the file links from a shared record into a new draft
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


def get_checksum_vs_name_for_linked_files(url, token, record_id):
    """
    Returns the name and the md5 hash of the content for each linked file in a draft
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


def get_checksum_vs_name_for_input_folder_files(input_folder_path):
    """
    Returns the name and the md5 hash of the content for each file in the input folder
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
    Returns list of linked files for which there is a file in the input folder with the same name but a different content
    """
    updated_files = []

    for file in checksum_vs_name_for_linked_files:
        filename = file['name']
        file_checksum = file['checksum']
        input_folder_files_with_same_name_and_different_content = [
            f for f in checksum_vs_name_for_input_folder_files
             if (f['name'] == filename and f['checksum'] != file_checksum)]
        number_of_input_folder_files_with_same_name_and_different_content = len(
            input_folder_files_with_same_name_and_different_content)

        if number_of_input_folder_files_with_same_name_and_different_content > 0:
            updated_files.append(file['name'])

    return updated_files


def get_missing_files(checksum_vs_name_for_linked_files, checksum_vs_name_for_input_folder_files):
    """
    Returns list of linked files for which there is no file in the input folder with the same name and the same content
    """
    missing_files = []

    for file in checksum_vs_name_for_linked_files:
        filename = file['name']
        file_checksum = file['checksum']
        input_folder_files_with_same_name_and_same_content = [
            f for f in checksum_vs_name_for_input_folder_files
             if (f['name'] == filename and f['checksum'] == file_checksum)]
        number_of_input_folder_files_with_same_name_and_same_content = len(
            input_folder_files_with_same_name_and_same_content)

        if number_of_input_folder_files_with_same_name_and_same_content == 0:
            missing_files.append(file['name'])

    return missing_files


def get_extra_files(checksum_vs_name_for_linked_files, checksum_vs_name_for_input_folder_files):
    """
    Returns list of files in the input folder that are not already attached to the draft
    """
    extra_files = [f['name'] for f in checksum_vs_name_for_input_folder_files
                   if f not in checksum_vs_name_for_linked_files]

    return extra_files


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging.INFO)

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

        # Create a draft from a shared record (if such a draft does not exist)
        # Get the id of the newly created draft
        shared_record_id = config.get('create_and_share_new_version_of_record', 'shared_record_id')
        record_id = create_draft(url, token, shared_record_id)
        logger.info(f'Draft with id={record_id} created with success')

        # Delete all file links in the draft (to avoid raising a HTTPError exception when importing file links)
        checksum_vs_name_for_linked_files = get_checksum_vs_name_for_linked_files(url, token, record_id)
        filenames = [f['name'] for f in checksum_vs_name_for_linked_files]
        delete_file_links(url, token, record_id, filenames)
        checksum_vs_name_for_linked_files = get_checksum_vs_name_for_linked_files(url, token, record_id)
        filenames = [f['name'] for f in checksum_vs_name_for_linked_files]
        logger.info(f'Links before import from previous version: {filenames}')

        if checksum_vs_name_for_linked_files:
            raise Exception('File links already present in the draft')

        # Import the file links from the shared record into the new draft
        import_file_links(url, token, record_id)
        checksum_vs_name_for_linked_files = get_checksum_vs_name_for_linked_files(url, token, record_id)
        filenames = [f['name'] for f in checksum_vs_name_for_linked_files]
        logger.info(f'Links after import: {filenames}')

        # Remove each file link for which there is a file with the same name but a different content in the input folder
        input_folder = config.get('create_and_share_new_version_of_record', 'input_folder')
        input_folder_path = os.path.join(basedir, input_folder)
        checksum_vs_name_for_input_folder_files = get_checksum_vs_name_for_input_folder_files(input_folder_path)
        updated_files = get_updated_files(checksum_vs_name_for_linked_files, checksum_vs_name_for_input_folder_files)
        delete_file_links(url, token, record_id, updated_files)
        logger.info(f'Links for updated file(s) {updated_files} removed')

        delete_missing = config.get('create_and_share_new_version_of_record', 'delete_missing')

        if delete_missing == 'True':
            # Remove each file link for which there is no file with the same name and the same content in the input folder
            checksum_vs_name_for_linked_files = get_checksum_vs_name_for_linked_files(url, token, record_id)
            missing_files = get_missing_files(checksum_vs_name_for_linked_files, checksum_vs_name_for_input_folder_files)
            delete_file_links(url, token, record_id, missing_files)
            logger.info(f'Links for missing file(s) {missing_files} removed')

        # Specify the extra files in the input folder to upload and link to the draft
        checksum_vs_name_for_linked_files = get_checksum_vs_name_for_linked_files(url, token, record_id)
        extra_files = get_extra_files(checksum_vs_name_for_linked_files, checksum_vs_name_for_input_folder_files)
        start_file_uploads(url, token, record_id, extra_files)
        logger.info(f'Record\'s metadata updated with extra file(s) {extra_files}')

        # Upload and link extra files
        for file in extra_files:
            file_path = os.path.join(basedir, input_folder, file)
            upload_file_content(url, token, record_id, file_path, file)
            complete_file_upload(url, token, record_id, file)

        publish = config.get('create_and_share_new_version_of_record', 'publish')

        if publish == 'True':
            set_publication_date(url, token, record_id)
            logger.info('Publication date set with success')

            # Share the draft with all archive's users
            publish_draft(url, token, record_id)
            logger.info('Record published with success')

    except requests.exceptions.HTTPError as e:
        logger.error('Error occurred: ' + str(e))

        status_code = e.response.status_code
        reason = e.response.reason

        if status_code == 403 and reason == 'FORBIDDEN':
            logger.error('Check token\'s validity')

    except Exception as e:
        logger.error('Error occurred: ' + str(e))