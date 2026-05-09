"""JSON serialisation / deserialisation for CVRP instances.

The on-disk format carries a ``format_version`` key (currently ``1``) so
that future schema changes can be detected and migrated.
"""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from models import Instance, Node, Vehicle

FORMAT_VERSION = 1


def instance_to_dict(instance: Instance) -> dict[str, Any]:
    """Convert an :class:`Instance` to a JSON-serialisable dict."""
    data: dict[str, Any] = asdict(instance)
    # asdict converts tuples to lists; this is fine for JSON.
    return data


def instance_from_dict(data: dict[str, Any]) -> Instance:
    """Reconstruct an :class:`Instance` from a plain dict.

    Raises:
        ValueError: If the format_version is unsupported.
    """
    version = data.get("format_version")
    if version != FORMAT_VERSION:
        raise ValueError(
            f"Unsupported format_version {version!r} (expected {FORMAT_VERSION})"
        )

    return Instance(
        name=data["name"],
        depot=Node(**data["depot"]),
        customers=tuple(Node(**c) for c in data["customers"]),
        vehicles=tuple(Vehicle(**v) for v in data["vehicles"]),
        format_version=data["format_version"],
    )


def save_instance(instance: Instance, path: str | Path) -> None:
    """Write an instance to a JSON file.

    Args:
        instance: The CVRP instance to persist.
        path: Destination file path.
    """
    data = instance_to_dict(instance)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")  # trailing newline


def load_instance(path: str | Path) -> Instance:
    """Load an instance from a JSON file.

    Args:
        path: Source file path.

    Returns:
        The deserialised :class:`Instance`.
    """
    with open(path, encoding="utf-8") as fh:
        data: dict[str, Any] = json.load(fh)
    return instance_from_dict(data)