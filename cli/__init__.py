"""Module for the command line interface.

Import here all groups that directly inherit from root.
"""
from cli.root import cmd_root
from cli.record import cmd_record
from cli.finales_db import cmd_finales_db

__all__ = [
    'cmd_root',
    'cmd_record',
    'cmd_finales_db'
]