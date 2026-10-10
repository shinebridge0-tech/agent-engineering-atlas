import argparse
from .indexing import rebuild
from .content import load_all
parser = argparse.ArgumentParser()
parser.add_argument("command", choices=["validate", "rebuild"])
args = parser.parse_args()
print({"valid_cards": len(load_all())} if args.command == "validate" else rebuild())
