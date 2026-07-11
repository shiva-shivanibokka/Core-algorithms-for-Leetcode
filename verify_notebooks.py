"""Run every code cell in every notebook and report any that fail.

Each cell ends in `assert ... ; print("All tests passed!")`, so a green run
means the solutions actually match their test expectations. Run before
committing:  python verify_notebooks.py
"""
import glob
import io
import json
import contextlib
import sys

failures = 0
for path in sorted(glob.glob("*.ipynb")):
    nb = json.load(open(path, encoding="utf-8"))
    ns, cell = {}, 0  # shared namespace: cells build on earlier definitions
    for c in nb["cells"]:
        if c["cell_type"] != "code":
            continue
        cell += 1
        src = "".join(c["source"])
        if not src.strip():
            continue
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                exec(compile(src, f"<{path}#cell{cell}>", "exec"), ns)
        except Exception as e:
            failures += 1
            first = src.strip().splitlines()[0][:70]
            print(f"FAIL  {path}  cell {cell}: {type(e).__name__}: {e}")
            print(f"        -> {first}")

print("\nAll notebooks pass." if not failures else f"\n{failures} failing cell(s).")
sys.exit(1 if failures else 0)
