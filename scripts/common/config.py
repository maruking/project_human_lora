"""Configuration boundary: explicit CLI > local YAML > internal fallback.

The example is used only when config.yaml is absent. Partial local files do not
merge the example, so omitted settings retain the script's documented fallback.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PureWindowsPath
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class ConfigError(ValueError):
    """An actionable configuration error (no model loading involved)."""


def validate_config(config: dict, schema_path: Path | None = None) -> None:
    try:
        import jsonschema
    except ImportError as exc:
        raise ConfigError("Missing jsonschema; install requirements.txt") from exc
    path = schema_path or PROJECT_ROOT / "config/config.schema.json"
    try:
        schema = json.loads(path.read_text(encoding="utf-8-sig"))
        jsonschema.Draft202012Validator.check_schema(schema)
        errors = sorted(jsonschema.Draft202012Validator(schema).iter_errors(config),
                        key=lambda error: str(list(error.absolute_path)))
    except (OSError, ValueError, jsonschema.SchemaError) as exc:
        raise ConfigError(f"Cannot read configuration schema {path}: {exc}") from exc
    if errors:
        details = "; ".join(f"{'.'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
                            for e in errors[:8])
        raise ConfigError(f"Configuration validation failed: {details}")


def load_config(path: str | Path | None = None, *, project_root: Path | None = None,
                validate: bool = True) -> dict[str, Any]:
    root = Path(project_root or PROJECT_ROOT).resolve()
    if path is None:
        source = root / "config/config.yaml"
        if not source.is_file():
            source = root / "config/config.example.yaml"
    else:
        source = resolve_project_path(path, root)
    try:
        import yaml
    except ImportError as exc:
        raise ConfigError("Missing PyYAML; install requirements.txt") from exc
    try:
        data = yaml.safe_load(source.read_text(encoding="utf-8-sig"))
    except (OSError, yaml.YAMLError, UnicodeError) as exc:
        raise ConfigError(f"Cannot load YAML configuration {source}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"Configuration {source} must contain a YAML mapping")
    if validate:
        validate_config(data, root / "config/config.schema.json")
    for value in get_section(data, "paths").values():
        resolve_project_path(value, root)
    return data


def get_section(config: dict, name: str) -> dict:
    section = config.get(name, {})
    if not isinstance(section, dict):
        raise ConfigError(f"Configuration section '{name}' must be a mapping")
    return section


def resolve_project_path(value: str | Path, project_root: Path | None = None) -> Path:
    """Resolve relative settings beneath root; allow explicit absolute inputs.

    Relative traversal (including symlink traversal) outside root is rejected.
    Windows drive-relative paths are ambiguous and therefore rejected.
    """
    root = Path(project_root or PROJECT_ROOT).resolve()
    windows = PureWindowsPath(str(value))
    if windows.drive and not windows.is_absolute():
        raise ConfigError(f"Use an absolute Windows path, not drive-relative '{value}'")
    path = Path(str(value).replace("\\", "/"))
    if path.is_absolute():
        return path.resolve()
    if windows.is_absolute():
        raise ConfigError(f"Windows absolute path cannot be used on this operating system: {value}")
    result = (root / path).resolve()
    if not result.is_relative_to(root):
        raise ConfigError(f"Relative path escapes project root: {value}")
    return result


def configure_parser(parser: argparse.ArgumentParser, config: dict, section: str,
                     *, aliases: dict[str, str] | None = None,
                     paths: dict[str, str] | None = None) -> None:
    """Set defaults before parse_args; explicit CLI always wins, even 0/False.

    'paths' maps argument destinations to shared path keys. Path-valued CLI
    overrides use the same project-root convention as configuration paths.
    """
    settings = get_section(config, section)
    shared_paths = get_section(config, "paths")
    aliases = aliases or {}
    paths = paths or {}
    defaults = {}
    for action in parser._actions:
        if action.dest in ("help", "config"):
            continue
        key = aliases.get(action.dest, action.dest)
        if action.dest in paths and paths[action.dest] in shared_paths:
            value = shared_paths[paths[action.dest]]
        elif key in settings:
            value = settings[key]
        else:
            continue
        if action.type is Path and value is not None:
            try:
                value = resolve_config_path(value, config)
            except ConfigError as exc:
                parser.error(str(exc))
        defaults[action.dest] = value
    parser.set_defaults(**defaults)
    # Review copies are disposable outputs, never source roots (all STEP CLIs).
    from common.step3_review import review_roots, require_source
    roots = review_roots(config)
    input_destinations = {'images', 'source', 'supplemental', 'supplemental_dir', 'reference', 'videos', 'input'}
    def input_path(value):
        return require_source(resolve_project_path(value), roots)
    # Resolve explicit relative CLI paths too, independently of the caller's cwd.
    for action in parser._actions:
        if action.type is Path:
            if action.dest in input_destinations:
                if action.default is not None:
                    require_source(action.default, roots)
                action.type = input_path
            else:
                action.type = resolve_project_path


def resolve_config_path(value: str | Path, config: dict) -> Path:
    for prefix, key in (("@reports/", "reports_dir"), ("@candidates/", "candidates_dir")):
        if str(value).startswith(prefix):
            base = get_section(config, "paths").get(key, {"reports_dir": "output/reports", "candidates_dir": "work/candidates"}[key])
            # Check the suffix independently so tokens cannot escape their directory.
            return resolve_project_path(str(value)[len(prefix):], resolve_project_path(base))
    return resolve_project_path(value)


def load_for_cli() -> dict:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config", type=Path)
    args, _ = parser.parse_known_args()
    try:
        return load_config(args.config)
    except ConfigError as exc:
        parser.error(str(exc))


def configure_constants(namespace: dict, config: dict, section: str,
                        names: list[str]) -> None:
    settings = get_section(config, section)
    for name in names:
        key = {"MIN_SKIN_TEXTURE_CLOSEUP": "min_skin_texture_close_up"}.get(name, name.lower())
        if key in settings:
            namespace[name] = settings[key]
