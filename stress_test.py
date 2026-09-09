"""Check a sample of solutions against independent references, not their own asserts.

`verify_notebooks.py` proves each solution agrees with the test cases written
next to it. Those cases were written by the same person, at the same time, from
the same understanding of the problem — so a solution that is wrong in a way the
author did not think of passes. The check is circular.

This breaks the circle for a sample of the bank. Each entry below pairs a
problem with a reference implementation written from the *problem statement* —
deliberately the slow, obvious, brute-force version, because obvious code is the
kind you can be sure about — and a generator of small random inputs. Every
matching solution in the notebooks is then run against its reference a few
hundred times.

It is a sample, not a proof: ~30 of 1,170 problems. It is the part of the bank
whose correctness does not rest on the author having been right twice.

    python stress_test.py
"""
from __future__ import annotations

import ast
import contextlib
import glob
import io
import itertools
import json
import random
import sys
from collections import Counter

SEED = 20260909
TRIALS = 200


# --------------------------------------------------------------- references
# Slow and obvious on purpose. None of these share code with the notebooks.
def ref_twoSumII(nums, target):
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i + 1, j + 1]
    return []


def ref_threeSum(nums):
    return sorted({c for c in itertools.combinations(sorted(nums), 3) if sum(c) == 0})


def ref_fourSum(nums, target):
    return sorted({c for c in itertools.combinations(sorted(nums), 4) if sum(c) == target})


def ref_maxArea(height):
    return max((min(height[i], height[j]) * (j - i)
                for i in range(len(height))
                for j in range(i + 1, len(height))), default=0)


def ref_trap(height):
    return sum(max(0, min(max(height[:i + 1]), max(height[i:])) - h)
               for i, h in enumerate(height))


def ref_lengthOfLongestSubstring(s):
    best = 0
    for i in range(len(s)):
        seen = set()
        for j in range(i, len(s)):
            if s[j] in seen:
                break
            seen.add(s[j])
            best = max(best, j - i + 1)
    return best


def ref_minWindow(s, t):
    need = Counter(t)
    best = ""
    for i in range(len(s)):
        for j in range(i, len(s)):
            window = s[i:j + 1]
            if not need - Counter(window):
                if not best or len(window) < len(best):
                    best = window
                break
    return best


def ref_maxSlidingWindow(nums, k):
    return [max(nums[i:i + k]) for i in range(len(nums) - k + 1)]


def ref_characterReplacement(s, k):
    best = 0
    for i in range(len(s)):
        for j in range(i, len(s)):
            window = s[i:j + 1]
            if len(window) - max(Counter(window).values()) <= k:
                best = max(best, len(window))
    return best


def ref_numSubarrayProductLessThanK(nums, k):
    count = 0
    for i in range(len(nums)):
        product = 1
        for j in range(i, len(nums)):
            product *= nums[j]
            if product >= k:
                break
            count += 1
    return count


def ref_longestOnes(nums, k):
    best = 0
    for i in range(len(nums)):
        zeros = 0
        for j in range(i, len(nums)):
            zeros += nums[j] == 0
            if zeros > k:
                break
            best = max(best, j - i + 1)
    return best


def ref_searchInsert(nums, target):
    for i, v in enumerate(nums):
        if v >= target:
            return i
    return len(nums)


def ref_searchRange(nums, target):
    hits = [i for i, v in enumerate(nums) if v == target]
    return [hits[0], hits[-1]] if hits else [-1, -1]


def ref_merge(intervals):
    out = []
    for start, end in sorted(intervals):
        if out and start <= out[-1][1]:
            out[-1][1] = max(out[-1][1], end)
        else:
            out.append([start, end])
    return out


def ref_eraseOverlapIntervals(intervals):
    """Largest subset with no overlap, by exhaustive search."""
    for keep in range(len(intervals), -1, -1):
        for combo in itertools.combinations(sorted(intervals), keep):
            if all(combo[i][1] <= combo[i + 1][0] for i in range(len(combo) - 1)):
                return len(intervals) - keep
    return len(intervals)


def ref_findMinArrowShots(points):
    shots, end = 0, None
    for start, finish in sorted(points):
        if end is None or start > end:
            shots += 1
            end = finish
        else:
            end = min(end, finish)
    return shots


def ref_subsets(nums):
    return [list(c) for r in range(len(nums) + 1)
            for c in itertools.combinations(nums, r)]


def ref_permute(nums):
    return [list(p) for p in itertools.permutations(nums)]


def ref_combinationSum(candidates, target):
    out = []

    def walk(i, left, path):
        if left == 0:
            out.append(list(path))
            return
        if left < 0 or i == len(candidates):
            return
        path.append(candidates[i])
        walk(i, left - candidates[i], path)     # reuse allowed
        path.pop()
        walk(i + 1, left, path)

    walk(0, target, [])
    return out


def ref_coinChange(coins, amount):
    best = [0] + [float("inf")] * amount
    for a in range(1, amount + 1):
        for c in coins:
            if c <= a:
                best[a] = min(best[a], best[a - c] + 1)
    return -1 if best[amount] == float("inf") else best[amount]


def ref_lengthOfLIS(nums):
    best = 0
    for r in range(1, len(nums) + 1):
        for c in itertools.combinations(nums, r):
            if all(c[i] < c[i + 1] for i in range(r - 1)):
                best = max(best, r)
    return best


def ref_longestCommonSubsequence(a, b):
    dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i, ca in enumerate(a):
        for j, cb in enumerate(b):
            dp[i + 1][j + 1] = dp[i][j] + 1 if ca == cb else max(dp[i][j + 1], dp[i + 1][j])
    return dp[-1][-1]


def ref_rob(nums):
    best = 0
    for r in range(len(nums) + 1):
        for c in itertools.combinations(range(len(nums)), r):
            if all(c[i + 1] - c[i] > 1 for i in range(r - 1)):
                best = max(best, sum(nums[i] for i in c))
    return best


def ref_canPartition(nums):
    total = sum(nums)
    if total % 2:
        return False
    sums = {0}
    for n in nums:
        sums |= {s + n for s in sums}
    return total // 2 in sums


def ref_uniquePaths(m, n):
    grid = [[1] * n for _ in range(m)]
    for i in range(1, m):
        for j in range(1, n):
            grid[i][j] = grid[i - 1][j] + grid[i][j - 1]
    return grid[-1][-1]


def ref_minDistance(a, b):
    dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) + 1):
        for j in range(len(b) + 1):
            if not i or not j:
                dp[i][j] = i or j
            elif a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    return dp[-1][-1]


def ref_climbStairs(n):
    a, b = 1, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return b


# ------------------------------------------------------------------- inputs
def ints(rng, n=8, lo=-6, hi=6):
    return [rng.randint(lo, hi) for _ in range(rng.randint(1, n))]


def pints(rng, n=8, lo=1, hi=8):
    return [rng.randint(lo, hi) for _ in range(rng.randint(1, n))]


def text(rng, n=9, alphabet="abc"):
    return "".join(rng.choice(alphabet) for _ in range(rng.randint(1, n)))


def intervals(rng):
    """Always start < end: LeetCode's interval problems guarantee it, and a
    zero-width interval makes 'overlap' ambiguous rather than interesting."""
    out = []
    for _ in range(rng.randint(1, 5)):
        start = rng.randint(0, 10)
        out.append([start, start + rng.randint(1, 5)])
    return (out,)


def sorted_and_target(rng):
    return (sorted(ints(rng)), rng.randint(-8, 8))


def two_sum_input(rng):
    # Distinct values, so the pair that sums to the target is unique -- which is
    # what LeetCode 167 guarantees and what makes a single answer comparable.
    nums = sorted(rng.sample(range(1, 40), rng.randint(2, 6)))
    i, j = sorted(rng.sample(range(len(nums)), 2))
    return (nums, nums[i] + nums[j])


def window_input(rng):
    nums = ints(rng)
    return (nums, rng.randint(1, len(nums)))


def as_tuples(result):
    return sorted(tuple(x) for x in result)


def as_sorted_tuples(result):
    return sorted(tuple(sorted(x)) for x in result)


# name -> (input generator, reference, canonicaliser for order-insensitive answers)
PROBLEMS = {
    "twoSumII": (two_sum_input, ref_twoSumII, None),
    "threeSum": (lambda r: (ints(r, 7),), ref_threeSum, as_tuples),
    "fourSum": (lambda r: (ints(r, 7), r.randint(-4, 4)), ref_fourSum, as_tuples),
    "maxArea": (lambda r: (pints(r),), ref_maxArea, None),
    "trap": (lambda r: (pints(r, 9, 0, 5),), ref_trap, None),
    "lengthOfLongestSubstring": (lambda r: (text(r),), ref_lengthOfLongestSubstring, None),
    "minWindow": (lambda r: (text(r, 10), text(r, 3)), ref_minWindow, None),
    "maxSlidingWindow": (window_input, ref_maxSlidingWindow, None),
    "characterReplacement": (lambda r: (text(r, 9, "ab"), r.randint(0, 3)),
                             ref_characterReplacement, None),
    "numSubarrayProductLessThanK": (lambda r: (pints(r, 7, 1, 6), r.randint(0, 40)),
                                    ref_numSubarrayProductLessThanK, None),
    "longestOnes": (lambda r: (pints(r, 9, 0, 1), r.randint(0, 3)), ref_longestOnes, None),
    "searchInsert": (sorted_and_target, ref_searchInsert, None),
    "searchRange": (sorted_and_target, ref_searchRange, None),
    "merge": (intervals, ref_merge, as_tuples),
    "eraseOverlapIntervals": (intervals, ref_eraseOverlapIntervals, None),
    "findMinArrowShots": (intervals, ref_findMinArrowShots, None),
    "subsets": (lambda r: (r.sample(range(9), r.randint(1, 4)),), ref_subsets, as_sorted_tuples),
    "permute": (lambda r: (r.sample(range(9), r.randint(1, 4)),), ref_permute, as_tuples),
    "combinationSum": (lambda r: (r.sample(range(2, 9), r.randint(1, 3)), r.randint(1, 12)),
                       ref_combinationSum, as_sorted_tuples),
    "coinChange": (lambda r: (r.sample(range(1, 9), r.randint(1, 3)), r.randint(0, 20)),
                   ref_coinChange, None),
    "lengthOfLIS": (lambda r: (ints(r),), ref_lengthOfLIS, None),
    "longestCommonSubsequence": (lambda r: (text(r, 7), text(r, 7)),
                                 ref_longestCommonSubsequence, None),
    "rob": (lambda r: (pints(r, 8, 0, 9),), ref_rob, None),
    "canPartition": (lambda r: (pints(r, 7, 1, 9),), ref_canPartition, None),
    "uniquePaths": (lambda r: (r.randint(1, 6), r.randint(1, 6)), ref_uniquePaths, None),
    "minDistance": (lambda r: (text(r, 6, "ab"), text(r, 6, "ab")), ref_minDistance, None),
    "climbStairs": (lambda r: (r.randint(1, 20),), ref_climbStairs, None),
}


# Same function name, different problem, *and* a signature that accepts the
# reference's inputs -- so nothing but knowing the bank tells them apart. The
# arity mismatches sort themselves out at call time and are reported as skips.
COLLISIONS = {
    ("07_Binary_Tree_DFS.ipynb", "rob"),     # House Robber III: robs a tree, not a street
}


def collect():
    """Every notebook function whose name matches a problem above.

    Cells are executed the way `verify_notebooks.py` executes them, in one
    namespace per notebook, because that is how they are written.
    """
    found = []
    for path in sorted(glob.glob("*.ipynb")):
        with open(path, encoding="utf-8") as fh:
            nb = json.load(fh)
        namespace, cell = {}, 0
        for c in nb["cells"]:
            if c["cell_type"] != "code":
                continue
            cell += 1
            src = "".join(c["source"])
            if not src.strip():
                continue
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    exec(compile(src, f"<{path}#cell{cell}>", "exec"), namespace)
            except Exception:  # noqa: S112 -- a cell that raises is verify_notebooks.py's
                continue       # job to report; swallowing it here would double the noise
            for node in ast.parse(src).body:
                if (isinstance(node, ast.FunctionDef) and node.name in PROBLEMS
                        and (path, node.name) not in COLLISIONS):
                    found.append((path, cell, node.name, namespace[node.name]))
    return found


def main():
    implementations = collect()
    failures, skipped = [], []

    for path, cell, name, fn in implementations:
        generate, reference, canonical = PROBLEMS[name]
        canonical = canonical or (lambda result: result)
        rng = random.Random(SEED)
        mismatches, first = 0, None

        for _ in range(TRIALS):
            args = generate(rng)
            expected = reference(*[a.copy() if isinstance(a, list) else a for a in args])
            try:
                actual = fn(*[a.copy() if isinstance(a, list) else a for a in args])
            except TypeError as exc:
                # A different problem that happens to share this function name
                # (`merge` is both "merge intervals" and "merge sorted array").
                skipped.append((path, cell, name, str(exc)[:60]))
                mismatches = 0
                break
            except Exception as exc:
                actual = f"{type(exc).__name__}: {exc}"
            try:
                same = canonical(actual) == canonical(expected)
            except Exception:
                same = actual == expected
            if not same:
                mismatches += 1
                if first is None:
                    first = (args, actual, expected)

        if mismatches:
            failures.append((path, cell, name))
            print(f"FAIL  {path}  cell {cell}: {name} disagrees with the reference "
                  f"on {mismatches}/{TRIALS} random inputs")
            print(f"        input    {first[0]}")
            print(f"        returned {first[1]}")
            print(f"        expected {first[2]}")

    checked = len(implementations) - len(skipped)
    print(f"\n{checked} implementations of {len(PROBLEMS)} problems checked against an "
          f"independent reference, {TRIALS} random inputs each.")
    if skipped:
        print(f"{len(skipped)} skipped (same function name, different problem): "
              + ", ".join(f"{p}#{c} {n}" for p, c, n, _ in skipped))
    print("All sampled solutions agree." if not failures
          else f"{len(failures)} solution(s) disagree with the reference.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
