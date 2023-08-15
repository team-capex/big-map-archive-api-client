import json
import os
import hashlib
from zipfile import (ZipFile, ZIP_DEFLATED)
from itertools import groupby
import yaml

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


def export_to_json_file(base_dir, output_dir, output_filename, data):
    """
    Exports data to json file
    """
    # TODO Create output_dir if it does not exist
    # TODO Overwrite content of output file instead of appending

    file_path = os.path.join(base_dir, output_dir, output_filename)

    with open(file_path, "w") as f:
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


def get_name_to_checksum_for_input_folder_files(base_dir, input_dir, metadata_filename):
    """
    Gets the names and md5 hashes of all files in the input folder, ignoring the metadata file
    """
    input_dir_path = os.path.join(base_dir, input_dir)

    filenames = [
        f for f in os.listdir(input_dir_path)
        if (os.path.isfile(os.path.join(input_dir_path, f)) and f != metadata_filename)
    ]

    input_folder_files = []

    for filename in filenames:
        file_path = os.path.join(input_dir_path, filename)

        with open(file_path, "rb") as f:
            file_hash = hashlib.md5()
            while chunk := f.read(8192):
                file_hash.update(chunk)

        input_folder_files.append(
            {
                'name': filename,
                'checksum': 'md5:' + file_hash.hexdigest()
            })

    return input_folder_files


def get_input_folder_files(base_dir, input_dir, metadata_filename):
    """
    Gets the names of all files in the input folder, ignoring the metadata file
    """
    input_folder_files = get_name_to_checksum_for_input_folder_files(base_dir, input_dir, metadata_filename)
    filenames = [f['name'] for f in input_folder_files]

    return filenames

def export_capabilities_to_zip_file(base_dir, output_dir, filename, capabilities):
    """
    Puts each capability in the list in its own json file
    Creates a zip file that contains all of these json files in the output folder
    """
    output_file_path = os.path.join(base_dir, output_dir, filename)
    filenames = []

    for c in capabilities:
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

def get_tenant_uuids(results_for_requests):
    """
    Extracts the tenant uuids from the obtained list of results [{}, {}, {}...]
    """
    tenant_uuids = [ r['result']['tenant_uuid'] for r in results_for_requests]
    tenant_uuids = list(set(tenant_uuids)) # Remove duplicates
    return tenant_uuids

def get_token_for_archive_account(base_dir, filename, tenant_uuid, archive_domain_name):
    """
    Extracts the email address for a tenant's account on an archive from a file
    """
    file_path = os.path.join(base_dir, filename)

    with open(file_path, 'r') as f:
        archive_accounts_of_tenants = yaml.safe_load(f)

    accounts = [t['archive_accounts'] for t in archive_accounts_of_tenants if t['finales_tenant_uuid'] == tenant_uuid]

    if len(accounts) == 0:
        raise Exception(f'No entry for the tenant with uuid {tenant_uuid} in the file {filename}')
    elif len(accounts) > 1:
        raise Exception(f'Multiple entries for the tenant with uuid {tenant_uuid} in the file {filename}')

    tokens = [a['token'] for a in accounts[0] if a['domain_name'] == archive_domain_name]

    if len(tokens) == 0:
        raise Exception(f'No token for the tenant with uuid {tenant_uuid} on the archive {archive_domain_name}')
    if len(tokens) > 1:
        raise Exception(f'Multiple tokens for the tenant with uuid {tenant_uuid} on the archive {archive_domain_name}')

    return tokens[0]

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



