from datetime import datetime, timedelta
from functools import wraps
from io import BytesIO
import argparse
import fnmatch
import json
import unidecode

import icalendar
import pycookiecheat
import recurring_ical_events
import x_wr_timezone

from . import fetch, GOOGLE_EXPORT_URL
from .extract import extract


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

    #
    # cheatgooglecal download ...
    #
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
    download_parser.set_defaults(func=cmd_download)

    #
    # cheatgooglecal extract ...
    #
    extract_parser = subparser.add_parser(
        'extract',
        help='extract ICS file from Google Calendar',
    )
    extract_parser.add_argument(
        '-i', '--include',
        action='append',
        help='include pattern',
    )
    extract_parser.add_argument(
        '-e', '--exclude',
        action='append',
        help='exclude pattern',
    )
    extract_parser.add_argument(
        'zipfile',
        help='zip file',
    )
    extract_parser.set_defaults(func=cmd_extract)

    #
    # cheatgooglecal export ...
    #
    export_parser = subparser.add_parser(
        'export',
        help='export ICS file from Google Calendar',
    )
    export_parser.add_argument(
        '-f', '--from',
        dest='from_',
        help='start date',
        type=lambda s: datetime.strptime(s, '%Y-%m-%d'),
        default=datetime.now().strftime('%Y-%m-%d'),
    )
    export_parser.add_argument(
        '-t', '--to',
        help='end date',
        type=lambda s: datetime.strptime(s, '%Y-%m-%d'),
        default=(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
    )
    export_parser.add_argument(
        '--default-time',
        help='default time for events without time',
        type=lambda s: datetime.strptime(s, '%H:%M').time(),
        default=datetime(2000, 1, 1, 9, 0).time(),
    )
    export_parser.add_argument(
        '-F', '--format',
        choices=['td150'],
        default='td150',
        help='output format',
    )
    export_parser.add_argument(
        '-i', '--include',
        action='append',
        help='include pattern',
    )
    export_parser.add_argument(
        '-e', '--exclude',
        action='append',
        help='exclude pattern',
    )
    export_parser.add_argument(
        'icsfiles',
        nargs='+',
        help='ics files',
    )
    export_parser.set_defaults(func=cmd_export)
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
def cmd_download(args, cookies=None):
    content = fetch.fetch(cookies)
    args.output.write(content.read())


def cmd_extract(args):
    with open(args.zipfile, 'rb') as zip_file:
        for name, content in extract(BytesIO(zip_file.read()), args.include, args.exclude):
            with open(name, 'wb') as f:
                f.write(content.read())


def cmd_export(args):
    def _get_events():
        for ics in args.icsfiles:
            with open(ics, 'rb') as f:
                acal = icalendar.Calendar.from_ical(f.read())
                cal = x_wr_timezone.to_standard(acal)
                for ev in recurring_ical_events.of(cal).between(args.from_, args.to):
                    if args.include and not any(fnmatch.fnmatch(ev['SUMMARY'], p) for p in args.include):
                        continue
                    if args.exclude and any(fnmatch.fnmatch(ev['SUMMARY'], p) for p in args.exclude):
                        continue
                    if type(ev['DTSTART'].dt) is not datetime:
                        ev['DTSTART'].dt = datetime.combine(ev['DTSTART'].dt, args.default_time).astimezone()
                    yield ev

    if args.format == 'td150':
        print(json.dumps({"appointments": [ to_td150(ev) for ev in sorted(_get_events(), key=lambda ev: ev['DTSTART'].dt) ],
                          "anniversaries": [],
                          "phone_numbers": [],
                          "lists": [],
                          "alarms": [],
                          "sound_options": {"hourly_chime": False,
                                            "button_beep": False},
                          "appointment_notification_minutes": 5}))

def to_td150(ev):
    return {
        "message": unidecode.unidecode(ev['SUMMARY']),
        "time": ev['DTSTART'].dt.astimezone().isoformat(),
    }

def main():
    parser = make_parser()
    args = parser.parse_args()
    args.func(args)

