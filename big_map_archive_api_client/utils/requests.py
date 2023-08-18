import json
import os
import hashlib
from zipfile import (ZipFile, ZIP_DEFLATED)
from datetime import datetime

def generate_full_metadata(metadata_file_path):
    """
    Generates a record's full metadata from a file containing only partial metadata
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

    with open(metadata_file_path, 'r') as f:
        partial_metadata = json.load(f)

    # Insert date and time in the description
    now = datetime.now()
    partial_metadata['description'] += f' This operation was performed on {now.date()} at {now.strftime("%H:%M:%S")}.'

    full_metadata['metadata'] = partial_metadata
    return full_metadata


def export_to_json_file(base_dir_path, output_file_path, data):
    """
    Exports data to a JSON file
    """
    output_file_path = os.path.join(base_dir_path, output_file_path)

    with open(output_file_path, "w") as f:
        json.dump(data, f, indent=4, sort_keys=True)


def change_metadata(full_record_metadata, base_dir_path, metadata_file_path):
    """
    Updates the value of the 'metadata' key in a full record's metadata using a file's content
    Re-inserts the publication date if the record is published
    """
    file_path = os.path.join(base_dir_path, metadata_file_path)
    with open(file_path, 'r') as f:
        partial_metadata = json.load(f)

    # Insert date and time in the description
    now = datetime.now()
    partial_metadata['description'] += f' This operation was performed on {now.date()} at {now.strftime("%H:%M:%S")}.'

    # Insert keywords extracted from results (e.g., values for 'quantity' and 'method') if not already in 'keywords'
    #keywords = extract_keywords(partial_metadata)
    #keyword_candidates

    if full_record_metadata['is_published']:
        publication_date = full_record_metadata['metadata']['publication_date']
        full_record_metadata['metadata'] = partial_metadata
        full_record_metadata['metadata']['publication_date'] = publication_date
    else:
        full_record_metadata['metadata'] = partial_metadata

    return full_record_metadata


def get_name_to_checksum_for_files_in_upload_dir(base_dir_path, upload_dir_path):
    """
    Gets the names and md5 hashes of all files in the upload folder
    """
    upload_dir_path = os.path.join(base_dir_path, upload_dir_path)

    filenames = [
        f for f in os.listdir(upload_dir_path)
        if os.path.isfile(os.path.join(upload_dir_path, f))
    ]

    files_in_upload_dir = []

    for filename in filenames:
        file_path = os.path.join(upload_dir_path, filename)

        with open(file_path, "rb") as f:
            file_hash = hashlib.md5()
            while chunk := f.read(8192):
                file_hash.update(chunk)

        files_in_upload_dir.append(
            {
                'name': filename,
                'checksum': 'md5:' + file_hash.hexdigest()
            })

    return files_in_upload_dir


def get_data_files_in_upload_dir(base_dir_path, upload_dir_path):
    """
    Gets the names of the files in the upload folder
    """
    files = get_name_to_checksum_for_files_in_upload_dir(base_dir_path, upload_dir_path)
    filenames = [f['name'] for f in files]
    return filenames

def export_capabilities_to_zip_file(base_dir_path, output_dir, filename, capabilities):
    """
    Puts each capability in the list in its own JSON file
    Creates a ZIP file that contains all of these JSON files in the output folder
    """
    output_file_path = os.path.join(base_dir_path, output_dir, filename)
    filenames = []

    for c in capabilities:
        quantity = c['quantity']
        quantity = quantity.strip().replace(" ", "_") # Remove leading and trailing spaces and replace remaining spaces by _
        method = c['method']
        method = method.strip() # remove leading and trailing spaces
        method = method.strip().replace(" ", "_")
        file = f'{quantity}_{method}.json'
        export_to_json_file(base_dir_path, output_dir, file, c)
        filenames.append(file)

    with ZipFile(output_file_path, 'w') as zf:
        for file in filenames:
            file_path = os.path.join(base_dir_path, output_dir, file)
            zf.write(file_path, file, compress_type=ZIP_DEFLATED)
            os.remove(file_path)

def export_results_to_zip_file(base_dir, output_dir, filename, results):
    """
    Puts each result in the list in its own JSON file
    Creates a ZIP file that contains all of these JSON files in the output folder
    """
    output_file_path = os.path.join(base_dir, output_dir, filename)
    filenames = []

    for r in results:
        quantity = c['quantity']
        quantity = quantity.strip().replace(" ", "_") # Remove leading and trailing spaces and replace remaining spaces by _
        method = c['method']
        method = method.strip() # remove leading and trailing spaces
        method = method.strip().replace(" ", "_")
        file = f'{quantity}_{method}.json'
        export_to_json_file(base_dir, output_dir, file, c)
        filenames.append(file)

    with ZipFile(output_file_path, 'w') as zf:
        for file in filenames:
            file_path = os.path.join(base_dir, output_dir, file)
            zf.write(file_path, file, compress_type=ZIP_DEFLATED)
            os.remove(file_path)




