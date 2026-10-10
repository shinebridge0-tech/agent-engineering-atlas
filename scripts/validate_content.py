"""Trusted baseline data-only validation; never executes contributor examples."""
import argparse
import os
from pathlib import Path
from backend.content import load_all

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    cards = load_all(Path(os.path.abspath(args.root)))
    print({"valid_cards": len(cards), "independent_source_verification": "not performed by schema validation"})
