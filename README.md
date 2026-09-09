# Core Algorithms for LeetCode

**A pattern-first coding-interview prep bank: 13 algorithm patterns, 90 worked problems each, every solution paired with runnable `assert` tests, a sample of them cross-checked against independent references, and the whole thing enforced green by CI.**

Built by Shivani Bokka.

[![Verify notebooks](https://github.com/shiva-shivanibokka/Core-algorithms-for-Leetcode/actions/workflows/verify.yml/badge.svg)](https://github.com/shiva-shivanibokka/Core-algorithms-for-Leetcode/actions/workflows/verify.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)

---

### Recruiter TL;DR

- **What it is** — a self-built coding-interview study bank organized by *pattern* (Two Pointers, Sliding Window, DP, …) rather than by random problem: 1,170 problem slots, 1,130 distinct problems, 655 distinct LeetCode numbers cited, all worked and all runnable.
- **Hardest problem solved** — making the bank *trustworthy*, which turned out to be a harder claim than it sounds. Inline asserts prove a solution matches the tests written beside it — by the same person, at the same sitting, from the same reading of the problem. That is circular, and three ways of being wrong survive it. All three are now checked by scripts that run in CI, and each one had already caught something real.
- **Impact** — 13 patterns × 90 problems, difficulty-tiered, **every cell green under CI on every push**, plus 27 problems sampled and re-verified against brute-force references that share no code with the solutions.

---

## Overview

Most interview prep is a pile of unrelated solved problems. This repo is organized the way the problems are actually *tested* — by the underlying pattern. Learn the shape of "Two Pointers" once, then drill 90 variations of it, from a warm-up Easy through a Hard that a FAANG onsite would use.

Each of the 13 notebooks is a self-contained lesson: a short explanation of the pattern, then a graded ladder of problems. Every problem states the approach and its time/space complexity, followed by a clean solution and `assert`-based tests.

**Who it's for:** primarily my own interview preparation, and anyone who wants a pattern-organized, *verified* problem bank to study from rather than trusting unverified snippets off the internet.

## What's inside

The 13 patterns, in the intended learning order:

| # | Pattern | # | Pattern |
|---|---------|---|---------|
| 01 | Two Pointers | 08 | Binary Tree BFS |
| 02 | Sliding Window | 09 | Graph DFS / BFS |
| 03 | Fast & Slow Pointers | 10 | Topological Sort |
| 04 | Binary Search | 11 | Top-K Elements (Heaps) |
| 05 | Merge Intervals | 12 | Subsets / Backtracking |
| 06 | Linked List Reversal (in-place) | 13 | Dynamic Programming |
| 07 | Binary Tree DFS | | |

### Anatomy of every problem

Each problem is a markdown cell (statement) followed by a code cell (solution + tests):

```
## Easy 1 — Two Sum II (LeetCode 167)
> 🏢 Asked by: Amazon, Microsoft, Google, Apple
Given a 1-indexed sorted array, find two numbers that add up to a target...
```

```python
def twoSumII(numbers, target):
    left, right = 0, len(numbers) - 1
    while left < right:
        s = numbers[left] + numbers[right]
        if s == target:
            return [left + 1, right + 1]   # 1-indexed
        elif s < target:
            left += 1
        else:
            right -= 1

assert twoSumII([2, 7, 11, 15], 9) == [1, 2]
assert twoSumII([2, 3, 4], 6) == [1, 3]
print("All tests passed!")
```

The `assert`s are the point: a solution isn't "done" until it proves itself.

### What the counts mean

Honest accounting, because the headline numbers are easy to inflate:

- **1,170 problem slots** — 13 notebooks × 90 problems. That is the size of the ladder you work through.
- **1,130 distinct problems** — 40 slots are a deliberate second pass at a problem already in the same notebook, usually a "Simplified" version early in the ladder and the "Full" version later (Sudoku Solver, N-Queens, Palindrome Partitioning). They are pedagogy, not padding, but they are not 40 more problems.
- **655 distinct LeetCode numbers** cited. The rest are variants and design questions with no LeetCode number, and problems that legitimately appear under two different patterns.
- **Difficulty** is the ladder's own tiering, not LeetCode's. Some notebooks label it per problem ("Medium 8 — …"), others group problems under an `# EASY Problems` section header. It is my judgement of the step size, so a LeetCode Medium sometimes sits in the Easy tier of a pattern I had already drilled.
- **The company tags are a rough prior, not sourced data.** Amazon is tagged on 99% of the problems and Google on nearly as many, so the tag mostly tells you a problem is a common interview problem. Treat it as a highlighter, not as evidence.

## Architecture

This is a study repo, not a deployed service — so its "architecture" is how correctness is guaranteed. Notebooks give you prose, runnable code, and tests in one place, but notebooks are notorious for silently rotting: a cell gets edited and never re-run. Three scripts close that gap, and CI runs all three on every push.

```mermaid
flowchart TD
    subgraph NB["13 pattern notebooks"]
        A["Markdown cell<br/>problem + approach + complexity"]
        B["Code cell<br/>solution + assert tests"]
        A --> B
    end
    B -->|executed top-to-bottom<br/>in a shared namespace| V["verify_notebooks.py<br/>every cell runs, every<br/>solution is reached"]
    B -->|run against brute-force<br/>references on random inputs| S["stress_test.py<br/>answers checked without<br/>the notebook's own asserts"]
    A -->|counted| C["check_claims.py<br/>this README's numbers"]
    V --> CI["GitHub Actions"]
    S --> CI
    C --> CI
    CI --> G{"All three pass?"}
    G -->|yes| OK["✅ green build"]
    G -->|no| BAD["❌ red build<br/>names the notebook,<br/>cell, and problem"]
```

**Why a shared namespace?** Cells build on earlier ones (helpers like `make_list` and `build_tree`, shared `TreeNode` / `ListNode` classes), so the verifier executes each notebook top-to-bottom exactly as a human would run it. A per-cell sandbox would report false failures on every cell that reuses a helper.

## Tech Stack

- **Python 3.12** — almost entirely the **standard library** (`heapq`, `bisect`, `collections`).
- **`sortedcontainers`** — the only third-party dependency (used in 5 cells) for `SortedList` / `SortedDict`, Python's balanced-BST / TreeMap equivalent, on problems that need an ordered structure with O(log n) operations.
- **Jupyter Notebooks** — chosen so explanation, solution, and tests live together in one readable artifact.
- **GitHub Actions** — CI that runs the full verification on every push.

## Skills Demonstrated

- **Data structures & algorithms** — 13 core patterns across arrays, strings, linked lists, trees, graphs, heaps, backtracking, and dynamic programming.
- **Algorithm design & complexity analysis** — every solution annotated with its time/space trade-off and the reasoning behind the approach.
- **Test design, including its limits** — inline asserts, plus an independent-reference layer built specifically because inline asserts cannot catch a misunderstanding of the problem.
- **CI/CD pipeline implementation** — GitHub Actions runs all three checks on each push and blocks a red build.
- **System design & architecture reasoning** — a purpose-built verification harness with a documented design trade-off (shared-namespace execution) that models how the notebooks are actually run.

## Getting Started

Python 3.12 and a single dependency (`sortedcontainers`).

```bash
git clone https://github.com/shiva-shivanibokka/Core-algorithms-for-Leetcode.git
cd Core-algorithms-for-Leetcode
pip install -r requirements.txt

# Study interactively:
jupyter notebook            # then open any NN_Pattern.ipynb

# Or verify every solution in one shot (no Jupyter needed):
python verify_notebooks.py
```

Expected output when everything is correct:

```
All notebooks pass.
```

## Usage

**Study a pattern:** open a notebook (e.g. `04_Binary_Search.ipynb`) and read top to bottom — each problem escalates in difficulty. Run a cell (`Shift+Enter`); a passing solution prints `All tests passed!`.

**Verify everything before committing:** run the harness. If a cell is wrong, it names the notebook, the cell number, and the error:

```bash
$ python verify_notebooks.py
FAIL  11_Top_K_Elements.ipynb  cell 85: IndexError: list index out of range
        -> import heapq
1 failing cell(s).
```

This is the same check CI runs, so a green local run means a green build.

## Project Structure

```
.
├── 01_Two_Pointers.ipynb          # ┐
├── 02_Sliding_Window.ipynb        # │
├── ...                            # │  13 pattern notebooks, each 90 graded
├── 13_Dynamic_Programming.ipynb   # ┘  problems + inline tests
├── verify_notebooks.py            # runs every cell; also fails on a problem with
│                                  #   no solution, or a solution never reached
├── stress_test.py                 # 27 problems vs independent brute-force references
├── check_claims.py                # the numbers in this README, recomputed
├── requirements.txt               # single dependency: sortedcontainers
├── .github/workflows/verify.yml   # CI: all three scripts on every push
├── LICENSE
└── README.md
```

## Testing

Testing is not a separate suite — it is built into every problem, and then checked from the outside because "built in" is not enough on its own.

### 1. `verify_notebooks.py` — does every solution run, and does it match its tests?

Executes all 1,178 code cells across the 13 notebooks in one namespace per notebook, and exits non-zero on any failure. It also enforces two things that executing cells cannot see on its own:

- **Every problem statement must be followed by a solution cell.** A heading with an approach note and no code passes any test runner in the world, because there is nothing to run.
- **Every solution a cell defines must be reached by that cell.** A cell that defines the solution and then asserts on a *different* function is green and proves nothing.

Both checks exist because both failures were in this repo:

| Problem | What shipped | Why nothing caught it |
|---|---|---|
| `11` H5 The Skyline Problem | a stub — the sweep loop's body was `pass` and `result` was returned still empty | the stub was never called; a second function did the work and the asserts tested that one |
| `10` M30 Course Schedule IV | a wrong answer — reachability propagated in forward topological order, reading sets still being built, and a `u in reachable[v] == False and …` expression that does not mean what it looks like | same shape: never called, asserts pointed at the alternative implementation |
| `01` H1 Trapping Rain Water | nothing at all — a heading, and a note saying it was already solved earlier | there was no cell to fail |

All three are fixed: the Skyline Problem now ships both the `SortedList` sweep and the lazy-deletion heap and asserts they agree, Course Schedule IV propagates in *reverse* topological order (with Floyd–Warshall alongside as a cross-check), and Trapping Rain Water gets the monotonic-stack approach — the genuine follow-up to the two-pointer version — checked against it on 2,000 random inputs.

### 2. `stress_test.py` — is the solution actually right?

The inline asserts were written by the same person who wrote the solution, at the same time, from the same reading of the problem. They prove the code agrees with its author. They cannot catch the author being wrong.

So 27 problems are pinned to a reference implementation written from the *problem statement* — deliberately the slow, obvious, brute-force version — and every matching solution in the notebooks is run against it on 200 random inputs. Currently 37 implementations, all agreeing.

The point is what this catches that the other script cannot. Break `coinChange` in a way its own three asserts do not reach:

```
$ python verify_notebooks.py
All notebooks pass.

$ python stress_test.py
FAIL  13_Dynamic_Programming.ipynb  cell 23: coinChange disagrees with the
      reference on 192/200 random inputs
```

It is a sample, not a proof — 27 of 1,130 problems. It is the slice whose correctness does not rest on my having been right twice.

### 3. `check_claims.py` — do this README's numbers still hold?

Every count on this page is computed from the notebooks and required to appear here verbatim. Add a problem and the build fails until the sentence describing the bank is corrected. Prose is the only part of a repo that cannot self-update, so it is the part that quietly goes wrong.

> An earlier audit found **41 cells whose asserts didn't hold** — the notebooks had never been run end to end. Fixing those (5 solution bugs, ~36 wrong expected values) and adding `verify_notebooks.py` is what made "all green" true. The two scripts above exist because "all green" still wasn't the same as "all correct".

## Impact / Results

All figures are computed from the notebooks by `check_claims.py`, which fails the build if this section drifts:

- **13** algorithm patterns, in a deliberate learning order.
- **90** problems per pattern — **1,170** problem slots, **1,130** distinct problems, **655** distinct LeetCode numbers cited.
- **100%** of solution cells pass, every problem has a solution, and every solution is reached — enforced by CI on every push.
- **27** problems additionally checked against independent brute-force references on random inputs.
- **1** third-party dependency (`sortedcontainers`); everything else is the standard library.

## Roadmap

- **Spaced-repetition tracking** — a lightweight workflow to schedule which solved problems to re-attempt and when, so review effort concentrates on the problems most likely to be forgotten.
- **More problems under an independent reference** — 27 of 1,130 is a sample; the ones with a cheap brute force are worth pinning.
- Additional patterns as needed (e.g. Union-Find, Trie, Monotonic Stack, Bit Manipulation).

## License

Released under the [MIT License](LICENSE).
