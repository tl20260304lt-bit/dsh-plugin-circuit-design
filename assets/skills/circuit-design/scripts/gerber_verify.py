#!/usr/bin/env python3
"""Verify Gerber files before sending to fab house.

Checks layer count, drill files, and file integrity.
Usage: python gerber_verify.py --gerber-dir ./gerber --drill-file ./drill.exc
"""
import argparse
from pathlib import Path
import os


def list_gerber_files(gerber_dir):
    """List all Gerber and drill files."""
    gerber_dir = Path(gerber_dir)
    gerbers = list(gerber_dir.glob('*.ger')) + list(gerber_dir.glob('*.gbr')) + list(gerber_dir.glob('*.RS274X'))
    drills = list(gerber_dir.glob('*.drl')) + list(gerber_dir.glob('*.exc'))
    other = list(gerber_dir.glob('*')) - gerbers - drills

    return {
        'gerbers': gerbers,
        'drills': drills,
        'other': other
    }


def verify_gerber_content(gerber_file):
    """Basic Gerber file content check."""
    issues = []

    with open(gerber_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Check for RS-274X format
    if '%FSLAX' not in content and '%FSLAY' not in content:
        issues.append("Missing format statement (FSLAX/FSLAY)")

    # Check for aperture definitions
    if '%AD' not in content:
        issues.append("Missing aperture definitions")

    # Check for end marker
    if 'M02' not in content:
        issues.append("Missing end marker (M02)")

    # Check for coordinate data
    if not any(line.strip().endswith('*') and len(line.strip()) > 2 for line in content.split('\n')[10:]):
        issues.append("No coordinate data found")

    return issues


def count_layers(gerber_files):
    """Count copper and non-copper layers."""
    copper = 0
    solder_mask = 0
    silk = 0
    fab = 0

    for f in gerber_files:
        name = f.stem.upper()
        if any(x in name for x in ['CU', 'TOP', 'BOTTOM', 'INNER', 'LAYER']):
            copper += 1
        elif 'MASK' in name or 'PASTE' in name:
            solder_mask += 1
        elif 'SILK' in name:
            silk += 1
        elif 'FAB' in name:
            fab += 1

    return {
        'copper': copper,
        'solder_mask': solder_mask,
        'silk': silk,
        'fab': fab,
        'total': len(gerber_files)
    }


def main():
    parser = argparse.ArgumentParser(description='Verify Gerber files')
    parser.add_argument('--gerber-dir', required=True, help='Gerber directory')
    parser.add_argument('--drill-file', required=False, help='Drill file (optional)')
    parser.add_argument('--expected-layers', type=int, default=4, help='Expected copper layers')
    parser.add_argument('--output', default='gerber_report.txt', help='Output report file')

    args = parser.parse_args()

    # List files
    files = list_gerber_files(args.gerber_dir)
    print(f"Found {len(files['gerbers'])} Gerber files")
    print(f"Found {len(files['drills'])} drill files")

    # Count layers
    layers = count_layers(files['gerbers'])
    print(f"\nLayer count:")
    print(f"  Copper: {layers['copper']}")
    print(f"  Solder mask: {layers['solder_mask']}")
    print(f"  Silk screen: {layers['silk']}")
    print(f"  Fab: {layers['fab']}")

    # Check copper layer count
    if layers['copper'] != args.expected_layers:
        print(f"\n⚠️  Copper layer count mismatch: expected {args.expected_layers}, found {layers['copper']}")

    # Verify each Gerber file
    print("\nVerifying Gerber files...")
    all_issues = []
    for gerber in files['gerbers']:
        issues = verify_gerber_content(gerber)
        if issues:
            print(f"  ❌ {gerber.name}: {len(issues)} issue(s)")
            all_issues.extend([(gerber.name, issue) for issue in issues])
        else:
            print(f"  ✅ {gerber.name}")

    # Check drill files
    if files['drills']:
        print(f"\n✓ Drill files present: {len(files['drills'])}")
    else:
        print(f"\n⚠️  No drill files found (may be okay for board without through-holes)")

    # Summary
    print(f"\n{'='*50}")
    if not all_issues:
        print("✅ All Gerber files passed verification")
    else:
        print(f"❌ Found {len(all_issues)} issue(s):")
        for filename, issue in all_issues:
            print(f"  {filename}: {issue}")

    # Save report
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write("Gerber Verification Report\n")
        f.write(f"{'='*50}\n\n")
        f.write(f"Gerber directory: {args.gerber_dir}\n")
        f.write(f"Total Gerber files: {len(files['gerbers'])}\n")
        f.write(f"Drill files: {len(files['drills'])}\n\n")
        f.write(f"Layer summary:\n")
        for k, v in layers.items():
            f.write(f"  {k}: {v}\n")
        f.write(f"\n")

        if all_issues:
            f.write(f"Issues found:\n")
            for filename, issue in all_issues:
                f.write(f"  {filename}: {issue}\n")
        else:
            f.write("No issues found.\n")

    print(f"\nReport saved to: {args.output}")


if __name__ == '__main__':
    main()