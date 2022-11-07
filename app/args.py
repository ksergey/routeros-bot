__all__ = ("args")

import argparse

def create_parser():
    parser = argparse.ArgumentParser(description="telegram bot for routeros (mikrotik)")
    parser.add_argument("--config", dest="config", metavar="PATH", required=True, help="path to config file")
    return parser

args = create_parser().parse_args()
