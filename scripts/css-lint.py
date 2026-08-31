#!/usr/bin/env python3
"""
CSS design system linter.

Enforces design system scales across CSS files:
- Color literals must use tokens (declared in :root)
- Spacing values must use the defined scale
- Font size, line height, and border radius must use defined scales
- All CSS variables must be declared and used (token hygiene)
"""

import re
import sys
from pathlib import Path


def read_file(path):
    """Read file and return lines."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.readlines()
    except (IOError, OSError):
        return []


def find_block_ranges(lines, block_start_pattern, block_end_pattern):
    """Find all ranges of lines inside blocks matching start/end patterns."""
    ranges = []
    start_idx = None
    depth = 0

    for i, line in enumerate(lines):
        # Check if this line starts a block
        if re.search(block_start_pattern, line):
            if start_idx is None:
                start_idx = i

        # Update brace depth only if we're in a block
        if start_idx is not None or re.search(block_start_pattern, line):
            depth += line.count('{') - line.count('}')

            # Check if block ended
            if depth <= 0 and start_idx is not None:
                ranges.append((start_idx, i))
                start_idx = None
                depth = 0

    return ranges


def is_in_ranges(line_idx, ranges):
    """Check if line_idx is in any of the ranges."""
    return any(start <= line_idx <= end for start, end in ranges)


def is_comment_line(line):
    """Check if line is a comment (starts with /*, *, or //)."""
    stripped = line.lstrip()
    return stripped.startswith('/*') or stripped.startswith('*') or stripped.startswith('//')


def extract_declared_tokens(lines, root_ranges):
    """Extract all --name tokens declared in :root."""
    tokens = set()
    for start, end in root_ranges:
        for i in range(start, end + 1):
            line = lines[i]
            # Match --name: value (including hyphens in names)
            matches = re.findall(r'--([\w-]+)\s*:', line)
            for match in matches:
                tokens.add(match)
    return tokens


def extract_used_tokens(lines):
    """Extract all var(--name) tokens used anywhere."""
    used = set()
    for line in lines:
        # Match var(--name) with optional spaces, including hyphens in names
        matches = re.findall(r'var\(\s*--([\w-]+)', line)
        for match in matches:
            used.add(match)
    return used


def check_color_literals(lines, root_ranges, errors):
    """Check for color literals outside :root."""
    color_patterns = [
        r'#[0-9a-fA-F]{3}(?:\b|[^0-9a-fA-F])',  # #rgb
        r'#[0-9a-fA-F]{6}(?:\b|[^0-9a-fA-F])',  # #rrggbb
        r'#[0-9a-fA-F]{8}(?:\b|[^0-9a-fA-F])',  # #rrggbbaa
        r'rgb\(',
        r'rgba\(',
        r'hsl\(',
        r'hsla\(',
        r'oklch\(',
    ]

    for i, line in enumerate(lines):
        if is_comment_line(line):
            continue
        if is_in_ranges(i, root_ranges):
            continue

        for pattern in color_patterns:
            if re.search(pattern, line):
                errors.append((i + 1, f'usa un token en lugar de literales de color'))
                break


def check_spacing_scale(lines, errors):
    """Check spacing values against the scale."""
    spacing_scale = {0, 4, 8, 12, 16, 24, 32, 48, 64}
    spacing_properties = {
        'margin', 'padding', 'gap', 'row-gap', 'column-gap',
        'inset', 'top', 'right', 'bottom', 'left'
    }
    excluded_properties = {
        'width', 'height', 'max-width', 'min-width', 'max-height', 'min-height',
        'flex', 'flex-basis', 'border', 'outline', 'box-shadow', 'background',
        'transform', 'font', 'font-size', 'letter-spacing', 'word-spacing', 'stroke'
    }

    # Regex to find property: value pairs
    prop_pattern = r'(\w+(?:-\w+)*)\s*:\s*([^;}\n]+)'

    for i, line in enumerate(lines):
        if is_comment_line(line):
            continue

        # Find all property: value pairs
        matches = re.findall(prop_pattern, line)
        for prop, value in matches:
            # Check if property is spacing-related
            is_spacing_prop = any(
                prop.startswith(p) or prop.startswith(p + '-')
                for p in spacing_properties
            )

            if not is_spacing_prop:
                continue

            # Check if property is excluded
            is_excluded = any(
                prop.startswith(p) or prop.startswith(p + '-') or p in prop
                for p in excluded_properties
            )

            if is_excluded:
                continue

            # Extract all Npx values
            px_matches = re.findall(r'(\d+)px', value)
            for px_val in px_matches:
                val_int = int(px_val)
                if val_int not in spacing_scale:
                    errors.append((i + 1, f'espaciado {val_int}px no está en la escala'))


def check_font_size_scale(lines, errors):
    """Check font-size values against the scale."""
    font_size_scale = {'0.875rem', '1rem', '1.125rem', '1.5rem', '2rem'}

    # Regex to find property: value pairs
    prop_pattern = r'(\w+(?:-\w+)*)\s*:\s*([^;}\n]+)'

    for i, line in enumerate(lines):
        if is_comment_line(line):
            continue

        # Find all property: value pairs
        matches = re.findall(prop_pattern, line)
        for prop, value in matches:
            if prop != 'font-size':
                continue

            # Skip if it's a var()
            if value.strip().startswith('var('):
                continue

            # Extract font-size value
            match = re.search(r'([\d.]+rem)', value)
            if match:
                val = match.group(1)
                if val not in font_size_scale:
                    errors.append((i + 1, f'font-size {val} no está en la escala'))


def check_line_height_scale(lines, errors):
    """Check line-height values against the scale."""
    line_height_scale = {'1.2', '1.3', '1.4', '1.6'}

    # Regex to find property: value pairs
    prop_pattern = r'(\w+(?:-\w+)*)\s*:\s*([^;}\n]+)'

    for i, line in enumerate(lines):
        if is_comment_line(line):
            continue

        # Find all property: value pairs
        matches = re.findall(prop_pattern, line)
        for prop, value in matches:
            if prop != 'line-height':
                continue

            # Skip if it's a var()
            if value.strip().startswith('var('):
                continue

            # Extract line-height value
            match = re.search(r'([\d.]+)', value)
            if match:
                val = match.group(1)
                if val not in line_height_scale:
                    errors.append((i + 1, f'line-height {val} no está en la escala'))


def check_border_radius_scale(lines, errors):
    """Check border-radius values against the scale."""
    border_radius_scale = {'0', '4px', '8px', '9999px'}

    # Regex to find property: value pairs
    prop_pattern = r'(\w+(?:-\w+)*)\s*:\s*([^;}\n]+)'

    for i, line in enumerate(lines):
        if is_comment_line(line):
            continue

        # Find all property: value pairs
        matches = re.findall(prop_pattern, line)
        for prop, value in matches:
            if prop != 'border-radius':
                continue

            # Skip if it's a var()
            if value.strip().startswith('var('):
                continue

            # Extract border-radius values
            px_matches = re.findall(r'(\d+px|\d(?![\d.]))', value)
            for px_val in px_matches:
                if px_val not in border_radius_scale:
                    errors.append((i + 1, f'border-radius {px_val} no está en la escala'))


def check_token_hygiene(lines, root_ranges, errors):
    """Check that all tokens are declared and used properly."""
    declared = extract_declared_tokens(lines, root_ranges)
    used = extract_used_tokens(lines)

    # Check declared but not used
    for token in declared:
        if token not in used:
            # Find the line where it's declared
            for start, end in root_ranges:
                for i in range(start, end + 1):
                    if f'--{token}' in lines[i]:
                        errors.append((i + 1, f'token --{token} no se usa'))
                        break

    # Check used but not declared
    for token in used:
        if token not in declared:
            # Find the line where it's used
            for i, line in enumerate(lines):
                if f'var(--{token})' in line or f'var( --{token})' in line:
                    errors.append((i + 1, f'token --{token} no está declarado'))
                    break


def lint_css_file(path):
    """Lint a single CSS file. Returns list of (line_num, message) tuples."""
    lines = read_file(path)
    if not lines:
        return []

    errors = []

    # Find :root and @font-face blocks
    root_ranges = find_block_ranges(lines, r':\s*root\s*\{', r'\}')
    fontface_ranges = find_block_ranges(lines, r'@font-face\s*\{', r'\}')

    # Combine all exempted ranges
    exempted_ranges = root_ranges + fontface_ranges

    # Run checks (some need exemptions, some don't)
    check_color_literals(lines, root_ranges, errors)
    check_spacing_scale(lines, errors)
    check_font_size_scale(lines, errors)
    check_line_height_scale(lines, errors)
    check_border_radius_scale(lines, errors)
    check_token_hygiene(lines, root_ranges, errors)

    # Format errors with file path
    result = []
    for line_num, message in errors:
        result.append(f'{path}:{line_num}: {message}')

    return result


def main():
    """Main entry point."""
    directory = sys.argv[1] if len(sys.argv) > 1 else '.'

    css_files = list(Path(directory).glob('*.css'))

    all_errors = []
    for css_file in sorted(css_files):
        errors = lint_css_file(str(css_file))
        all_errors.extend(errors)

    if all_errors:
        for error in all_errors:
            print(error, file=sys.stderr)
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
