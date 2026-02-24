#!/usr/bin/env python3
"""Generate TypeScript types from Pydantic models."""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent
MODELS_PATH = PROJECT_ROOT / "app" / "models" / "initial_data.py"
OUTPUT_DIR = PROJECT_ROOT / "src" / "types"
OUTPUT_FILE = OUTPUT_DIR / "initial-data.ts"


def post_process_generated_file(file_path: Path) -> None:
    """Post-process the generated TypeScript file to remove unnecessary directives."""
    if not file_path.exists():
        return

    content = file_path.read_text()
    lines = content.split("\n")
    processed_lines: list[str] = []

    for line in lines:
        # Remove unnecessary ESLint disable comments
        if line.strip() == "/* eslint-disable */":
            continue
        processed_lines.append(line)

    # Write back the processed content
    file_path.write_text("\n".join(processed_lines))


def generate_types_to_file(output_path: Path) -> None:
    """Generate TypeScript types to specified file."""
    # Run pydantic-to-typescript
    cmd = [
        "uv",
        "run",
        "pydantic2ts",
        "--module",
        str(MODELS_PATH),
        "--output",
        str(output_path),
        "--json2ts-cmd",
        "npx json2ts",
    ]

    # Change to project root directory so imports work correctly
    original_cwd = os.getcwd()
    os.chdir(PROJECT_ROOT)

    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        # Post-process the generated file to remove unnecessary directives
        post_process_generated_file(output_path)
    except subprocess.CalledProcessError as e:
        print("Error generating TypeScript types:")
        print(e.stderr)
        sys.exit(1)
    finally:
        # Restore original working directory
        os.chdir(original_cwd)


def files_are_different(file1: Path, file2: Path) -> bool:
    """Compare two files and return True if they are different."""
    if not file1.exists() or not file2.exists():
        return True
    return file1.read_text() != file2.read_text()


def main() -> None:
    """Generate TypeScript types from Pydantic models."""
    parser = argparse.ArgumentParser(
        description="Generate TypeScript types from Pydantic models"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if types are up-to-date without modifying files",
    )
    args = parser.parse_args()

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.check:
        # Check mode: generate to temp file and compare
        print("Checking if TypeScript types are up-to-date...")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".ts", delete=False
        ) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            # Generate to temporary file
            generate_types_to_file(tmp_path)

            # Compare with existing file
            if files_are_different(OUTPUT_FILE, tmp_path):
                print("TypeScript types are out of date!")
                print(f"Please run 'npm run types' to update {OUTPUT_FILE}")
                sys.exit(1)
            else:
                print("TypeScript types are up-to-date")
                sys.exit(0)
        finally:
            # Clean up temp file
            tmp_path.unlink(missing_ok=True)
    else:
        # Normal generation mode
        print(f"Generating TypeScript types from {MODELS_PATH}...")
        print(f"Output will be written to {OUTPUT_FILE}")

        # Remove existing file to ensure clean generation
        if OUTPUT_FILE.exists():
            OUTPUT_FILE.unlink()
            print(f"Removed existing {OUTPUT_FILE}")

        generate_types_to_file(OUTPUT_FILE)
        print("TypeScript types generated successfully!")


if __name__ == "__main__":
    main()
