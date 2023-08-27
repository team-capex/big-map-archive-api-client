import click
from pathlib import Path
import os
from datetime import datetime


from cli.root import cmd_root
from cli.record import cmd_record_create
from big_map_archive_api_client.client.client_config import ClientConfig
from big_map_archive_api_client.utils import (export_to_json_file,
                                              recreate_directory,
                                              get_title_from_metadata_file)

from finales_api_client.client.client_config import FinalesClientConfig


@cmd_root.group('finales-db')
def cmd_finales_db():
    """
    Copy data from the database of a FINALES server to a BIG-MAP Archive.
    """

@cmd_finales_db.command('back-up')
@click.option(
    '--bma-config-file',
    show_default=True,
    default='bma_config.yaml',
    help='Relative path to the file specifying the domain name and a personal access token for the targeted BIG-MAP Archive.',
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
)
@click.option(
    '--finales-config-file',
    show_default=True,
    default='finales_config.yaml',
    help='Relative path to the file specifying the IP address, the port, and the credentials of a user account for the targeted FINALES server.',
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
)
@click.option(
    '--record-id',
    show_default=True,
    default='',
    help='Id of the published version for the previous back-up (e.g., "pxrf9-zfh45"). For the first back-up, leave to the default.',
    type=str
)
@click.option(
    '--metadata-file',
    show_default=True,
    default='data/input/metadata.yaml',
    help='Relative path to the file that contains the metadata (title, list of authors, etc) for creating a new version.',
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
)
@click.pass_context
def cmd_finales_db_copy(ctx,
                        bma_config_file,
                        finales_config_file,
                        record_id,
                        metadata_file):
    """
    Perform a partial back-up from the database of a FINALES server to a BIG-MAP Archive. A new entry version is created and published. Its linked files include data related to capabilities, requests, and results for requests.
    """
    # Create/re-create folder where files are stored temporarily
    base_dir_path = Path(__file__).absolute().parent.parent
    temp_dir_path = 'data/temp'
    recreate_directory(base_dir_path, temp_dir_path)

    # Create a FinalesAPIClient object to interact with a FINALES server
    config_file_path = os.path.join(base_dir_path, finales_config_file)
    client_config = FinalesClientConfig.load_from_config_file(config_file_path)
    client = client_config.create_client()

    # Get access token from FINALES server
    response = client.post_authenticate()
    finales_token = response['access_token']

    # Get data from the FINALES database
    # 1. Capabilities
    response = client.get_capabilities(finales_token)
    capabilities_filename = 'capabilities.json'
    capabilities_file_path = os.path.join(base_dir_path, temp_dir_path, capabilities_filename)
    export_to_json_file(base_dir_path, capabilities_file_path, response)

    # 2. Requests
    response = client.get_all_requests(finales_token)
    requests_filename = 'requests.json'
    requests_file_path = os.path.join(base_dir_path, temp_dir_path, requests_filename)
    export_to_json_file(base_dir_path, requests_file_path, response)

    # 3. Results for requests
    response = client.get_results_requested(finales_token)
    results_filename = 'results_for_requests.json'
    results_file_path = os.path.join(base_dir_path, temp_dir_path, results_filename)
    export_to_json_file(base_dir_path, results_file_path, response)

    # Create an ArchiveAPIClient object to interact with the archive
    config_file_path = os.path.join(base_dir_path, bma_config_file)
    client_config = ClientConfig.load_from_config_file(config_file_path)
    client = client_config.create_client()

    title = get_title_from_metadata_file(base_dir_path, metadata_file)

    now = datetime.now()
    additional_description = f' The back-up was performed on {now.strftime("%B %-d, %Y")} at {now.strftime("%H:%M")}.'

    # If a record id is not provided
    if record_id == '':
        # Check whether the archive user already owns a published record with that title
        record_ids = client.get_published_user_records_with_given_title(title)

        # If there is no such a record, assume that the non-provided record id is intentional, otherwise ask for confirmation
        if not record_ids:
            # Create a new entry
            ctx.invoke(cmd_record_create,
                       config_file=bma_config_file,
                       metadata_file=metadata_file,
                       data_files=temp_dir_path,
                       publish=True)
        else:
            # Ask for confirmation
            click.echo(f'You already own a published record on the BIG-MAP Archive with the same title (record {record_ids[0]}).')
            click.echo('But you did not provide that record id via the option "--record-id".')
            click.confirm('Do you prefer creating a new entry rather than updating the existing one?', abort=True)

            # Create a new entry
            ctx.invoke(cmd_record_create,
                       config_file=bma_config_file,
                       metadata_file=metadata_file,
                       data_files=temp_dir_path,
                       publish=True)