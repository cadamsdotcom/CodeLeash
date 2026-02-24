#!/usr/bin/env python3
"""
Script to check for non-permitted Tailwind color classes in frontend code.

This script enforces that only brand colors are used in the codebase.
This ensures consistency with the brand design system.

Additionally enforces that hover/active states use brightness classes
instead of explicit color changes for consistent brand theming.

Fast string-based approach - no regex for performance.
"""

import re
import sys
from pathlib import Path

# Disallowed standard Tailwind color names
DISALLOWED_COLORS = {
    "amber",
    "blue",
    "cyan",
    "emerald",
    "fuchsia",
    "gray",
    "green",
    "indigo",
    "lime",
    "neutral",
    "orange",
    "pink",
    "purple",
    "red",
    "rose",
    "sky",
    "slate",
    "stone",
    "teal",
    "violet",
    "yellow",
    "zinc",
}

# State prefixes that should use brightness classes
STATE_PREFIXES = [
    "hover:",
    "active:",
    "focus:",
    "focus-visible:",
    "disabled:",
    "group-hover:",
]


def extract_brand_colors_from_config() -> set[str]:
    """
    Extract brand color names from tailwind.config.js.
    Returns a set of brand color names.
    Raises an error if the config can't be read or no brand colors are found.
    """
    config_path = Path("tailwind.config.js")
    if not config_path.exists():
        print("❌ Error: tailwind.config.js not found")
        print("This script must be run from the project root directory.")
        sys.exit(1)

    try:
        with open(config_path, encoding="utf-8") as f:
            content = f.read()

        # Extract brand color keys from the config
        # Look for patterns like 'brand-xxx': 'var(...)'
        brand_colors = set()
        pattern = r"'(brand-[a-z-]+)':"
        matches = re.findall(pattern, content)
        brand_colors.update(matches)

        if not brand_colors:
            print("❌ Error: No brand colors found in tailwind.config.js")
            print("Expected to find color definitions like 'brand-xxx': 'var(...)'")
            sys.exit(1)

        return brand_colors
    except Exception as e:
        print(f"❌ Error reading tailwind.config.js: {e}")
        sys.exit(1)


def check_file(file_path: Path) -> list[tuple[int, str, str]]:
    """
    Check a single TypeScript/React file for non-permitted color usage.

    Uses fast string searching instead of regex.
    Returns list of (line_number, found_pattern, color_name) tuples.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        print(f"Unicode decode error in {file_path}, skipping")
        return []

    violations = []

    for line_no, line in enumerate(lines, start=1):
        # Fast check: look for disallowed color patterns like "-blue-", "-red-"
        for color in DISALLOWED_COLORS:
            pattern = f"-{color}-"
            if pattern in line:
                # Found a violation - extract the full class for reporting
                # Simple extraction: find the word containing the pattern
                words = line.split()
                for word in words:
                    if pattern in word:
                        # Clean up quotes, brackets, etc.
                        clean_word = word.strip("\",'{}()[]<>;:")
                        if pattern in clean_word:
                            violations.append((line_no, clean_word, color))

    return violations


def check_state_brightness(
    file_path: Path, brand_colors: set[str]
) -> list[tuple[int, str, str]]:
    """
    Check for hover/active states that use explicit colors instead of brightness.

    Returns list of (line_number, found_pattern, suggestion) tuples.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        return []

    violations = []

    # Design system standard brightness values
    state_standards = {
        "hover:": {
            "bg": "brightness-90",
            "text": "brightness-110",
            "border": "brightness-90",
        },
        "active:": {
            "bg": "brightness-75",
            "text": "brightness-75",
            "border": "brightness-75",
        },
        "focus:": {
            "bg": "brightness-98",
            "text": "brightness-98",
            "border": "brightness-98",
        },
        "focus-visible:": {
            "bg": "brightness-98",
            "text": "brightness-98",
            "border": "brightness-98",
        },
        "disabled:": {"bg": "opacity-50", "text": "opacity-50", "border": "opacity-50"},
        "group-hover:": {
            "bg": "brightness-90",
            "text": "brightness-110",
            "border": "brightness-90",
        },
    }

    # Pre-build all pattern combinations (major performance optimization)
    # Map pattern -> (state, prefix_type, suggestion)
    pattern_map: dict[str, tuple[str, str, str]] = {}
    for state in STATE_PREFIXES:
        standards = state_standards[state]
        for brand_color in brand_colors:
            for prefix_type, standard in [
                ("bg", standards["bg"]),
                ("text", standards["text"]),
                ("border", standards["border"]),
            ]:
                pattern = f"{state}{prefix_type}-{brand_color}"
                suggestion = f"Replace with '{state}{standard}'"
                pattern_map[pattern] = (state, prefix_type, suggestion)

    # Convert state prefixes to set for O(1) lookup
    state_prefix_set = set(STATE_PREFIXES)

    for line_no, line in enumerate(lines, start=1):
        # Early exit: skip lines that don't contain any state prefixes
        if not any(prefix in line for prefix in state_prefix_set):
            continue

        # Split line into words once
        words = line.split()
        for word in words:
            # Clean up the word once
            clean_word = word.strip("\",'{}()[]<>;:")
            if not clean_word:
                continue

            # Check if this word matches any of our pre-built patterns
            for pattern, (_state, _prefix_type, suggestion) in pattern_map.items():
                if pattern in clean_word:
                    violations.append((line_no, clean_word, suggestion))
                    # Don't break - a word could theoretically have multiple violations

    return violations


def main() -> None:
    """Main function."""
    if len(sys.argv) > 1:
        files = [Path(arg) for arg in sys.argv[1:]]
    else:
        # Default to checking all TypeScript/React files in src/
        files = []
        for pattern in ["src/**/*.ts", "src/**/*.tsx"]:
            files.extend(Path(".").glob(pattern))

    # Extract brand colors from tailwind config
    brand_colors = extract_brand_colors_from_config()

    total_color_violations = 0
    violations_by_color: dict[str, int] = {}
    total_state_violations = 0
    state_violations_by_file: dict[str, int] = {}

    for file_path in files:
        if not file_path.is_file():
            continue

        # Skip files in node_modules
        if "node_modules" in str(file_path):
            continue

        # Check for disallowed standard colors
        color_violations = check_file(file_path)
        if color_violations:
            print(f"\n{file_path}:")
            for line_no, full_class, color_name in color_violations:
                print(f"  Line {line_no}: {full_class} (color: {color_name})")
                total_color_violations += 1

                # Track violations by color for summary
                if color_name not in violations_by_color:
                    violations_by_color[color_name] = 0
                violations_by_color[color_name] += 1

        # Check for state classes that should use brightness
        state_violations = check_state_brightness(file_path, brand_colors)
        if state_violations:
            if not color_violations:  # Only print filename if not already printed
                print(f"\n{file_path}:")
            for line_no, full_class, suggestion in state_violations:
                print(f"  Line {line_no}: {full_class}")
                print(f"    → {suggestion}")
                total_state_violations += 1
                file_key = str(file_path)
                if file_key not in state_violations_by_file:
                    state_violations_by_file[file_key] = 0
                state_violations_by_file[file_key] += 1

    # Report results
    has_violations = total_color_violations > 0 or total_state_violations > 0

    if total_color_violations > 0:
        print(f"\n{'='*60}")
        print(f"❌ Found {total_color_violations} disallowed Tailwind colors")
        print(
            f"\nViolations: {', '.join(f'{c}({n})' for c, n in sorted(violations_by_color.items(), key=lambda x: x[1], reverse=True))}"
        )
        print("\nOnly brand colors are permitted.")
        print(f"{'='*60}")

    if total_state_violations > 0:
        print(f"\n{'='*60}")
        print(f"❌ Found {total_state_violations} state classes using explicit colors")
        print(f"\nAffected files: {len(state_violations_by_file)}")
        print("\nDesign System Standards:")
        print("  • hover:bg-* → hover:brightness-90")
        print("  • hover:text-* → hover:brightness-110")
        print("  • active:* → active:brightness-75")
        print("  • focus:* → focus:brightness-98")
        print("  • disabled:* → disabled:opacity-50")
        print(f"{'='*60}")

    if has_violations:
        sys.exit(1)
    else:
        print("✓ All colors are brand colors")
        print("✓ All state classes use brightness modifiers")
        sys.exit(0)


if __name__ == "__main__":
    main()
