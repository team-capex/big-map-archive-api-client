from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import datetime
from big_map_archive_api_client.client.client_config import ClientConfig
from big_map_archive_api_client.utils import (get_data_files_in_upload_dir,
                                              export_to_json_file,
                                              get_title_from_metadata_file,
                                              create_or_recreate_directory)

from finales_api_client.client.client_config import FinalesClientConfig


def create_record(token,
                  metadata_file_path='data/input/metadata.yaml',
                  upload_dir_path='data/input/upload',
                  additional_description='',
                  publish=True):
    """
    Creates a record on a BIG-MAP Archive and, optionally, publishes it.

    :param token: personal access token for the archive
    :param metadata_file_path: relative path to the metadata file used for creating a record (title, list of authors...)
    :param upload_dir_path: relative path to the directory where files to be uploaded to the archive and to be linked to the newly created record are located
    :param additional_description: text that will be appended to the description taken from the metadata file
    :param publish: whether the created record (draft) should be published or not
    :return: the id of the created record
    """
    base_dir_path = Path(__file__).absolute().parent.parent.parent
    config_file_path = os.path.join(base_dir_path, 'archive_config.yaml')
    client_config = ClientConfig.load_from_config_file(config_file_path)
    client = client_config.create_client(token)

    # Create draft from input metadata.yaml
    response = client.post_records(base_dir_path, metadata_file_path, additional_description)
    record_id = response['id']

    # Upload data files and insert links in the draft's metadata
    filenames = get_data_files_in_upload_dir(base_dir_path, upload_dir_path)
    client.upload_files(record_id, base_dir_path, upload_dir_path, filenames)

    # Publish draft depending on user's choice
    if publish:
        client.insert_publication_date(record_id)
        client.post_publish(record_id)

    return record_id


def get_metadata_of_published_record(token,
                                     record_id,
                                     export=True,
                                     metadata_file_path='data/output/metadata.json'):
    """
    Retrieves the metadata of a published record on a BIG-MAP Archive and optionally saves it to a file.

    :param token: personal access token for the archive
    :param record_id: id of the targeted published record
    :param export: whether the obtained metadata of the record should be saved to a file
    :param metadata_file_path: relative path to the obtained record's metadata
    :return: the obtained record's metadata
    """
    base_dir_path = Path(__file__).absolute().parent.parent.parent
    output_dir_path = os.path.dirname(metadata_file_path)
    create_or_recreate_directory(base_dir_path, output_dir_path)

    # Create an ArchiveAPIClient object to interact with the archive
    config_file_path = os.path.join(base_dir_path, 'archive_config.yaml')
    client_config = ClientConfig.load_from_config_file(config_file_path)
    client = client_config.create_client(token)

    response = client.get_record(record_id)

    if export:
        export_to_json_file(base_dir_path, metadata_file_path, response)

    return response


def get_metadata_of_published_records(token,
                                      export=True,
                                      metadata_file_path='data/output/metadata.json',
                                      all_versions=False,
                                      response_size='1e6'):
    """
    Retrieves the metadata of all published records on a BIG-MAP Archive and, optionally, saves it to a file.

    :param token: personal access token for the archive
    :param export: whether the obtained metadata of the records should be saved to a file
    :param metadata_file_path: relative path to the obtained records' metadata
    :param all_versions: whether all published versions of each entry should be considered or only the latest published version
    :param response_size: maximum number of items in a response body
    :return: the obtained records' metadata
    """
    # Create/re-create the output folder
    base_dir_path = Path(__file__).absolute().parent.parent.parent
    output_dir_path = os.path.dirname(metadata_file_path)
    create_or_recreate_directory(base_dir_path, output_dir_path)

    # Create an ArchiveAPIClient object to intereact with the archive
    config_file_path = os.path.join(base_dir_path, 'archive_config.yaml')
    client_config = ClientConfig.load_from_config_file(config_file_path)
    client = client_config.create_client(token)

    response = client.get_records(all_versions, response_size)

    if export:
        export_to_json_file(base_dir_path, metadata_file_path, response)

    return response


def update_published_record(token,
                            record_id,
                            force=True,
                            metadata_file_path='data/input/metadata.yaml',
                            upload_dir_path='data/input/upload',
                            additional_description='',
                            discard=True,
                            publish=False):
    """
    Updates an entry by either modifying its latest version, which should be published, or creating a new version and optionally publishing it.
    Raises an exception if the latest version does not exist or is not published

    :param token: personal access token for the archive
    :param record_id: id of the latest version of the entry
    :param force: whether a new version should be created - for 'force=False', only the metadata can be modified
    :param metadata_file_path: relative path to the metadata file (title, list of authors...)
    :param upload_dir_path: relative path to the directory where data files to be linked to the new version are located
    :param discard: whether file links from the previous version should be discarded (i.e., not imported) when considering the new version, with the exception of the links for data files currently in the upload folder
    :param publish: whether the new version should be published or not
    :return: the id of the updated version or the new version
    """
    base_dir_path = Path(__file__).absolute().parent.parent.parent
    config_file_path = os.path.join(base_dir_path, 'archive_config.yaml')
    client_config = ClientConfig.load_from_config_file(config_file_path)
    client = client_config.create_client(token)

    if not force:
        # Update the latest version
        # 1. Create a draft (same version) and get the draft's id (same id)
        response = client.post_draft(record_id)
        record_id = response['id']  # Unchanged value for record_id

        # 2. Update the draft's metadata
        client.update_metadata(record_id, base_dir_path, metadata_file_path, additional_description)

        # 3. Publish the draft (update published record)
        client.post_publish(record_id)
    else:
        # Create and publish a new version
        # 1. Create a draft (new version) and get its id
        response = client.post_versions(record_id)
        record_id = response['id']  # Modified value for record_id

        # 2. Update the draft's metadata
        client.update_metadata(record_id, base_dir_path, metadata_file_path, additional_description)

        # 3. Import all file links from the previous version after cleaning
        filenames = client.get_links(record_id)
        client.delete_links(record_id, filenames)
        client.post_file_import(record_id)

        # 4. Get a list of all file links to be removed and remove them
        filenames = client.get_links_to_delete(record_id, base_dir_path, upload_dir_path, discard)
        client.delete_links(record_id, filenames)

        # 5. Get a list of files to upload and upload them
        filenames = client.get_files_to_upload(record_id, base_dir_path, upload_dir_path)
        client.upload_files(record_id, base_dir_path, upload_dir_path, filenames)

        # 6. Publish (optional)
        if publish:
            client.insert_publication_date(record_id)
            client.post_publish(record_id)

    return record_id


def back_up_finales_db(finales_username,
                       finales_password,
                       archive_token,
                       metadata_file_path='data/input/metadata.yaml',
                       record_id=None,
                       capabilities_filename='capabilities.json',
                       requests_filename='requests.json',
                       results_filename='results_for_requests.json',
                       publish=True):
    """
    Performs a partial back-up of a FINALES database by creating a new version in a BIG-MAP Archive and optionally publishing it. Backed-up data includes:
      - all capabilities
      - all requests
      - all results for requests.

    :param finales_username: username for an account on the FINALES server
    :param finales_password: password for the account
    :param archive_token: personal access token for the FINALES account on the selected BIG-MAP Archive
    :param metadata_file_path: relative path to the metadata file used for creating/updating an entry (title, list of authors...)
    :param record_id: id of the version to update - if not provided, a new entry may be created
    :param capabilities_filename: name of the file where capabilities obtained from the FINALES database are stored
    :param requests_filename: name of the file where requests obtained from the FINALES database are stored
    :param results_filename: name of the file where results for requests obtained from the FINALES database are stored
    :param publish: whether the new version should be published or not
    :return: the id of the version
    """
    # Create/re-create folder where files are stored temporarily
    base_dir_path = Path(__file__).absolute().parent.parent.parent
    temp_dir_path = 'data/temp'
    create_or_recreate_directory(base_dir_path, temp_dir_path)

    # Create a FinalesAPIClient object to interact with FINALES server
    config_file_path = os.path.join(base_dir_path, 'finales_config.yaml')
    client_config = FinalesClientConfig.load_from_config_file(config_file_path)
    client = client_config.create_client(finales_username, finales_password)

    # Get access token from FINALES server
    response = client.post_authenticate()
    finales_token = response['access_token']

    # Get data from the FINALES database
    # 1. Capabilities
    response = client.get_capabilities(finales_token)
    capabilities_file_path = os.path.join(base_dir_path, temp_dir_path, capabilities_filename)
    export_to_json_file(base_dir_path, capabilities_file_path, response)

    # 2. Requests
    response = client.get_all_requests(finales_token)
    requests_file_path = os.path.join(base_dir_path, temp_dir_path, requests_filename)
    export_to_json_file(base_dir_path, requests_file_path, response)

    # 3. Results for requests
    response = client.get_results_requested(finales_token)
    results_file_path = os.path.join(base_dir_path, temp_dir_path, results_filename)
    export_to_json_file(base_dir_path, results_file_path, response)

    # Create an ArchiveAPIClient object to interact with the archive
    config_file_path = os.path.join(base_dir_path, 'archive_config.yaml')
    client_config = ClientConfig.load_from_config_file(config_file_path)
    client = client_config.create_client(archive_token)

    title = get_title_from_metadata_file(base_dir_path, metadata_file_path)

    now = datetime.now()
    additional_description = f' The back-up was performed on {now.strftime("%B %-d, %Y")} at {now.strftime("%H:%M")}.'

    # If record_id is not provided (None is a falsy value)
    if (not record_id):
        # Count the number of published records owned by the user that have the same title as that in the provided metadata file
        record_ids = client.get_published_user_records_with_given_title(title)
        nb_records = len(record_ids)

        # If the user does not own any such record, create a new entry in the archive
        if nb_records == 0:
            record_id = create_record(archive_token,
                                      metadata_file_path=metadata_file_path,
                                      upload_dir_path=temp_dir_path,
                                      additional_description=additional_description,
                                      publish=publish)

            return record_id

        # User may have forgotten to set record_id to already existing entry version
        raise Exception(f'You already own a published record (e.g., {record_ids[0]}) with the same title as your provided title "{title}". '
                        f'Are you sure that you prefer creating a new entry rather than updating an existing one?')

    # If record_id is provided
    client.exists_and_is_published(record_id)

    # Extract the title of the published record
    record_metadata = get_metadata_of_published_record(archive_token, record_id, export=False)
    record_title = record_metadata['metadata']['title']

    # Compare the title of the published record with the title in the provided metadata file
    if record_title == title:
        # Update the entry by creating a new version
        record_id = update_published_record(archive_token,
                                            record_id,
                                            force=True,
                                            metadata_file_path=metadata_file_path,
                                            upload_dir_path=temp_dir_path,
                                            discard=True,
                                            publish=True)
        return record_id

    # User may have set record_id to a wrong value
    raise Exception(f'Your provided title "{title}" differs from the title of the record {record_id}. '
          f'Are you sure that you prefer updating the existing entry rather than creating a new one?')
