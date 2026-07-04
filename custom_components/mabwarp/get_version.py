# custom_components/mabwarp/get_version.py

import json
import pathlib

_manifest = json.loads((pathlib.Path(__file__).parent / "manifest.json").read_text(encoding="utf-8"))
__version__ = _manifest["version"]
