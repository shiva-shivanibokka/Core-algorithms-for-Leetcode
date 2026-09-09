"""Check a sample of solutions against independent references, not their own asserts.

`verify_notebooks.py` proves each solution agrees with the test cases written
next to it. Those cases were written by the same person, at the same time, from
the same understanding of the problem — so a solution that is wrong in a way the
author did not think of passes. The check is circular.

This breaks the circle for a sample of the bank. Each entry below pairs a
problem with a reference written from the *problem statement* — deliberately
the slow, obvious, brute-force version, because obvious code is the kind you
can be sure about — and a generator of small random inputs. Every matching
solution in the notebooks is then run against its reference a few hundred times.

Three kinds of problem need more than "call it and compare":

  * linked lists, trees and graphs have to be *built* before they can be passed,
    and built out of the node classes that notebook defines, so a solution is
    handed exactly the shape it expects;
  * a solution that returns a node has to be flattened back to values before
    anything can be compared;
  * some problems have more than one correct answer — a topological order is
    not unique — so those are checked against the property the answer must
    have, not against one particular answer.

It is a sample, not a proof. It is the part of the bank whose correctness does
not rest on the author having been right twice.

    python stress_test.py
"""
from __future__ import annotations

import ast
import contextlib
import copy
import glob
import io
import itertools
import json
import random
import sys
from collections import Counter, deque
from collections.abc import Callable
from dataclasses import dataclass

SEED = 20260909
TRIALS = 200


@dataclass(frozen=True)
class Spec:
    """One problem: how to build an input, and how to judge the answer.

    `build(rng, ns)` returns `(args, plain)` — `args` is what the notebook's
    solution is called with, `plain` is the same input described in ordinary
    Python for the reference to work on. For array problems the two are the
    same thing.
    """

    build: Callable
    #: (*plain) -> the expected answer
    expect: Callable | None = None
    #: (result) -> something comparable, for solutions that return nodes
    shape: Callable | None = None
    #: (plain, result) -> bool, for problems whose answer is not unique
    accept: Callable | None = None
    #: (answer) -> canonical form, for answers whose order does not matter
    canon: Callable | None = None


# ══════════════════════════════════════════════ building and reading shapes ══
def make_list(ns, values, cycle_at: int | None = None):
    """A linked list out of *this notebook's* ListNode."""
    node_cls = ns["ListNode"]
    head = None
    nodes = []
    for v in reversed(values):
        head = node_cls(v)
        head.next = nodes[-1] if nodes else None
        nodes.append(head)
    nodes.reverse()
    if cycle_at is not None and nodes:
        nodes[-1].next = nodes[cycle_at]
    return nodes[0] if nodes else None


def list_values(node, limit=200):
    out = []
    while node is not None and len(out) < limit:
        out.append(node.val)
        node = node.next
    return out


def random_tree(rng, size, values):
    """A plain tree: None, or (value, left, right)."""
    if size == 0:
        return None
    left = rng.randint(0, size - 1)
    return (values.pop(), random_tree(rng, left, values), random_tree(rng, size - 1 - left, values))


def make_tree(ns, plain):
    if plain is None:
        return None
    node_cls = ns["TreeNode"]
    val, left, right = plain
    node = node_cls(val)
    node.left = make_tree(ns, left)
    node.right = make_tree(ns, right)
    return node


def tree_levels(plain):
    """Values by depth, from a plain tree."""
    levels, frontier = [], [plain] if plain else []
    while frontier:
        levels.append([n[0] for n in frontier])
        frontier = [c for n in frontier for c in (n[1], n[2]) if c]
    return levels


def tree_values(node):
    """Level order off a real tree, so a returned tree can be compared."""
    levels, frontier = [], [node] if node else []
    while frontier:
        levels.append([n.val for n in frontier])
        frontier = [c for n in frontier for c in (n.left, n.right) if c]
    return levels


def tree_paths(plain):
    """Every root-to-leaf path of values."""
    if plain is None:
        return []
    val, left, right = plain
    if left is None and right is None:
        return [[val]]
    return [[val] + p for c in (left, right) if c for p in tree_paths(c)]


def mirror(plain):
    if plain is None:
        return None
    val, left, right = plain
    return (val, mirror(right), mirror(left))


def tree_inorder(plain):
    if plain is None:
        return []
    val, left, right = plain
    return tree_inorder(left) + [val] + tree_inorder(right)


def tree_size(plain):
    return 0 if plain is None else 1 + tree_size(plain[1]) + tree_size(plain[2])


def tree_height(plain):
    return 0 if plain is None else 1 + max(tree_height(plain[1]), tree_height(plain[2]))


def components(n, edges):
    """Connected components by union-find — a different algorithm from any
    traversal, which is what makes it worth comparing against."""
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for u, v in edges:
        parent[find(u)] = find(v)
    return len({find(i) for i in range(n)})


def reachable(n, edges, start):
    graph = {i: [] for i in range(n)}
    for u, v in edges:
        graph[u].append(v)
    seen, stack = {start}, [start]
    while stack:
        for nxt in graph[stack.pop()]:
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen


def is_dag(n, edges):
    indegree = [0] * n
    graph = {i: [] for i in range(n)}
    for u, v in edges:
        graph[u].append(v)
        indegree[v] += 1
    queue = deque(i for i in range(n) if indegree[i] == 0)
    taken = 0
    while queue:
        taken += 1
        for nxt in graph[queue.popleft()]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    return taken == n


# ═════════════════════════════════════════════════════════════ generators ════
def ints(rng, n=8, lo=-6, hi=6):
    return [rng.randint(lo, hi) for _ in range(rng.randint(1, n))]


def pints(rng, n=8, lo=1, hi=8):
    return [rng.randint(lo, hi) for _ in range(rng.randint(1, n))]


def text(rng, n=9, alphabet="abc"):
    return "".join(rng.choice(alphabet) for _ in range(rng.randint(1, n)))


def plain_args(fn):
    """For array problems the solution and the reference take the same thing.

    Deep copies, not shallow ones: nearly every grid solution in the bank
    marks visited cells by writing into the grid, and a one-level copy shares
    the rows -- so the reference would be handed the input *after* the solution
    had scribbled on it, and report a correct answer as wrong.
    """
    def build(rng, _ns):
        args = fn(rng)
        return copy.deepcopy(args), copy.deepcopy(args)
    return build


def dag_edges(rng, n):
    """Random edges that respect one hidden order, so the graph is acyclic."""
    order = list(range(n))
    rng.shuffle(order)
    return [[order[i], order[j]] for i in range(n) for j in range(i + 1, n) if rng.random() < 0.35]


def grid_of(rng, rows, cols, values):
    return [[rng.choice(values) for _ in range(cols)] for _ in range(rows)]


# ═══════════════════════════════════════════════════════════════ references ══
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
    return [list(c) for r in range(len(nums) + 1) for c in itertools.combinations(nums, r)]


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
        walk(i, left - candidates[i], path)
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


def ref_isHappy(n):
    seen = set()
    while n != 1 and n not in seen:
        seen.add(n)
        n = sum(int(c) ** 2 for c in str(n))
    return n == 1


def ref_findDuplicate(nums):
    return next(v for v, c in Counter(nums).items() if c > 1)


def ref_floodFill(image, sr, sc, color):
    start = image[sr][sc]
    out = [row[:] for row in image]
    if start == color:
        return out
    stack = [(sr, sc)]
    while stack:
        r, c = stack.pop()
        if 0 <= r < len(out) and 0 <= c < len(out[0]) and out[r][c] == start:
            out[r][c] = color
            stack += [(r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)]
    return out


def ref_maxAreaOfIsland(grid):
    seen = set()
    best = 0
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] != 1 or (r, c) in seen:
                continue
            area, stack = 0, [(r, c)]
            seen.add((r, c))
            while stack:
                y, x = stack.pop()
                area += 1
                for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                    inside = 0 <= ny < len(grid) and 0 <= nx < len(grid[0])
                    if inside and grid[ny][nx] == 1 and (ny, nx) not in seen:
                        seen.add((ny, nx))
                        stack.append((ny, nx))
            best = max(best, area)
    return best


def ref_islandPerimeter(grid):
    total = 0
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] != 1:
                continue
            for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if not (0 <= nr < len(grid) and 0 <= nc < len(grid[0])) or grid[nr][nc] == 0:
                    total += 1
    return total


# ══════════════════════════════════════════════════════════════════ specs ════
def _tree_build(max_size=7, lo=1, hi=9, min_size=0):
    """`min_size=1` where LeetCode's constraints say the tree is never empty --
    a solution that assumes a root exists is not wrong for saying so."""
    def build(rng, ns):
        size = rng.randint(min_size, max_size)
        values = [rng.randint(lo, hi) for _ in range(size)]
        plain = random_tree(rng, size, values)
        return (make_tree(ns, plain),), (plain,)
    return build


def _complete_tree(rng, ns):
    """LC 222 is about a *complete* tree, and the perfect-subtree shortcut the
    good solutions use is only valid on one."""
    n = rng.randint(1, 12)
    values = list(range(1, n + 1))
    nodes = [ns["TreeNode"](v) for v in values]
    for i, node in enumerate(nodes):
        node.left = nodes[2 * i + 1] if 2 * i + 1 < n else None
        node.right = nodes[2 * i + 2] if 2 * i + 2 < n else None
    return (nodes[0],), (n,)


def _list_build(max_len=8, lo=1, hi=9, sort=False):
    def build(rng, ns):
        values = [rng.randint(lo, hi) for _ in range(rng.randint(0, max_len))]
        if sort:
            values.sort()
        return (make_list(ns, values),), (values,)
    return build


def _graph_build(max_n=6, acyclic=True):
    def build(rng, _ns):
        n = rng.randint(2, max_n)
        edges = dag_edges(rng, n)
        if not acyclic and rng.random() < 0.4 and n >= 2:
            edges.append([rng.randrange(n), rng.randrange(n)])
        return (n, [e[:] for e in edges]), (n, [e[:] for e in edges])
    return build


def _valid_topological_order(plain, order):
    n, edges = plain
    if is_dag(n, edges):
        if sorted(order) != list(range(n)):
            return False
        place = {node: i for i, node in enumerate(order)}
        return all(place[u] < place[v] for u, v in edges)
    return list(order) == []


def _remove_elements_input(rng, ns):
    values = [rng.randint(1, 4) for _ in range(rng.randint(0, 8))]
    target = rng.randint(1, 4)
    return (make_list(ns, values), target), (values, target)


def _kth_largest_input(rng):
    nums = [rng.randint(-9, 9) for _ in range(rng.randint(1, 9))]
    return nums, rng.randint(1, len(nums))


def _k_closest_input(rng):
    points = [[rng.randint(-6, 6), rng.randint(-6, 6)] for _ in range(rng.randint(1, 7))]
    return points, rng.randint(1, len(points))


def _closest_elements_input(rng):
    arr = sorted({rng.randint(-9, 9) for _ in range(rng.randint(1, 9))})
    return arr, rng.randint(1, len(arr)), rng.randint(-9, 9)


def _components_input(rng, _ns):
    n = rng.randint(2, 7)
    edges = [[a, b] for a in range(n) for b in range(a + 1, n) if rng.random() < 0.25]
    return (n, copy.deepcopy(edges)), (n, edges)


def _two_sum_input(rng):
    """Distinct values and two *different* positions, so exactly one pair sums
    to the target -- which is what LeetCode 167 guarantees."""
    nums = sorted(rng.sample(range(1, 40), rng.randint(2, 6)))
    i, j = rng.sample(range(len(nums)), 2)
    return nums, nums[i] + nums[j]


def _cycle_input(rng, ns):
    values = [rng.randint(1, 9) for _ in range(rng.randint(1, 7))]
    at = rng.randrange(len(values)) if rng.random() < 0.5 else None
    return (make_list(ns, values, at),), (values, at)


def _path_sum_input(rng, ns):
    size = rng.randint(0, 6)
    plain = random_tree(rng, size, [rng.randint(1, 5) for _ in range(size)])
    target = rng.randint(1, 14)
    return (make_tree(ns, plain), target), (plain, target)


def _intervals(rng):
    """Always start < end: LeetCode's interval problems guarantee it, and a
    zero-width interval makes 'overlap' ambiguous rather than interesting."""
    out = []
    for _ in range(rng.randint(1, 5)):
        start = rng.randint(0, 10)
        out.append([start, start + rng.randint(1, 5)])
    return out


def _diameter(plain):
    if plain is None:
        return 0
    _, left, right = plain
    through = tree_height(left) + tree_height(right)
    return max(through, _diameter(left), _diameter(right))


def _balanced(plain):
    if plain is None:
        return True
    _, left, right = plain
    return (abs(tree_height(left) - tree_height(right)) <= 1
            and _balanced(left) and _balanced(right))


PROBLEMS: dict[str, Spec] = {
    # ── arrays and strings ────────────────────────────────────────────────────
    "twoSumII": Spec(build=plain_args(_two_sum_input), expect=ref_twoSumII),
    "threeSum": Spec(build=plain_args(lambda r: (ints(r, 7),)), expect=ref_threeSum,
                     canon=lambda v: sorted(tuple(x) for x in v)),
    "fourSum": Spec(build=plain_args(lambda r: (ints(r, 7), r.randint(-4, 4))),
                    expect=ref_fourSum, canon=lambda v: sorted(tuple(x) for x in v)),
    "maxArea": Spec(build=plain_args(lambda r: (pints(r),)), expect=ref_maxArea),
    "trap": Spec(build=plain_args(lambda r: (pints(r, 9, 0, 5),)), expect=ref_trap),
    "lengthOfLongestSubstring": Spec(build=plain_args(lambda r: (text(r),)),
                                     expect=ref_lengthOfLongestSubstring),
    "minWindow": Spec(build=plain_args(lambda r: (text(r, 10), text(r, 3))), expect=ref_minWindow),
    "maxSlidingWindow": Spec(
        build=plain_args(lambda r: (lambda a: (a, r.randint(1, len(a))))(ints(r))),
        expect=ref_maxSlidingWindow),
    "characterReplacement": Spec(build=plain_args(lambda r: (text(r, 9, "ab"), r.randint(0, 3))),
                                 expect=ref_characterReplacement),
    "numSubarrayProductLessThanK": Spec(
        build=plain_args(lambda r: (pints(r, 7, 1, 6), r.randint(0, 40))),
        expect=ref_numSubarrayProductLessThanK),
    "longestOnes": Spec(build=plain_args(lambda r: (pints(r, 9, 0, 1), r.randint(0, 3))),
                        expect=ref_longestOnes),
    "searchInsert": Spec(build=plain_args(lambda r: (sorted(ints(r)), r.randint(-8, 8))),
                         expect=ref_searchInsert),
    "searchRange": Spec(build=plain_args(lambda r: (sorted(ints(r)), r.randint(-8, 8))),
                        expect=ref_searchRange),
    "merge": Spec(build=plain_args(lambda r: (_intervals(r),)), expect=ref_merge,
                  canon=lambda v: sorted(tuple(x) for x in v)),
    "eraseOverlapIntervals": Spec(build=plain_args(lambda r: (_intervals(r),)),
                                  expect=ref_eraseOverlapIntervals),
    "findMinArrowShots": Spec(build=plain_args(lambda r: (_intervals(r),)),
                              expect=ref_findMinArrowShots),
    "subsets": Spec(build=plain_args(lambda r: (r.sample(range(9), r.randint(1, 4)),)),
                    expect=ref_subsets, canon=lambda v: sorted(tuple(sorted(x)) for x in v)),
    "permute": Spec(build=plain_args(lambda r: (r.sample(range(9), r.randint(1, 4)),)),
                    expect=ref_permute, canon=lambda v: sorted(tuple(x) for x in v)),
    "combinationSum": Spec(
        build=plain_args(lambda r: (r.sample(range(2, 9), r.randint(1, 3)), r.randint(1, 12))),
        expect=ref_combinationSum, canon=lambda v: sorted(tuple(sorted(x)) for x in v)),
    "coinChange": Spec(
        build=plain_args(lambda r: (r.sample(range(1, 9), r.randint(1, 3)), r.randint(0, 20))),
        expect=ref_coinChange),
    "lengthOfLIS": Spec(build=plain_args(lambda r: (ints(r),)), expect=ref_lengthOfLIS),
    "longestCommonSubsequence": Spec(build=plain_args(lambda r: (text(r, 7), text(r, 7))),
                                     expect=ref_longestCommonSubsequence),
    "rob": Spec(build=plain_args(lambda r: (pints(r, 8, 0, 9),)), expect=ref_rob),
    "canPartition": Spec(build=plain_args(lambda r: (pints(r, 7, 1, 9),)), expect=ref_canPartition),
    "uniquePaths": Spec(build=plain_args(lambda r: (r.randint(1, 6), r.randint(1, 6))),
                        expect=ref_uniquePaths),
    "minDistance": Spec(build=plain_args(lambda r: (text(r, 6, "ab"), text(r, 6, "ab"))),
                        expect=ref_minDistance),
    "climbStairs": Spec(build=plain_args(lambda r: (r.randint(1, 20),)), expect=ref_climbStairs),

    # ── fast & slow pointers ──────────────────────────────────────────────────
    "isHappy": Spec(build=plain_args(lambda r: (r.randint(1, 200),)), expect=ref_isHappy),
    "findDuplicate": Spec(
        build=plain_args(lambda r: ((lambda n, d: r.sample(list(range(1, n + 1)) + [d], n + 1))
                                    (r.randint(2, 7), r.randint(1, 2)),)),
        expect=ref_findDuplicate),
    "hasCycle": Spec(build=_cycle_input, expect=lambda vals, at: at is not None),
    "middleNode": Spec(
        build=_list_build(),
        expect=lambda vals: vals[len(vals) // 2:],
        shape=list_values,
    ),

    # ── linked list, rebuilt from values ──────────────────────────────────────
    "reverseList": Spec(build=_list_build(), expect=lambda vals: vals[::-1], shape=list_values),
    "oddEvenList": Spec(
        build=_list_build(),
        expect=lambda vals: vals[0::2] + vals[1::2],
        shape=list_values,
    ),
    "removeElements": Spec(
        build=_remove_elements_input,
        expect=lambda vals, target: [v for v in vals if v != target],
        shape=list_values,
    ),
    "deleteDuplicates": Spec(
        build=_list_build(sort=True, hi=5),
        expect=lambda vals: [v for i, v in enumerate(vals) if i == 0 or v != vals[i - 1]],
        shape=list_values,
    ),
    "partition": Spec(
        build=lambda rng, ns: (lambda vals, x: ((make_list(ns, vals), x), (vals, x)))(
            [rng.randint(1, 9) for _ in range(rng.randint(0, 8))], rng.randint(1, 9)),
        expect=lambda vals, x: [v for v in vals if v < x] + [v for v in vals if v >= x],
        shape=list_values,
    ),
    "mergeTwoLists": Spec(
        build=lambda rng, ns: (lambda a, b: ((make_list(ns, a), make_list(ns, b)), (a, b)))(
            sorted(rng.randint(1, 9) for _ in range(rng.randint(0, 5))),
            sorted(rng.randint(1, 9) for _ in range(rng.randint(0, 5)))),
        expect=lambda a, b: sorted(a + b),
        shape=list_values,
    ),
    "getDecimalValue": Spec(
        build=lambda rng, ns: (lambda bits: ((make_list(ns, bits),), (bits,)))(
            [rng.randint(0, 1) for _ in range(rng.randint(1, 8))]),
        expect=lambda bits: int("".join(map(str, bits)), 2),
    ),

    # ── trees ─────────────────────────────────────────────────────────────────
    "maxDepth": Spec(build=_tree_build(), expect=tree_height),
    "countNodes": Spec(build=_complete_tree, expect=lambda n: n),
    "inorderTraversal": Spec(build=_tree_build(), expect=tree_inorder),
    "levelOrder": Spec(build=_tree_build(), expect=tree_levels),
    "levelOrderBottom": Spec(build=_tree_build(), expect=lambda p: tree_levels(p)[::-1]),
    "averageOfLevels": Spec(
        build=_tree_build(max_size=6),
        expect=lambda p: [sum(lv) / len(lv) for lv in tree_levels(p)],
        canon=lambda v: [round(x, 6) for x in v] if isinstance(v, list) else v,
    ),
    "largestValues": Spec(build=_tree_build(), expect=lambda p: [max(lv) for lv in tree_levels(p)]),
    "findBottomLeftValue": Spec(
        build=_tree_build(max_size=7, min_size=1),
        expect=lambda p: tree_levels(p)[-1][0] if p else None,
    ),
    "minDepth": Spec(
        build=_tree_build(),
        expect=lambda p: 0 if p is None else min(len(path) for path in tree_paths(p)),
    ),
    "invertTree": Spec(build=_tree_build(), expect=lambda p: tree_levels(mirror(p)),
                       shape=tree_values),
    "isSymmetric": Spec(build=_tree_build(min_size=1), expect=lambda p: mirror(p) == p),
    "hasPathSum": Spec(
        build=_path_sum_input,
        expect=lambda plain, target: any(sum(p) == target for p in tree_paths(plain)),
    ),
    "deepestLeavesSum": Spec(
        build=_tree_build(min_size=1, ),
        expect=lambda p: sum(tree_levels(p)[-1]) if p else 0,
    ),
    "diameterOfBinaryTree": Spec(
        build=_tree_build(min_size=1, ),
        expect=lambda p: _diameter(p),
    ),
    "isBalanced": Spec(build=_tree_build(), expect=lambda p: _balanced(p)),

    # ── graphs ────────────────────────────────────────────────────────────────
    "countComponents": Spec(build=_components_input, expect=components),
    "islandPerimeter": Spec(
        build=plain_args(lambda r: (grid_of(r, r.randint(1, 4), r.randint(1, 4), [0, 1]),)),
        expect=ref_islandPerimeter,
    ),
    "maxAreaOfIsland": Spec(
        build=plain_args(lambda r: (grid_of(r, r.randint(1, 4), r.randint(1, 4), [0, 1]),)),
        expect=ref_maxAreaOfIsland,
    ),
    "floodFill": Spec(
        build=plain_args(lambda r: (lambda g: (g, r.randrange(len(g)), r.randrange(len(g[0])),
                                               r.randint(0, 3)))
                         (grid_of(r, r.randint(1, 4), r.randint(1, 4), [0, 1, 2]))),
        expect=ref_floodFill,
    ),
    "canVisitAllRooms": Spec(
        build=plain_args(lambda r: ((lambda n: [[k for k in range(n) if r.random() < 0.35]
                                                for _ in range(n)])(r.randint(2, 5)),)),
        expect=lambda rooms: len(reachable(len(rooms),
                                           [[i, k] for i, ks in enumerate(rooms) for k in ks],
                                           0)) == len(rooms),
    ),

    # ── top k elements ───────────────────────────────────────
    "findKthLargest": Spec(
        build=plain_args(_kth_largest_input),
        expect=lambda nums, k: sorted(nums, reverse=True)[k - 1],
    ),
    "kClosest": Spec(
        build=plain_args(_k_closest_input),
        expect=lambda points, k: sorted(points, key=lambda q: q[0] ** 2 + q[1] ** 2)[:k],
        # two points can sit the same distance out, and then which of them comes
        # back is arbitrary -- so compare the distances, not the points
        canon=lambda v: (sorted(q[0] ** 2 + q[1] ** 2 for q in v)
                         if isinstance(v, list) else v),
    ),
    "findClosestElements": Spec(
        build=plain_args(_closest_elements_input),
        expect=lambda arr, k, x: sorted(sorted(arr, key=lambda v: (abs(v - x), v))[:k]),
    ),

    # ── topological sort ──────────────────────────────────────────────────────
    "canFinish": Spec(
        build=_graph_build(acyclic=False),
        expect=lambda n, edges: is_dag(n, [[v, u] for u, v in edges]),
    ),
    "findOrder": Spec(
        build=_graph_build(acyclic=False),
        accept=lambda plain, order: _valid_topological_order(
            (plain[0], [[v, u] for u, v in plain[1]]), order),
    ),
    "isDAG": Spec(build=_graph_build(acyclic=False), expect=is_dag),
    "countSources": Spec(
        build=_graph_build(acyclic=True),
        expect=lambda n, edges: sum(1 for i in range(n) if all(v != i for _, v in edges)),
    ),
    "countSinks": Spec(
        build=_graph_build(acyclic=True),
        expect=lambda n, edges: sum(1 for i in range(n) if all(u != i for u, _ in edges)),
    ),
}


# Same function name, different problem, *and* a signature that accepts the
# reference's inputs -- so nothing but knowing the bank tells them apart. Shape
# mismatches sort themselves out at call time and are reported as skips.
COLLISIONS = {
    ("07_Binary_Tree_DFS.ipynb", "rob"),          # House Robber III: robs a tree
    ("03_Fast_And_Slow_Pointers.ipynb", "countNodes"),   # counts a linked list
    ("06_Linked_List_Reversal.ipynb", "countNodes"),
}


def collect():
    """Every notebook function whose name matches a problem above.

    Cells are executed the way `verify_notebooks.py` executes them, in one
    namespace per notebook, and the namespace travels with each function so an
    input can be built out of that notebook's own ListNode and TreeNode.
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
                    found.append((path, cell, node.name, namespace[node.name], dict(namespace)))
    return found


def check(name, spec, fn, ns):
    """Run one implementation. Returns (mismatches, first_example, skipped_because)."""
    rng = random.Random(SEED)
    canon = spec.canon or (lambda v: v)
    mismatches, shape_errors, first = 0, 0, None

    for _ in range(TRIALS):
        try:
            args, plain = spec.build(rng, ns)
        except KeyError:
            # the notebook has no ListNode/TreeNode, so this problem is not the
            # one this function solves
            return 0, None, "no node class in this notebook"

        try:
            actual = fn(*args)
        except (TypeError, AttributeError) as exc:
            shape_errors += 1
            if first is None:
                first = (plain, f"{type(exc).__name__}: {exc}", "—")
            continue
        except Exception as exc:
            actual = f"{type(exc).__name__}: {exc}"

        if spec.shape and not isinstance(actual, str):
            try:
                actual = spec.shape(actual)
            except Exception as exc:
                actual = f"{type(exc).__name__}: {exc}"

        if spec.accept:
            ok = spec.accept(plain, actual)
            expected = "any valid answer"
        else:
            expected = spec.expect(*plain)
            try:
                ok = canon(actual) == canon(expected)
            except Exception:
                ok = actual == expected
        if not ok:
            mismatches += 1
            if first is None:
                first = (plain, actual, expected)

    # Failing the same way on every single input is a signature mismatch -- a
    # different problem that happens to share this name. Failing on some of
    # them is a bug, and is reported.
    if shape_errors == TRIALS:
        return 0, None, "same name, different problem"
    return mismatches + shape_errors, first, None


def main():
    implementations = collect()
    failures, skipped = [], []

    for path, cell, name, fn, ns in implementations:
        spec = PROBLEMS[name]
        bad, first, reason = check(name, spec, fn, ns)
        if reason:
            skipped.append((path, cell, name, reason))
            continue
        if bad:
            failures.append((path, cell, name))
            print(f"FAIL  {path}  cell {cell}: {name} disagrees with the reference "
                  f"on {bad}/{TRIALS} random inputs")
            print(f"        input    {first[0]}")
            print(f"        returned {first[1]}")
            print(f"        expected {first[2]}")

    skipped_keys = {(p, c, n) for p, c, n, _ in skipped}
    checked_impls = [(p, c, n) for p, c, n, _, _ in implementations
                     if (p, c, n) not in skipped_keys]
    checked = len(checked_impls)
    covered = sorted({p for p, _, _ in checked_impls})
    print(f"\n{checked} implementations of {len(PROBLEMS)} problems checked against an "
          f"independent reference, {TRIALS} random inputs each.")
    print(f"covering {len(covered)} of 13 patterns: "
          f"{', '.join(p[:2] for p in covered)}")
    if skipped:
        print(f"{len(skipped)} skipped (same name, different problem)")
    print("All sampled solutions agree." if not failures
          else f"{len(failures)} solution(s) disagree with the reference.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
