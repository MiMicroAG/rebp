#!/usr/bin/env python3
"""Simple entrypoint for RealEstateBusinessPlan."""
import argparse
import logging


def main(argv=None):
    parser = argparse.ArgumentParser(description="Real Estate Business Plan helper")
    parser.add_argument("--name", "-n", default="World", help="Name to greet")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.info(f"Hello, {args.name} — スクリプトはPythonで書かれています。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
