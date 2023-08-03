import json
import os

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
