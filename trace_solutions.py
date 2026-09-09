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
import sys

#: A trace longer than this is not worth watching, and the JSON gets large.
MAX_FRAMES = 56
#: Rows wider than this do not fit on the page as cells.
MAX_SEQ = 26
#: A sequence in this range makes a watchable animation.
GOOD_SEQ = range(3, 21)
#: Guard against a solution that loops forever on a traced run.
MAX_STEPS = 400_000


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
            out.append((i, value, "numbers", built))
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
    """Run one call, keeping a frame per executed line of the solution."""
    frames = []
    steps = [0]

    def tracer(frame, event, _arg):
        if event != "line" or frame.f_code.co_filename != "<solution>":
            return tracer
        steps[0] += 1
        if steps[0] > MAX_STEPS:
            raise TimeoutError("solution ran too long under the tracer")
        if len(frames) >= MAX_FRAMES:
            return None
        ints, nodes = {}, {}
        for k, v in frame.f_locals.items():
            if k.startswith("_"):
                continue
            if isinstance(v, int) and not isinstance(v, bool):
                ints[k] = v
            elif node_map and id(v) in node_map:
                nodes[k] = node_map[id(v)]
        frames.append({"line": frame.f_lineno - 1, "ints": ints, "nodes": nodes})
        return tracer

    sys.settrace(tracer)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            fn(*args)
    finally:
        sys.settrace(None)
    return frames


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
        if not seqs:
            continue
        try:
            fn, args, node_map = _prepare(solution, call, base_ns)
            frames = _record(fn, args, node_map)
        except Exception:  # noqa: S112 -- a solution that will not run under the
            continue       # tracer simply gets no animation; the cell's own
                           # asserts are what report a solution that is broken
        if not frames:
            continue
        length = sum(len(s[1]) for s in seqs)
        score = (1 if length in GOOD_SEQ else 0, min(len(frames), MAX_FRAMES))
        if best is None or score > best[0]:
            best = (score, call, seqs, frames)

    if best is None:
        return None
    _, call, seqs, frames = best

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
            rows.append({"name": name, "kind": kind, "values": values, "movers": movers})

    if not rows:
        return None

    tracked = {m for row in rows for m in row["movers"]}
    steps = []
    for f in frames:
        marks = {k: v for k, v in {**f["ints"], **f["nodes"]}.items() if k in tracked}
        if steps and steps[-1]["l"] == f["line"] and steps[-1]["m"] == marks:
            continue        # the same line with nothing moved is not a step
        steps.append({"l": f["line"], "m": marks})

    return {"rows": rows, "steps": steps, "call": ast.unparse(call)}
