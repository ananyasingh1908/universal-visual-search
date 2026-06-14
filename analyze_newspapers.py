#!/usr/bin/env python3
"""
Analyze newspaper matching between VERIFIED_NEWSPAPERS and newspaper_registry.json
"""

import json
import re
import sys

def extract_ui_newspapers():
    """Extract newspapers from VERIFIED_NEWSPAPERS in page.tsx"""
    with open('frontend/app/page.tsx', 'r') as f:
        content = f.read()
    
    # Find the VERIFIED_NEWSPAPERS section
    pattern = r'const VERIFIED_NEWSPAPERS: Record<Newspaper\["language"\], Newspaper\[]> = ({.*?})\n\nconst DISTRICT_AVAILABILITY'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        print("ERROR: Could not extract VERIFIED_NEWSPAPERS from page.tsx")
        return []
    
    newspapers_section = match.group(1)
    
    ui_newspapers = []
    
    # Extract English newspapers
    english_match = re.search(r'English: \[(.*?)\]', newspapers_section, re.DOTALL)
    if english_match:
        english_text = english_match.group(1)
        # Extract name, language, and columnKey
        english_names = re.findall(r'name: "([^"]+)"', english_text)
        for name in english_names:
            ui_newspapers.append({
                'name': name,
                'language': 'English'
            })
    
    # Extract Hindi newspapers
    hindi_match = re.search(r'Hindi: \[(.*?)\]', newspapers_section, re.DOTALL)
    if hindi_match:
        hindi_text = hindi_match.group(1)
        hindi_names = re.findall(r'name: "([^"]+)"', hindi_text)
        for name in hindi_names:
            ui_newspapers.append({
                'name': name,
                'language': 'Hindi'
            })
    
    # Extract Marathi newspapers
    marathi_match = re.search(r'Marathi: \[(.*?)\]', newspapers_section, re.DOTALL)
    if marathi_match:
        marathi_text = marathi_match.group(1)
        marathi_names = re.findall(r'name: "([^"]+)"', marathi_text)
        for name in marathi_names:
            ui_newspapers.append({
                'name': name,
                'language': 'Marathi'
            })
    
    return ui_newspapers

def load_registry_newspapers():
    """Load newspapers from newspaper_registry.json"""
    with open('backend/newspaper_registry.json', 'r') as f:
        registry = json.load(f)
    
    registry_newspapers = []
    for language in registry.keys():
        for newspaper in registry[language]:
            registry_newspapers.append({
                'name': newspaper['name'],
                'language': language,
                'columnKey': newspaper.get('columnKey', ''),
                'url_pattern': newspaper.get('url_pattern', '')
            })
    
    return registry_newspapers

def main():
    print("=" * 80)
    print("NEWSPAPER ANALYSIS: VERIFIED_NEWSPAPERS vs newspaper_registry.json")
    print("=" * 80)
    
    # Extract data
    ui_newspapers = extract_ui_newspapers()
    registry_newspapers = load_registry_newspapers()
    
    print(f"UI VERIFIED_NEWSPAPERS: {len(ui_newspapers)} newspapers")
    print(f"REGISTRY newspapers: {len(registry_newspapers)} newspapers")
    print()
    
    # Group A: UI newspapers not in registry (Registry Failure)
    group_a = []
    for ui_paper in ui_newspapers:
        found = False
        for reg_paper in registry_newspapers:
            if ui_paper['name'] == reg_paper['name'] and ui_paper['language'] == reg_paper['language']:
                found = True
                break
        if not found:
            group_a.append(ui_paper)
    
    # Group B: Registry newspapers in UI (Resolver Works)
    group_b = []
    for reg_paper in registry_newspapers:
        for ui_paper in ui_newspapers:
            if reg_paper['name'] == ui_paper['name'] and reg_paper['language'] == ui_paper['language']:
                group_b.append(reg_paper)
                break
    
    # Group C: Fully working (need to check pagination support)
    group_c = []
    for reg_paper in group_b:
        # Check if newspaper has columnKey (indicates pagination support)
        if reg_paper['columnKey']:
            group_c.append(reg_paper)
    
    # Summary table
    print("NEWSPAPER STATUS SUMMARY")
    print("=" * 80)
    print(f"{'UI Name':<50} {'Language':<10} {'In Registry':<12} {'Status':<20} {'Notes':<30}")
    print("-" * 140)
    
    # Display all UI newspapers
    for ui_paper in ui_newspapers:
        in_registry = any(
            reg['name'] == ui_paper['name'] and reg['language'] == ui_paper['language']
            for reg in registry_newspapers
        )
        
        if not in_registry:
            status = "GROUP A"
            notes = "Registry Failure"
        else:
            reg_paper = next(
                reg for reg in registry_newspapers
                if reg['name'] == ui_paper['name'] and reg['language'] == ui_paper['language']
            )
            
            if reg_paper['columnKey']:
                status = "GROUP C"
                notes = "Pagination supported"
            else:
                status = "GROUP B"
                notes = "Resolver works, single page only"
        
        print(f"{ui_paper['name']:<50} {ui_paper['language']:<10} {'✓' if in_registry else '✗':<12} {status:<20} {notes}")
    
    print("\n" + "=" * 80)
    print("GROUP ANALYSIS")
    print("=" * 80)
    print(f"GROUP A (Registry Failure): {len(group_a)} newspapers")
    print(f"  These newspapers appear in UI but are not in the registry.")
    print(f"  The resolver will say 'not found in registry'.")
    print()
    print(f"GROUP B (Resolver Works, Single Page Only): {len(group_b)} newspapers")
    print(f"  These newspapers are in registry and UI, but only page 1 is scanned.")
    print(f"  No pagination discovery - page 2, 3, etc. are not scanned.")
    print()
    print(f"GROUP C (Fully Working): {len(group_c)} newspapers")
    print(f"  These newspapers have pagination support and are fully functional.")
    print()
    print("=" * 80)
    print("ROOT CAUSE ANALYSIS")
    print("=" * 80)
    print("1. The newspaper scanning workflow only scans page 1 by default")
    print("2. Page discovery/pagination is not implemented for most newspapers")
    print("3. The VERIFIED_NEWSPAPERS in page.tsx excludes some registry newspapers")
    print("4. Only newspapers with columnKey support pagination")
    print()
    print("TO FIX THIS:")
    print("1. Add missing newspapers from registry to VERIFIED_NEWSPAPERS")
    print("2. Implement page discovery for newspapers without pagination support")
    print("3. Make page parameter optional in API to discover all pages")
    print("=" * 80)

if __name__ == "__main__":
    main()