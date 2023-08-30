"""Topmost command line, kept separate to prevent import cycles."""

import click


@click.group('bma')
def cmd_root():
    """
    Command line client to interact with a BIG-MAP Archive. Source code available on GitHub: https://github.com/materialscloud-org/big-map-archive-api-client.
    """
    pass