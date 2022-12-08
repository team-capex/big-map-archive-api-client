#!/usr/bin/env python
import click


@click.group(help="CLI tool to manage BIG-MAP archive records")
def main():
    pass


@main.command(help="Upload the records.")
@click.argument("records_path", default=".")
@click.option("--publish", is_flag=True, default=False, help="Publish the records")
def upload(records_path, publish):
    from big_map_archive_api.api import BMA

    bma = BMA()
    bma.upload_records(records_path)
    if publish:
        bma.publish()


@main.command(help="Add token.")
@click.argument("token", default="")
def add_token(token):
    from big_map_archive_api.utils import add_token

    token = click.prompt("Your token:", default="")
    add_token(token)


if __name__ == "__main__":
    main()
