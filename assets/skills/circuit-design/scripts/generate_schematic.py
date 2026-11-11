#!/usr/bin/env python3
"""Generate KiCad schematic from component list.

Creates a valid KiCad 6/7 schematic with proper sheet structure.
Usage: python generate_schematic.py --bom components.csv --output design.kicad_sch
"""
import argparse
import json
import uuid
from pathlib import Path
import csv


def generate_uuid():
    return str(uuid.uuid4())


def parse_bom(bom_file):
    """Parse BOM CSV into component list."""
    components = []
    with open(bom_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('RefDes'):
                # Handle multiple refs like "R1;R2;R3"
                for ref in row['RefDes'].replace(',', ';').split(';'):
                    components.append({
                        'ref': ref.strip(),
                        'value': row.get('Value', ''),
                        'footprint': row.get('Footprint', ''),
                        'datasheet': row.get('Datasheet', ''),
                    })
    return components


def generate_schematic(components, title, rev='A', date='2026-01-01', company='Custom'):
    """Generate KiCad 6/7 schematic S-expression."""
    proj_uuid = generate_uuid()
    sheet_uuid = generate_uuid()

    lines = []
    lines.append(f'(kicad_sch')
    lines.append(f'\t(version 20211014)')
    lines.append(f'\t(generator eeschema)')
    lines.append(f'\t(uuid "{proj_uuid}")')
    lines.append(f'\t(paper "A4")')
    lines.append(f'\t(title_block')
    lines.append(f'\t\t(title "{title}")')
    lines.append(f'\t\t(date "{date}")')
    lines.append(f'\t\t(rev "{rev}")')
    lines.append(f'\t\t(company "{company}")')
    lines.append(f'\t)')

    # Library symbols
    lines.append(f'\t(lib_symbols')
    for comp in components:
        lib_id = f"UserLib:{comp['value'].replace(' ', '_')}"
        lines.append(f'\t\t(symbol "{lib_id}"')
        lines.append(f'\t\t\t(in_bom yes) (on_board yes)')
        lines.append(f'\t\t\t(property "Reference" "{comp["ref"]}" (at 0 0 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'\t\t\t(property "Value" "{comp["value"]}" (at 0 10 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'\t\t\t(property "Footprint" "{comp["footprint"]}" (at 0 20 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'\t\t\t(property "Datasheet" "{comp["datasheet"]}" (at 0 30 0) (effects (font (size 1.27 1.27))))')
        lines.append(f'\t\t)')
    lines.append(f'\t)')

    # Sheet
    lines.append(f'\t(sheet (uuid "{sheet_uuid}")')
    lines.append(f'\t\t(sheet_name "{title} Main")')
    lines.append(f'\t\t(sheet_file "main.kicad_sch" "utf-8")')
    lines.append(f'\t)')

    lines.append(f')')

    return '\n'.join(lines)


def generate_kicad_project(title, output_dir='.', layers=4):
    """Generate KiCad project file (.kicad_pro)."""
    proj_uuid = generate_uuid()

    project = {
        "general": {
            "version": 20211014,
            "uuid": proj_uuid
        },
        "pages": {
            "stock": [
                {"name": "A3", "width": 420, "height": 297},
                {"name": "A4", "width": 297, "height": 210},
                {"name": "A5", "width": 210, "height": 148}
            ],
            "custom": []
        },
        "net_settings": {
            "nc_run": 0,
            "max_net_count": 0,
            "exclude_filters": []
        },
        "pcbnew": {
            "board_layers_definition": {
                "layerCount": layers,
                "copperLayers": layers,
                "inplaneAxis": "R"
            }
        },
        "eeschema": {
            "symbol_lib_mapping": {},
            "symbol_lib_table": {
                "entries": []
            },
            "user_fields": []
        }
    }

    output_path = Path(output_dir) / f"{title}.kicad_pro"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(project, f, indent='\t')

    return output_path


def main():
    parser = argparse.ArgumentParser(description='Generate KiCad schematic from BOM')
    parser.add_argument('--bom', required=True, help='BOM CSV file')
    parser.add_argument('--title', default='Custom Design', help='Project title')
    parser.add_argument('--rev', default='A', help='Revision')
    parser.add_argument('--date', default='2026-01-01', help='Date (YYYY-MM-DD)')
    parser.add_argument('--company', default='Custom', help='Company name')
    parser.add_argument('--output', default='design.kicad_sch', help='Output schematic file')
    parser.add_argument('--project', action='store_true', help='Also generate .kicad_pro project file')
    parser.add_argument('--layers', type=int, default=4, help='PCB layer count (for project file)')

    args = parser.parse_args()

    # Parse BOM
    components = parse_bom(args.bom)
    print(f"Parsed {len(components)} components from BOM")

    # Generate schematic
    schematic = generate_schematic(
        components,
        title=args.title,
        rev=args.rev,
        date=args.date,
        company=args.company
    )

    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(schematic)
    print(f"✓ Schematic written to {args.output}")

    # Generate project file if requested
    if args.project:
        proj_file = generate_kicad_project(args.title, Path(args.output).parent, args.layers)
        print(f"✓ Project file written to {proj_file}")


if __name__ == '__main__':
    main()