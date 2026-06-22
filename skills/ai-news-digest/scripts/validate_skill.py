#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import sys


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _parse_frontmatter(skill_md: str) -> dict[str, str]:
    if not skill_md.startswith("---\n"):
        raise ValueError("SKILL.md missing YAML frontmatter (expected starting ---).")
    end = skill_md.find("\n---\n", 4)
    if end == -1:
        raise ValueError("SKILL.md frontmatter not terminated (expected second ---).")
    block = skill_md[4:end].strip("\n")
    data: dict[str, str] = {}
    for line in block.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        m = re.fullmatch(r"([A-Za-z0-9_-]+):\s*(.*)", line)
        if not m:
            raise ValueError(f"Invalid frontmatter line: {line!r}")
        key, value = m.group(1), m.group(2)
        data[key] = value
    return data


def _parse_simple_yaml(yaml_text: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in yaml_text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.fullmatch(r"([A-Za-z0-9_-]+):\s*(.*)", line)
        if not m:
            raise ValueError(f"Invalid agents/openai.yaml line: {line!r}")
        data[m.group(1)] = m.group(2)
    return data


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Validate ai-news-digest skill files without external deps.")
    parser.add_argument("--skill-dir", default=os.path.normpath(os.path.join(os.path.dirname(__file__), "..")))
    args = parser.parse_args(argv)

    skill_dir = os.path.abspath(args.skill_dir)
    skill_name = os.path.basename(skill_dir)

    skill_md_path = os.path.join(skill_dir, "SKILL.md")
    openai_yaml_path = os.path.join(skill_dir, "agents", "openai.yaml")

    if not os.path.exists(skill_md_path):
        print(f"error: missing {skill_md_path}", file=sys.stderr)
        return 2
    if not os.path.exists(openai_yaml_path):
        print(f"error: missing {openai_yaml_path}", file=sys.stderr)
        return 2

    fm = _parse_frontmatter(_read(skill_md_path))
    for required in ("name", "description"):
        if required not in fm or not str(fm[required]).strip():
            raise ValueError(f"SKILL.md frontmatter missing required field: {required}")
    extra = sorted(set(fm.keys()) - {"name", "description"})
    if extra:
        raise ValueError(f"SKILL.md frontmatter has extra keys (only name/description allowed): {extra}")
    if fm["name"].strip() != skill_name:
        raise ValueError(f"SKILL.md name={fm['name']!r} does not match folder name {skill_name!r}")

    oy = _parse_simple_yaml(_read(openai_yaml_path))
    for required in ("display_name", "short_description", "default_prompt"):
        if required not in oy or not str(oy[required]).strip():
            raise ValueError(f"agents/openai.yaml missing required field: {required}")

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
