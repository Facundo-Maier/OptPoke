"""CLI for one-time imports; never packages private workbooks with the source."""
from __future__ import annotations

import argparse
from .db import initialize, database_path
from .importers import import_bank, import_hunts


def main():
    parser = argparse.ArgumentParser(description="Opt. Poke — inicialización e importación")
    parser.add_argument("--bank", help="Ruta al archivo 26Febrero27.xlsx")
    parser.add_argument("--hunts", help="Ruta al archivo ShinyHunts.xlsm")
    args = parser.parse_args()
    initialize()
    print("Base de datos:", database_path())
    if args.bank:
        print("Bank:", import_bank(args.bank))
    if args.hunts:
        print("Cacerías:", import_hunts(args.hunts))
    if not args.bank and not args.hunts:
        print("Catálogo inicializado; no se importó ningún progreso")


if __name__ == "__main__":
    main()
