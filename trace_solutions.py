"""Record what each solution actually does, so the site can replay it.

An animation per pattern is a compromise: ninety Two Pointers problems get the
same picture, and none of them get one that shows *their* input. An animation
per problem cannot be drawn by hand 1,170 times.

So it is not drawn, it is recorded. Each solution is run on one of its own test
cases under a line tracer, and every step keeps two things: which line of the
solution is executing, and where each of its pointers is sitting. The site
replays that. The animation cannot drift from the code, because it is a
recording of the code running.

What gets tracked is read off the source, never guessed:

  * a variable counts as a pointer into a sequence only if the solution
    actually subscripts that sequence with it — `s[left]` is what makes `left`
    a pointer into `s`. A variable that merely happens to hold a small number,
    like `target`, is not a pointer and is not drawn as one.
  * a variable holding a node of a linked list is reported as the position of
    that node, because the list was built here and its identities are known.
    That is what makes `prev` and `curr` visible in a reversal.

Problems whose state is none of those — a tree, a graph, a dictionary — get no
trace, and the site falls back to the pattern-level animation for them.
"""
from __future__ import annotations

import ast
import contextlib
import io
import math
import sys

#: A trace longer than this is not worth watching, and the JSON gets large.
MAX_FRAMES = 56
#: Rows wider than this do not fit on the page as cells.
MAX_SEQ = 26
#: A sequence in this range makes a watchable animation.
GOOD_SEQ = range(3, 21)
#: At most this many changing lists are worth watching at once.
MAX_STATE_ROWS = 2
#: More labels than this under one row is a wall of text, not a picture.
MAX_MOVERS = 4
#: Guard against a solution that loops forever on a traced run.
MAX_STEPS = 400_000


def as_row(value):
    """A list short and simple enough to draw as a row of cells, or None."""
    if not isinstance(value, list) or not 1 <= len(value) <= MAX_SEQ:
        return None
    cells = []
    for item in value:
        # bool before int: bool is a subclass of int, and "False" does not fit
        if isinstance(item, bool):
            cells.append("T" if item else "F")
        elif isinstance(item, float) and not math.isfinite(item):
            # `dp = [float('inf')] * n` is a real starting state and worth
            # showing -- but json.dumps writes it as the literal `Infinity`,
            # which no JSON parser accepts. A symbol says the same thing.
            cells.append("∞" if item > 0 else "-∞")
        elif isinstance(item, (int, float)):
            cells.append(item)
        elif isinstance(item, str) and len(item) <= 3:
            cells.append(item)
        else:
            return None
    return cells


def _literal(node):
    try:
        return ast.literal_eval(node)
    except (ValueError, SyntaxError, TypeError):
        return None


def literal_sequences(call):
    """Short flat lists or strings among the arguments.

    Also looks one level inside a builder — `make_list([1,2,3])` is a linked
    list whose values are worth showing as a row.
    """
    out = []
    for i, arg in enumerate(call.args):
        value = _literal(arg)
        built = False
        if value is None and isinstance(arg, ast.Call) and arg.args:
            value = _literal(arg.args[0])
            built = value is not None
        if isinstance(value, str) and 1 <= len(value) <= MAX_SEQ:
            out.append((i, list(value), "text", built))
        elif (isinstance(value, list) and 1 <= len(value) <= MAX_SEQ
              and all(isinstance(v, (int, float)) for v in value)):
            # bool is a subclass of int in Python, so a list of flags lands
            # here too. "False" does not fit in a cell; T and F do.
            cells = [("T" if v else "F") if isinstance(v, bool) else v for v in value]
            out.append((i, cells, "numbers", built))
    return out


def test_calls(tests, defined):
    """Calls in the test lines that invoke something this cell defines."""
    try:
        tree = ast.parse(tests)
    except SyntaxError:
        return []
    return [n for n in ast.walk(tree)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in defined]


def index_owners(solution):
    """variable -> the sequence it is used to subscript.

    This is the whole basis for drawing a pointer: `nums[left]` in the source
    is what says `left` points into `nums`.
    """
    owners = {}
    with contextlib.suppress(SyntaxError):
        tree = ast.parse(solution)
        for node in ast.walk(tree):
            # nums[left] -- the plainest statement that left points into nums
            if (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name)
                    and isinstance(node.slice, ast.Name)):
                owners.setdefault(node.slice.id, node.value.id)
            # for i, ch in enumerate(s) -- i walks s without ever subscripting it
            elif isinstance(node, ast.For) and isinstance(node.iter, ast.Call):
                seq = _iterated_name(node.iter)
                if seq is None:
                    continue
                target = node.target
                if isinstance(target, ast.Tuple) and target.elts:
                    target = target.elts[0]
                if isinstance(target, ast.Name):
                    owners.setdefault(target.id, seq)

        # One hop outwards: `mid = (left + right) // 2` makes mid a pointer
        # into arr, and left and right are plainly pointers into the same arr
        # even though neither ever appears inside a bracket. Repeat until it
        # settles, so a chain of two resolves too.
        for _ in range(3):
            grew = False
            for node in ast.walk(tree):
                if not isinstance(node, ast.Assign) or len(node.targets) != 1:
                    continue
                target = node.targets[0]
                if not isinstance(target, ast.Name) or target.id not in owners:
                    continue
                row = owners[target.id]
                for inner in ast.walk(node.value):
                    if isinstance(inner, ast.Name) and inner.id not in owners:
                        owners[inner.id] = row
                        grew = True
            if not grew:
                break
    return owners


def _iterated_name(call):
    """The sequence behind `enumerate(seq)` or `range(len(seq))`."""
    func = call.func
    name = func.id if isinstance(func, ast.Name) else None
    if name == "enumerate" and call.args and isinstance(call.args[0], ast.Name):
        return call.args[0].id
    if name == "range":
        for arg in call.args:
            if (isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name)
                    and arg.func.id == "len" and arg.args
                    and isinstance(arg.args[0], ast.Name)):
                return arg.args[0].id
            # range(len(seq) - 1) and friends
            if isinstance(arg, ast.BinOp):
                for side in (arg.left, arg.right):
                    if (isinstance(side, ast.Call) and isinstance(side.func, ast.Name)
                            and side.func.id == "len" and side.args
                            and isinstance(side.args[0], ast.Name)):
                        return side.args[0].id
    return None


def param_names(solution, fname):
    with contextlib.suppress(SyntaxError):
        for node in ast.parse(solution).body:
            if isinstance(node, ast.FunctionDef) and node.name == fname:
                return [a.arg for a in node.args.args]
    return []


def node_positions(head, limit=MAX_SEQ):
    """id(node) -> its position, for a linked list built from the test values."""
    out, i, node = {}, 0, head
    while node is not None and i < limit and id(node) not in out:
        out[id(node)] = i
        node = getattr(node, "next", None)
        i += 1
    return out


def _record(fn, args, node_map):
    """Run one call, keeping a frame per executed line of the solution.

    Returns the frames and whether the run finished inside the frame budget. A
    truncated recording stops mid-answer and -- worse -- may be cut off before
    the state it was chosen for ever changes, which made the choice of test
    case depend on exactly where the cut fell.
    """
    frames = []
    steps = [0]
    truncated = [False]
    # Which lists change is decided over the *whole* run, while only the first
    # frames are kept to replay. Judging a candidate by the truncated view made
    # the choice of test case depend on where the cut fell.
    last_seen: dict[str, tuple] = {}
    changed: set[str] = set()

    def tracer(frame, event, _arg):
        if event != "line" or frame.f_code.co_filename != "<solution>":
            return tracer
        steps[0] += 1
        if steps[0] > MAX_STEPS:
            raise TimeoutError("solution ran too long under the tracer")

        ints, nodes, lists = {}, {}, {}
        for k, v in frame.f_locals.items():
            if k.startswith("_"):
                continue
            if isinstance(v, int) and not isinstance(v, bool):
                ints[k] = v
            elif node_map and id(v) in node_map:
                nodes[k] = node_map[id(v)]
            else:
                row = as_row(v)
                if row is not None:
                    lists[k] = row
                    shape = tuple(row)
                    if k in last_seen and last_seen[k] != shape:
                        changed.add(k)
                    last_seen[k] = shape

        if len(frames) >= MAX_FRAMES:
            truncated[0] = True
            return tracer      # keep watching; just stop storing
        frames.append({"line": frame.f_lineno - 1, "ints": ints,
                       "nodes": nodes, "lists": lists})
        return tracer

    sys.settrace(tracer)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            fn(*args)
    finally:
        sys.settrace(None)
    return frames, not truncated[0], changed


def _prepare(solution, call, base_ns):
    """Evaluate the arguments once, and keep them.

    The traced run is given these exact objects, so a local holding one of them
    really is that node -- rather than an address that happened to be reused.
    """
    namespace = dict(base_ns)
    exec(compile(solution, "<solution>", "exec"), namespace)
    args = [eval(compile(ast.Expression(arg), "<arg>", "eval"), namespace)
            for arg in call.args]
    mapping = {}
    for value in args:
        if hasattr(value, "next"):
            mapping.update(node_positions(value))
    return namespace[call.func.id], args, mapping


def _state_rows(frames, changed):
    """The changing lists worth drawing, busiest first.

    `changed` comes from the whole run; the ordering is by how much of the
    change is visible in the frames that will actually be replayed.
    """
    ranked = []
    for name in changed:
        seen = {tuple(f["lists"][name]) for f in frames if name in f["lists"]}
        ranked.append((len(seen), name))
    ranked.sort(reverse=True)
    return [name for _, name in ranked[:MAX_STATE_ROWS]]


def trace(solution: str, tests: str, base_ns: dict) -> dict | None:
    """A replayable recording of this solution, or None if it has no shape.

    Every candidate test case is traced and the one that reads best wins: a
    sequence long enough to be worth watching, and then the most steps. Picking
    the smallest input gave Valid Palindrome a one-character string.
    """
    try:
        tree = ast.parse(solution)
    except SyntaxError:
        return None
    defined = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    if not defined:
        return None

    owners = index_owners(solution)
    best = None

    for call in test_calls(tests, defined):
        seqs = literal_sequences(call)
        try:
            fn, args, node_map = _prepare(solution, call, base_ns)
            frames, complete, changed = _record(fn, args, node_map)
        except Exception:  # noqa: S112 -- a solution that will not run under the
            continue       # tracer simply gets no animation; the cell's own
                           # asserts are what report a solution that is broken
        if not frames:
            continue
        length = sum(len(s[1]) for s in seqs) if seqs else 0
        # Every part of this is a property of the whole execution, so two
        # machines agree: how much state moved, whether the run finished, and
        # how big the example is. Nothing here depends on the frame budget.
        score = (len(changed),
                 1 if complete else 0,
                 1 if length in GOOD_SEQ else 0,
                 min(len(frames), MAX_FRAMES))
        if best is None or score > best[0]:
            best = (score, call, seqs, frames, changed)

    if best is None:
        return None
    _, call, seqs, frames, changed = best

    params = param_names(solution, call.func.id)
    rows = []
    for pos, values, kind, built in seqs:
        name = params[pos] if pos < len(params) else f"arg{pos}"
        # A pointer into this row is a variable the source subscripts this row
        # with. For a row built into nodes there are no subscripts, so the
        # variables that held one of its nodes are the pointers instead.
        by_index = {k for k, owner in owners.items() if owner == name}
        by_node = {k for f in frames for k in f["nodes"]} if built else set()
        span = range(len(values))
        movers = sorted(
            {k for f in frames for k, v in f["ints"].items()
             if k in by_index and v in span}
            | {k for f in frames for k, v in f["nodes"].items()
               if k in by_node and v in span}
        )
        if movers:
            # A reversal can have eleven locals holding a node at some point,
            # which is a wall of labels rather than a picture. Keep the few
            # that actually travel -- the ones that visit the most positions.
            if len(movers) > MAX_MOVERS:
                seen = {m: set() for m in movers}
                for f in frames:
                    for k, v in {**f["ints"], **f["nodes"]}.items():
                        if k in seen:
                            seen[k].add(v)
                movers = sorted(sorted(movers, key=lambda m: (-len(seen[m]), m))[:MAX_MOVERS])
            rows.append({"name": name, "kind": kind, "values": values, "movers": movers})

    # Lists whose contents change get a row of their own, drawn as cells that
    # light up as they are written to. This is what topological sort and
    # dynamic programming have instead of a pointer.
    state = _state_rows(frames, changed)
    shown = {row["name"] for row in rows}
    state = [n for n in state if n not in shown]
    for name in state:
        first = next((f["lists"][name] for f in frames if name in f["lists"]), None)
        if first is not None:
            rows.append({"name": name, "kind": "state", "values": first, "movers": []})

    if not rows:
        return None

    tracked = {m for row in rows for m in row["movers"]}
    steps, previous = [], {}
    for f in frames:
        marks = {k: v for k, v in {**f["ints"], **f["nodes"]}.items() if k in tracked}
        delta = {}
        for name in state:
            current = f["lists"].get(name)
            if current is None:
                continue
            was = previous.get(name)
            if was is None:
                previous[name] = list(current)
                continue
            if len(current) != len(was):
                changed = dict(enumerate(current))
            else:
                pairs = zip(was, current, strict=True)
                changed = {i: b for i, (a, b) in enumerate(pairs) if a != b}
            if changed:
                delta[name] = {str(i): v for i, v in changed.items()}
                previous[name] = list(current)
        if (steps and steps[-1]["l"] == f["line"] and steps[-1]["m"] == marks and not delta):
            continue        # the same line with nothing moved is not a step
        steps.append({"l": f["line"], "m": marks, "d": delta})

    return {"rows": rows, "steps": steps, "call": ast.unparse(call)}
