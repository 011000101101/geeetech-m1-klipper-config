#!/usr/bin/env python3
"""Prepare a Klipper binary for the Geeetech M1 stock SD updater."""

import argparse
import hashlib
from pathlib import Path
import sys


OUTPUT_NAME = "GTM32Source.bin"
MAX_SIZE_EXCLUSIVE = 0x78000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Pad a Klipper binary for the Geeetech M1 stock bootloader and "
            f"write it as {OUTPUT_NAME}."
        )
    )
    parser.add_argument("input", type=Path, help="Klipper out/klipper.bin")
    parser.add_argument(
        "--output-directory",
        "-o",
        type=Path,
        default=Path.cwd(),
        help="existing destination directory (default: current directory)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help=f"replace an existing {OUTPUT_NAME}",
    )
    return parser.parse_args()


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    args = parse_args()
    source = args.input
    destination_directory = args.output_directory

    if not source.is_file():
        fail(f"input is not a regular file: {source}")
    if not destination_directory.is_dir():
        fail(f"output directory does not exist: {destination_directory}")

    destination = destination_directory / OUTPUT_NAME
    if source.resolve() == destination.resolve():
        fail("input and output paths are the same")
    if destination.exists() and not args.force:
        fail(f"output already exists: {destination} (use --force to replace it)")

    firmware = source.read_bytes()
    if not firmware:
        fail("input is empty")

    padding_size = (-len(firmware)) % 4
    packaged = firmware + (b"\xff" * padding_size)
    if len(packaged) >= MAX_SIZE_EXCLUSIVE:
        fail(
            f"padded image is {len(packaged)} bytes; the stock bootloader "
            f"requires fewer than {MAX_SIZE_EXCLUSIVE} bytes"
        )

    destination.write_bytes(packaged)
    digest = hashlib.sha256(packaged).hexdigest()
    print(f"wrote: {destination}")
    print(f"size: {len(packaged)} bytes ({padding_size} padding bytes)")
    print(f"sha256: {digest}")


if __name__ == "__main__":
    main()
