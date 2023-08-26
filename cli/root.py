"""Topmost command line, kept separate to prevent import cycles."""

import click


@click.group('bma')
def cmd_root():
    """
    Command line interface for interacting with BIG-MAP Archive
    """
    pass