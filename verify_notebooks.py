"""Run every code cell in every notebook and report any that fail.

Each cell ends in `assert ... ; print("All tests passed!")`, so a green run
means the solutions actually match their test expectations. Run before
committing:  python verify_notebooks.py

Executing the cells is necessary but not sufficient, because there are two ways
for a solution to be broken that no amount of running can see, and the repo has
carried one of each:

  * a problem with no code cell at all — a heading, an approach note, and
    nothing to run (Two Pointers had "Hard 1 — Trapping Rain Water" like this);
  * a cell that defines the solution and then asserts on a *different* function,
    so the one under the heading is never called (Top K's Skyline Problem
    shipped a stub whose loop body was `pass`, and Topological Sort's Course
    Schedule IV shipped a wrong answer, both perfectly green).

Both are checked here, so "all notebooks pass" means every problem has a
solution and every solution was actually run.
"""
import ast
import contextlib
import glob
import io
import json
import sys

TAG = "\N{OFFICE BUILDING}"      # marks a problem statement: "> 🏢 Asked by: ..."

# Shared scaffolding — node classes, list/tree builders — defined in one cell
# and used by later ones, so "never called here" is expected of them.
HELPERS = {"ListNode", "TreeNode", "Node", "TNode", "MLNode", "RandNode", "TreeNodeFlat",
           "make_list", "to_list", "make_ll", "ll_to_list", "build_tree", "from_list",
           "tree_to_list", "topo_sort"}


def is_exercised(definition, tree):
    """Is this definition used anywhere in the cell outside its own body?

    Any reference counts, not just a direct call: solutions get passed to a
    helper or looped over as often as they are called by name. References from
    inside the definition itself do not count — a function whose only mention
    is its own recursive call is exactly what an unreachable solution looks
    like.
    """
    own = set(map(id, ast.walk(definition)))
    return any(isinstance(node, ast.Name) and node.id == definition.name
               and isinstance(node.ctx, ast.Load) and id(node) not in own
               for node in ast.walk(tree))


def title_of(cell):
    return "".join(cell["source"]).splitlines()[0].strip("# ").strip()


failures = 0
for path in sorted(glob.glob("*.ipynb")):
    with open(path, encoding="utf-8") as fh:
        nb = json.load(fh)

    # Every problem statement needs a solution before the next one starts.
    statements = [i for i, c in enumerate(nb["cells"])
                  if c["cell_type"] == "markdown" and TAG in "".join(c["source"])]
    for n, i in enumerate(statements):
        stop = statements[n + 1] if n + 1 < len(statements) else len(nb["cells"])
        between = (nb["cells"][j] for j in range(i + 1, stop))
        if not any(c["cell_type"] == "code" and "".join(c["source"]).strip() for c in between):
            failures += 1
            print(f"FAIL  {path}  no solution cell for: {title_of(nb['cells'][i])}")

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
            continue

        # A cell that tests something must test everything it defines. Cells
        # with no asserts are the shared-helper cells, which later cells use.
        tree = ast.parse(src)
        if not any(isinstance(n, ast.Assert) for n in ast.walk(tree)):
            continue
        untested = [d.name for d in tree.body
                    if isinstance(d, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                    and d.name not in HELPERS and not is_exercised(d, tree)]
        for name in untested:
            failures += 1
            print(f"FAIL  {path}  cell {cell}: {name}() is defined but never called, "
                  f"so its asserts prove nothing about it")

print("\nAll notebooks pass." if not failures else f"\n{failures} failing cell(s).")
sys.exit(1 if failures else 0)
