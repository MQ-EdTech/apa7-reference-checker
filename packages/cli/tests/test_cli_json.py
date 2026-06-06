import json
from pathlib import Path

from apa7_check.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_json_output_is_valid_json(tmp_path: Path):
    src = tmp_path / "essay.txt"
    src.write_text("Climate is warming (Smith, 2020).")
    result = runner.invoke(app, [str(src), "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "references" in payload
    assert "citations" in payload
    assert "issues" in payload
