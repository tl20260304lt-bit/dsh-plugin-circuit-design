#!/usr/bin/env python3
"""BOM integrity check - verify BOM matches schematic components."""
import csv
import argparse
from pathlib import Path
import re

def parse_sch_components(sch_file):
    """Extract component references from KiCad schematic."""
    refs = set()
    with open(sch_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Match (symbol (lib_id "U1:*") (at ...) (property "Reference" "U1" ...))
    for match in re.finditer(r'\(property\s+"Reference"\s+"(U\d+|R\d+|C\d+|L\d+|D\d+|J\d+|Y\d+)"', content):
        refs.add(match.group(1))
    
    return refs

def parse_bom(bom_file):
    """Parse BOM CSV file."""
    refs = set()
    with open(bom_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Try common column names
            ref = row.get('RefDes') or row.get('Reference') or row.get('Designator')
            if ref:
                # Handle multiple refs like "R1;R2;R3"
                for r in ref.replace(',', ';').split(';'):
                    refs.add(r.strip())
    return refs

def main():
    parser = argparse.ArgumentParser(description='Check BOM vs schematic component match')
    parser.add_argument('--bom', required=True, help='BOM CSV file')
    parser.add_argument('--sheet', required=False, help='KiCad schematic file (optional)')
    args = parser.parse_args()
    
    bom_refs = parse_bom(args.bom)
    print(f"BOM components: {len(bom_refs)}")
    
    if args.sheet:
        sch_refs = parse_sch_components(args.sheet)
        print(f"Schematic components: {len(sch_refs)}")
        
        missing_in_bom = sch_refs - bom_refs
        missing_in_sheet = bom_refs - sch_refs
        
        if missing_in_bom:
            print(f"\n⚠️  In schematic but missing in BOM ({len(missing_in_bom)}):")
            for ref in sorted(missing_in_bom)[:20]:
                print(f"  {ref}")
        
        if missing_in_sheet:
            print(f"\n⚠️  In BOM but missing in schematic ({len(missing_in_sheet)}):")
            for ref in sorted(missing_in_sheet)[:20]:
                print(f"  {ref}")
        
        if not missing_in_bom and not missing_in_sheet:
            print("\n✅ BOM and schematic match perfectly!")
        else:
            print(f"\n❌ Found {len(missing_in_bom)} schematic mismatches, {len(missing_in_sheet)} BOM mismatches")
    else:
        print(f"\n✅ BOM parsed successfully: {len(bom_refs)} components")

if __name__ == '__main__':
    main()