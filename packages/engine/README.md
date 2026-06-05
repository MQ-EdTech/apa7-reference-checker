# apa7-validator

Pure-Python APA 7 reference and citation validator.

```python
from apa7_validator import validate
from apa7_validator.clients import Clients

with open("essay.docx", "rb") as f:
    report = validate(f.read(), "docx", clients=Clients.dry_run())

for issue in report.issues:
    print(issue.severity.value, issue.code, issue.message)
```

See repository root README for the project overview.
