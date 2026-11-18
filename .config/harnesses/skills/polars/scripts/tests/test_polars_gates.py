"""Tests for polars_gates: every rule, suppression, scoping, and both entry points."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "polars_gates.py"
SPEC = importlib.util.spec_from_file_location("polars_gates", SCRIPT)
polars_gates = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["polars_gates"] = polars_gates
SPEC.loader.exec_module(polars_gates)

POLARS_PREAMBLE = "import polars as pl\n"


def write_module(directory: Path, name: str, body: str) -> Path:
    path = directory / name
    path.write_text(body, encoding="utf-8")
    return path


def codes_for(directory: Path, body: str) -> list[str]:
    path = write_module(directory, "sample.py", body)
    findings, _suppressed = polars_gates.check_file(path)
    return [finding.rule.code for finding in findings]


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        (POLARS_PREAMBLE + 'frame = pl.read_csv("data.csv")\n', "POL001"),
        (
            POLARS_PREAMBLE + 'frame.select(pl.col("a").map_elements(lambda value: value))\n',
            "POL002",
        ),
        (
            POLARS_PREAMBLE + 'frame.select(pl.col("a").map_batches(lambda values: values))\n',
            "POL003",
        ),
        (POLARS_PREAMBLE + "for row in frame.iter_rows():\n    pass\n", "POL004"),
        (POLARS_PREAMBLE + "back = frame.to_pandas()\n", "POL005"),
        (
            "import pandas as pd\nimport polars as pl\n\nframe = pd.read_csv('data.csv')\n",
            "POL006",
        ),
        (
            POLARS_PREAMBLE + 'frame.lazy().collect().filter(pl.col("a") > 1)\n',
            "POL007",
        ),
        (
            POLARS_PREAMBLE + 'frame.select([(pl.col(name) * 2).alias(name) for name in ["a"]])\n',
            "POL008",
        ),
        (POLARS_PREAMBLE + 'frame.groupby("a").count()\n', "POL009"),
        (POLARS_PREAMBLE + "row = frame.iloc[0]\n", "POL009"),
        (
            "import warnings\n" + POLARS_PREAMBLE + 'warnings.filterwarnings("ignore")\n',
            "POL010",
        ),
    ],
)
def test_rule_fires(tmp_path: Path, body: str, expected: str) -> None:
    assert expected in codes_for(tmp_path, body)


def test_non_polars_file_is_ignored(tmp_path: Path) -> None:
    body = "values = [1, 2, 3]\nvalues.apply(str)\nvalues.iloc = None\n"
    assert codes_for(tmp_path, body) == []


def test_iterrows_is_reported_once_as_row_loop(tmp_path: Path) -> None:
    body = POLARS_PREAMBLE + "for _, row in frame.iterrows():\n    pass\n"
    assert codes_for(tmp_path, body) == ["POL004"]


def test_clean_polars_lazy_pipeline_has_no_findings(tmp_path: Path) -> None:
    body = (
        POLARS_PREAMBLE
        + 'frame = (\n    pl.scan_parquet("data.parquet")\n'
        + '    .filter(pl.col("year") == 2024)\n'
        + '    .group_by("region")\n'
        + '    .agg(pl.col("value").sum().alias("total"))\n'
        + "    .collect()\n)\n"
    )
    assert codes_for(tmp_path, body) == []


def test_line_suppression_removes_finding(tmp_path: Path) -> None:
    body = POLARS_PREAMBLE + 'frame = pl.read_csv("data.csv")  # polars-gate: allow POL001\n'
    path = write_module(tmp_path, "sample.py", body)
    findings, suppressed = polars_gates.check_file(path)
    assert findings == []
    assert suppressed == 1


def test_file_suppression_removes_finding(tmp_path: Path) -> None:
    body = "# polars-gate: allow-file POL001, POL005\n" + POLARS_PREAMBLE + 'frame = pl.read_csv("data.csv")\n'
    path = write_module(tmp_path, "sample.py", body)
    findings, suppressed = polars_gates.check_file(path)
    assert findings == []
    assert suppressed == 1


def test_syntax_error_is_not_a_gate_failure(tmp_path: Path) -> None:
    assert codes_for(tmp_path, POLARS_PREAMBLE + "def broken(:\n") == []


def run_cli(*arguments: str, stdin: str | None = None) -> subprocess.CompletedProcess:  # style:allow shared helper
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        input=stdin,
        capture_output=True,
        text=True,
        check=False,
    )


def test_cli_exits_one_on_findings(tmp_path: Path) -> None:
    path = write_module(tmp_path, "sample.py", POLARS_PREAMBLE + 'frame = pl.read_csv("data.csv")\n')
    result = run_cli(str(path))
    assert result.returncode == 1
    assert "POL001" in result.stderr


def test_cli_errors_only_ignores_hints(tmp_path: Path) -> None:
    path = write_module(tmp_path, "sample.py", POLARS_PREAMBLE + "back = frame.to_pandas()\n")
    assert run_cli(str(path)).returncode == 1
    assert run_cli("--errors-only", str(path)).returncode == 0


def test_cli_json_shape(tmp_path: Path) -> None:
    path = write_module(tmp_path, "sample.py", POLARS_PREAMBLE + "back = frame.to_pandas()\n")
    result = run_cli("--json", str(path))
    payload = json.loads(result.stdout)
    assert payload["findings"][0]["code"] == "POL005"
    assert payload["findings"][0]["severity"] == "hint"


def test_hook_blocks_on_error_and_passes_on_hint(tmp_path: Path) -> None:
    error_path = write_module(tmp_path, "error_case.py", POLARS_PREAMBLE + "rows = frame.iter_rows()\n")
    hint_path = write_module(tmp_path, "hint_case.py", POLARS_PREAMBLE + "back = frame.to_pandas()\n")
    payload = json.dumps({"tool_input": {"file_path": str(error_path)}})
    assert run_cli("--event", "edit", stdin=payload).returncode == 2
    payload = json.dumps({"tool_input": {"file_path": str(hint_path)}})
    assert run_cli("--event", "edit", stdin=payload).returncode == 0


def test_hook_ignores_non_python_payload(tmp_path: Path) -> None:
    markdown = write_module(tmp_path, "notes.md", "# notes\n")
    payload = json.dumps({"tool_input": {"file_path": str(markdown)}})
    assert run_cli("--event", "edit", stdin=payload).returncode == 0


def test_explain_documents_rule() -> None:
    result = run_cli("--explain", "pol002")
    assert result.returncode == 0
    assert "POL002" in result.stdout
    assert result.returncode == 0


def test_explain_rejects_unknown_rule() -> None:
    assert run_cli("--explain", "POL999").returncode == 2
