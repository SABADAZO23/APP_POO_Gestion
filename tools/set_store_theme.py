"""Save a store theme (palette, dark mode, logo) into Firestore settings/{store_id}.

Usage example:
  python tools\set_store_theme.py --store-id STORE123 --logo-path "C:\\Users\\Biblio\\Documents\\logo.jpg" --palette "#212A3E,#59788E,#F28C4F" --dark

This script re-uses `modules.theme.save_theme` so it will use the same storage format as the app.
Make sure your Firebase credentials are available (ServiceAccountKey.json in the project root or
the env var GOOGLE_APPLICATION_CREDENTIALS / FIREBASE_CREDENTIALS pointing to the JSON key).
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import List

try:
    # reuse the project's theme saving function
    from modules.theme import save_theme, DEFAULT_PALETTE
except Exception as e:  # pragma: no cover - friendly error for missing firebase/config
    print("Error importing project theme utilities. Make sure you run this from the project root and you have Python path configured.")
    print("Import error:", e)
    raise


def parse_palette(s: str) -> List[str]:
    parts = [p.strip() for p in s.split(',') if p.strip()]
    return parts


def main():
    parser = argparse.ArgumentParser(description="Save store theme (palette + logo) into Firestore settings/{store_id}.")
    parser.add_argument('--store-id', required=True, help='Target store id (document id in settings collection)')
    parser.add_argument('--logo-path', required=True, help='Path to logo image file (png/jpg)')
    parser.add_argument('--palette', required=False, help='Comma-separated list of up to 6 hex colors, e.g. "#212A3E,#59788E,#F28C4F"')
    parser.add_argument('--dark', action='store_true', help='Set dark_mode true')

    args = parser.parse_args()

    logo_path = args.logo_path
    if not os.path.isabs(logo_path):
        logo_path = os.path.abspath(logo_path)

    if not os.path.exists(logo_path):
        print(f"Logo file not found: {logo_path}")
        sys.exit(2)

    with open(logo_path, 'rb') as f:
        logo_bytes = f.read()

    palette = DEFAULT_PALETTE
    if args.palette:
        parsed = parse_palette(args.palette)
        if parsed:
            palette = parsed

    print(f"Saving theme for store: {args.store_id}")
    ok = save_theme(args.store_id, palette, args.dark, logo_bytes)
    if ok:
        print("Theme saved successfully to Firestore (collection 'settings').")
        print("You can now open the app and the store should pick up the logo and palette on login/load.")
        sys.exit(0)
    else:
        print("Failed to save theme. Check logs and Firebase credentials.")
        sys.exit(3)


if __name__ == '__main__':
    main()
