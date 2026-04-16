<div align="center">

<h1 align="center" style="border-bottom: none;">GmailGen</h1>

**Dotted & Plus-Tag Alias Generator**

[![License](https://img.shields.io/github/license/lvlify/GmailGen)](./LICENSE)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-black)

</div>

### setup
```bash
pip install .
```

### run
```bash
gmailgen [email] [flags]
```

### flags
```text
-n   count      Number of aliases to create
-m   mode       Strategy: dots, plus, both (default)
-o   output     File path (default: aliases.txt)
--shuffle       Randomize output order
--json          Emit machine-readable JSON
--overwrite     Replace existing file without asking
```

### json
```json
{
  "canonical_email": "name@gmail.com",
  "mode": "both",
  "count": 128,
  "aliases": ["..."]
}
```