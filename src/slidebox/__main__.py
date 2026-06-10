"""`python -m slidebox` — small CLI for one-shot tasks.

Subcommands:
    upload   — upload a .pptx to Drive as Google Slides; prints the URL.
"""

from __future__ import annotations

import argparse
import sys

from pptx import Presentation

from slidebox.drive import to_google_slides


def _cmd_upload(args: argparse.Namespace) -> int:
    prs = Presentation(args.path)
    result = to_google_slides(prs, name=args.name, file_id=args.file_id,
                              folder_id=args.folder)
    print(result.url)
    print(result.id, file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="slidebox")
    sub = ap.add_subparsers(dest="cmd", required=True)

    up = sub.add_parser("upload", help="Upload a .pptx to Drive as Google Slides.")
    up.add_argument("path", help="Path to the .pptx file.")
    up.add_argument("--name", default=None, help="Name for the Drive file.")
    up.add_argument("--file-id", default=None,
                    help="Update an existing Google Slides file in place.")
    up.add_argument("--folder", default=None, help="Target Drive folder id.")
    up.set_defaults(func=_cmd_upload)

    args = ap.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
