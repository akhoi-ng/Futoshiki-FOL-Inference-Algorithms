#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import runpy
import sys
from pathlib import Path


def _normalize_input_path(args, source_dir):
    if not args:
        return args

    input_arg = args[0]
    input_path = Path(input_arg)

    if input_path.is_absolute() or input_path.exists():
        return args

    source_candidate = source_dir / input_arg
    if source_candidate.exists():
        args = list(args)
        args[0] = str(source_candidate)
    return args


def main():
    root_dir = Path(__file__).resolve().parent
    source_dir = root_dir / "Source"
    source_main = source_dir / "main.py"

    if not source_main.exists():
        raise FileNotFoundError(f"Khong tim thay file: {source_main}")

    args = _normalize_input_path(sys.argv[1:], source_dir)
    sys.argv = [str(source_main)] + list(args)
    sys.path.insert(0, str(source_dir))
    runpy.run_path(str(source_main), run_name="__main__")


if __name__ == "__main__":
    main()
