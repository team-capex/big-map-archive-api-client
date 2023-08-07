from pathlib import Path
import os
from big_map_archive_api_client.client.client_config import ClientConfig
from big_map_archive_api_client.utils import (get_input_folder_files,
                                              export_to_file)

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
        export_to_file(base_dir, output_dir, output_filename, response)

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
        export_to_file(base_dir, output_dir, output_filename, response)


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


if __name__ == '__main__':
    record_id = create_record()
    #retrieve_record()
    #retrieve_records()
    #record_id = update_record()
    print(record_id)
