"""Check the numbers in README.md against the notebooks.

Prose cannot self-update. Every count in the README — how many patterns, how
many problems, how many of those are distinct, how many LeetCode numbers are
cited — was true when it was typed and goes stale the moment a notebook
changes. Asserts inside the notebooks do not notice, because none of them know
the README exists.

So the counts are computed here and the README is required to state them. Add a
problem and this fails until the sentence describing the bank is corrected.

    python check_claims.py
"""
import glob
import json
import re
import sys
from collections import Counter

TAG = "\N{OFFICE BUILDING}"
LC_ID = re.compile(r"\b(?:LC|LeetCode)\s*(\d+)")


def normalise(title):
    """Two headings name the same problem if they survive to the same string.

    Strips the LeetCode reference, the ladder position ("Easy 12", "M4."), and
    the qualifiers the bank uses when it revisits a problem it already solved.
    """
    title = re.sub(r"\((?:LC|LeetCode)\s*\d+[^)]*\)", "", title)
    title = re.sub(r"[^a-z0-9 ]", " ", title.lower())
    title = re.sub(r"\b(?:easy|medium|hard)\s*\d+\b", " ", title)
    title = re.sub(r"\b[emh]\d+\b", " ", title)
    title = re.sub(r"\b\d+\b", " ", title)
    for word in ("full", "basic", "simplified", "extended", "iterative", "recursive"):
        title = re.sub(rf"\b{word}\b", " ", title)
    return " ".join(title.split())


def survey():
    notebooks = sorted(glob.glob("*.ipynb"))
    per_notebook, distinct, ids, tags, code_cells = [], 0, set(), Counter(), 0
    for path in notebooks:
        with open(path, encoding="utf-8") as fh:
            nb = json.load(fh)
        titles = []
        for cell in nb["cells"]:
            src = "".join(cell["source"])
            if cell["cell_type"] == "code" and src.strip():
                code_cells += 1
            if cell["cell_type"] != "markdown" or TAG not in src:
                continue
            titles.append(normalise(src.splitlines()[0]))
            ids.update(int(m) for m in LC_ID.findall(src))
            asked = re.search(r"Asked by:\*\*\s*(.+)", src)
            if asked:
                tags.update(c.strip() for c in asked.group(1).split(",") if c.strip())
        per_notebook.append(len(titles))
        distinct += len(set(titles))
    return notebooks, per_notebook, distinct, ids, tags, code_cells


def main():
    notebooks, per_notebook, distinct, ids, tags, code_cells = survey()
    total = sum(per_notebook)
    deps = [ln for ln in open("requirements.txt", encoding="utf-8")
            if ln.strip() and not ln.startswith("#")]
    sys.path.insert(0, ".")
    import stress_test

    claims = {
        "pattern notebooks": str(len(notebooks)),
        "problems per notebook": str(per_notebook[0]),
        "problem slots": f"{total:,}",
        "code cells": f"{code_cells:,}",
        "distinct problems": f"{distinct:,}",
        "LeetCode numbers cited": str(len(ids)),
        "third-party dependencies": str(len(deps)),
        "problems with an independent reference": str(len(stress_test.PROBLEMS)),
    }
    if len(set(per_notebook)) != 1:
        print(f"FAIL  notebooks hold different numbers of problems: {per_notebook}")
        return 1

    readme = open("README.md", encoding="utf-8").read()
    missing = [(what, value) for what, value in claims.items()
               if not re.search(rf"(?<![\d,]){re.escape(value)}(?![\d,])", readme)]
    for what, value in missing:
        print(f"FAIL  README.md never states {value} for {what}")

    # The company tags are sold as a feature, so their thinness has to stay on
    # the page: two names cover almost the whole bank.
    top, count = tags.most_common(1)[0]
    share = round(100 * count / total)
    if f"{share}%" not in readme:
        print(f"FAIL  README.md should say that {top} is tagged on {share}% of the problems")
        missing.append(("company tag share", f"{share}%"))

    for what, value in claims.items():
        print(f"  {value:>6}  {what}")
    print(f"  {share:>5}%  share of problems tagged {top}")
    print("\nREADME matches the notebooks." if not missing
          else f"\n{len(missing)} claim(s) in README.md do not match the notebooks.")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
