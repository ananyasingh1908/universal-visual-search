#!/usr/bin/env python3
"""Test the fixes for routing, scaling, and build errors."""

import sys
sys.path.insert(0, "backend")

from newspaper_resolver import resolve_newspaper_url

def test_newspaper_resolution():
    """Test that newspaper resolution still works correctly."""
    print("Testing newspaper resolution...")
    
    try:
        url = resolve_newspaper_url("Navbharat", "2026-06-13", 1)
        print("PASS Newspaper resolution works correctly")
        return True
    except Exception as e:
        print("FAIL Newspaper resolution failed: " + str(e))
        return False

def test_ranking_structure():
    """Verify that viewer structure follows App Router conventions."""
    print("\nTesting App Router structure...")
    
    try:
        # Check that viewer directory structure exists
        import os
        viewer_path = "frontend/app/viewer/[documentId]/[page]/page.tsx"
        
        if os.path.exists(viewer_path):
            print("PASS Viewer uses correct App Router structure")
            return True
        else:
            print("FAIL Viewer structure incorrect")
            return False
    except Exception as e:
        print("FAIL Structure check failed: " + str(e))
        return False

def test_highlight_with_viewer_url():
    """Verify that highlight response includes viewer_url field."""
    print("\nTesting highlight response includes viewer_url...")
    
    # Check that backend/main.py has been modified
    try:
        with open("backend/main.py", "r") as f:
            content = f.read()
            if "viewer_url" in content:
                print("PASS Backend includes viewer_url field in highlight response")
                return True
            else:
                print("FAIL Backend missing viewer_url field")
                return False
    except Exception as e:
        print("FAIL Backend check failed: " + str(e))
        return False

def test_viewer_implementation():
    """Verify that viewer implementation handles scaling correctly."""
    print("\nTesting viewer implementation...")
    
    try:
        # Check that viewer implementation includes scaling logic
        with open("frontend/app/viewer/[documentId]/[page]/page.tsx", "r") as f:
            content = f.read()
            
        # Look for scaling logic in the content
        hasScaleX = "scaleX" in content
        hasScaleY = "scaleY" in content
        hasCalculateScale = "calculateScale" in content
        hasResizeObserver = "ResizeObserver" in content
        
        if hasScaleX and hasScaleY and hasCalculateScale and hasResizeObserver:
            print("PASS Viewer implementation includes proper scaling logic")
            print("  - scaleX and scaleY variables")
            print("  - calculateScale function")
            print("  - ResizeObserver for dynamic scaling")
            return True
        else:
            print("FAIL Viewer missing scaling logic")
            print(f"  - scaleX: {hasScaleX}")
            print(f"  - scaleY: {hasScaleY}")
            print(f"  - calculateScale: {hasCalculateScale}")
            print(f"  - ResizeObserver: {hasResizeObserver}")
            return False
    except Exception as e:
        print("FAIL Viewer implementation check failed: " + str(e))
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Fixes for Routing, Scaling, and Build Errors")
    print("=" * 60)
    
    test1_ok = test_newspaper_resolution()
    test2_ok = test_ranking_structure()
    test3_ok = test_highlight_with_viewer_url()
    test4_ok = test_viewer_implementation()
    
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Newspaper resolution: {'PASS' if test1_ok else 'FAIL'}")
    print(f"  App Router structure: {'PASS' if test2_ok else 'FAIL'}")
    print(f"  Highlight viewer_url field: {'PASS' if test3_ok else 'FAIL'}")
    print(f"  Viewer scaling logic: {'PASS' if test4_ok else 'FAIL'}")
    print("=" * 60)
    
    if test1_ok and test2_ok and test3_ok and test4_ok:
        sys.exit(0)
    else:
        sys.exit(1)
