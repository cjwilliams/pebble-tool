from __future__ import absolute_import, print_function
__author__ = 'cherie'

from filepicker import FilepickerClient
import os
import requests

from pebble_tool.account import get_default_account
from pebble_tool.commands.sdk import BaseCommand
from pebble_tool.exceptions import PebbleProjectException, ToolError, ValidationError
from pebble_tool.sdk.project import PebbleProject


class ReleaseManager(BaseCommand):
    """Manages releases for a Pebble project"""
    command = 'release'
    has_subcommands = True

    def __call__(self, args):
        super(ReleaseManager, self).__call__(args)
        args.sub_func(args)

    @classmethod
    def add_parser(cls, parser):
        parser = super(ReleaseManager, cls).add_parser(parser)
        subparsers = parser.add_subparsers(title="subcommand")

        publish_parser = subparsers.add_parser("publish", help="Publishes a new release to the developer portal")
        publish_parser.set_defaults(sub_func=cls.do_publish)
        publish_parser.add_argument('pbw', help="Path to the PBW file to be uploaded as a new release", nargs='?')
        publish_parser.add_argument('--notes', help="A short string describing the release")

        delete_parser = subparsers.add_parser("delete", help="Deletes the release specified from the developer portal")
        delete_parser.set_defaults(sub_func=cls.do_delete)
        delete_parser.add_argument('release_id', help="Release ID of the release to delete")
        return parser

    @classmethod
    def _get_auth_header(cls):
        bearer_token = os.environ.get('PEBBLE_TOKEN') or get_default_account().get_access_token()
        if bearer_token is None:
            raise ToolError("You must be logged in to use the 'publish' command. "
                            "Please log in using the 'pebble login' command")
        return {'Authorization': 'Bearer {}'.format(bearer_token)}

    @classmethod
    def _get_app_releases_url(cls):
        base_url = os.environ.get('DEV_PORTAL_URL', "http://dev-portal.getpebble.com")
        # Make this work also with parsing a PBW
        try:
            app_uuid = str(PebbleProject().uuid)
        except PebbleProjectException:
            raise ToolError("You must either use this command from a pebble project or specify --app-uuid.")
        return os.path.join(base_url, "api/applications", app_uuid, "releases")

    @classmethod
    def _upload_pbw(cls, pbw):
        client = FilepickerClient(api_key="Ag3QJFpN1QuueH0z0XgKUz")
        return client.store_local_file(pbw).url

    @classmethod
    def _create_release(cls, pbw_file, release_notes=""):
        data = {
            "pbw_file": pbw_file,
            "release-notes": release_notes
        }
        r = requests.post(cls._get_app_releases_url(), data, headers=cls._get_auth_header())
        if r.status_code == 422:
            print("Invalid UUID - Are you sure you've previously published a release for this app?")
        r.raise_for_status()
        response = r.json()
        return response['release']['id']

    @classmethod
    def _publish_release(cls, release_id):
        url = os.path.join(cls._get_app_releases_url(), release_id, "publish")
        requests.post(url, headers=cls._get_auth_header())

    @classmethod
    def _release_is_ready(cls, release_id):
        url = os.path.join(cls._get_app_releases_url(), release_id)
        r = requests.get(url, headers = cls._get_auth_header())
        r.raise_for_status()
        response = r.json()

        if response['release']['status'] == 'ready':
            return True
        elif response['release']['status'] == 'validation_failed':
            raise ValidationError(response['release']['validation_error'])
        else:
            return False

    @classmethod
    def do_publish(cls, args):
        release_notes = args.notes or ""
        pbw = args.pbw or 'build/{}.pbw'.format(os.path.basename(os.getcwd()))
        if pbw is None:
            raise ToolError("You must either run this command from a project directory or specify the pbw "
                            "to upload.")

        pbw_file = cls._upload_pbw(pbw)

        release_id = cls._create_release(pbw_file, release_notes)
        print("Created release {}".format(release_id))

        while True: # Should do a timeout here
            if cls._release_is_ready(release_id):
                break

        cls._publish_release(release_id)
        print("Published release {}".format(release_id))

    @classmethod
    def do_unpublish(cls, args):
        pass

    @classmethod
    def do_delete(cls, release_id):
        url = os.path.join(cls._get_app_releases_url(), release_id)
        r = requests.delete(url)
        r.raise_for_status()
        print("Removed release {}".format(release_id))
