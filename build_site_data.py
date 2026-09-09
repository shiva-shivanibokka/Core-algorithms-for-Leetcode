"""Turn the notebooks into the JSON the browsable bank is built from.

The site is static: it ships this file and nothing else, so there is no server
to keep alive and no way for the page to drift from the notebooks. Re-run it
after editing a notebook; CI checks the committed output is current.

    python build_site_data.py           # writes web/public/data/*.json
    python build_site_data.py --check   # fails if the committed files are stale
"""
from __future__ import annotations

import argparse
import ast
import glob
import json
import re
import sys
from pathlib import Path

OUT = Path("web") / "public" / "data"

TAG = "\N{OFFICE BUILDING}"
LC_ID = re.compile(r"\((?:LC|LeetCode)\s*(\d+)[^)]*\)")
SECTION = re.compile(r"^#{1,2}\s+(easy|medium|hard)\b", re.I)
# "Easy 12 — ...", "Medium 8 -- ...", "H20. ...", "E1. ...", "M13. ..."
LADDER = re.compile(r"^\s*#*\s*(?:(easy|medium|hard)\s*(\d+)|([EMH])(\d+)\.)", re.I)
COMPLEXITY = re.compile(r"\*\*Time:?\*\*:?\s*([^|\n]+?)\s*(?:\||$)"
                        r"|(?:^|\n)\s*-\s*\*\*Time\*\*:\s*([^\n]+)", re.M)
SPACE = re.compile(r"\*\*Space:?\*\*:?\s*([^|\n]+)"
                   r"|(?:^|\n)\s*-\s*\*\*Space\*\*:\s*([^\n]+)", re.M)
FULL = {"E": "Easy", "M": "Medium", "H": "Hard"}
# "**Space:** O(n) -- worse space than the two-pointer": the complexity is
# the part before the dash. The rest is commentary and belongs in the
# approach, not in a field the page renders as a number.
ASIDE = re.compile(r"\s+(?:[\u2014\u2013-]{1,2}|,)\s+\S.*$")
PARENTHETICAL = re.compile(r"\s*\(([^)]*)\)\s*$")
TIERS = ["Easy", "Medium", "Hard"]
PLAIN = re.compile(r"^\s*(\d+)\.\s")


def slugify(text):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")


def clean_title(heading):
    """The heading without its markdown, ladder position, or LeetCode number."""
    title = heading.lstrip("#").strip()
    title = LADDER.sub("", title)
    title = re.sub(r"^\s*\d+\.\s*", "", title)
    title = LC_ID.sub("", title)
    title = re.sub(r"^\s*[—\-–.]+\s*", "", title)
    return re.sub(r"\s{2,}", " ", title).strip(" —-–")


def strip_complexity(text):
    lines = [ln for ln in text.splitlines()
             if not re.match(r"\s*(?:-\s*)?\*\*(?:Time|Space)\*?\*?:", ln.strip())]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def first_group(match):
    if not match:
        return None
    found = next((g.strip() for g in match.groups() if g), None)
    return ASIDE.sub("", found).strip(" .") if found else None


def split_solution(source):
    """Separate the solution from the tests that prove it.

    The split is the first top-level `assert`: everything above is the answer
    to the problem, everything from there down is the evidence. Falls back to
    the whole cell as solution when a cell has no top-level assert.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source, ""
    lines = source.splitlines()
    # The first top-level statement that *contains* an assert, not just one that
    # is an assert: a handful of cells drive their cases from a loop.
    starts = [n.lineno for n in tree.body
              if any(isinstance(x, ast.Assert) for x in ast.walk(n))
              and not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    if not starts:
        return source, ""
    cut = starts[0] - 1
    # Pull a comment introducing the tests down with them.
    while cut > 0 and lines[cut - 1].lstrip().startswith("#"):
        cut -= 1
    return "\n".join(lines[:cut]).rstrip(), "\n".join(lines[cut:]).strip()


def annotations(code):
    """Line index -> the comment that explains that line.

    A comment on its own line explains the line below it; a trailing comment
    explains its own line. Both are the notebooks' own words, not new prose.
    """
    out, lines = {}, code.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#"):
            note = stripped.lstrip("#").strip()
            target = next((j for j in range(i + 1, len(lines)) if lines[j].strip()), None)
            if note and target is not None:
                out[target] = note
        elif "  #" in line and not stripped.startswith(('"', "'")):
            note = line.split("  #", 1)[1].strip()
            if note:
                out[i] = note
    return out


def difficulty_of(heading, section, run):
    """Three sources, in order of how directly they say it.

    Most headings state the tier ("Medium 8 — …", "H11. …"). Where they do not,
    two notebooks group problems under an `# EASY Problems` header. Where there
    is neither — the first 45 problems of Binary Search, Merge Intervals,
    Linked List Reversal and Binary Tree DFS — the plain numbering restarts at
    1 for each tier, so the run a problem falls in is the tier. That inference
    is not a guess: Binary Tree BFS and Graph DFS/BFS number the same way *and*
    carry the section headers, and the two agree on every boundary.
    """
    match = LADDER.match(heading.lstrip("#").strip())
    if match:
        word, letter = match.group(1), match.group(3)
        tier = word.capitalize() if word else FULL[letter.upper()]
        return tier, match.group(2) or match.group(4)
    if section:
        return section, None
    return (TIERS[run] if run < len(TIERS) else None), None


def pattern_name(nb, path):
    """The notebook's own H1, split into a name and its parenthetical aside.

    "Fast & Slow Pointers (Floyd's Cycle Detection)" is a better label than the
    filename, which flattens the ampersand into "And" and loses the aside.
    """
    head = next(("".join(c["source"]).splitlines()[0] for c in nb["cells"]
                 if c["cell_type"] == "markdown"), path)
    title = re.sub(r"\s+Pattern$", "", head.lstrip("#").strip())
    aside = PARENTHETICAL.search(title)
    return PARENTHETICAL.sub("", title).strip(), aside.group(1) if aside else None


def build():
    import stress_test
    referenced = set(stress_test.PROBLEMS) - {n for _, n in stress_test.COLLISIONS}

    patterns, unresolved = [], []
    for path in sorted(glob.glob("*.ipynb")):
        with open(path, encoding="utf-8") as fh:
            nb = json.load(fh)
        number = path.split("_", 1)[0]
        # The slug stays derived from the filename, so a renamed heading
        # never moves a URL that has already been shared.
        slug = slugify(path.split("_", 1)[1][:-6].replace("_", " "))
        name, note = pattern_name(nb, path)
        problems, section, pending, order = [], None, None, 0
        run = -1          # which plain-numbered block we are in

        for cell in nb["cells"]:
            src = "".join(cell["source"])
            if not src.strip():
                continue
            if cell["cell_type"] == "markdown":
                head = src.splitlines()[0]
                if TAG in src:
                    body = [ln for ln in src.splitlines()[1:] if ln.strip()]
                    statement = " ".join(ln for ln in body if TAG not in ln).strip()
                    pending = {"heading": head, "statement": statement, "approach": ""}
                elif pending is not None:
                    pending["approach"] += ("\n\n" if pending["approach"] else "") + src.strip()
                else:
                    found = SECTION.match(head)
                    if found:
                        section = found.group(1).capitalize()
                continue

            if pending is None:
                continue                        # a shared-helper cell, not a solution

            order += 1
            heading, approach = pending["heading"], pending["approach"]
            plain = PLAIN.match(heading.lstrip("#").strip())
            if plain and not LADDER.match(heading.lstrip("#").strip()):
                if plain.group(1) == "1":
                    run += 1
            level, rung = difficulty_of(heading, section, run)
            if level is None:
                unresolved.append(f"{path}: {heading[:60]}")
            lc = LC_ID.search(heading)
            solution, tests = split_solution(src)
            defined = {n.name for n in ast.parse(src).body if isinstance(n, ast.FunctionDef)}
            title = clean_title(heading)
            problems.append({
                "id": f"{number}-{order:02d}-{slugify(title)}"[:60],
                "n": order,
                "title": title,
                "leetcode": int(lc.group(1)) if lc else None,
                "difficulty": level or "Medium",
                "rung": int(rung) if rung else None,
                "statement": pending["statement"],
                # The complexity is pulled out into its own field, so drop the
                # line that states it rather than showing it twice.
                "approach": strip_complexity(re.sub(r"^#+\s*Approach\s*", "", approach)),
                "time": first_group(COMPLEXITY.search(approach)),
                "space": first_group(SPACE.search(approach)),
                "solution": solution,
                "notes": {str(k): v for k, v in annotations(solution).items()},
                "tests": tests,
                "verified": sorted(defined & referenced),
            })
            pending = None

        patterns.append({"id": number, "slug": slug, "name": name, "note": note,
                         "notebook": path, "problems": problems})

    if unresolved:
        print(f"{len(unresolved)} problems have no resolvable difficulty:")
        for u in unresolved[:10]:
            print("   ", u)
        return None
    return {"patterns": patterns,
            "totals": {
                "patterns": len(patterns),
                "problems": sum(len(p["problems"]) for p in patterns),
                "verified": sum(1 for p in patterns for q in p["problems"] if q["verified"]),
            }}


def files(data):
    """One small index, then one file per pattern.

    Everything in one file is 1.5 MB, which is a lot to download to read the
    landing page. The index carries only what the lists and filters need; a
    pattern's solutions arrive when that pattern is opened.
    """
    out = {}
    index = {"totals": data["totals"], "patterns": []}
    for pattern in data["patterns"]:
        out[f"{pattern['slug']}.json"] = pattern
        index["patterns"].append({
            "id": pattern["id"], "slug": pattern["slug"], "name": pattern["name"],
            "note": pattern["note"], "notebook": pattern["notebook"],
            "counts": {tier: sum(1 for q in pattern["problems"] if q["difficulty"] == tier)
                       for tier in TIERS},
            "verified": sum(1 for q in pattern["problems"] if q["verified"]),
        })
    out["index.json"] = index
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="fail if the committed JSON is out of date")
    args = parser.parse_args()

    data = build()
    if data is None:
        return 1
    written = {name: json.dumps(body, ensure_ascii=False, indent=1) + "\n"
               for name, body in files(data).items()}

    if args.check:
        stale = [name for name, text in written.items()
                 if not (OUT / name).exists() or (OUT / name).read_text(encoding="utf-8") != text]
        present = [p.name for p in OUT.glob("*.json")] if OUT.exists() else []
        extra = [name for name in present if name not in written]
        if stale or extra:
            for name in stale:
                print(f"FAIL  web/public/data/{name} is stale")
            for name in extra:
                print(f"FAIL  web/public/data/{name} is no longer generated")
            print("      run: python build_site_data.py")
            return 1
        print(f"{len(written)} data files are up to date.")
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    for name, text in written.items():
        (OUT / name).write_text(text, encoding="utf-8", newline="\n")
    for path in OUT.glob("*.json"):
        if path.name not in written:
            path.unlink()
    t = data["totals"]
    print(f"wrote {len(written)} files to {OUT}: {t['patterns']} patterns, "
          f"{t['problems']} problems, {t['verified']} with an independent reference")
    return 0


if __name__ == "__main__":
    sys.exit(main())
