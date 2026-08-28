from __future__ import annotations

import importlib.util
from pathlib import Path


def load_validator():
    script = Path("scripts/validate_specs.py")
    spec = importlib.util.spec_from_file_location("validate_specs", script)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_valid_spec_has_no_validation_errors(tmp_path: Path) -> None:
    validator = load_validator()
    spec_path = tmp_path / "HRP-99-example.md"
    spec_path.write_text(
        "# HRP-99 — Example\n\n"
        "**Jira:** HRP-99\n\n"
        "## Objetivo\n\nA verifiable outcome.\n\n"
        "## Criterios de aceptación\n\n- [ ] One observable criterion.\n",
        encoding="utf-8",
    )

    assert validator.validate_spec(spec_path) == []


def test_spec_with_mismatched_jira_key_is_rejected(tmp_path: Path) -> None:
    validator = load_validator()
    spec_path = tmp_path / "HRP-99-example.md"
    spec_path.write_text(
        "# HRP-98 — Example\n\n"
        "**Jira:** HRP-98\n\n"
        "## Objetivo\n\nA verifiable outcome.\n\n"
        "## Criterios de aceptación\n\n- [ ] One observable criterion.\n",
        encoding="utf-8",
    )

    errors = validator.validate_spec(spec_path)

    assert any("heading" in error for error in errors)
    assert any("metadata" in error for error in errors)
