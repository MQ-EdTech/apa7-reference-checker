import io
import zipfile
from pathlib import Path

from apa7_check.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_annotate_writes_docx(tmp_path: Path):
    src = tmp_path / "essay.txt"
    src.write_text("Climate is warming (Smith, 2020).")
    out = tmp_path / "out.docx"
    result = runner.invoke(app, [str(src), "--annotate", str(out)])
    assert result.exit_code == 0, result.stdout
    assert out.exists()
    with zipfile.ZipFile(io.BytesIO(out.read_bytes())) as z:
        assert "word/comments.xml" in z.namelist()
