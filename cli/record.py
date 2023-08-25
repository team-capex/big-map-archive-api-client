"""Commands to manage one record at a time."""
import click
from pathlib import Path
import os
import requests


from cli.root import cmd_root
from big_map_archive_api_client.client.client_config import ClientConfig
from big_map_archive_api_client.utils import (get_data_files_in_upload_dir)


@cmd_root.group('record')
def cmd_record():
    """
    Deal with single records
    """

@cmd_record.command('create')
@click.option(
    '--config-file',
    show_default=True,
    default='bma_config.yaml',
    help='Relative path to the file specifying the domain name and a personal access token for the targeted BIG-MAP Archive.',
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
)
@click.option(
    '--metadata-file',
    show_default=True,
    default='data/input/metadata.yaml',
    help='Relative path to the file for the record\'s metadata (title, list of authors...).',
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
)
@click.option(
    '--data-files',
    show_default=True,
    default='data/input/upload',
    help='Relative path to the data files to be uploaded and linked to the record.',
    type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option(
    '--publish',
    is_flag=True,
    help='Publish the created record.',
    default=False
)
def cmd_record_create(config_file, metadata_file, data_files, publish):
    """
    Create a record on a BIG-MAP Archive and optionally publish it
    """
    try:
        base_dir_path = Path(__file__).absolute().parent.parent
        config_file_path = os.path.join(base_dir_path, config_file)
        client_config = ClientConfig.load_from_config_file(config_file_path)
        client = client_config.create_client()

        # Create draft from input metadata.yaml
        response = client.post_records(base_dir_path, metadata_file, additional_description='')
        record_id = response['id']

        # Upload data files and insert links in the draft's metadata
        filenames = get_data_files_in_upload_dir(base_dir_path, data_files)
        client.upload_files(record_id, base_dir_path, data_files, filenames)

        click.echo('Record created')

        # Publish draft depending on user's choice
        if publish:
            client.insert_publication_date(record_id)
            client.post_publish(record_id)
            click.echo('Record published')
            click.echo(f'Please visit https://{client_config.domain_name}/records/{record_id}')
            exit(0)

        click.echo(f'Please visit https://{client_config.domain_name}/uploads/{record_id}')
    except requests.exceptions.ConnectionError as e:
        click.echo(f'An error of type ConnectionError occurred. Check the domain name in {config_file}. More info: {str(e)}.')
    except requests.exceptions.HTTPError as e:
        click.echo(f'An error of type HTTPError occurred. Check your token in {config_file}. More info: {str(e)}.')
    except Exception as e:
        click.echo(f'An error occurred. More info: {str(e)}.')



