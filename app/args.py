__all__ = ("args")

import argparse

def create_parser():
    parser = argparse.ArgumentParser(description="Telegram bot for 3D printer")
    parser.add_argument("--config", dest="config", metavar="PATH", required=True, help="path to config file")
    return parser

args = create_parser().parse_args()
