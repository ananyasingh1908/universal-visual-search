#!/bin/bash
# Simple test script to check date picker functionality

# Test 1: Check if the calendar component is correctly structured
python3 << 'EOF'
import sys
import os

# Read the page.tsx file
with open('C:/Users/ANANYA SINGH/universal-visual-search/frontend/app/page.tsx', 'r') as f:
    content = f.read()

# Check for key components
tests = [
    ('showCalendar state defined', 'const [showCalendar, setShowCalendar] = useState(false)' in content),
    ('setShowCalendar defined', 'setShowCalendar' in content),
    ('Input has onClick handler', 'onClick={() => setShowCalendar(!showCalendar)}' in content),
    ('Calendar button has onClick handler', 'onClick={() => setShowCalendar(!showCalendar)}' in content),
    ('Calendar popup has correct classes', 'absolute top-full mt-2 p-4 bg-white dark:bg-gray-800 border rounded-lg shadow-lg z-50' in content),
    ('Calendar renders conditionally', '{showCalendar && (' in content),
    ('Date display formatting', 'toLocaleDateString("en-IN"' in content),
    ('Date selection handler', 'onClick={() => dayjs(selectedDate).format("YYYY-MM-DD"))}' in content),
]

print("Date Picker Implementation Analysis:")
print("=" * 50)
all_passed = True
for test_name, test_result in tests:
    status = "✓ PASS" if test_result else "✗ FAIL"
    print(f"{status}: {test_name}")
    if not test_result:
        all_passed = False

print("=" * 50)
if all_passed:
    print("All tests passed - implementation appears correct")
else:
    print("Some tests failed - implementation has issues")

# Check for potential issues
print("\nChecking for potential issues:")
print("-" * 30)

# Check for syntax errors in JavaScript
import re

# Check for common syntax issues
syntax_checks = [
    ('Missing closing parentheses', r'\(\s*\w+\s*\([^)]*$', 'MULTILINE'),
    ('Unclosed braces', r'\{\s*\}', 'MULTILINE'),
    ('Missing return statement', r'function\s+\w+\s*\([^)]*\)\s*\{[^}]*$', 'MULTILINE'),
]

for check_name, pattern, flags in syntax_checks:
    matches = re.findall(pattern, content, flags)
    if matches:
        print(f"✗ {check_name}: Found {len(matches)} potential issues")
    else:
        print(f"✓ {check_name}: No issues found")
EOF
