#!/usr/bin/env python3
"""
CKC Component Documentation Export
Genererer dokumentation for komponenter.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import List

def generate_component_readme(manifest: dict, output_path: Path):
    """Generer README.md for en komponent."""
    content = f"""# {manifest['name']}

**Version:** {manifest['version']}
**Type:** {manifest['type']}
**Status:** {manifest['status']}
**Created:** {manifest.get('created', 'Unknown')}
**Author:** {manifest.get('author', 'Unknown')}

---

## Description

{manifest.get('description', 'No description provided.')}

## Capabilities

"""

    for cap in manifest.get('capabilities', []):
        content += f"- `{cap}`\n"

    content += "\n## Dependencies\n\n"
    for dep, version in manifest.get('dependencies', {}).items():
        content += f"- **{dep}**: {version}\n"

    # Type-specific sections
    if manifest['type'] == 'kommandant':
        content += "\n## Egenskaber (Properties)\n\n"
        for egen in manifest.get('egenskaber', []):
            content += f"### {egen['name']}\n"
            content += f"- **File:** `{egen.get('file', 'N/A')}`\n"
            if 'description' in egen:
                content += f"- **Description:** {egen['description']}\n"
            content += "\n"

    elif manifest['type'] == 'team':
        content += "\n## Agents\n\n"
        for agent in manifest.get('agents', []):
            content += f"### {agent['name']}\n"
            content += f"- **File:** `{agent.get('file', 'N/A')}`\n"
            content += f"- **Role:** {agent.get('role', 'N/A')}\n\n"

    elif manifest['type'] == 'system':
        content += "\n## Components\n\n"
        for comp in manifest.get('components', []):
            content += f"- **{comp['name']}**: `{comp.get('file', 'N/A')}`\n"

        if 'endpoints' in manifest:
            content += "\n## API Endpoints\n\n"
            for endpoint in manifest['endpoints']:
                content += f"- `{endpoint}`\n"

    content += f"""
## Source

**Location:** `{manifest.get('source', 'N/A')}`

## Tests

- **Unit Tests:** `{manifest.get('tests', {}).get('unit', 'N/A')}`
- **Coverage:** {manifest.get('tests', {}).get('coverage', 'N/A')}

---

*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""

    if manifest.get('frozen'):
        content += f"\n**🔒 FROZEN** - Checksum: `{manifest.get('checksum', 'N/A')}`\n"

    output_path.write_text(content, encoding='utf-8')
    return content

def generate_index(components: List[dict], output_path: Path):
    """Generer index over alle komponenter."""
    content = f"""# CKC Components Index

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## Overview

| Name | Version | Type | Status | Frozen |
|------|---------|------|--------|--------|
"""

    for comp in components:
        frozen = "🔒" if comp.get('frozen') else "📝"
        content += f"| {comp['name']} | {comp['version']} | {comp['type']} | {comp['status']} | {frozen} |\n"

    content += """
---

## Kommandanter

"""
    for comp in [c for c in components if c['type'] == 'kommandant']:
        content += f"### [{comp['name']}](kommandanter/{comp['name']}/README.md)\n"
        content += f"{comp.get('description', 'No description')}\n\n"

    content += """
## Teams

"""
    for comp in [c for c in components if c['type'] == 'team']:
        content += f"### [{comp['name']}](teams/{comp['name']}/README.md)\n"
        content += f"{comp.get('description', 'No description')}\n\n"

    content += """
## Systems

"""
    for comp in [c for c in components if c['type'] == 'system']:
        content += f"### [{comp['name']}](systems/{comp['name']}/README.md)\n"
        content += f"{comp.get('description', 'No description')}\n\n"

    output_path.write_text(content, encoding='utf-8')
    return content

def export_all_docs(base_path: str = None):
    """Eksporter dokumentation for alle komponenter."""
    if base_path is None:
        base_path = Path(__file__).parent
    else:
        base_path = Path(base_path)

    all_components = []

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

                    # Generate README
                    readme_path = comp_dir / "docs" / "README.md"
                    readme_path.parent.mkdir(exist_ok=True)
                    generate_component_readme(manifest, readme_path)
                    print(f"✅ Generated: {readme_path}")

                    all_components.append(manifest)

    # Generate index
    index_path = base_path / "INDEX.md"
    generate_index(all_components, index_path)
    print(f"✅ Generated: {index_path}")

    return all_components

if __name__ == "__main__":
    print("CKC Documentation Export")
    print("=" * 40)
    export_all_docs()
