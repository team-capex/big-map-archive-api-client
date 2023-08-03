from pathlib import Path
import os
from big_map_archive_api_client.client.client_config import ClientConfig
from big_map_archive_api_client.utils import get_data_filenames, export_to_file

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
    response = client.post_record(base_dir, input_dir, metadata_filename)
    record_id = response['id']
    print(record_id)

    # Upload data files and insert links in the draft's metadata
    filenames = get_data_filenames(base_dir, input_dir, metadata_filename)
    client.post_files(record_id, filenames)

    for filename in filenames:
        client.put_content(record_id, base_dir, input_dir, filename)
        client.post_commit(record_id, filename)

    # Publish draft depending on user's choice
    publish = client_config.publish

    if publish:
        client.insert_publication_date(record_id)
        client.post_publish(record_id)

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

    all_versions = client_config.all_versions
    response_size = client_config.response_size
    client = client_config.create_client()
    response = client.get_records(all_versions, response_size)

    export = client_config.export

    if export:
        output_dir = client_config.output_dir
        output_filename = client_config.output_filename
        export_to_file(base_dir, output_dir, output_filename, response)


def update_record():
    """

    """
    pass

if __name__ == '__main__':
    #create_record()
    #retrieve_record()
    retrieve_records()
    #update_record()
