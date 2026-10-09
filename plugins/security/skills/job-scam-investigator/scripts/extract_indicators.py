#!/usr/bin/env python3
"""Offline indicator extraction from UTF-8 text or stdin. No network or persistence."""
import argparse
import json
import re
import sys
from pathlib import Path

EMAIL = re.compile(r'(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])')
URL = re.compile(r'https?://[^\s<>"\']+', re.I)
HANDLE = re.compile(r'(?<!\w)@[A-Za-z][A-Za-z0-9_]{3,31}\b')
# Conservative: phone extraction is intentionally limited to BR numbers with DDD.
PHONE = re.compile(r'(?<!\d)(?:\+?55[\s.-]?)?\(?([1-9]\d)\)?[\s.-]?(9?\d{4})[\s.-]?(\d{4})(?!\d)')


def extract(content: str) -> dict:
    phones = set()
    for match in PHONE.finditer(content):
        ddd, prefix, suffix = match.groups()
        phones.add(f'+55{ddd}{prefix}{suffix}')
    return {
        'emails': sorted(set(EMAIL.findall(content)), key=str.casefold),
        'urls': sorted(set(url.rstrip('.,);!?') for url in URL.findall(content))),
        'handles': sorted(set(HANDLE.findall(content)), key=str.casefold),
        'phones_br': sorted(phones),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', nargs='?', help='UTF-8 text file; omit for stdin')
    parser.add_argument('--redact', action='store_true', help='Mask extracted values for safer display')
    args = parser.parse_args()
    raw = Path(args.input).read_text(encoding='utf-8') if args.input else sys.stdin.read()
    data = extract(raw)
    if args.redact:
        data = {k: [v[:3] + '…' if len(v) > 3 else '***' for v in items] for k, items in data.items()}
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
