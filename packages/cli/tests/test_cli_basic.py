from pathlib import Path

from apa7_check.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_basic_run_on_text_file(tmp_path: Path):
    src = tmp_path / "essay.txt"
    src.write_text(
        "Climate is warming (Smith, 2020).\n\n"
        "References\n\n"
        "Smith, J. (2020). Foundations of climate research. Earth Press."
    )
    result = runner.invoke(app, [str(src)])
    assert result.exit_code == 0
    assert "References found" in result.stdout
    assert "Citations found" in result.stdout
