from pathlib import Path
import os
from datetime import datetime
from big_map_archive_api_client.client.client_config import ClientConfig
from big_map_archive_api_client.utils import (get_data_files_in_upload_dir,
                                              export_to_json_file)

from finales_api_client.client.client_config import FinalesClientConfig


def create_record(token,
                  metadata_file_path='data/input/metadata.json',
                  upload_dir_path='data/input/upload',
                  publish=True):
    """
    Creates a record on a BIG-MAP Archive and, optionally, publishes it.

    :param token: personal access token for the archive
    :param metadata_file_path: relative path to the metadata file used for creating a record (title, list of authors...)
    :param upload_dir_path: relative path to the directory where files to be uploaded to the archive and to be linked to the newly created record are located
    :param publish: whether the created record (draft) should be published or not
    :return: the id of the created record
    """
    base_dir_path = Path(__file__).absolute().parent.parent.parent
    config_file_path = os.path.join(base_dir_path, 'archive_config.yaml')
    client_config = ClientConfig.load_from_config_file(config_file_path)
    client = client_config.create_client(token)

    # Create draft from input metadata.json
    response = client.post_records(base_dir_path, metadata_file_path)
    record_id = response['id']

    # Upload data files and insert links in the draft's metadata
    filenames = get_data_files_in_upload_dir(base_dir_path, upload_dir_path)
    client.upload_files(record_id, base_dir_path, upload_dir_path, filenames)

    # Publish draft depending on user's choice
    if publish:
        client.insert_publication_date(record_id)
        client.post_publish(record_id)

    return record_id


def retrieve_published_record(token,
                              record_id,
                              export=True,
                              output_file_path='data/output/metadata.json'):
    """
    Retrieves the metadata of a published record on a BIG-MAP Archive and, optionally, saves it to a file.

    :param token: personal access token for the archive
    :param record_id: id of the published record to retrieve
    :param export: whether the obtained metadata of the record should be saved to a file
    :param output_file_path: relative path to the output file
    """
    base_dir_path = Path(__file__).absolute().parent.parent.parent
    config_file_path = os.path.join(base_dir_path, 'archive_config.yaml')
    client_config = ClientConfig.load_from_config_file(config_file_path)
    client = client_config.create_client(token)
    response = client.get_record(record_id)

    if export:
        export_to_json_file(base_dir_path, output_file_path, response)


def retrieve_published_records(token,
                               export=True,
                               output_file_path='data/output/metadata.json',
                               all_versions=False,
                               response_size='1e6'):
    """
    Retrieves the metadata of all published records on a BIG-MAP Archive and, optionally, saves it to a file.

    :param token: personal access token for the archive
    :param export: whether the obtained metadata of the records should be saved to a file
    :param output_file_path: relative path to the output file
    :param all_versions: whether all record versions or only the latest record versions should be harvested
    :param response_size: maximum number of items in a response body
    """
    base_dir_path = Path(__file__).absolute().parent.parent.parent
    config_file_path = os.path.join(base_dir_path, 'archive_config.yaml')
    client_config = ClientConfig.load_from_config_file(config_file_path)
    client = client_config.create_client(token)

    response = client.get_records(all_versions, response_size)

    if export:
        export_to_json_file(base_dir_path, output_file_path, response)


def update_published_record(token,
                            record_id,
                            new_version=True,
                            metadata_file_path='data/input/metadata.json',
                            upload_dir_path='data/input/upload',
                            force=False,
                            publish=True):
    """
    Updates a published record by either modifying the current version or creating a new version and, optionally, publishing it.

    :param token: personal access token for the archive
    :param record_id: id of the published record to update
    :param new_version: whether a new record version should be created
    :param metadata_file_path: relative path to the metadata file used for updating a record (title, list of authors...)
    :param upload_dir_path: relative path to the directory where files to be uploaded to the archive and to be linked to the updated record are located
    :param force: whether the new version should contain file links only for data files in the input folder
    (note that if such a file is already linked to the previous version, the link is simply imported, avoiding an extra upload)
    or the new version may also contain file links imported from the previous version for data files that do not appear in the input folder
    :param publish: whether the new version should be published
    :return: the id of the updated version or the new version
    """
    base_dir_path = Path(__file__).absolute().parent.parent.parent
    config_file_path = os.path.join(base_dir_path, 'archive_config.yaml')
    client_config = ClientConfig.load_from_config_file(config_file_path)
    client = client_config.create_client(token)

    if not new_version:
        # Create a draft (same version) and get the draft's id (same id)
        response = client.post_draft(record_id)
        record_id = response['id']  # Unchanged value for record_id

        # Update the draft's metadata
        client.update_metadata(record_id, base_dir_path, metadata_file_path)

        # Publish the draft (update published record)
        client.post_publish(record_id)
    else:
        # Create a draft (new version) and get its id
        response = client.post_versions(record_id)
        record_id = response['id']  # Modified value for record_id

        # Update the draft's metadata
        client.update_metadata(record_id, base_dir_path, metadata_file_path)

        # Import all file links from the previous version
        filenames = client.get_links(record_id)
        client.delete_links(record_id, filenames)
        client.post_file_import(record_id)

        # Get file links to remove and remove them
        filenames = client.get_links_to_delete(record_id, base_dir_path, upload_dir_path, force)
        client.delete_links(record_id, filenames)

        # Get list of files to upload and upload them
        filenames = client.get_files_to_upload(record_id, base_dir_path, upload_dir_path)
        client.upload_files(record_id, base_dir_path, upload_dir_path, filenames)

        if publish:
            client.insert_publication_date(record_id)
            client.post_publish(record_id)

    return record_id


def back_up_finales_db(finales_username,
                       finales_password,
                       archive_token,
                       capabilities_file_path='data/output/capabilities.json',
                       results_file_path='data/output/results.json'):
    """
    Saves capabilities and results for requests stored in a FINALES database to a BIG-MAP Archive

    :param finales_username: username for an account on the FINALES server
    :param finales_password: password for the account
    :param archive_token: personal access token for the FINALES account on the selected BIG-MAP Archive
    :param capabilities_file_path: relative path to the local file for all capabilities obtained from the FINALES server
    :param results_file_path: to the local file for all results for requests obtained from the FINALES server
    """
    base_dir_path = Path(__file__).absolute().parent.parent.parent
    config_file_path = os.path.join(base_dir_path, 'finales_config.yaml')
    client_config = FinalesClientConfig.load_from_config_file(config_file_path)
    client = client_config.create_client(finales_username, finales_password)

    # Get access token from FINALES server
    response = client.post_authenticate()
    finales_token = response['access_token']

    # Get all capabilities stored in the FINALES database
    response = client.get_capabilities(finales_token)

    # If at least one capability is found, generate a JSON file that contains each found capability
    if len(response) > 0:
        export_to_json_file(base_dir_path, capabilities_file_path, response)

    # Get all results associated with requests stored in the FINALES database
    response = client.get_results_requested(finales_token)

    # If at least one result is found, generate a JSON file that contains each found result
    if len(response) > 0:
        export_to_json_file(base_dir_path, results_file_path, response)

    # Get the ids of the latest version on the archive for FINALES
    config_file_path = os.path.join(base_dir_path, 'archive_config.yaml')
    client_config = ClientConfig.load_from_config_file(config_file_path)
    client = client_config.create_client(archive_token)
    latest_versions = client.get_latest_versions()
    number_of_latest_versions = len(latest_versions)

    # Only zero or one id is allowed
    if number_of_latest_versions == 0:
        # Create a first record version
        record_id = create_record(archive_token,
                                  metadata_file_path='data/input/metadata.json',
                                  upload_dir_path='data/output',
                                  publish=True)
        return record_id

    if number_of_latest_versions == 1:
        id = latest_versions[0]['id']
        is_published = latest_versions[0]['is_published']

        if is_published:
            # Update the current record version
            record_id = update_published_record(archive_token,
                                                id,
                                                new_version=True,
                                                metadata_file_path='data/input/metadata.json',
                                                upload_dir_path='data/output',
                                                force=False,
                                                publish=True)
            return record_id

        # The latest version is in status 'draft'
        client.delete_draft(id)
        record_id = back_up_finales_db(finales_username,
                           finales_password,
                           archive_token,
                           capabilities_file_path,
                           results_file_path)
        return record_id

    raise Exception('Multiple latest versions')


