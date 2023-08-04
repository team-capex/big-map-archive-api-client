import json
import os
import hashlib

def generate_full_metadata(provided_metadata_file_path):
    """
    Generates a record's metadata from a file
    """
    full_metadata = {
            "access": {
                "files": "public",
                "record": "public",
                "status": "open"
            },
            "files": {
                "enabled": True
            }
    }

    with open(provided_metadata_file_path, 'r') as f:
        provided_metadata = json.load(f)

    full_metadata['metadata'] = provided_metadata
    return full_metadata


def get_data_filenames(base_dir, input_dir, metadata_filename):
    """
    Returns the filenames in the input folder, ignoring
    - the metadata file
    """
    input_dir_path = os.path.join(base_dir, input_dir)

    data_filenames = [
        f for f in os.listdir(input_dir_path)
        if os.path.isfile(os.path.join(input_dir_path, f)) and f != metadata_filename
    ]

    return data_filenames


def export_to_file(base_dir, output_dir, output_filename, data):
    """
    Exports data to file
    """
    #TODO Create output_dir if it does not exist
    #TODO Overwrite content of output file instead of appending

    file_path = os.path.join(base_dir, output_dir, output_filename)

    with open(file_path, "a") as f:
        json.dump(data, f, indent=4, sort_keys=True)


def change_metadata(full_record_metadata, base_dir, input_dir, metadata_filename):
    """
    Updates the value of the 'metadata' key in a full record's metadata using a file's content
    Re-inserts the publication date if the record is published
    """
    file_path = os.path.join(base_dir, input_dir, metadata_filename)
    with open(file_path, 'r') as f:
        metadata = json.load(f)

    if full_record_metadata['is_published']:
        publication_date = full_record_metadata['metadata']['publication_date']
        full_record_metadata['metadata'] = metadata
        full_record_metadata['metadata']['publication_date'] = publication_date
    else:
        full_record_metadata['metadata'] = metadata

    return full_record_metadata

def get_name_to_checksum_for_input_folder_files(base_dir, input_dir):
    """
    Gets the names and md5 hashes of all files in the input folder
    """
    input_folder_path = os.path.join(base_dir, input_dir)
    filenames = [item for item in os.listdir(input_folder_path)
             if os.path.isfile(os.path.join(input_folder_path, item))]

    key_to_checksum_for_input_folder_files = []

    for filename in filenames:
        file_path = os.path.join(input_folder_path, filename)

        with open(file_path, "rb") as f:
            file_hash = hashlib.md5()
            while chunk := f.read(8192):
                file_hash.update(chunk)

        key_to_checksum_for_input_folder_files.append(
            {
                'name': filename,
                'checksum': 'md5:' + file_hash.hexdigest()
            })

    return key_to_checksum_for_input_folder_files
