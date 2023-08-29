"""Topmost command line, kept separate to prevent import cycles."""

import click


@click.group('bma')
def cmd_root():
    """
    Command line client to interact with a BIG-MAP Archive.
    """
    pass