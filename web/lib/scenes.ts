/**
 * The scripted animation for each pattern.
 *
 * A pattern is a *shape of movement*, and that is the thing a paragraph is
 * worst at describing: converging pointers, a window that grows and shrinks, a
 * range halving, a frontier spreading. Each pattern gets a short loop showing
 * its shape on a tiny worked example, with a caption per step saying what just
 * happened.
 *
 * These are per pattern rather than per problem. Ninety Two Pointers problems
 * move their pointers the same way; what changes is the condition, and the
 * condition is what the solution and its notes are for.
 */

export type Tone = "idle" | "live" | "kept" | "gone" | "found";

export interface CellStep {
  kind: "cells";
  /** the values in the row */
  cells: (string | number)[];
  /** pointers sitting under a cell */
  marks?: { at: number; label: string; tone?: Tone }[];
  /** per-cell state, same length as cells */
  tones?: Tone[];
  /** an inclusive span drawn as a band behind the cells */
  band?: [number, number];
  caption: string;
}

export interface NodeStep {
  kind: "nodes";
  nodes: { id: string; x: number; y: number; label: string; tone?: Tone }[];
  edges: [string, string][];
  /** edges drawn with an arrowhead, for directed graphs and linked lists */
  directed?: boolean;
  marks?: { on: string; label: string }[];
  caption: string;
}

export type Step = CellStep | NodeStep;

const row = (...v: (string | number)[]) => v;

/** two pointers ───────────────────────────────────────────────────────────── */
const twoPointers: Step[] = (() => {
  const cells = row(2, 7, 11, 15, 19);
  const at = (l: number, r: number, caption: string, tones?: Tone[]): CellStep => ({
    kind: "cells",
    cells,
    marks: [
      { at: l, label: "left", tone: "live" },
      { at: r, label: "right", tone: "live" },
    ],
    tones,
    caption,
  });
  return [
    at(0, 4, "Target 18. A pointer at each end: 2 + 19 = 21."),
    at(0, 3, "21 is too big. Only moving the right pointer in can lower the sum, so it moves."),
    at(1, 3, "2 + 15 = 17, too small this time — so the left pointer moves in instead."),
    at(1, 2, "7 + 15 = 22, too big again. Right moves in once more."),
    {
      kind: "cells",
      cells,
      marks: [
        { at: 1, label: "left", tone: "found" },
        { at: 2, label: "right", tone: "found" },
      ],
      tones: ["gone", "found", "found", "gone", "gone"],
      caption:
        "7 + 11 = 18. Each step ruled out a whole set of pairs, so one pass was enough — " +
        "and that only works because the array is sorted.",
    },
  ];
})();

/** sliding window ─────────────────────────────────────────────────────────── */
const slidingWindow: Step[] = (() => {
  const cells = row(4, 2, 1, 7, 8, 1, 2, 8);
  const at = (a: number, b: number, caption: string): CellStep => ({
    kind: "cells",
    cells,
    band: [a, b],
    marks: [
      { at: a, label: "start", tone: "live" },
      { at: b, label: "end", tone: "live" },
    ],
    caption,
  });
  return [
    at(0, 0, "Longest run summing to at most 12. The window starts as a single cell."),
    at(0, 2, "Grow from the right while the sum still fits: 4 + 2 + 1 = 7."),
    at(0, 3, "Adding 7 makes 14, which is over the limit."),
    at(2, 3, "So pull the left edge in until it fits again — 1 + 7 = 8."),
    at(2, 4, "Room to grow once more: 1 + 7 + 8 = 16 is over, so this is the edge of it."),
    at(3, 4, "Every element is added once and removed once. One pass, not one pass per start."),
  ];
})();

/** fast & slow pointers ───────────────────────────────────────────────────── */
const fastSlow: Step[] = (() => {
  const pos: Record<string, [number, number]> = {
    a: [10, 50], b: [30, 50], c: [50, 50], d: [70, 34], e: [86, 50], f: [70, 66],
  };
  const nodes = (slow: string, fast: string, tone: Tone = "live") =>
    Object.entries(pos).map(([id, [x, y]]) => ({
      id,
      x,
      y,
      label: id.toUpperCase(),
      tone: id === slow && id === fast ? "found" : id === slow || id === fast ? tone : "idle",
    })) as NodeStep["nodes"];
  const edges: [string, string][] = [["a", "b"], ["b", "c"], ["c", "d"], ["d", "e"], ["e", "f"], ["f", "c"]];
  const step = (slow: string, fast: string, caption: string, tone: Tone = "live"): NodeStep => ({
    kind: "nodes",
    nodes: nodes(slow, fast, tone),
    edges,
    directed: true,
    marks: [
      { on: slow, label: "slow" },
      { on: fast, label: "fast" },
    ],
    caption,
  });
  return [
    step("a", "a", "Both start at the head. The tail loops back to C, but nothing knows that yet."),
    step("b", "c", "Slow takes one step, fast takes two."),
    step("c", "e", "The gap widens while the list is straight."),
    step("d", "c", "Fast has come round the loop and is now behind slow."),
    step("e", "e", "They land on the same node. Two runners on a circular track always meet.", "found"),
  ];
})();

/** binary search ──────────────────────────────────────────────────────────── */
const binarySearch: Step[] = (() => {
  const cells = row(1, 3, 5, 8, 13, 21, 34, 55);
  const step = (lo: number, hi: number, mid: number, caption: string): CellStep => ({
    kind: "cells",
    cells,
    tones: cells.map((_, i) =>
      i < lo || i > hi ? "gone" : i === mid ? "live" : "idle",
    ) as Tone[],
    marks: [
      { at: lo, label: "lo" },
      { at: mid, label: "mid", tone: "live" },
      { at: hi, label: "hi" },
    ],
    caption,
  });
  return [
    step(0, 7, 3, "Looking for 34. Check the middle of the whole range: 8."),
    step(4, 7, 5, "8 is too small, so nothing to its left can be the answer. Half the array is gone."),
    step(6, 7, 6, "21 is still too small. Half of what remains goes too."),
    {
      kind: "cells",
      cells,
      tones: cells.map((_, i) => (i === 6 ? "found" : "gone")) as Tone[],
      marks: [{ at: 6, label: "found", tone: "found" }],
      caption: "34, in three comparisons. Eight items, three halvings — that is what log n means.",
    },
  ];
})();

/** merge intervals ────────────────────────────────────────────────────────── */
const mergeIntervals: Step[] = (() => {
  const cells = row("1–3", "2–6", "8–10", "9–12", "15–18");
  const step = (tones: Tone[], caption: string, band?: [number, number]): CellStep => ({
    kind: "cells",
    cells,
    tones,
    band,
    caption,
  });
  return [
    step(["idle", "idle", "idle", "idle", "idle"], "Sort by start first. Every decision below depends on that order."),
    step(["live", "live", "idle", "idle", "idle"], "1–3 and 2–6 overlap: 2 starts before 3 ends.", [0, 1]),
    step(["kept", "kept", "idle", "idle", "idle"], "So they become one interval, 1–6. Take the further of the two ends."),
    step(["kept", "kept", "live", "live", "idle"], "8–10 and 9–12 overlap the same way → 8–12.", [2, 3]),
    step(["kept", "kept", "kept", "kept", "found"], "15 starts after 12 ends, so 15–18 stands alone. One pass after the sort."),
  ];
})();

/** linked list reversal ───────────────────────────────────────────────────── */
const listReversal: Step[] = (() => {
  const at = (n: number) => [12 + n * 22, 50] as [number, number];
  const ids = ["a", "b", "c", "d"];
  const step = (flipped: number, caption: string): NodeStep => ({
    kind: "nodes",
    nodes: ids.map((id, i) => ({
      id,
      x: at(i)[0],
      y: at(i)[1],
      label: String(i + 1),
      tone: i < flipped ? "kept" : i === flipped ? "live" : "idle",
    })),
    edges: ids.slice(0, -1).map((id, i) =>
      i < flipped ? ([ids[i + 1], id] as [string, string]) : ([id, ids[i + 1]] as [string, string]),
    ),
    directed: true,
    marks: flipped < ids.length ? [{ on: ids[flipped], label: "curr" }] : [],
    caption,
  });
  return [
    step(0, "Four nodes, each pointing at the next. Nothing is copied — only the links change."),
    step(1, "Point the first node's link backwards. Keep hold of the next node first, or the rest is lost."),
    step(2, "Same move again: one link flipped per step."),
    step(3, "Three pointers do the whole job — previous, current, and the one held aside."),
    step(4, "Reversed in place. O(1) extra space, because nothing was ever duplicated."),
  ];
})();

/** binary tree DFS ────────────────────────────────────────────────────────── */
const TREE: Record<string, [number, number]> = {
  a: [50, 16], b: [28, 46], c: [72, 46], d: [16, 78], e: [40, 78], f: [84, 78],
};
const TREE_EDGES: [string, string][] = [["a", "b"], ["a", "c"], ["b", "d"], ["b", "e"], ["c", "f"]];
const treeLabels: Record<string, string> = { a: "1", b: "2", c: "3", d: "4", e: "5", f: "6" };

const treeStep = (live: string[], done: string[], caption: string): NodeStep => ({
  kind: "nodes",
  nodes: Object.entries(TREE).map(([id, [x, y]]) => ({
    id,
    x,
    y,
    label: treeLabels[id],
    tone: live.includes(id) ? "live" : done.includes(id) ? "kept" : "idle",
  })),
  edges: TREE_EDGES,
  caption,
});

const treeDfs: Step[] = [
  treeStep(["a"], [], "Depth-first: go as deep as possible before trying anything sideways."),
  treeStep(["b"], ["a"], "Down the left branch first."),
  treeStep(["d"], ["a", "b"], "Keep going down until there is nowhere left to go."),
  treeStep(["e"], ["a", "b", "d"], "Only then come back up and take the sibling."),
  treeStep(["c"], ["a", "b", "d", "e"], "The whole left subtree is finished before the right is touched."),
  treeStep(["f"], ["a", "b", "d", "e", "c"], "1, 2, 4, 5, 3, 6 — the call stack is doing the remembering."),
];

/** binary tree BFS ────────────────────────────────────────────────────────── */
const treeBfs: Step[] = [
  treeStep(["a"], [], "Breadth-first: finish a whole level before dropping to the next."),
  treeStep(["b", "c"], ["a"], "Level 2, both nodes together. A queue holds them in arrival order."),
  treeStep(["d", "e", "f"], ["a", "b", "c"], "Level 3. Take the queue's length before the loop and you get exact levels."),
  treeStep([], ["a", "b", "c", "d", "e", "f"], "1 · 2,3 · 4,5,6 — this is why BFS finds the shortest path first."),
];

/** graph DFS / BFS ────────────────────────────────────────────────────────── */
const graphFrontier: Step[] = (() => {
  const grid: [number, number][] = [];
  for (let r = 0; r < 3; r++) for (let c = 0; c < 4; c++) grid.push([r, c]);
  const id = (r: number, c: number) => `${r}${c}`;
  const step = (rings: number, caption: string): NodeStep => ({
    kind: "nodes",
    nodes: grid.map(([r, c]) => {
      const d = Math.abs(r - 1) + Math.abs(c - 0);
      return {
        id: id(r, c),
        x: 12 + c * 25,
        y: 22 + r * 28,
        label: String(d),
        tone: d < rings ? "kept" : d === rings ? "live" : "idle",
      };
    }),
    edges: [],
    caption,
  });
  return [
    step(0, "Start from one cell. The number in each cell is how many steps away it is."),
    step(1, "BFS spreads one ring at a time — every neighbour of the start."),
    step(2, "Then every neighbour of those, and so on."),
    step(3, "Because rings arrive in order, the first time a cell is reached is by the shortest route."),
    step(5, "Mark cells as you queue them, not as you visit them, or they get queued twice."),
  ];
})();

/** topological sort ───────────────────────────────────────────────────────── */
const topo: Step[] = (() => {
  const pos: Record<string, [number, number]> = {
    a: [14, 30], b: [14, 72], c: [45, 50], d: [74, 30], e: [74, 72],
  };
  const edges: [string, string][] = [["a", "c"], ["b", "c"], ["c", "d"], ["c", "e"]];
  const step = (indeg: Record<string, number>, taken: string[], ready: string[], caption: string): NodeStep => ({
    kind: "nodes",
    nodes: Object.entries(pos).map(([id, [x, y]]) => ({
      id,
      x,
      y,
      label: taken.includes(id) ? "✓" : String(indeg[id]),
      tone: taken.includes(id) ? "gone" : ready.includes(id) ? "live" : "idle",
    })),
    edges,
    directed: true,
    caption,
  });
  return [
    step({ a: 0, b: 0, c: 2, d: 1, e: 1 }, [], ["a", "b"],
      "Each node shows how many things must come before it. Two are already at zero."),
    step({ a: 0, b: 0, c: 1, d: 1, e: 1 }, ["a"], ["b"],
      "Take one of them and remove it. Everything it pointed at loses a prerequisite."),
    step({ a: 0, b: 0, c: 0, d: 1, e: 1 }, ["a", "b"], ["c"],
      "Now C has nothing left in front of it, so it becomes available."),
    step({ a: 0, b: 0, c: 0, d: 0, e: 0 }, ["a", "b", "c"], ["d", "e"],
      "Removing C frees both D and E at once."),
    step({ a: 0, b: 0, c: 0, d: 0, e: 0 }, ["a", "b", "c", "d", "e"], [],
      "If the queue empties before every node is taken, the graph had a cycle."),
  ];
})();

/** top K ──────────────────────────────────────────────────────────────────── */
const topK: Step[] = (() => {
  const stream = row(5, 1, 9, 3, 7);
  const step = (seen: number, heap: number[], caption: string): CellStep => ({
    kind: "cells",
    cells: stream,
    tones: stream.map((v, i) =>
      i > seen ? "idle" : heap.includes(v as number) ? "kept" : "gone",
    ) as Tone[],
    marks: [{ at: Math.min(seen, stream.length - 1), label: "next", tone: "live" }],
    caption,
  });
  return [
    step(0, [5], "Keep the largest 2. A min-heap of size 2 does it — the smallest kept value sits on top."),
    step(1, [5, 1], "Room for both so far."),
    step(2, [5, 9], "9 arrives. The heap is full, so it beats the smallest kept value and 1 is dropped."),
    step(3, [5, 9], "3 loses to the smallest kept value, so it never enters."),
    step(4, [7, 9], "7 beats 5. Only k items are ever held, so this is O(n log k), not a full sort."),
  ];
})();

/** subsets & backtracking ─────────────────────────────────────────────────── */
const backtracking: Step[] = (() => {
  const pos: Record<string, [number, number]> = {
    root: [50, 14], no: [26, 46], yes: [74, 46],
    nn: [12, 80], ny: [38, 80], yn: [62, 80], yy: [88, 80],
  };
  const edges: [string, string][] = [
    ["root", "no"], ["root", "yes"], ["no", "nn"], ["no", "ny"], ["yes", "yn"], ["yes", "yy"],
  ];
  const labels: Record<string, string> = {
    root: "{}", no: "{}", yes: "{a}", nn: "{}", ny: "{b}", yn: "{a}", yy: "{a,b}",
  };
  const step = (live: string[], done: string[], caption: string): NodeStep => ({
    kind: "nodes",
    nodes: Object.entries(pos).map(([id, [x, y]]) => ({
      id, x, y, label: labels[id],
      tone: live.includes(id) ? "live" : done.includes(id) ? "kept" : "idle",
    })),
    edges,
    directed: true,
    caption,
  });
  return [
    step(["root"], [], "Every element is one decision: leave it out, or put it in."),
    step(["yes"], ["root"], "Take 'a'. Go as deep as the choices go."),
    step(["yy"], ["root", "yes"], "Take 'b' too — {a,b} is one complete answer."),
    step(["yn"], ["root", "yes", "yy"], "Step back up and try the other branch: {a} alone."),
    step(["no"], ["root", "yes", "yy", "yn"], "Undo the choice — that undo *is* the backtracking step."),
    step([], ["root", "yes", "yy", "yn", "no", "nn", "ny"], "Four subsets from two elements. Every leaf is an answer."),
  ];
})();

/** dynamic programming ────────────────────────────────────────────────────── */
const dp: Step[] = (() => {
  const stairs = ["n=0", "n=1", "n=2", "n=3", "n=4", "n=5"];
  const values = [1, 1, 2, 3, 5, 8];
  const step = (filled: number, caption: string): CellStep => ({
    kind: "cells",
    cells: stairs.map((s, i) => (i <= filled ? String(values[i]) : "?")),
    tones: stairs.map((_, i) =>
      i < filled ? "kept" : i === filled ? "live" : "idle",
    ) as Tone[],
    band: filled >= 2 ? [filled - 2, filled] : undefined,
    caption,
  });
  return [
    step(1, "Ways to climb n stairs, taking 1 or 2 at a time. The first two are given."),
    step(2, "Every later answer is the two before it added together — the last step was a 1 or a 2."),
    step(3, "2 + 1 = 3. Each cell is computed once and then only read."),
    step(4, "3 + 2 = 5."),
    step(5, "5 + 3 = 8. The recursion would recompute these thousands of times; the table does not."),
  ];
})();

export const SCENES: Record<string, Step[]> = {
  "two-pointers": twoPointers,
  "sliding-window": slidingWindow,
  "fast-and-slow-pointers": fastSlow,
  "binary-search": binarySearch,
  "merge-intervals": mergeIntervals,
  "linked-list-reversal": listReversal,
  "binary-tree-dfs": treeDfs,
  "binary-tree-bfs": treeBfs,
  "graph-dfs-bfs": graphFrontier,
  "topological-sort": topo,
  "top-k-elements": topK,
  "subsets-backtracking": backtracking,
  "dynamic-programming": dp,
};
