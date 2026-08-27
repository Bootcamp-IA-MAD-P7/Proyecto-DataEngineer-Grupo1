"""Validate the minimum traceability structure of HR Pro task specifications."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

SPEC_PATTERN = re.compile(r"HRP-(\d+)-.+\.md$")
REQUIRED_SECTIONS = ("## Objetivo", "## Criterios de aceptación")


def validate_spec(path: Path) -> list[str]:
    """Return all structural errors found in one task specification."""
    errors: list[str] = []
    match = SPEC_PATTERN.fullmatch(path.name)
    if match is None:
        return [f"{path}: filename must match HRP-<number>-<slug>.md"]

    jira_key = f"HRP-{match.group(1)}"
    content = path.read_text(encoding="utf-8")

    if not content.startswith(f"# {jira_key}"):
        errors.append(f"{path}: heading must start with '# {jira_key}'")
    if f"**Jira:** {jira_key}" not in content:
        errors.append(f"{path}: missing matching '**Jira:** {jira_key}' metadata")

    for section in REQUIRED_SECTIONS:
        if section not in content:
            errors.append(f"{path}: missing required section '{section}'")

    acceptance_match = re.search(
        r"^## Criterios de aceptación\s*$(.*?)(?=^## |\Z)",
        content,
        flags=re.MULTILINE | re.DOTALL,
    )
    has_checklist_item = acceptance_match and re.search(
        r"^- \[[ xX]\] .+", acceptance_match.group(1), re.MULTILINE
    )
    if acceptance_match and not has_checklist_item:
        errors.append(f"{path}: acceptance criteria must contain at least one checklist item")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("docs/specs"),
        help="directory containing HRP task specifications (default: docs/specs)",
    )
    args = parser.parse_args()

    if not args.root.is_dir():
        print(f"Specification directory not found: {args.root}")
        return 1

    files = sorted(path for path in args.root.glob("HRP-*.md") if path.is_file())
    if not files:
        print(f"No HRP specifications found in {args.root}")
        return 1

    errors = [error for path in files for error in validate_spec(path)]
    if errors:
        print("Specification validation failed:")
        print("\n".join(f"- {error}" for error in errors))
        return 1

    print(f"Specification validation passed for {len(files)} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
