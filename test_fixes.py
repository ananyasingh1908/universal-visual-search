#!/usr/bin/env python3
"""Test the fixes for the three tasks."""

import sys
sys.path.insert(0, "backend")

from newspaper_resolver import resolve_newspaper_url, NewspaperNotFoundError, InvalidDateError, InvalidPageError

def test_task1():
    """Test that Deshonnati and Navbharat resolve successfully."""
    print("Testing TASK 1 - Registry name mismatches...")

    # Test Deshonnati (new registry entry)
    try:
        result = resolve_newspaper_url("Deshonnati", "2026-06-13", 1)
        print("PASS Deshonnati: " + result)
    except NewspaperNotFoundError as e:
        print("FAIL Deshonnati failed: " + str(e))
        return False

    # Test Navbharat (new registry entry)
    try:
        result = resolve_newspaper_url("Navbharat", "2026-06-13", 1)
        print("PASS Navbharat: " + result)
    except NewspaperNotFoundError as e:
        print("FAIL Navbharat failed: " + str(e))
        return False

    print("TASK 1 completed successfully!\n")
    return True

def test_task2():
    """Test date conversion for Lokshahi Varta."""
    print("Testing TASK 2 - Date conversion for Lokshahi Varta...")

    # Test Lokshahi Varta Edition 16 with frontend date format (YYYY-MM-DD)
    try:
        result = resolve_newspaper_url("Lokshahi Varta Edition 16", "2026-06-08", 1)
        print("PASS Lokshahi Varta Edition 16: " + result)
        # Check if date is converted to DD/MM/YYYY format
        if "date=08/06/2026" in result:
            print("  PASS Date correctly converted to DD/MM/YYYY format")
        else:
            print("  FAIL Date not in expected format: " + result)
            return False
    except Exception as e:
        print("FAIL Lokshahi Varta Edition 16 failed: " + str(e))
        return False

    # Test Lokshahi Varta Edition 11 with frontend date format (YYYY-MM-DD)
    try:
        result = resolve_newspaper_url("Lokshahi Varta Edition 11", "2026-06-08", 1)
        print("PASS Lokshahi Varta Edition 11: " + result)
        # Check if date is converted to DD/MM/YYYY format
        if "date=08/06/2026" in result:
            print("  PASS Date correctly converted to DD/MM/YYYY format")
        else:
            print("  FAIL Date not in expected format: " + result)
            return False
    except Exception as e:
        print("FAIL Lokshahi Varta Edition 11 failed: " + str(e))
        return False

    print("TASK 2 completed successfully!\n")
    return True


def test_task3():
    """Test that URL probing works for specified newspapers."""
    print("Testing TASK 3 - URL probing pagination...")

    # Test that the registry entries have supports_page_probing set
    from newspaper_resolver import NewspaperRegistry
    registry = NewspaperRegistry()
    
    newspapers_to_test = [
        "Lokmat Hello Nagpur",
        "Lokmat Hello Wardha",
        "Lokmat Samachar Apna Nagpur",
        "Lokmat Samachar Apna Vidarbha",
        "Maharashtra Times Nagpur",
        "Maharashtra Times Nagpur Plus",
        "Navarashtra",
        "Navbharat Nagpur Plus",
        "Loksatta Nagpur",
    ]
    
    all_good = True
    for newspaper_name in newspapers_to_test:
        try:
            newspaper_info = registry._find_newspaper_by_name(newspaper_name)
            if newspaper_info.get("supports_page_probing") == True:
                print("PASS " + newspaper_name + ": supports_page_probing = True")
            else:
                print("FAIL " + newspaper_name + ": supports_page_probing is missing or False")
                all_good = False
        except NewspaperNotFoundError:
            print("FAIL " + newspaper_name + ": not found in registry")
            all_good = False

    if all_good:
        print("\nTASK 3 completed successfully!\n")
    else:
        print("\nTASK 3 has issues!\n")
    return all_good


if __name__ == "__main__":
    print("=" * 60)
    print("Testing the three tasks for newspaper scanning fixes")
    print("=" * 60)
    print()

    task1_ok = test_task1()
    task2_ok = test_task2()
    task3_ok = test_task3()

    print("=" * 60)
    print("Summary:")
    print(f"  TASK 1 (Registry names): {'PASS' if task1_ok else 'FAIL'}")
    print(f"  TASK 2 (Date conversion): {'PASS' if task2_ok else 'FAIL'}")
    print(f"  TASK 3 (URL probing): {'PASS' if task3_ok else 'FAIL'}")
    print("=" * 60)

    if task1_ok and task2_ok and task3_ok:
        sys.exit(0)
    else:
        sys.exit(1)
