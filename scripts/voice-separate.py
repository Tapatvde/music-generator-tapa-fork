"""Isolated separator process; exits before voice synthesis starts."""
import json
import os
import sys
from dataclasses import replace
from pathlib import Path

spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
root = Path(spec["root"]).resolve()
run = Path(spec["run"]).resolve()
if not run.is_relative_to(root):
    raise ValueError("Arbeitsordner außerhalb des Forks.")
rvc = root / "engine/rvc"
sys.argv = [sys.argv[0]]
sys.path.insert(0, str(rvc))
os.chdir(rvc)
from tools.pymss_webui import MSSTBatchSeparator, resolve_model

best = spec["request"]["quality"] == "best"
model = replace(resolve_model("vocals-bs-roformer-368"), overlap_size=308700 if best else 264600, batch_size=1)
with MSSTBatchSeparator(model, "wav", str(run / "stems"), str(run / "stems")) as separator:
    separator.separator.use_tta = best
    result = separator.separate_file(str(run / "input.wav"))
(run / "separation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
