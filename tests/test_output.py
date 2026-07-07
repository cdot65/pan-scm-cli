"""Tests for the shared output layer (scm_cli.utils.output).

All user-facing output flows through this module: data (tables, detail
views, JSON, YAML) goes to stdout; messages (success, error, warning,
info) go to stderr. This keeps stdout pipe-safe.
"""

import json

import yaml

from scm_cli.utils import output
from scm_cli.utils.output import OutputFormat, emit, error, info, render_detail, render_table, success, warning

SAMPLE_ROWS = [
    {"name": "web1", "folder": "Texas", "ip_netmask": "10.0.0.1/32"},
    {"name": "web2", "folder": "Texas", "ip_netmask": "10.0.0.2/32"},
]


class TestMessagesGoToStderr:
    def test_success_writes_to_stderr(self, capsys):
        success("Created address 'web1' in folder Texas")
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "Created address 'web1' in folder Texas" in captured.err
        assert "✓" in captured.err

    def test_error_writes_to_stderr(self, capsys):
        error("something broke")
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "something broke" in captured.err
        assert "✗" in captured.err

    def test_warning_writes_to_stderr(self, capsys):
        warning("careful")
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "careful" in captured.err

    def test_info_writes_to_stderr(self, capsys):
        info("fyi")
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "fyi" in captured.err


class TestRenderTable:
    def test_table_goes_to_stdout(self, capsys):
        render_table(SAMPLE_ROWS, title="Addresses")
        captured = capsys.readouterr()
        assert "web1" in captured.out
        assert "web2" in captured.out
        assert captured.err == ""

    def test_table_columns_derived_from_keys(self, capsys):
        render_table(SAMPLE_ROWS)
        out = capsys.readouterr().out
        assert "Name" in out
        assert "Folder" in out
        assert "Ip Netmask" in out

    def test_table_explicit_columns_subset(self, capsys):
        render_table(SAMPLE_ROWS, columns=["name", "folder"])
        out = capsys.readouterr().out
        assert "web1" in out
        assert "10.0.0.1/32" not in out

    def test_empty_rows_prints_message(self, capsys):
        render_table([], title="Addresses")
        captured = capsys.readouterr()
        assert "No results" in captured.err
        assert captured.out == ""

    def test_nested_values_rendered_compactly(self, capsys):
        rows = [{"name": "r1", "source": ["any", "trust"]}]
        render_table(rows)
        out = capsys.readouterr().out
        assert "any" in out
        assert "trust" in out


class TestRenderDetail:
    def test_detail_goes_to_stdout(self, capsys):
        render_detail({"name": "web1", "folder": "Texas"}, title="Address")
        captured = capsys.readouterr()
        assert "web1" in captured.out
        assert "Texas" in captured.out
        assert captured.err == ""

    def test_detail_field_labels_humanized(self, capsys):
        render_detail({"ip_netmask": "10.0.0.1/32"})
        out = capsys.readouterr().out
        assert "Ip Netmask" in out


class TestEmit:
    def test_emit_json_is_pure_parseable_stdout(self, capsys):
        emit(SAMPLE_ROWS, OutputFormat.json)
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed == SAMPLE_ROWS
        assert captured.err == ""

    def test_emit_yaml_is_pure_parseable_stdout(self, capsys):
        emit(SAMPLE_ROWS, OutputFormat.yaml)
        captured = capsys.readouterr()
        parsed = yaml.safe_load(captured.out)
        assert parsed == SAMPLE_ROWS

    def test_emit_table_renders_table_for_list(self, capsys):
        emit(SAMPLE_ROWS, OutputFormat.table, title="Addresses")
        out = capsys.readouterr().out
        assert "web1" in out

    def test_emit_table_renders_detail_for_dict(self, capsys):
        emit({"name": "web1"}, OutputFormat.table)
        out = capsys.readouterr().out
        assert "web1" in out

    def test_emit_accepts_string_format(self, capsys):
        emit(SAMPLE_ROWS, "json")
        parsed = json.loads(capsys.readouterr().out)
        assert parsed == SAMPLE_ROWS

    def test_emit_json_handles_non_serializable(self, capsys):
        from datetime import datetime

        emit([{"when": datetime(2026, 7, 6)}], OutputFormat.json)
        parsed = json.loads(capsys.readouterr().out)
        assert "2026" in parsed[0]["when"]


class TestOutputOption:
    def test_output_option_exists(self):
        assert hasattr(output, "OUTPUT_OPTION")

    def test_output_format_values(self):
        assert {f.value for f in OutputFormat} == {"table", "json", "yaml"}
