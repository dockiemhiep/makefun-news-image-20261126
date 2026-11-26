#!/usr/bin/env python3
"""Deterministic make.fun entry runner: copies entry.png to the output directory."""

import os
import shutil


def main() -> None:
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(repo_dir, "entry.png")

    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(output_dir, exist_ok=True)

    dst = os.path.join(output_dir, "entry.png")
    shutil.copyfile(src, dst)


if __name__ == "__main__":
    main()
