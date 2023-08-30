import click
from pathlib import Path
import os
from datetime import datetime
import requests

from cli.root import cmd_root
from cli.record import (cmd_record_create,
                        cmd_record_update)
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
    required=True,
    help='Path to the YAML file that specifies the domain name and a personal access token for the targeted BIG-MAP Archive. See bma_config.yaml in the GitHub repository.',
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
)
@click.option(
    '--finales-config-file',
    required=True,
    help='Path to the YAML file that specifies the IP address, the port, and the credentials of a user account for the targeted FINALES server. See finales_config.yaml in the GitHub repository.',
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
    required=True,
    help='Path to the YAML file that contains the metadata (title, list of authors, etc) for creating a new version. See data/input/example/create_record/metadata.yaml in the GitHub repository.',
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
)
@click.option(
    '--link-all-files-from-previous',
    is_flag=True,
    help='Link all files that are already linked to the previous version to the new version, with the exception of files whose content changed.'
)
@click.option(
    '--no-publish',
    is_flag=True,
    help='Do not publish the newly created version. This is discouraged in production. If you select this option, either publish or delete the newly created draft, e.g., via the GUI.'
)
@click.pass_context
def cmd_finales_db_copy(ctx,
                        bma_config_file,
                        finales_config_file,
                        record_id,
                        metadata_file,
                        link_all_files_from_previous,
                        no_publish):
    """
    Perform a partial back-up from the database of a FINALES server to a BIG-MAP Archive. A new entry version is created and published. Its linked files include data related to capabilities, requests, and results for requests.
    """
    try:
        # Create/re-create folder where files are stored temporarily
        base_dir_path = os.getcwd()
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

        publish = not no_publish

        # Is a record id provided by the user?
        if record_id == '':
            # Check whether the archive user already owns a published record with that title
            record_ids = client.get_published_user_records_with_given_title(title)

            if not record_ids:
                # If there is no such record, it is assumed that setting the record id to its default value is intentional
                # Create a new entry
                ctx.invoke(cmd_record_create,
                           config_file=bma_config_file,
                           metadata_file=metadata_file,
                           data_files=temp_dir_path,
                           publish=publish)
            else:
                # Ask for confirmation
                click.echo(f'Found a published record with the title "{title}" on the BIG-MAP Archive.')
                click.echo(f'To update the existing entry instead of creating a new one, execute the command with the option --record-id="{record_ids[0]}".')
                click.confirm('Do you want to create a new entry?', abort=True)

                # Create a new entry
                ctx.invoke(cmd_record_create,
                           config_file=bma_config_file,
                           metadata_file=metadata_file,
                           data_files=temp_dir_path,
                           publish=publish)
        else:
            if not client.exists_and_is_published(record_id):
                # The provided record id does not correspond to a published record on the BIG-MAP Archive owned by the user
                click.echo(f'Invalid record id: {record_id}. You do not own a published record with this id.')
                raise click.Abort

            # Extract the title of the published record
            record_title = client.get_record_title(record_id)

            if title == record_title:
                # If the title in the metadata file matches the title of the published record, it is assumed that the value given to the record id is intentional
                # Update the entry by creating a new version
                ctx.invoke(cmd_record_update,
                           config_file=bma_config_file,
                           record_id=record_id,
                           update_only=False,
                           metadata_file=metadata_file,
                           data_files=temp_dir_path,
                           link_all_files_from_previous=link_all_files_from_previous,
                           publish=publish)
            else:
                # Ask for confirmation
                click.echo(f'The title "{title}" in the metadata file differs from the title of the published record "{record_title}".')
                click.confirm(f'Do you want to continue with the new title?', abort=True)

                # Update the entry by creating a new version
                ctx.invoke(cmd_record_update,
                           config_file=bma_config_file,
                           record_id=record_id,
                           update_only=False,
                           metadata_file=metadata_file,
                           data_files=temp_dir_path,
                           link_all_files_from_previous=link_all_files_from_previous,
                           publish=publish)

    except click.Abort:
        click.echo('Aborted.')
    except requests.exceptions.ConnectionError as e:
        click.echo(f'An error of type ConnectionError occurred. Check domain names/IP addresses/ports in {bma_config_file} and {finales_config_file}. More info: {str(e)}.')
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        if status_code == 400:
            click.echo(f'An error of type HTTPError occurred. Check tokens/credentials in {bma_config_file} and {finales_config_file}. More info: {str(e)}.')
        else:
            click.echo(f'An error of type HTTPError occurred. More info: {str(e)}.')
    except Exception as e:
        click.echo(f'An error occurred. More info: {str(e)}.')
