from __future__ import absolute_import, print_function
__author__ = "katharine"

from ..base import BaseCommand
from pebble_tool.sdk import sdk_manager


class SDKManager(BaseCommand):
    """Manages available SDKs"""
    command = 'sdk'

    def __call__(self, args):
        super(SDKManager, self).__call__(args)
        args.sub_func(args)


    @classmethod
    def add_parser(cls, parser):
        parser = super(SDKManager, cls).add_parser(parser)
        subparsers = parser.add_subparsers()

        list_parser = subparsers.add_parser("list", help="Lists available SDKs.")
        list_parser.set_defaults(sub_func=cls.do_list)

        install_parser = subparsers.add_parser("install", help="Installs the given SDK.")
        install_parser.add_argument('version', help="Version to install, or 'latest' for the latest.")
        install_parser.set_defaults(sub_func=cls.do_install)

        activate_parser = subparsers.add_parser("activate", help="Makes the given, installed SDK active.")
        activate_parser.add_argument('version', help="Version to make active.")
        activate_parser.set_defaults(sub_func=cls.do_activate)

        uninstall_parser = subparsers.add_parser("uninstall", help="Uninstalls the given SDK.")
        uninstall_parser.add_argument('version', help="Version to uninstall.")
        uninstall_parser.set_defaults(sub_func=cls.do_uninstall)
        return parser

    @classmethod
    def do_list(cls, args):
        local_sdks = sdk_manager.list_local_sdks()
        current_sdk = sdk_manager.get_current_sdk()
        print("Available SDKs:")
        for sdk in sdk_manager.list_remote_sdks():
            if sdk['version'] in local_sdks:
                line = ' * '
            else:
                line = '   '
            line += sdk['version']
            if sdk['channel']:
                line += " ({})".format(sdk['channel'])
            if sdk['version'] == current_sdk:
                line += " (active)"
            print(line)

    @classmethod
    def do_install(cls, args):
        print("Installing SDK...")
        sdk_manager.install_remote_sdk(args.version)
        print("Installed.")

    @classmethod
    def do_uninstall(cls, args):
        print("Uninstalling SDK {}...".format(args.version))
        sdk_manager.uninstall_sdk(args.version)
        print("Done.")

    @classmethod
    def do_activate(cls, args):
        sdk_manager.set_current_sdk(args.version)

