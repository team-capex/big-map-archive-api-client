from pathlib import Path
import os
from big_map_archive_api_client.client.client_config import ClientConfig
from big_map_archive_api_client.utils import (get_input_folder_files,
                                              export_to_json_file,
                                              export_capabilities_to_zip_file,
                                              get_tenant_uuids,
                                              get_token_for_archive_account)

from finales_api_client.client.client_config import FinalesClientConfig


def create_a_record(token,
                    input_dir='data/input',
                    metadata_filename='metadata.json',
                    publish=True):
    """
    Creates a record on a BIG-MAP Archive and, optionally, publishes it.

    :param token: personal access token for the archive
    :param input_dir: directory where input files (metadata file and data files) are located
    :param metadata_filename: name of the metadata file used for creating a record
    :param publish: whether the created record (draft) should be published or not
    :return: the id of the created record
    """
    base_dir = Path(__file__).absolute().parent.parent.parent
    config_file_path = os.path.join(base_dir, 'archive_config.yaml')
    client_config = ClientConfig.load_from_config_file(config_file_path)
    client = client_config.create_client(token)

    # Create draft from input metadata.json
    response = client.post_records(base_dir, input_dir, metadata_filename)
    record_id = response['id']

    # Upload data files and insert links in the draft's metadata
    filenames = get_input_folder_files(base_dir, input_dir, metadata_filename)
    client.upload_files(record_id, base_dir, input_dir, filenames)

    # Publish draft depending on user's choice
    if publish:
        client.insert_publication_date(record_id)
        client.post_publish(record_id)

    return record_id


def retrieve_a_published_record(token,
                                record_id,
                                export=True,
                                output_dir='data/output',
                                output_filename='metadata.json'):
    """
    Retrieves the metadata of a published record on a BIG-MAP Archive and, optionally, saves it to a file.

    :param token: personal access token for the archive
    :param record_id: id of the published record to retrieve
    :param export: whether the obtained metadata of the record should be saved to a file
    :param output_dir: directory where the output file is located
    :param output_filename: name of the output file
    """
    base_dir = Path(__file__).absolute().parent.parent.parent
    config_file_path = os.path.join(base_dir, 'archive_config.yaml')
    client_config = ClientConfig.load_from_config_file(config_file_path)
    client = client_config.create_client(token)
    response = client.get_record(record_id)

    if export:
        export_to_json_file(base_dir, output_dir, output_filename, response)


def retrieve_all_published_records(token,
                                   export=True,
                                   output_dir='data/output',
                                   output_filename='metadata.json',
                                   all_versions=False,
                                   response_size='1e6'):
    """
    Retrieves the metadata of all published records on a BIG-MAP Archive and, optionally, saves it to a file.

    :param token: personal access token for the archive
    :param export: whether the obtained metadata of the records should be saved to a file
    :param output_dir: directory where the output file is located
    :param output_filename: name of the output file
    :param all_versions: whether all record versions or only the latest record versions should be harvested
    :param response_size: maximum number of items in a response body
    """
    base_dir = Path(__file__).absolute().parent.parent.parent
    config_file_path = os.path.join(base_dir, 'archive_config.yaml')
    client_config = ClientConfig.load_from_config_file(config_file_path)
    client = client_config.create_client(token)

    response = client.get_records(all_versions, response_size)

    if export:
        export_to_json_file(base_dir, output_dir, output_filename, response)


def update_a_published_record(token,
                              record_id,
                              new_version=True,
                              input_dir='data/input',
                              metadata_filename='metadata.json',
                              force=True,
                              publish=True):
    """
    Updates a published record by either modifying the current version or creating a new version and, optionally, publishing it.

    :param token: personal access token for the archive
    :param record_id: id of the published record to update
    :param new_version: whether a new record version should be created
    :param input_dir: directory where input files (metadata file and data files) are located
    :param metadata_filename: name of the metadata file
    :param force: whether the new version should contain file links only for data files in the input folder
    (note that if such a file is already linked to the previous version, the link is simply imported, avoiding an extra upload)
    or the new version may also contain file links imported from the previous version for data files that do not appear in the input folder
    :param publish: whether the new version should be published
    :return: the id of the updated version or the new version
    """
    base_dir = Path(__file__).absolute().parent.parent.parent
    config_file_path = os.path.join(base_dir, 'archive_config.yaml')
    client_config = ClientConfig.load_from_config_file(config_file_path)
    client = client_config.create_client(token)

    if not new_version:
        # Create a draft (same version) and get the draft's id (same id)
        response = client.post_draft(record_id)
        record_id = response['id'] # Unchanged value for record_id

        # Update the draft's metadata
        client.update_metadata(record_id, base_dir, input_dir, metadata_filename)

        # Publish the draft (update published record)
        client.post_publish(record_id)
    else:
        # Create a draft (new version) and get its id
        response = client.post_versions(record_id)
        record_id = response['id'] # Modified value for record_id

        # Update the draft's metadata
        client.update_metadata(record_id, base_dir, input_dir, metadata_filename)

        # Import all file links from the previous version
        filenames = client.get_links(record_id)
        client.delete_links(record_id, filenames)
        client.post_file_import(record_id)

        # Get file links to remove and remove them
        filenames = client.get_links_to_delete(record_id, base_dir, input_dir, metadata_filename, force)
        client.delete_links(record_id, filenames)

        # Get list of files to upload and upload them
        filenames = client.get_files_to_upload(record_id, base_dir, input_dir, metadata_filename)
        client.upload_files(record_id, base_dir, input_dir, filenames)

        if publish:
            client.insert_publication_date(record_id)
            client.post_publish(record_id)

    return record_id

"""
output_dir: output
capabilities_filename: capabilities.zip
results_requested_filename: results_requested.json
archives_for_tenants_filename: archives_for_finales_tenants.json # Accounts of tenants on archives
archive_domain_name: big-map-archive-demo.materialscloud.org
"""


def back_up_finales_db(username,
                       password,
                       output_dir='data/output',
                       capabilities_filename='capabilities.zip',
                       archive_domain_name=''):
    """
    Saves capabilities and results for requests stored in a FINALES database to a BIG-MAP Archive

    :param username: username for an account on FINALES
    :param password: password for the account
    :param output_dir: directory where the output file is located
    :param capabilities_filename: name of the file that contains all the capabilities as JSON files
    """
    base_dir = Path(__file__).absolute().parent.parent.parent
    config_file_path = os.path.join(base_dir, 'finales_config.yaml')
    client_config = FinalesClientConfig.load_from_config_file(config_file_path)
    client = client_config.create_client(username, password)

    # Get access token from FINALES server
    response = client.post_authenticate()
    token = response['access_token']

    # Get all capabilities stored in the FINALES database
    response = client.get_capabilities(token)

    # If at least one capability was found, generate a ZIP file that contains each found capability as a JSON file
    if len(response) > 0:
        export_capabilities_to_zip_file(base_dir, output_dir, capabilities_filename, response)

    # Get all results associated with requests stored in the FINALES database
    response = client.get_results_requested(token)

    # TODO: remove after testing
    response = [
        {'uuid': 'd7b4bda2-4eef-40b3-a2f4-528648360030',
         'ctime': '2023-08-14T09:13:50',
         'status': 'original',
         'result': {
             'data': {
                 'success': True,
                 'reservation_id': 'no-apply'},
             'quantity': 'cycling_channel',
             'method': ['service'],
             'parameters': {
                 'service': {
                     'number_required_channels': 5,
                     'cycling_protocol': 'normal',
                     'number_cycles': 100}
             },
             'tenant_uuid': 'ad771155-97b9-46e9-92bd-5e9b2c378a0a',
             'request_uuid': 'c88a808e-a417-416a-b441-6250505680de'}
        },
        {'uuid': 'r7b4bda2-4eef-40b3-a2f4-528648360031',
         'ctime': '2023-08-14T09:13:50',
         'status': 'original',
         'result': {
             'data': {
                 'success': True,
                 'reservation_id': 'no-apply'},
             'quantity': 'cycling_channel',
             'method': ['service'],
             'parameters': {
                 'service': {
                     'number_required_channels': 5,
                     'cycling_protocol': 'normal',
                     'number_cycles': 100}
             },
             'tenant_uuid': 'ad771155-97b9-46e9-92bd-5e9b2c378a0a',
             'request_uuid': 'h99a808e-a417-416a-b441-6250505680de'}
        },
        {'uuid': 'c289592b-0603-4b88-b0ab-675f4624da9a',
         'ctime': '2023-08-14T10:20:11',
         'status': 'original',
         'result': {
             'data': {
                 'success': True,
                 'reservation_id': 'no-apply'},
             'quantity': 'cycling_channel',
             'method': ['service'],
             'parameters': {
                 'service': {
                     'number_required_channels': 5,
                     'cycling_protocol': 'normal',
                     'number_cycles': 100}
             },
             'tenant_uuid': 'e0262ca0-c546-4e9a-a4a1-5ea6cb9b1e13',
             'request_uuid': '1cc3f8ba-b953-408e-af33-d859a252b85d'}
         },
    ]

    # Determine what results have already been published to the archive
    # This will be done tenant by tenant
    tenant_uuids = get_tenant_uuids(response)

    # latest_version_ids = [{tenant_uuid:.., latest_version_id:...}, {tenant_uuid:.., latest_version_id:...}, {tenant_uuid:.., latest_version_id:...}...]
    latest_version_ids = []

    for tenant_uuid in tenant_uuids:
        # Get a personal access token for the tenant
        config_file_path = os.path.join(base_dir, 'archive_config.yaml')
        client_config = ClientConfig.load_from_config_file(config_file_path)
        domain_name = client_config.domain_name
        token = get_token_for_archive_account(base_dir,
                                              'archive_finales_config.yaml',
                                              tenant_uuid,
                                              domain_name) # TODO Improve; do not store tokens in config files

        # Retrieve the linked files for the latest published version of the tenant (assuming that there is only one)
        client = client_config.create_client(token)

        all_versions = False
        response_size = int(float('1e6'))
        response = client.get_user_records(all_versions, response_size)

        if response['hits']['total'] == 0:
            latest_version_ids.append({
                'tenant_uuid': tenant_uuid,
                'latest_version_id': None
            })
        elif response['hits']['total'] == 1:
            # TODO: get latest version id
            pass
        else:
            raise Exception(f'Multiple latest record versions for the tenant with uuid {tenant_uuid} on the archive {archive_domain_name}')

    print('')


if __name__ == '__main__':
    #token = ''
    #record_id = create_a_record(token)

    #record_id = 'jtk7g-95k79'
    #retrieve_a_published_record(token, record_id)

    #retrieve_all_published_records(token, all_versions=True)

    #record_id = update_a_published_record(token, record_id, new_version=True, force=False)

    username = ''
    password = ''
    record_id = back_up_finales_db(username, password)

    #print(record_id)