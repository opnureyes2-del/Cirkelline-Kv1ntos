#!/usr/bin/env python3
"""
CKC Component Freeze Tool
Fryser en komponent så den ikke kan ændres uden at oprette ny version.
"""
import json
import hashlib
import os
import sys
from datetime import datetime
from pathlib import Path

def calculate_checksum(directory: Path) -> str:
    """Beregn SHA256 checksum for alle filer i komponenten."""
    hasher = hashlib.sha256()

    for filepath in sorted(directory.rglob("*")):
        if filepath.is_file() and filepath.name != "manifest.json":
            hasher.update(filepath.read_bytes())
            hasher.update(str(filepath.relative_to(directory)).encode())

    return hasher.hexdigest()[:16]

def freeze_component(component_path: str) -> dict:
    """Frys en komponent og opdater manifest."""
    path = Path(component_path)
    manifest_path = path / "manifest.json"

    if not manifest_path.exists():
        raise FileNotFoundError(f"Ingen manifest.json fundet i {component_path}")

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    if manifest.get("frozen"):
        print(f"⚠️  {manifest['name']} er allerede frozen")
        return manifest

    # Beregn checksum
    checksum = calculate_checksum(path)

    # Opdater manifest
    manifest["frozen"] = True
    manifest["checksum"] = checksum
    manifest["frozen_at"] = datetime.now().isoformat()
    manifest["status"] = "frozen"

    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"✅ {manifest['name']} v{manifest['version']} frozen")
    print(f"   Checksum: {checksum}")

    return manifest

def verify_component(component_path: str) -> bool:
    """Verificer at en frozen komponent ikke er ændret."""
    path = Path(component_path)
    manifest_path = path / "manifest.json"

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    if not manifest.get("frozen"):
        print(f"⚠️  {manifest['name']} er ikke frozen")
        return True

    current_checksum = calculate_checksum(path)
    stored_checksum = manifest.get("checksum", "")

    if current_checksum == stored_checksum:
        print(f"✅ {manifest['name']} integritet verificeret")
        return True
    else:
        print(f"❌ {manifest['name']} ÆNDRET! Forventet: {stored_checksum}, Fundet: {current_checksum}")
        return False

def list_components(base_path: str = None) -> list:
    """List alle komponenter og deres status."""
    if base_path is None:
        base_path = Path(__file__).parent
    else:
        base_path = Path(base_path)

    components = []

    for category in ["kommandanter", "teams", "systems"]:
        category_path = base_path / category
        if not category_path.exists():
            continue

        for comp_dir in category_path.iterdir():
            if comp_dir.is_dir():
                manifest_path = comp_dir / "manifest.json"
                if manifest_path.exists():
                    with open(manifest_path) as f:
                        manifest = json.load(f)
                    components.append({
                        "path": str(comp_dir),
                        "name": manifest.get("name"),
                        "version": manifest.get("version"),
                        "type": manifest.get("type"),
                        "status": manifest.get("status"),
                        "frozen": manifest.get("frozen", False)
                    })

    return components

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("CKC Component Freeze Tool")
        print("=" * 40)
        print("\nBrug:")
        print("  python freeze_component.py list              # List alle komponenter")
        print("  python freeze_component.py freeze <path>     # Frys komponent")
        print("  python freeze_component.py verify <path>     # Verificer integritet")
        print("  python freeze_component.py freeze-all        # Frys alle stable komponenter")
        print("\nKomponenter:")

        for comp in list_components():
            status = "🔒" if comp["frozen"] else "📝"
            print(f"  {status} {comp['name']} v{comp['version']} ({comp['type']}) - {comp['status']}")

        sys.exit(0)

    command = sys.argv[1]

    if command == "list":
        for comp in list_components():
            status = "🔒 FROZEN" if comp["frozen"] else "📝 OPEN"
            print(f"{comp['name']:20} v{comp['version']:8} {comp['type']:12} {status}")

    elif command == "freeze" and len(sys.argv) > 2:
        freeze_component(sys.argv[2])

    elif command == "verify" and len(sys.argv) > 2:
        verify_component(sys.argv[2])

    elif command == "freeze-all":
        base = Path(__file__).parent
        for comp in list_components(str(base)):
            if not comp["frozen"] and comp["status"] in ["stable", "testing"]:
                freeze_component(comp["path"])

    else:
        print(f"Ukendt kommando: {command}")
        sys.exit(1)
