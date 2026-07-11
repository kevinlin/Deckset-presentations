"""Theme compiler: parse design-md DESIGN.md files and compile to CSS themes.

Reads YAML token systems from design-md/*/DESIGN.md, resolves internal
references, maps tokens to the CSS variable contract, and emits per-theme
CSS files plus a themes.json manifest.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict

import yaml

from models import ThemeCompileError

logger = logging.getLogger(__name__)

_REFERENCE_RE = re.compile(r"\{([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_.-]+)\}")


def parse_design_file(path: Path) -> Dict[str, Any]:
    """Strip ``---`` fences and trailing markdown notes, then YAML-parse the body.

    Raises :class:`ThemeCompileError` on unreadable/invalid YAML or
    non-dict result.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ThemeCompileError(
            f"Cannot read design file: {exc}", context={"path": str(path)}
        ) from exc

    lines = raw.split("\n")

    fence_indices = [i for i, line in enumerate(lines) if line.strip() == "---"]
    if len(fence_indices) < 2:
        raise ThemeCompileError(
            "Design file missing YAML fences (expected two '---' lines)",
            context={"path": str(path)},
        )

    yaml_body = "\n".join(lines[fence_indices[0] + 1 : fence_indices[1]])

    try:
        data = yaml.safe_load(yaml_body)
    except yaml.YAMLError as exc:
        raise ThemeCompileError(
            f"Invalid YAML in design file: {exc}", context={"path": str(path)}
        ) from exc

    if not isinstance(data, dict):
        raise ThemeCompileError(
            f"Expected a YAML mapping, got {type(data).__name__}",
            context={"path": str(path)},
        )

    return data


def resolve_references(data: Dict[str, Any]) -> Dict[str, Any]:
    """Replace every ``{section.key}`` string with its target value.

    Iterative with a visited set; raises :class:`ThemeCompileError` on
    cycles or unknown targets. Non-string and non-reference values pass
    through unchanged.
    """
    flat: Dict[str, Any] = {}
    _flatten(data, "", flat)

    MAX_ITERATIONS = len(flat) + 1
    for _ in range(MAX_ITERATIONS):
        changed = False
        for key, value in list(flat.items()):
            if not isinstance(value, str):
                continue
            match = _REFERENCE_RE.search(value)
            if not match:
                continue
            ref_key = f"{match.group(1)}.{match.group(2)}"
            if ref_key not in flat:
                is_nested = any(
                    k.startswith(ref_key + ".") for k in flat
                )
                if is_nested:
                    continue
                raise ThemeCompileError(
                    f"Unknown reference '{{{ref_key}}}' in key '{key}'"
                )
            target = flat[ref_key]
            if isinstance(target, str) and _REFERENCE_RE.search(target):
                changed = True
                continue
            new_value = value[: match.start()] + str(target) + value[match.end() :]
            if new_value != value:
                flat[key] = new_value
                changed = True
        if not changed:
                truly_unresolved = []
                for k, v in flat.items():
                    if not isinstance(v, str):
                        continue
                    m = _REFERENCE_RE.search(v)
                    if not m:
                        continue
                    rk = f"{m.group(1)}.{m.group(2)}"
                    is_nested = any(
                        fk.startswith(rk + ".") for fk in flat
                    )
                    if not is_nested:
                        truly_unresolved.append(k)
                if truly_unresolved:
                    raise ThemeCompileError(
                        f"Circular reference detected involving: {truly_unresolved}"
                    )
                break
    else:
        truly_unresolved = []
        for k, v in flat.items():
            if not isinstance(v, str):
                continue
            m = _REFERENCE_RE.search(v)
            if not m:
                continue
            rk = f"{m.group(1)}.{m.group(2)}"
            is_nested = any(fk.startswith(rk + ".") for fk in flat)
            if not is_nested:
                truly_unresolved.append(k)
        if truly_unresolved:
            raise ThemeCompileError(
                f"Circular references detected: {truly_unresolved}"
            )

    return _unflatten(flat)


def _flatten(
    obj: Any, prefix: str, out: Dict[str, Any]
) -> None:
    """Recursively flatten a nested dict into dotted keys."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{prefix}.{k}" if prefix else k
            _flatten(v, new_key, out)
    else:
        out[prefix] = obj


def _unflatten(flat: Dict[str, Any]) -> Dict[str, Any]:
    """Rebuild nested dict from dotted keys."""
    result: Dict[str, Any] = {}
    for key, value in flat.items():
        parts = key.split(".")
        current = result
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = value
    return result
