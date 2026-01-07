#!/usr/bin/env python3
"""
common.py - Shared utilities for three-lens-audit scripts

Provides consolidated implementations used by multiple scripts:
- Markdown table parsing
- Keyword extraction
"""

import re
from typing import List, Dict


def parse_markdown_table(content: str) -> List[Dict[str, str]]:
    """
    Parse markdown tables and return data rows as dicts.

    Args:
        content: Markdown content potentially containing tables

    Returns:
        List of dicts mapping header names to cell values.
        Empty list if no valid table found.
    """
    rows = []
    lines = content.split('\n')
    current_headers = []
    in_table = False

    for line in lines:
        stripped = line.strip()
        if '|' in stripped:
            # Extract cells (skip empty first/last from leading/trailing |)
            cells = [c.strip() for c in stripped.split('|')[1:-1]]

            if re.match(r'^[\s\-:|]+$', stripped.replace('|', '')):
                # Separator row - previous row was headers
                in_table = True
            elif not in_table and cells:
                # Potential header row
                current_headers = cells
            elif in_table and cells:
                # Data row
                if len(cells) == len(current_headers):
                    rows.append(dict(zip(current_headers, cells)))
                else:
                    # Mismatched columns - store raw
                    rows.append({'raw': ' | '.join(cells)})
        else:
            if stripped and not stripped.startswith('#'):
                in_table = False

    return rows


def count_table_rows(content: str) -> int:
    """
    Count data rows in markdown tables (excludes header and separator).

    Args:
        content: Markdown content potentially containing tables

    Returns:
        Number of data rows found across all tables.
    """
    lines = content.split('\n')
    row_count = 0
    in_table = False

    for line in lines:
        stripped = line.strip()
        if '|' in stripped:
            if re.match(r'^\|[\s\-:|]+\|$', stripped):
                # Separator row - table body starts after this
                in_table = True
            elif in_table and stripped.startswith('|') and stripped.endswith('|'):
                # Data row
                row_count += 1
            elif not stripped.startswith('|'):
                in_table = False
        else:
            in_table = False

    return row_count
