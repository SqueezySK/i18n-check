# SPDX-License-Identifier: GPL-3.0-or-later
"""
Tests for aria_labels.py check functionality.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from i18n_check.check.aria_labels import (
    aria_labels_check_and_fix,
    find_aria_label_punctuation_issues,
    report_and_fix_aria_labels,
)

from ..test_utils import checks_fail_json_dir, checks_pass_json_dir


class TestAriaLabels(unittest.TestCase):
    def test_find_aria_label_punctuation_issues_with_problems(self):
        """
        Test finding aria label punctuation issues.
        """
        aria_label_issues = find_aria_label_punctuation_issues(
            i18n_directory=checks_fail_json_dir
        )

        expected_issues = {
            "i18n.test_file.form_button_aria_label": {
                str(checks_fail_json_dir / "test_i18n_src.json"): {
                    "correct_value": "Click here to submit the form",
                    "current_value": "Click here to submit the form.",
                },
                str(checks_fail_json_dir / "test_i18n_locale.json"): {
                    "correct_value": "Click here to submit the form in another language",
                    "current_value": "Click here to submit the form in another language.",
                },
            },
        }

        self.assertEqual(aria_label_issues, expected_issues)

    @patch("i18n_check.check.aria_labels.rprint")
    @patch("sys.exit")
    def test_report_with_issues_no_fix(self, mock_exit, mock_rprint):
        """
        Test reporting when there are issues but not fixing.
        """
        aria_label_issues = find_aria_label_punctuation_issues(
            i18n_directory=checks_fail_json_dir
        )

        report_and_fix_aria_labels(aria_label_issues, fix=False)

        # Should call rprint twice - once for errors, once for tip.
        self.assertEqual(mock_rprint.call_count, 2)
        mock_exit.assert_called_once_with(1)

    def test_find_aria_label_punctuation_issues_without_problems(self):
        """
        Test finding aria label punctuation issues when there are none.
        """
        aria_label_issues = find_aria_label_punctuation_issues(
            i18n_directory=checks_pass_json_dir
        )
        self.assertEqual(aria_label_issues, {})

    @patch("i18n_check.check.aria_labels.read_json_file")
    @patch("i18n_check.check.aria_labels.rprint")
    def test_report_no_issues(self, mock_rprint, mock_read_json):
        """
        Test reporting when there are no issues.
        """
        aria_label_issues = find_aria_label_punctuation_issues(
            i18n_directory=checks_pass_json_dir
        )
        report_and_fix_aria_labels(aria_label_issues, fix=False)

        mock_rprint.assert_called_once_with(
            "[green]✅ aria_labels: All aria label keys have appropriate punctuation.[/green]"
        )

    @patch("i18n_check.check.aria_labels.replace_text_in_file")
    @patch("i18n_check.check.aria_labels.rprint")
    def test_report_and_fix_aria_labels_with_issues_and_fix_calls_replace_text_in_file_and_reports_count(
        self, mock_rprint, mock_replace_text_in_file
    ):
        """
        When fix=True the report_and_fix_aria_labels should call replace_text_in_file for each replacement (fix) needed (key and file combination)
        and print a summary indicating how many fixes were applied.
        The fail case is tested in which there are 2 replacements (fixes) needed.
        """
        aria_label_issues = find_aria_label_punctuation_issues(
            i18n_directory=checks_fail_json_dir
        )

        report_and_fix_aria_labels(aria_label_issues, fix=True)

        self.assertEqual(mock_replace_text_in_file.call_count, 2)

        printed_texts = [call.args[0] for call in mock_rprint.call_args_list]
        self.assertTrue(
            any("Fixed 2 aria label punctuation issues" in t for t in printed_texts)
        )

    def test_report_and_fix_aria_labels_with_issues_and_all_checks_enabled_and_without_fix_raises_value_error(
        self,
    ):
        """
        When there are issues and all_checks_enabled is True and fix is False the report_and_fix_aria_labels should raise ValueError
        instead of calling sys.exit().
        """
        aria_label_issues = find_aria_label_punctuation_issues(
            i18n_directory=checks_fail_json_dir
        )

        with self.assertRaises(ValueError):
            report_and_fix_aria_labels(
                aria_label_issues, all_checks_enabled=True, fix=False
            )

    def test_find_aria_label_punctuation_issues_preserves_trailing_space_when_removing_punctuation(
        self,
    ):
        """
        When using find_aria_label_punctuation_issues function, verify trailing space after removed punctuation is preserved.
        """
        with tempfile.TemporaryDirectory() as td:
            tmpdir = Path(td)
            file1 = tmpdir / "file1.json"
            data1 = {"greeting_aria_label": "Hello! "}
            file1.write_text(json.dumps(data1, ensure_ascii=False), encoding="utf-8")

            issues = find_aria_label_punctuation_issues(i18n_directory=tmpdir)

            file1_path = str(file1)
            self.assertIn("greeting_aria_label", issues)
            self.assertEqual(
                issues["greeting_aria_label"][file1_path]["current_value"], "Hello! "
            )
            self.assertEqual(
                issues["greeting_aria_label"][file1_path]["correct_value"], "Hello "
            )

    def test_find_aria_label_punctuation_issues_ignores_non_string_values_for_aria_labels(
        self,
    ):
        """
        When using find_aria_label_punctuation_issues function, non-string values for keys ending with _aria_label should be ignored by the function.
        List of integers and nested dictionary are tested as non-string values.
        """
        with tempfile.TemporaryDirectory() as td:
            tmpdir = Path(td)
            file = tmpdir / "file_non_string.json"
            data = {"list_aria_label": [1, 2, 3], "dict_aria_label": {"a": "b"}}
            file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            issues = find_aria_label_punctuation_issues(i18n_directory=tmpdir)
            # No issues should be found.
            self.assertEqual(issues, {})

    def test_find_aria_label_punctuation_issues_handles_arabic_question_mark_punctuation(
        self,
    ):
        """
        When using find_aria_label_punctuation_issues function, verify that Arabic question mark (؟) is detected and removed correctly.
        """
        with tempfile.TemporaryDirectory() as td:
            tmpdir = Path(td)
            file = tmpdir / "file_arabic.json"
            data = {"ask_aria_label": "What؟"}
            file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

            issues = find_aria_label_punctuation_issues(i18n_directory=tmpdir)

            file_path = str(file)
            self.assertIn("ask_aria_label", issues)
            self.assertEqual(
                issues["ask_aria_label"][file_path]["current_value"], "What؟"
            )
            self.assertEqual(
                issues["ask_aria_label"][file_path]["correct_value"], "What"
            )

    @patch("i18n_check.check.aria_labels.find_aria_label_punctuation_issues")
    @patch("i18n_check.check.aria_labels.report_and_fix_aria_labels")
    def test_aria_labels_check_and_fix_delegates_to_report_and_fix_aria_labels(
        self, mock_report_and_fix_aria_labels, mock_find_aria_label_punctuation_issues
    ):
        """
        Ensure the top-level check function aria_labels_check_and_fix delegates to report_and_fix_aria_labels correctly.
        """
        fake_issues = {
            "k_aria_label": {
                "/fake/path.json": {"current_value": "a.", "correct_value": "a"}
            }
        }
        mock_find_aria_label_punctuation_issues.return_value = fake_issues

        result = aria_labels_check_and_fix(fix=True, all_checks_enabled=False)

        mock_find_aria_label_punctuation_issues.assert_called_once()
        mock_report_and_fix_aria_labels.assert_called_once_with(
            aria_label_issues=fake_issues, all_checks_enabled=False, fix=True
        )
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
