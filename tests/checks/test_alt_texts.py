# SPDX-License-Identifier: GPL-3.0-or-later
"""
Tests for alt_texts.py check functionality.
"""

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from i18n_check.check.alt_texts import (
    alt_texts_check_and_fix,
    find_alt_text_punctuation_issues,
    report_and_fix_alt_texts,
)

from ..test_utils import checks_fail_json_dir, checks_pass_json_dir


class TestAltTexts(unittest.TestCase):
    def test_find_alt_text_punctuation_issues_with_problems(self):
        """
        Test finding alt text punctuation issues.
        """
        alt_text_issues = find_alt_text_punctuation_issues(
            i18n_directory=checks_fail_json_dir
        )

        expected_issues = {
            "i18n.test_file.fox_image_alt_text": {
                str(checks_fail_json_dir / "test_i18n_src.json"): {
                    "correct_value": "The quick brown fox jumps over the lazy dog.",
                    "current_value": "The quick brown fox jumps over the lazy dog",
                }
            }
        }

        self.maxDiff = None

        self.assertEqual(alt_text_issues, expected_issues)

    @patch("i18n_check.check.alt_texts.rprint")
    @patch("sys.exit")
    def test_report_issues_without_fix(self, mock_exit, mock_rprint):
        """
        Test reporting issues without fixing them.
        """
        alt_text_issues = find_alt_text_punctuation_issues(
            i18n_directory=checks_fail_json_dir
        )

        report_and_fix_alt_texts(alt_text_issues, fix=False)

        # Check that appropriate error messages were printed.
        self.assertEqual(mock_rprint.call_count, 2)
        mock_exit.assert_called_once_with(1)

    def test_find_alt_text_punctuation_issues_without_problems(self):
        """
        Test finding alt text punctuation issues when there are none.
        """
        alt_text_issues = find_alt_text_punctuation_issues(
            i18n_directory=checks_pass_json_dir
        )
        self.assertEqual(alt_text_issues, {})

    @patch("i18n_check.check.alt_texts.read_json_file")
    @patch("i18n_check.check.alt_texts.rprint")
    def test_report_no_issues(self, mock_rprint, mock_read_json):
        """
        Test reporting when there are no issues.
        """
        report_and_fix_alt_texts({}, fix=False)

        mock_rprint.assert_called_once_with(
            "[green]✅ alt_texts: All alt text keys have appropriate punctuation.[/green]"
        )

    @patch("i18n_check.check.alt_texts.replace_text_in_file")
    @patch("i18n_check.check.alt_texts.rprint")
    def test_report_and_fix_alt_texts_with_issues_and_fix_calls_replace_text_in_file_and_reports_count(
        self, mock_rprint, mock_replace_text_in_file
    ):
        """
        When fix=True the report_and_fix_alt_texts should call replace_text_in_file for each replacement (fix) needed (key and file combination)
        and print a summary indicating how many fixes were applied.
        The fail case is tested in which there is 1 replacement (fix) needed.
        """
        alt_text_issues = find_alt_text_punctuation_issues(
            i18n_directory=checks_fail_json_dir
        )

        report_and_fix_alt_texts(alt_text_issues, fix=True)

        self.assertEqual(mock_replace_text_in_file.call_count, 1)

        printed_texts = [call.args[0] for call in mock_rprint.call_args_list]
        self.assertTrue(
            any("Fixed 1 alt text punctuation issues" in t for t in printed_texts)
        )

    def test_report_and_fix_alt_texts_with_issues_and_all_checks_enabled_and_without_fix_raises_value_error(
        self,
    ):
        """
        When there are issues and all_checks_enabled is True and fix is False the report_and_fix_alt_texts should raise ValueError
        instead of calling sys.exit().
        """
        alt_text_issues = find_alt_text_punctuation_issues(
            i18n_directory=checks_fail_json_dir
        )

        with self.assertRaises(ValueError):
            report_and_fix_alt_texts(
                alt_text_issues, all_checks_enabled=True, fix=False
            )

    @patch("i18n_check.check.alt_texts.replace_text_in_file")
    def test_report_and_fix_alt_texts_with_fix_calls_replace_text_in_file_with_expected_old_and_new_patterns(
        self, mock_replace_text_in_file
    ):
        """
        When using report_and_fix_alt_texts function and fix is True and there are issues, verify the exact old/new JSON key-value patterns passed to replace_text_in_file.
        The fail case is tested in which there is 1 replacement (fix) needed.
        """
        alt_text_issues = find_alt_text_punctuation_issues(
            i18n_directory=checks_fail_json_dir
        )

        # Extract a sample key and its current/correct values from the discovered issues.
        sample_key = next(iter(alt_text_issues.keys()))
        sample_file = next(iter(alt_text_issues[sample_key].keys()))
        current_value = alt_text_issues[sample_key][sample_file]["current_value"]
        correct_value = alt_text_issues[sample_key][sample_file]["correct_value"]

        report_and_fix_alt_texts(alt_text_issues, fix=True)

        # Ensure replace_text_in_file was called and examine kwargs.
        mock_replace_text_in_file.assert_called_once()
        called_kwargs = mock_replace_text_in_file.call_args.kwargs
        self.assertIn("old", called_kwargs)
        self.assertIn("new", called_kwargs)

        expected_old = f'"{sample_key}": "{current_value}"'
        expected_new = f'"{sample_key}": "{correct_value}"'
        self.assertEqual(called_kwargs["old"], expected_old)
        self.assertEqual(called_kwargs["new"], expected_new)

    @patch("i18n_check.check.alt_texts.find_alt_text_punctuation_issues")
    @patch("i18n_check.check.alt_texts.report_and_fix_alt_texts")
    def test_alt_texts_check_and_fix_delegates_to_report_and_fix_alt_texts(
        self, mock_report_and_fix_alt_texts, mock_find_alt_text_punctuation_issues
    ):
        """
        Ensure the top-level check function alt_texts_check_and_fix delegates to report_and_fix_alt_texts correctly.
        """
        fake_issues = {
            "k_alt_text": {
                "/fake/path.json": {"current_value": "a", "correct_value": "a."}
            }
        }
        mock_find_alt_text_punctuation_issues.return_value = fake_issues

        result = alt_texts_check_and_fix(fix=True, all_checks_enabled=False)

        mock_find_alt_text_punctuation_issues.assert_called_once()
        mock_report_and_fix_alt_texts.assert_called_once_with(
            alt_text_issues=fake_issues, all_checks_enabled=False, fix=True
        )
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
