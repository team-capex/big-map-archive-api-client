from pathlib import Path
import os
from big_map_archive_api_client.client.client_config import ClientConfig
from big_map_archive_api_client.utils import (get_input_folder_files,
                                              export_to_json_file,
                                              export_capabilities_to_zip_file,
                                              group_results_by_tenant,
                                              get_archive_token)
from finales_api_client.client.client_config import FinalesClientConfig
from itertools import groupby


def create_record():
    """
    Creates a record and publishes it
    """
    base_dir = Path(__file__).absolute().parent.parent.parent
    config_file_path = os.path.join(base_dir, 'config.yaml')
    client_config = ClientConfig.load_from_config_file(config_file_path)
    client = client_config.create_client()

    # Create draft from input metadata.json
    input_dir = client_config.input_dir
    metadata_filename = client_config.metadata_filename
    response = client.post_records(base_dir, input_dir, metadata_filename)
    record_id = response['id']

    # Upload data files and insert links in the draft's metadata
    filenames = get_input_folder_files(base_dir, input_dir, metadata_filename)
    client.upload_files(record_id, base_dir, input_dir, filenames)

    # Publish draft depending on user's choice
    publish = client_config.publish

    if publish:
        client.insert_publication_date(record_id)
        client.post_publish(record_id)

    return record_id


def retrieve_record():
    """
    Retrieves a published record
    """
    base_dir = Path(__file__).absolute().parent.parent.parent
    config_file_path = os.path.join(base_dir, 'config.yaml')
    client_config = ClientConfig.load_from_config_file(config_file_path)
    client = client_config.create_client()

    record_id = client_config.requested_record_id
    response = client.get_record(record_id)

    export = client_config.export

    if export:
        output_dir = client_config.output_dir
        output_filename = client_config.output_filename
        export_to_json_file(base_dir, output_dir, output_filename, response)


def retrieve_records():
    """
    Retrieves published records
    """
    base_dir = Path(__file__).absolute().parent.parent.parent
    config_file_path = os.path.join(base_dir, 'config.yaml')
    client_config = ClientConfig.load_from_config_file(config_file_path)
    client = client_config.create_client()

    all_versions = client_config.all_versions
    response_size = client_config.response_size
    response = client.get_records(all_versions, response_size)

    export = client_config.export

    if export:
        output_dir = client_config.output_dir
        output_filename = client_config.output_filename
        export_to_json_file(base_dir, output_dir, output_filename, response)




def update_record():
    """
    Updates a published record by either modifying the current version or creating a new version
    """
    base_dir = Path(__file__).absolute().parent.parent.parent
    config_file_path = os.path.join(base_dir, 'config.yaml')
    client_config = ClientConfig.load_from_config_file(config_file_path)
    client = client_config.create_client()

    published_record_id = client_config.published_record_id
    same_version = client_config.same_version
    input_dir = client_config.input_dir
    metadata_filename = client_config.metadata_filename

    if same_version:
        # Create a draft (same version) and get the draft's id (same id)
        response = client.post_draft(published_record_id)
        record_id = response['id']

        # Update the draft's metadata
        client.update_metadata(record_id, base_dir, input_dir, metadata_filename)

        # Publish the draft (update published record)
        client.post_publish(record_id)
    else:
        # Create a draft (new version) and get its id
        response = client.post_versions(published_record_id)
        record_id = response['id']

        # Update the draft's metadata
        client.update_metadata(record_id, base_dir, input_dir, metadata_filename)

        # Import all file links from the previous version
        filenames = client.get_links(record_id)
        client.delete_links(record_id, filenames)
        client.post_file_import(record_id)

        # Get file links to remove and remove them
        force = client_config.force
        filenames = client.get_links_to_delete(record_id, base_dir, input_dir, metadata_filename, force)
        client.delete_links(record_id, filenames)

        # Get list of files to upload and upload them
        filenames = client.get_files_to_upload(record_id, base_dir, input_dir, metadata_filename)
        client.upload_files(record_id, base_dir, input_dir, filenames)

        # Publish draft depending on user's choice
        publish = client_config.publish

        if publish:
            client.insert_publication_date(record_id)
            client.post_publish(record_id)

        return record_id


def back_up_finales_db():
    """

    """
    base_dir = Path(__file__).absolute().parent.parent.parent
    config_file_path = os.path.join(base_dir, 'finales_config.yaml')
    client_config = FinalesClientConfig.load_from_config_file(config_file_path)
    username = client_config.username
    password = client_config.password
    output_dir = client_config.output_dir
    capabilities_filename = client_config.capabilities_filename
    results_requested_filename = client_config.results_requested_filename
    archives_for_tenants_filename = client_config.archives_for_tenants_filename
    archive_domain_name = client_config.archive_domain_name

    client = client_config.create_client()

    # Get access token from server
    response = client.post_authenticate(username, password)
    token = response['access_token']

    # Get capabilities (i.e., JSON schemas used for request bodies and response bodies)
    query_string = 'currently_available=false'
    response = client.get_capabilities(token, query_string)

    # Generate a zip file that contains all capabilities as json files
    # This zip file is ready to be uploaded to the archive
    if len(response) > 0:
        export_capabilities_to_zip_file(base_dir, output_dir, capabilities_filename, response)
    else:
        print('No capabilities found in the FINALES database.')
        exit(0)

    # Get calculation/measurement results posted by the tenants to Finales
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

    # Group results by tenant_uuid
    lists_of_results = group_results_by_tenant(base_dir, output_dir, response)

    # Determine results already saved to the archive
    tenant_uuids = [lor[0]['tenant_uuid'] for lor in lists_of_results]

    for tenant_uuid in tenant_uuids:
        # Get corresponding archive token from file
        archive_token = get_archive_token(base_dir, archives_for_tenants_filename, tenant_uuid, archive_domain_name)

        # Retrieves the metadata for all records(drafts and published records) of a user
        archive_config_file_path = os.path.join(base_dir, 'config.yaml')
        archive_client_config = ClientConfig.load_from_config_file(archive_config_file_path)
        archive_client = archive_client_config.create_client()

        archive_client_config.domain_name = archive_domain_name
        archive_client_config.token = archive_token
        archive_client_config.all_versions = False

        response = archive_client.get_user_records(
            archive_client_config.all_versions,
            archive_client_config.response_size)


if __name__ == '__main__':
    # record_id = create_record()
    # retrieve_record()
    # retrieve_records()
    # record_id = update_record()
    record_id = back_up_finales_db()
    print(record_id)
