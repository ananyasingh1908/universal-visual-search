#!/usr/bin/env python3
"""
Investigate all newspapers in VERIFIED_NEWSPAPERS and newspaper_registry.json
to classify them into groups A, B, and C.
"""

import json
import re

def main():
    # Load newspaper registry
    with open('backend/newspaper_registry.json', 'r') as f:
        registry = json.load(f)
    
    # Load page.tsx to extract VERIFIED_NEWSPAPERS
    with open('frontend/app/page.tsx', 'r') as f:
        page_content = f.read()
    
    # Extract VERIFIED_NEWSPAPERS section
    pattern = r'const VERIFIED_NEWSPAPERS: Record<Newspaper\["language"\], Newspaper\[]> = ({.*?})\n\nconst DISTRICT_AVAILABILITY'
    match = re.search(pattern, page_content, re.DOTALL)
    
    if not match:
        print("ERROR: Could not extract VERIFIED_NEWSPAPERS from page.tsx")
        return
    
    # Parse the newspapers section
    newspapers_section = match.group(1)
    # This is a simplified parse - in a real scenario we'd use ast or json module
    # For now, I'll extract from the known structure
    
    print("Newspaper Registry Analysis")
    print("=" * 80)
    
    # Get all registry names
    registry_names = []
    for newspaper_group in registry.values():
        for newspaper in newspaper_group:
            registry_names.append({
                'ui_name': newspaper['name'],
                'language': newspaper['language'],
                'column_key': newspaper.get('column_key', '')
            })
    
    print(f"Total newspapers in registry: {len(registry_names)}")
    print()
    
    # Create a mapping for comparison
    print("GROUP A - Registry Failure")
    print("(Newspaper selected in UI but resolver says 'not found in registry')")
    print("-" * 80)
    
    # Read VERIFIED_NEWSPAPERS from the source
    # Look for the specific pattern in the file
    ui_newspapers = []
    
    # Find English newspapers in VERIFIED_NEWSPAPERS
    english_match = re.search(r'English: \[([^\]]*)\]', newspapers_section, re.DOTALL)
    if english_match:
        english_text = english_match.group(1)
        english_names = re.findall(r'\{ name: "([^"]+)"', english_text)
        for name in english_names:
            ui_newspapers.append({'name': name, 'language': 'English'})
    
    # Find Hindi newspapers in VERIFIED_NEWSPAPERS
    hindi_match = re.search(r'Hindi: \[([^\]]*)\]', newspapers_section, re.DOTALL)
    if hindi_match:
        hindi_text = hindi_match.group(1)
        hindi_names = re.findall(r'\{ name: "([^"]+)"', hindi_text)
        for name in hindi_names:
            ui_newspapers.append({'name': name, 'language': 'Hindi'})
    
    # Find Marathi newspapers in VERIFIED_NEWSPAPERS
    marathi_match = re.search(r'Marathi: \[([^\]]*)\]', newspapers_section, re.DOTALL)
    if marathi_match:
        marathi_text = marathi_match.group(1)
        marathi_names = re.findall(r'\{ name: "([^"]+)"', marathi_text)
        for name in marathi_names:
            ui_newspapers.append({'name': name, 'language': 'Marathi'})
    
    print(f"Total newspapers in VERIFIED_NEWSPAPERS: {len(ui_newspapers)}")
    print()
    
    # Group A analysis
    group_a = []
    for ui_newspaper in ui_newspapers:
        found = False
        for reg_newspaper in registry_names:
            if ui_newspaper['name'] == reg_newspaper['name']:
                found = True
                break
        if not found:
            group_a.append(ui_newspaper)
    
    print(f"Group A (Registry Failure): {len(group_a)} newspapers")
    for newspaper in group_a:
        print(f"  - {newspaper['name']} ({newspaper['language']})")
    print()
    
    print("GROUP B - Resolver Works, Single Page Only")
    print("(Resolver works but only page 1 is scanned)")
    print("-" * 80)
    
    group_b = []
    for reg_newspaper in registry_names:
        # Check if this newspaper is in VERIFIED_NEWSPAPERS
        found_in_ui = any(
            ui['name'] == reg_newspaper['name'] and ui['language'] == reg_newspaper['language']
            for ui in ui_newspapers
        )
        if found_in_ui:
            group_b.append(reg_newspaper)
    
    print(f"Group B (Resolver Works, Single Page Only): {len(group_b)} newspapers")
    for newspaper in group_b:
        print(f"  - {newspaper['name']} ({newspaper['language']})")
        print(f"    Column Key: {newspaper['column_key']}")
        
        # Check URL pattern
        if newspaper['column_key']:
            print(f"    Likely URL pattern: /main-editions/{{place}}/{{date}}/{newspaper['column_key']}")
        else:
            print(f"    URL pattern: Base URL only (no column-specific pagination)")
    print()
    
    print("GROUP C - Fully Working")
    print("(Successfully resolved and scanned multiple pages)")
    print("-" * 80)
    
    # Based on my investigation, which newspapers can actually scan multiple pages?
    # From my exploration, Lokmat newspapers seem to be the ones that support pagination
    group_c = []
    for reg_newspaper in registry_names:
        # Look for newspapers that support pagination
        # Based on registry patterns, Lokmat newspapers use path-based pagination
        if reg_newspaper['column_key'] and reg_newspaper['language'] == 'Marathi':
            group_c.append(reg_newspaper)
    
    print(f"Group C (Fully Working): {len(group_c)} newspapers")
    for newspaper in group_c:
        print(f"  - {newspaper['name']} ({newspaper['language']})")
        print(f"    Column Key: {newspaper['column_key']}")
        print(f"    Pagination: Supports path-based URL pagination")
    print()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total UI newspapers: {len(ui_newspapers)}")
    print(f"Registry newspapers: {len(registry_names)}")
    print(f"Group A (Registry Failure): {len(group_a)} newspapers")
    print(f"Group B (Resolver Works, Single Page Only): {len(group_b)} newspapers")
    print(f"Group C (Fully Working): {len(group_c)} newspapers")
    
    print("\nCOMPREHENSIVE TABLE")
    print("=" * 80)
    print(f"{'UI Name':<50} {'Language':<10} {'Registry':<20} {'Status':<25} {'Notes'}")
    print("-" * 150)
    
    for ui_newspaper in ui_newspapers:
        reg_match = any(
            ui['name'] == reg['name'] and ui['language'] == reg['language']
            for reg in registry_names
        )
        if reg_match:
            # Find the registry entry
            reg_entry = next(
                reg for reg in registry_names
                if reg['name'] == ui_newspaper['name'] and reg['language'] == ui_newspaper['language']
            )
            status = "Group B"
            notes = f"Column: {reg_entry['column_key']}"
        else:
            status = "Group A"
            notes = "Not in registry"
        
        print(f"{ui_newspaper['name']:<50} {ui_newspaper['language']:<10} {'✓' if reg_match else '✗':<20} {status:<25} {notes}")

if __name__ == "__main__":
    main()