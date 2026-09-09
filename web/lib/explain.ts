/**
 * Short explanations for lines of Python, derived from the line itself.
 *
 * The point of the site is that a student should not have to copy a solution
 * somewhere else and ask what it does. Most solutions in the bank carry few or
 * no comments, so the margin was empty on three problems in four.
 *
 * Every rule here describes *what the line does*, read off its own syntax. None
 * of them assert anything about the problem being solved, because that cannot
 * be derived and guessing it would put confident wrong prose next to correct
 * code. A line that matches nothing gets no note rather than a vague one.
 *
 * A comment the author wrote always wins over anything in this file.
 */

type Rule = { re: RegExp; say: (m: RegExpMatchArray) => string };

const rules: Rule[] = [
  // ── setting up ────────────────────────────────────────────────────────────
  {
    re: /^\s*(\w+)\s*,\s*(\w+)\s*=\s*0\s*,\s*len\((\w+)\)\s*-\s*1\s*$/,
    say: (m) => `${m[1]} starts at the front, ${m[2]} at the back — one pointer at each end`,
  },
  {
    re: /^\s*(\w+)\s*,\s*(\w+)\s*=\s*0\s*,\s*0\s*$/,
    say: (m) => `both ${m[1]} and ${m[2]} start at the front and move the same way`,
  },
  {
    re: /^\s*(\w+)\s*=\s*(\w+)\s*=\s*(\w+)\s*$/,
    say: (m) => `${m[1]} and ${m[2]} both start at ${m[3]}`,
  },
  {
    re: /^\s*(\w+)\s*=\s*\[\s*\]\s*$/,
    say: (m) => `${m[1]} starts empty and gets filled as we go`,
  },
  {
    re: /^\s*(\w+)\s*=\s*set\(\s*\)\s*$/,
    say: (m) => `${m[1]} remembers what we have already seen, so nothing is handled twice`,
  },
  {
    re: /^\s*(\w+)\s*=\s*(?:collections\.)?Counter\((\w+)\)/,
    say: (m) => `count how many of each item ${m[2]} holds`,
  },
  {
    re: /^\s*(\w+)\s*=\s*(?:collections\.)?defaultdict\((\w+)\)/,
    say: (m) => `a map where a missing key starts as an empty ${m[2] === "list" ? "list" : m[2]}`,
  },
  {
    re: /^\s*(\w+)\s*=\s*(?:collections\.)?deque\(/,
    say: (m) => `${m[1]} is a queue — we take from the front and add at the back`,
  },
  {
    re: /^\s*(\w+)\s*=\s*\[\s*(?:0|False|float\("inf"\)|float\('inf'\))\s*\]\s*\*/,
    say: (m) => `${m[1]} holds one slot per subproblem, all starting the same`,
  },
  {
    re: /^\s*(\w+)\s*=\s*\[\s*\[[^\]]*\]\s*(?:for|\*)/,
    say: (m) => `${m[1]} is a grid — one row per state, one column per state`,
  },
  {
    re: /^\s*(\w+)\s*=\s*float\(["']inf["']\)\s*$/,
    say: (m) => `start ${m[1]} at infinity so the first real value always beats it`,
  },
  {
    re: /^\s*(\w+)\s*=\s*float\(["']-inf["']\)\s*$/,
    say: (m) => `start ${m[1]} at negative infinity so any real value beats it`,
  },
  {
    re: /^\s*(\w+)\s*=\s*(?:0|1)\s*$/,
    say: (m) => `${m[1]} starts here and is updated as we scan`,
  },
  { re: /^\s*(\w+)\.sort\(\)/, say: (m) => `sort ${m[1]} first — the scan below relies on order` },
  {
    re: /^\s*(\w+)\.sort\(key\s*=\s*lambda\s*\w+\s*:\s*([^)]+)\)/,
    say: (m) => `sort ${m[1]} by ${m[2].trim()}, which is the order the sweep needs`,
  },
  { re: /^\s*(\w+)\s*=\s*sorted\(/, say: (m) => `work on a sorted copy, leaving the input alone` },

  // ── guards ────────────────────────────────────────────────────────────────
  {
    re: /^\s*if\s+not\s+(\w+)\s*:\s*$/,
    say: (m) => `nothing to do when ${m[1]} is empty`,
  },
  {
    re: /^\s*if\s+not\s+(\w+)\s+or\s+not\s+(\w+)\s*:/,
    say: (m) => `bail out if either ${m[1]} or ${m[2]} is empty`,
  },
  {
    re: /^\s*if\s+len\((\w+)\)\s*(<|<=)\s*(\d+)\s*:/,
    say: (m) => `too small to do any work — handle it directly`,
  },

  // ── walking ───────────────────────────────────────────────────────────────
  {
    re: /^\s*while\s+(\w+)\s*<\s*(\w+)\s*:\s*$/,
    say: (m) => `keep going while ${m[1]} is still left of ${m[2]} — they close the gap together`,
  },
  {
    re: /^\s*while\s+(\w+)\s*<=\s*(\w+)\s*:\s*$/,
    say: (m) => `keep going while the range ${m[1]}..${m[2]} still has something in it`,
  },
  {
    re: /^\s*while\s+(\w+)\s+and\s+\1\.next\s*:/,
    say: (m) => `stop when the fast pointer runs off the end of the list`,
  },
  {
    re: /^\s*while\s+(\w+)\s*:\s*$/,
    say: (m) => `keep going until ${m[1]} runs out`,
  },
  {
    re: /^\s*for\s+(\w+)\s*,\s*(\w+)\s+in\s+enumerate\((\w+)\)\s*:/,
    say: (m) => `walk ${m[3]}, keeping both the position ${m[1]} and the value ${m[2]}`,
  },
  {
    re: /^\s*for\s+(\w+)\s+in\s+range\(len\((\w+)\)\)\s*:/,
    say: (m) => `walk every position of ${m[2]}`,
  },
  {
    re: /^\s*for\s+(\w+)\s+in\s+range\(([^,)]+),\s*([^,)]+),\s*-1\)\s*:/,
    say: () => `walk backwards — later states are settled before earlier ones need them`,
  },
  {
    re: /^\s*for\s+(\w+)\s+in\s+range\(/,
    say: (m) => `step ${m[1]} through the range below`,
  },
  {
    re: /^\s*for\s+(\w+)\s+in\s+(\w+)\s*:/,
    say: (m) => `take each ${m[1]} of ${m[2]} in turn`,
  },

  // ── moving pointers ───────────────────────────────────────────────────────
  { re: /^\s*(\w+)\s*\+=\s*1\s*$/, say: (m) => `move ${m[1]} one step forward` },
  { re: /^\s*(\w+)\s*-=\s*1\s*$/, say: (m) => `move ${m[1]} one step back` },
  {
    re: /^\s*(\w+)\s*=\s*\1\.next\s*$/,
    say: (m) => `step ${m[1]} to the next node`,
  },
  {
    re: /^\s*(\w+)\s*=\s*\1\.next\.next\s*$/,
    say: (m) => `step ${m[1]} two nodes at once — twice the speed of the slow pointer`,
  },
  {
    re: /^\s*(\w+)\s*,\s*(\w+)\s*=\s*\2\s*,\s*\1\s*$/,
    say: (m) => `swap ${m[1]} and ${m[2]}`,
  },
  {
    re: /^\s*(\w+)\[(\w+)\]\s*,\s*\1\[(\w+)\]\s*=\s*\1\[\3\]\s*,\s*\1\[\2\]/,
    say: (m) => `swap the two elements in place — no extra array needed`,
  },

  // ── binary search ─────────────────────────────────────────────────────────
  {
    re: /^\s*(\w+)\s*=\s*\((\w+)\s*\+\s*(\w+)\)\s*\/\/\s*2\s*$/,
    say: (m) => `${m[1]} is the middle of the range still in play`,
  },
  {
    re: /^\s*(\w+)\s*=\s*(\w+)\s*\+\s*\((\w+)\s*-\s*\2\)\s*\/\/\s*2/,
    say: () => `the midpoint, written so the sum can never overflow`,
  },
  {
    re: /^\s*(\w+)\s*=\s*mid\s*\+\s*1\s*$/,
    say: (m) => `the answer is to the right — throw away everything up to mid`,
  },
  {
    re: /^\s*(\w+)\s*=\s*mid\s*-\s*1\s*$/,
    say: (m) => `the answer is to the left — throw away everything from mid on`,
  },
  { re: /^\s*(\w+)\s*=\s*mid\s*$/, say: () => `mid might still be the answer, so keep it` },

  // ── stacks, queues, heaps ─────────────────────────────────────────────────
  {
    re: /^\s*heapq\.heappush\((\w+),\s*(.+)\)\s*$/,
    say: (m) => `push onto the heap, which keeps the smallest at the front`,
  },
  {
    re: /^\s*heapq\.heappop\((\w+)\)/,
    say: () => `take the smallest item off the heap`,
  },
  { re: /^\s*heapq\.heapify\((\w+)\)/, say: (m) => `turn ${m[1]} into a heap in place` },
  {
    re: /^\s*(\w+)\.append\((\w+)\)\s*$/,
    say: (m) => `remember ${m[2]} on ${m[1]} for later`,
  },
  { re: /^\s*(\w+)\.append\(/, say: (m) => `record this on ${m[1]}` },
  { re: /^\s*(\w+)\.pop\(\)\s*$/, say: (m) => `take the most recent item back off ${m[1]}` },
  { re: /^\s*(\w+)\.popleft\(\)/, say: () => `take the oldest item off the front of the queue` },
  { re: /^\s*(\w+)\s*=\s*(\w+)\.pop\(\)/, say: (m) => `take the top of ${m[2]} off into ${m[1]}` },

  // ── graphs and trees ──────────────────────────────────────────────────────
  {
    re: /^\s*(\w+)\[(\w+)\]\.append\((\w+)\)\s*$/,
    say: (m) => `record the edge ${m[2]} → ${m[3]}`,
  },
  {
    re: /^\s*(?:visited|seen)\.add\((\w+)\)/,
    say: (m) => `mark ${m[1]} as visited so we never come back to it`,
  },
  {
    re: /^\s*(\w+)\.add\((.+)\)\s*$/,
    say: (m) => `remember ${m[2].trim()} in ${m[1]}`,
  },
  {
    re: /^\s*if\s+(\w+)\s+in\s+(?:visited|seen)\s*:/,
    say: (m) => `already handled ${m[1]} — skip it`,
  },
  {
    re: /^\s*indegree\[(\w+)\]\s*\+=\s*1/,
    say: (m) => `one more thing has to come before ${m[1]}`,
  },
  {
    re: /^\s*indegree\[(\w+)\]\s*-=\s*1/,
    say: (m) => `one fewer prerequisite left for ${m[1]}`,
  },
  {
    re: /^\s*(?:dfs|helper|backtrack|walk)\(/,
    say: () => `recurse — the same problem, one step smaller`,
  },
  {
    re: /^\s*(\w+)\.pop\(\)\s*#?.*$|^\s*path\.pop\(\)/,
    say: () => `undo the last choice and try the next one — this is the backtracking step`,
  },

  // ── answers ───────────────────────────────────────────────────────────────
  {
    re: /^\s*(\w+)\s*=\s*max\(\1\s*,\s*(.+)\)\s*$/,
    say: (m) => `keep ${m[1]} if it is bigger than what we had`,
  },
  {
    re: /^\s*(\w+)\s*=\s*min\(\1\s*,\s*(.+)\)\s*$/,
    say: (m) => `keep the smaller of the two`,
  },
  { re: /^\s*(\w+)\s*\+=\s*(.+)$/, say: (m) => `add ${m[2].trim()} to the running ${m[1]}` },
  { re: /^\s*return\s+(True|False)\s*$/, say: (m) => `answer: ${m[1].toLowerCase()}` },
  { re: /^\s*return\s+-1\s*$/, say: () => `nothing matched — the agreed "not found" answer` },
  { re: /^\s*return\s*$/, say: () => `stop here and go back up` },
  { re: /^\s*return\s+(.+)$/, say: (m) => `hand back ${m[1].trim()}` },

  // -- the shapes the bank uses over and over -------------------------------
  {
    re: /^\s*(\w+)\s*=\s*(\w+)\.popleft\(\)/,
    say: (m) => `take the next ${m[1]} off the front of the queue`,
  },
  {
    re: /^\s*(\w+)\s*=\s*(\w+)\.popleft\(\)\s*if/,
    say: () => `take from the front of the queue`,
  },
  {
    re: /^\s*self\.(\w+)\s*=\s*(\w+)\s*(?:;|$)/,
    say: (m) => `each node carries its own ${m[1]}`,
  },
  {
    re: /^\s*(\w+)\s*,\s*(\w+)\s*=\s*(\w+)\.popleft\(\)/,
    say: () => `take the next cell off the front of the queue`,
  },
  {
    re: /^\s*(\w+)\s*=\s*(\w+)\.next\s*$/,
    say: () => `hold on to the next node before the links get rewritten`,
  },
  {
    re: /^\s*(\w+)\s*=\s*(\w+)\.(left|right)\s*$/,
    say: (m) => `walk down to the ${m[3]} child`,
  },
  {
    re: /^\s*if\s+not\s+(\w+)\s*:\s*return\s*(.*)$/,
    say: (m) =>
      m[2].trim()
        ? `an empty ${m[1]} gives back ${m[2].trim()}, and nothing else happens`
        : `an empty ${m[1]} has nothing to do -- go straight back`,
  },
  {
    re: /^\s*if\s+len\((\w+)\)\s*>\s*(\w+)\s*:/,
    say: (m) => `${m[1]} has grown past ${m[2]} -- drop the one we no longer want`,
  },
  {
    re: /^\s*for\s+(\w+)\s*,\s*(\w+)\s+in\s+(?:dirs|directions)\s*:/,
    say: () => `try each of the four directions out of this cell`,
  },
  {
    re: /^\s*for\s+(\w+)\s*,\s*(\w+)\s+in\s+\[\(/,
    say: () => `try each direction in turn`,
  },
  {
    re: /^\s*if\s+indegree\[(\w+)\]\s*==\s*0\s*:\s*\w+\.append/,
    say: (m) => `nothing has to come before ${m[1]} any more, so it is ready to go`,
  },
  {
    re: /^\s*(\w+)\[0\]\s*=\s*(.+)$/,
    say: (m) => `the base case that the rest of ${m[1]} is built on`,
  },
  {
    re: /^\s*@(?:lru_cache|cache|functools\.lru_cache)/,
    say: () => `cache every call, so a repeated subproblem is answered instantly`,
  },
  {
    re: /^\s*if\s+(\w+)\s*==\s*(\w+)\s*:\s*return/,
    say: (m) => `reached ${m[2]} -- that is the answer for this branch`,
  },
  {
    re: /^\s*(\w+)\s*=\s*(\w+)\s*\+\s*(\w+)\s*$/,
    say: (m) => `${m[1]} is ${m[2]} and ${m[3]} added together`,
  },
  {
    re: /^\s*(\w+)\s*=\s*(\w+)\s*$/,
    say: (m) => `step ${m[1]} along to ${m[2]}`,
  },
  {
    re: /^\s*self\.\w+\s*=\s*\w+\s*;\s*self\./,
    say: () => `the fields every node in this structure carries`,
  },
  {
    re: /^\s*for\s+(\w+)\s+in\s+(?:graph|adj)\[(\w+)\]\s*:/,
    say: (m) => `visit every neighbour of ${m[2]} in turn`,
  },
  {
    re: /^\s*for\s+(\w+)\s*,\s*(\w+)\s+in\s+(\w*edges\w*)\s*:/,
    say: (m) => `each edge, running from ${m[1]} to ${m[2]}`,
  },
  {
    re: /^\s*(\w+)\s*=\s*ListNode\(0(?:,\s*\w+)?\)\s*$/,
    say: () => `a throwaway node in front of the list, so the first node needs no special case`,
  },
  {
    re: /^\s*(\w+)\s*=\s*(head|dummy|root)\s*$/,
    say: (m) => `${m[1]} is the walker — it moves while ${m[2]} stays put`,
  },
  {
    re: /^\s*(\w+)\.next\s*=\s*(\w+)\s*$/,
    say: (m) => `relink: ${m[1]} now points at ${m[2]}`,
  },
  {
    re: /^\s*(\w+)\.next\s*=\s*ListNode\(/,
    say: () => `hang a new node off the end`,
  },
  {
    re: /^\s*from\s+(\S+)\s+import\s+(.+)$/,
    say: (m) => `bring in ${m[2].trim()} from ${m[1]}`,
  },
  { re: /^\s*import\s+(\w+)\s*$/, say: (m) => `bring in ${m[1]}` },
  { re: /^\s*break\s*$/, say: () => `stop the loop here — nothing further can help` },
  { re: /^\s*continue\s*$/, say: () => `skip straight to the next round` },
  {
    re: /^\s*(\w+)\s*,\s*(\w+)\s*=\s*(\w+)\s*\+\s*(\w+)\s*,\s*(\w+)\s*\+\s*(\w+)\s*$/,
    say: () => `step to the neighbouring cell in this direction`,
  },
  {
    re: /^\s*(\w+)\s*=\s*len\((\w+)\)\s*$/,
    say: (m) => `${m[1]} is how many items ${m[2]} holds`,
  },
  {
    re: /^\s*(\w+)\s*,\s*(\w+)\s*=\s*len\((\w+)\)\s*,\s*len\(/,
    say: () => `the two dimensions of the grid`,
  },
  {
    re: /^\s*MOD\s*=\s*10\s*\*\*\s*9\s*\+\s*7/,
    say: () => `answers are reported modulo this, so they stay small enough to hold`,
  },
  {
    re: /^\s*if\s+(\w+)\.(left|right)\s*:\s*\w+\.append\(\1\.\2\)/,
    say: (m) => `queue the ${m[2]} child if there is one — that is the next level down`,
  },
  {
    re: /^\s*(\w+)\s*=\s*\[\s*\[\s*(?:0|False)\s*\]/,
    say: (m) => `${m[1]} is a grid of states, all starting the same`,
  },
  {
    re: /^\s*(?:dirs|directions)\s*=\s*\[/,
    say: () => `the four steps from a cell: right, left, down, up`,
  },
  {
    re: /^\s*if\s+0\s*<=\s*(\w+)\s*<\s*(\w+)\s+and\s+0\s*<=/,
    say: () => `only step to a cell that is actually inside the grid`,
  },
  {
    re: /^\s*(\w+)\s*=\s*\{\s*\}\s*$/,
    say: (m) => `${m[1]} caches answers we have already worked out`,
  },
  {
    re: /^\s*if\s+(\w+)\s+in\s+(memo|cache|seen|dp)\s*:/,
    say: (m) => `already solved for ${m[1]} — reuse it rather than redo it`,
  },
  {
    re: /^\s*(memo|cache)\[(\w+)\]\s*=\s*(.+)$/,
    say: (m) => `remember the answer for ${m[2]} so it is never recomputed`,
  },
  {
    re: /^\s*(\w+)\s*=\s*(\w+)\s*%\s*(\w+)/,
    say: () => `wrap around with a remainder`,
  },
  {
    re: /^\s*(\w+)\[(\w+)\]\s*=\s*True\s*$/,
    say: (m) => `mark ${m[2]} as reached`,
  },
  {
    re: /^\s*(\w+)\s*=\s*\w+\[(\w+)\s*-\s*1\]\s*\+/,
    say: () => `build this state out of the one before it`,
  },
  {
    re: /^\s*(\w+)\s*=\s*(\w+)\[(\w+)\]\s*$/,
    say: (m) => `read ${m[2]} at ${m[3]}`,
  },

  // ── definitions ───────────────────────────────────────────────────────────
  {
    re: /^\s*def\s+(\w+)\(self,?\s*([^)]*)\)/,
    say: (m) => (m[2].trim() ? `method: takes ${m[2].trim()}` : `method: takes nothing`),
  },
  {
    re: /^\s*def\s+(\w+)\(([^)]*)\)/,
    say: (m) => (m[2].trim() ? `the solution — it takes ${m[2].trim()}` : `the solution`),
  },
  { re: /^\s*class\s+(\w+)/, say: (m) => `${m[1]}: the shape of one node` },
];

/**
 * A one-line explanation, or null when nothing is recognised.
 *
 * Only the first matching rule fires, and the table is ordered specific to
 * general, so `right = mid - 1` is explained as a binary-search step rather
 * than as an assignment.
 */
export function explainLine(line: string): string | null {
  const code = line.split("#")[0].trimEnd();
  if (!code.trim()) return null;
  for (const rule of rules) {
    const m = code.match(rule.re);
    if (m) return rule.say(m);
  }
  return null;
}

/**
 * Notes for a whole solution: the author's comments where they exist, a
 * derived explanation where they do not.
 */
export function explainSolution(
  solution: string,
  authored: Record<string, string>,
): Record<number, { text: string; derived: boolean }> {
  const out: Record<number, { text: string; derived: boolean }> = {};
  solution.split("\n").forEach((line, i) => {
    const own = authored[String(i)];
    if (own) {
      out[i] = { text: own, derived: false };
      return;
    }
    const derived = explainLine(line);
    if (derived) out[i] = { text: derived, derived: true };
  });
  return out;
}
