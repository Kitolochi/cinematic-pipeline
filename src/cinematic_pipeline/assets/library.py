"""Asset library — local caching, metadata, search.

Downloads assets once, stores them in ~/.cinematic-pipeline/assets/
with JSON metadata for reuse across projects.
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_LIBRARY_DIR = Path.home() / ".cinematic-pipeline" / "assets"


@dataclass
class AssetMetadata:
    """Metadata for a cached asset."""

    asset_id: str
    source: str  # "polyhaven", "sketchfab", "local"
    asset_type: str  # "hdri", "texture", "model"
    name: str = ""
    file_path: str = ""
    tags: list[str] = field(default_factory=list)
    resolution: str = ""
    license: str = "CC0"
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "asset_id": self.asset_id,
            "source": self.source,
            "asset_type": self.asset_type,
            "name": self.name,
            "file_path": self.file_path,
            "tags": self.tags,
            "resolution": self.resolution,
            "license": self.license,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, d: dict) -> AssetMetadata:
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class AssetLibrary:
    """Local asset library with download-once caching."""

    def __init__(self, library_dir: str | Path | None = None):
        self.library_dir = Path(library_dir) if library_dir else DEFAULT_LIBRARY_DIR
        self.manifest_path = self.library_dir / "manifest.json"
        self._ensure_dirs()
        self._manifest: dict[str, AssetMetadata] = {}
        self._load_manifest()

    def _ensure_dirs(self):
        """Create library directory structure."""
        for subdir in ["hdris", "textures", "models"]:
            (self.library_dir / subdir).mkdir(parents=True, exist_ok=True)

    def _load_manifest(self):
        """Load manifest from disk."""
        if self.manifest_path.exists():
            data = json.loads(self.manifest_path.read_text())
            self._manifest = {
                k: AssetMetadata.from_dict(v) for k, v in data.items()
            }

    def _save_manifest(self):
        """Persist manifest to disk."""
        data = {k: v.to_dict() for k, v in self._manifest.items()}
        self.manifest_path.write_text(json.dumps(data, indent=2))

    def _make_key(self, source: str, asset_id: str, resolution: str = "") -> str:
        """Create a unique key for an asset."""
        parts = [source, asset_id]
        if resolution:
            parts.append(resolution)
        return ":".join(parts)

    def has(self, source: str, asset_id: str, resolution: str = "") -> bool:
        """Check if an asset is already cached."""
        key = self._make_key(source, asset_id, resolution)
        if key not in self._manifest:
            return False
        # Verify file still exists
        meta = self._manifest[key]
        return meta.file_path and os.path.exists(meta.file_path)

    def get(self, source: str, asset_id: str, resolution: str = "") -> AssetMetadata | None:
        """Get cached asset metadata, or None if not cached."""
        key = self._make_key(source, asset_id, resolution)
        meta = self._manifest.get(key)
        if meta and meta.file_path and os.path.exists(meta.file_path):
            return meta
        return None

    def register(self, metadata: AssetMetadata) -> None:
        """Register a downloaded asset in the library."""
        key = self._make_key(metadata.source, metadata.asset_id, metadata.resolution)
        self._manifest[key] = metadata
        self._save_manifest()

    def register_file(
        self,
        source: str,
        asset_id: str,
        asset_type: str,
        file_path: str,
        name: str = "",
        resolution: str = "",
        tags: list[str] | None = None,
        copy_to_library: bool = False,
    ) -> AssetMetadata:
        """Register a file as a library asset, optionally copying it."""
        if copy_to_library:
            dest_dir = self.library_dir / f"{asset_type}s"
            dest = dest_dir / os.path.basename(file_path)
            if not dest.exists():
                shutil.copy2(file_path, dest)
            file_path = str(dest)

        meta = AssetMetadata(
            asset_id=asset_id,
            source=source,
            asset_type=asset_type,
            name=name or asset_id,
            file_path=str(file_path),
            tags=tags or [],
            resolution=resolution,
        )
        self.register(meta)
        return meta

    def list_assets(self, asset_type: str = "") -> list[AssetMetadata]:
        """List all cached assets, optionally filtered by type."""
        assets = list(self._manifest.values())
        if asset_type:
            assets = [a for a in assets if a.asset_type == asset_type]
        return assets

    def search(self, query: str) -> list[AssetMetadata]:
        """Search assets by name, tags, or ID."""
        query_lower = query.lower()
        results = []
        for meta in self._manifest.values():
            if (
                query_lower in meta.name.lower()
                or query_lower in meta.asset_id.lower()
                or any(query_lower in t.lower() for t in meta.tags)
            ):
                results.append(meta)
        return results

    def remove(self, source: str, asset_id: str, resolution: str = "", delete_file: bool = False) -> bool:
        """Remove an asset from the library."""
        key = self._make_key(source, asset_id, resolution)
        if key not in self._manifest:
            return False
        meta = self._manifest.pop(key)
        if delete_file and meta.file_path and os.path.exists(meta.file_path):
            os.remove(meta.file_path)
        self._save_manifest()
        return True

    @property
    def count(self) -> int:
        return len(self._manifest)

    def summary(self) -> str:
        """Human-readable summary of library contents."""
        by_type: dict[str, int] = {}
        for meta in self._manifest.values():
            by_type[meta.asset_type] = by_type.get(meta.asset_type, 0) + 1
        parts = [f"{count} {atype}(s)" for atype, count in sorted(by_type.items())]
        return f"Asset Library: {self.count} assets ({', '.join(parts) or 'empty'})"
