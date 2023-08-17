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

# def get_tenant_uuids(results_for_requests):
#     """
#     Extracts the tenant uuids from the obtained list of results [{}, {}, {}...]
#     """
#     tenant_uuids = [ r['result']['tenant_uuid'] for r in results_for_requests]
#     tenant_uuids = list(set(tenant_uuids)) # Remove duplicates
#     return tenant_uuids
#
# def get_token(base_dir, filename, archive_domain_name):
#     """
#     Gets a personal access token for a user of a BIG-MAP Archive from a file
#     """
#     file_path = os.path.join(base_dir, filename)
#
#     with open(file_path, 'r') as f:
#         accounts = yaml.safe_load(f)
#
#     tokens = [a['token'] for a in accounts if a['domain_name'] == archive_domain_name]
#
#     if len(tokens) == 0:
#         raise Exception(f'No token for FINALES on the archive {archive_domain_name}')
#     if len(tokens) > 1:
#         raise Exception(f'Multiple tokens for FINALES on the archive {archive_domain_name}')
#
#     return tokens[0]

# def group_result_uuids_by_tenant(base_dir, output_dir, data):
#     """
#     Gives the result uuids grouped by tenant
#     Starting from a list of results [{}, {}, {}...], we get [[{}, {}, {}...], [{}, {}, {}...], [{}, {}, {}...]...],
#     where each internal list corresponds to all result uuids for a given tenant
#     """
#     results = [
#         {
#             'tenant_uuid': r['result']['tenant_uuid'],
#             'result_uuid': r['uuid']
#         } for r in data]
#     key_func = lambda x: x['tenant_uuid']
#     results = sorted(results, key=key_func) # Order by tenant_uuid
#     lists_of_results = [list(group) for (k, group) in groupby(results, key=key_func)] # Group results by tenant_uuid
#     return lists_of_results
#
# def get_archive_token(base_dir, archives_for_tenants_filename, tenant_uuid, archive_domain_name):
#     """
#     Gets a personal access token of a tenant for an archive from a file
#     """
#     file_path = os.path.join(base_dir, archives_for_tenants_filename)
#
#     with open(file_path, 'r') as f:
#         tenant_archive_couples = json.load(f)
#
#     tokens = [tac['archive_token'] for tac in tenant_archive_couples
#               if (tac['finales_tenant_uuid'] == tenant_uuid and tac['archive_domain_name'] == archive_domain_name)]
#
#     if len(tokens) != 1:
#         raise Exception(f'Number of tokens for tenant {tenant_uuid} on {archive_domain_name}: {len(tokens)}')
#
#     return tokens[0]



