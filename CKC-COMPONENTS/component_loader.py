#!/usr/bin/env python3
"""
CKC Component Loader / Import System
Loader komponenter fra CKC-COMPONENTS strukturen.
"""
import json
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class ComponentInfo:
    """Information om en loaded komponent."""
    name: str
    version: str
    type: str
    status: str
    frozen: bool
    path: Path
    manifest: dict
    module: Optional[Any] = None

class CKCComponentLoader:
    """Loader og manager for CKC komponenter."""

    def __init__(self, base_path: str = None):
        if base_path is None:
            self.base_path = Path(__file__).parent
        else:
            self.base_path = Path(base_path)

        self._components: Dict[str, ComponentInfo] = {}
        self._scan_components()

    def _scan_components(self):
        """Scan alle komponenter i strukturen."""
        for category in ["kommandanter", "teams", "systems"]:
            category_path = self.base_path / category
            if not category_path.exists():
                continue

            for comp_dir in category_path.iterdir():
                if comp_dir.is_dir():
                    manifest_path = comp_dir / "manifest.json"
                    if manifest_path.exists():
                        self._load_manifest(comp_dir, manifest_path)

    def _load_manifest(self, comp_dir: Path, manifest_path: Path):
        """Load manifest og registrer komponent."""
        with open(manifest_path) as f:
            manifest = json.load(f)

        comp_info = ComponentInfo(
            name=manifest.get("name"),
            version=manifest.get("version"),
            type=manifest.get("type"),
            status=manifest.get("status"),
            frozen=manifest.get("frozen", False),
            path=comp_dir,
            manifest=manifest
        )

        self._components[comp_info.name] = comp_info

    def list_components(self, type_filter: str = None) -> List[ComponentInfo]:
        """List alle komponenter, optionelt filtreret på type."""
        components = list(self._components.values())
        if type_filter:
            components = [c for c in components if c.type == type_filter]
        return components

    def get_component(self, name: str) -> Optional[ComponentInfo]:
        """Hent specifik komponent."""
        return self._components.get(name)

    def get_kommandanter(self) -> List[ComponentInfo]:
        """Hent alle kommandanter."""
        return self.list_components("kommandant")

    def get_teams(self) -> List[ComponentInfo]:
        """Hent alle teams."""
        return self.list_components("team")

    def get_systems(self) -> List[ComponentInfo]:
        """Hent alle systems."""
        return self.list_components("system")

    def load_source(self, name: str) -> Optional[Any]:
        """Load source kode for en komponent."""
        comp = self.get_component(name)
        if not comp:
            return None

        source_path = comp.manifest.get("source")
        if not source_path:
            return None

        # Konverter relativ path til absolut
        if not Path(source_path).is_absolute():
            # Antag det er relativt til cirkelline-system root
            source_path = self.base_path.parent / source_path

        if not Path(source_path).exists():
            return None

        # Dynamic import
        spec = importlib.util.spec_from_file_location(name, source_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            comp.module = module
            return module

        return None

    def check_dependencies(self, name: str) -> Dict[str, bool]:
        """Check om dependencies er opfyldt."""
        comp = self.get_component(name)
        if not comp:
            return {}

        deps = comp.manifest.get("dependencies", {})
        results = {}

        for dep_name, version_req in deps.items():
            # Simple check - bare se om pakken findes
            try:
                if dep_name == "cirkelline-system":
                    results[dep_name] = True  # Vi er i cirkelline-system
                elif dep_name == "agno":
                    import agno
                    results[dep_name] = True
                else:
                    importlib.import_module(dep_name.replace("-", "_"))
                    results[dep_name] = True
            except ImportError:
                results[dep_name] = False

        return results

    def export_component(self, name: str, output_dir: str) -> bool:
        """Eksporter en komponent til standalone mappe."""
        import shutil

        comp = self.get_component(name)
        if not comp:
            return False

        output_path = Path(output_dir) / name
        output_path.mkdir(parents=True, exist_ok=True)

        # Kopier manifest
        shutil.copy(comp.path / "manifest.json", output_path / "manifest.json")

        # Kopier source hvis den findes
        source_path = comp.manifest.get("source")
        if source_path:
            abs_source = self.base_path.parent / source_path
            if abs_source.exists():
                if abs_source.is_file():
                    shutil.copy(abs_source, output_path / Path(source_path).name)
                else:
                    shutil.copytree(abs_source, output_path / "src", dirs_exist_ok=True)

        return True

# Singleton instance
_loader: Optional[CKCComponentLoader] = None

def get_loader() -> CKCComponentLoader:
    """Hent global component loader instance."""
    global _loader
    if _loader is None:
        _loader = CKCComponentLoader()
    return _loader

if __name__ == "__main__":
    loader = get_loader()

    print("CKC Component Loader")
    print("=" * 50)

    print("\n📦 Kommandanter:")
    for comp in loader.get_kommandanter():
        status = "🔒" if comp.frozen else "📝"
        print(f"   {status} {comp.name} v{comp.version}")

    print("\n👥 Teams:")
    for comp in loader.get_teams():
        status = "🔒" if comp.frozen else "📝"
        print(f"   {status} {comp.name} v{comp.version}")

    print("\n⚙️  Systems:")
    for comp in loader.get_systems():
        status = "🔒" if comp.frozen else "📝"
        print(f"   {status} {comp.name} v{comp.version}")
