"""Tests for the CLI module."""

import json
from pathlib import Path

import pytest

from python_file_trace.cli import main


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestCLI:
    """Tests for the CLI."""

    def test_basic_trace(self, capsys):
        """Test basic file tracing."""
        utils_file = str(FIXTURES_DIR / "simple_project" / "utils.py")

        exit_code = main([utils_file, "--no-site-packages"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "utils.py" in captured.out

    def test_json_output(self, capsys):
        """Test JSON output format."""
        utils_file = str(FIXTURES_DIR / "simple_project" / "utils.py")

        exit_code = main([utils_file, "--json", "--no-site-packages"])

        assert exit_code == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "files" in output
        assert len(output["files"]) >= 1

    def test_relative_output(self, capsys):
        """Test relative path output."""
        utils_file = str(FIXTURES_DIR / "simple_project" / "utils.py")
        base = str(FIXTURES_DIR / "simple_project")

        exit_code = main([utils_file, "--base", base, "--relative", "--no-site-packages"])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "utils.py" in captured.out
        # Should not contain full path
        assert FIXTURES_DIR.as_posix() not in captured.out

    def test_show_reasons(self, capsys):
        """Test showing reasons."""
        main_file = str(FIXTURES_DIR / "simple_project" / "main.py")
        base = str(FIXTURES_DIR / "simple_project")

        exit_code = main([
            main_file,
            "--base", base,
            "--relative",
            "--show-reasons",
            "--no-site-packages",
        ])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "[initial]" in captured.out or "[import]" in captured.out

    def test_json_with_reasons(self, capsys):
        """Test JSON output with reasons."""
        main_file = str(FIXTURES_DIR / "simple_project" / "main.py")
        base = str(FIXTURES_DIR / "simple_project")

        exit_code = main([
            main_file,
            "--base", base,
            "--json",
            "--show-reasons",
            "--no-site-packages",
        ])

        assert exit_code == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert "files" in output
        assert "reasons" in output

    def test_ignore_pattern(self, capsys):
        """Test ignore pattern."""
        main_file = str(FIXTURES_DIR / "simple_project" / "main.py")
        base = str(FIXTURES_DIR / "simple_project")

        exit_code = main([
            main_file,
            "--base", base,
            "--relative",
            "--ignore", "**/models/**",
            "--no-site-packages",
        ])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "models" not in captured.out

    def test_multiple_files(self, capsys):
        """Test tracing multiple entry files."""
        utils_file = str(FIXTURES_DIR / "simple_project" / "utils.py")
        main_file = str(FIXTURES_DIR / "simple_project" / "main.py")
        base = str(FIXTURES_DIR / "simple_project")

        exit_code = main([
            utils_file,
            main_file,
            "--base", base,
            "--relative",
            "--no-site-packages",
        ])

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "utils.py" in captured.out
        assert "main.py" in captured.out
