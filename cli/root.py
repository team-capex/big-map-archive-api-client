"""Topmost command line, kept separate to prevent import cycles."""

import click


@click.group('bma')
def cmd_root():
    """
    Command line interface for interacting with BIG-MAP Archive
    """
    pass
#
#
# @click.group()
# def bma():
#     """Command line interface for archive-cli."""
#     pass
#
# @bma.command()
# @click.option('-n', '--name', type=str, help='Name to greet', default='World')
# def hello(name):
#     click.echo(f'Hello {name}')