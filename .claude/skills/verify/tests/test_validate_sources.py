#!/usr/bin/env python3
"""Tests for validate_sources.py URL validation."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from validate_sources import extract_source_urls, validate_url, URLResult


class TestExtractSourceUrls(unittest.TestCase):
    """Tests for URL extraction from known-claims.md."""

    def test_extract_single_url(self):
        content = """## Skills

**Source:** https://example.com/skills.md

| Claim | Verdict |
"""
        urls = extract_source_urls(content)
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls["Skills"], "https://example.com/skills.md")

    def test_extract_multiple_urls(self):
        content = """## Skills

**Source:** https://example.com/skills.md

## Hooks

**Source:** https://example.com/hooks.md
"""
        urls = extract_source_urls(content)
        self.assertEqual(len(urls), 2)
        self.assertEqual(urls["Skills"], "https://example.com/skills.md")
        self.assertEqual(urls["Hooks"], "https://example.com/hooks.md")

    def test_no_source_line(self):
        content = """## Skills

| Claim | Verdict |
"""
        urls = extract_source_urls(content)
        self.assertEqual(len(urls), 0)

    def test_source_without_section(self):
        content = """**Source:** https://example.com/orphan.md
"""
        urls = extract_source_urls(content)
        self.assertEqual(len(urls), 0)

    def test_section_regex_matches_single_word(self):
        """Section regex matches single words only."""
        content = """## Skills Extra

**Source:** https://example.com/skills.md
"""
        urls = extract_source_urls(content)
        # The regex ^## (\w+) captures "Skills" not "Skills Extra"
        self.assertEqual(urls.get("Skills"), "https://example.com/skills.md")


class TestValidateUrl(unittest.TestCase):
    """Tests for URL validation (mocked)."""

    @patch('validate_sources.urllib.request.urlopen')
    def test_valid_url(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = validate_url("https://example.com", "Test")
        self.assertEqual(result.status, 200)
        self.assertIsNone(result.error)

    @patch('validate_sources.urllib.request.urlopen')
    def test_timeout_error(self, mock_urlopen):
        mock_urlopen.side_effect = TimeoutError()

        result = validate_url("https://example.com", "Test", timeout=1)
        self.assertIsNone(result.status)
        self.assertEqual(result.error, "Timeout")

    def test_url_result_structure(self):
        result = URLResult(url="https://test.com", section="Test", status=200, error=None)
        self.assertEqual(result.url, "https://test.com")
        self.assertEqual(result.section, "Test")
        self.assertEqual(result.status, 200)
        self.assertIsNone(result.error)

    def test_url_result_is_namedtuple(self):
        """URLResult is a NamedTuple with expected fields."""
        result = URLResult("https://test.com", "Test", 200, None)
        self.assertEqual(result[0], "https://test.com")  # url
        self.assertEqual(result[1], "Test")  # section
        self.assertEqual(result[2], 200)  # status
        self.assertEqual(result[3], None)  # error


if __name__ == "__main__":
    unittest.main()
