import argparse
from functools import wraps

import pycookiecheat

from . import fetch, GOOGLE_EXPORT_URL


def make_parser():
    parser = argparse.ArgumentParser(
        description='Cheat Google Calendar',
    )
    parser.add_argument(
        '-b', '--browser',
        choices=['chrome', 'firefox'],
        default='chrome',
        help='Browser to use for cookies',
    )
    subparser = parser.add_subparsers(
        dest='command',
        help='sub-command help',
        required=True,
    )
    download_parser = subparser.add_parser(
        'download',
        help='download ICS file from Google Calendar',
    )
    download_parser.add_argument(
        '-o', '--output',
        type=argparse.FileType('wb'),
        default='calendar.zip',
        help='output file',
    )
    download_parser.set_defaults(func=download)
    return parser


def get_cookies(func):
    @wraps(func)
    def _get_cookies(args):
        if args.browser == 'chrome':
            cookies = pycookiecheat.chrome_cookies(GOOGLE_EXPORT_URL)
        elif args.browser == 'firefox':
            cookies = pycookiecheat.firefox_cookies(GOOGLE_EXPORT_URL)
        else:
            raise ValueError("Unknown browser: %s" % args.browser)
        return func(args, cookies=cookies)
    return _get_cookies


@get_cookies
def download(args, cookies=None):
    content = fetch.fetch(cookies)
    args.output.write(content.read())


def main():
    parser = make_parser()
    args = parser.parse_args()
    args.func(args)

