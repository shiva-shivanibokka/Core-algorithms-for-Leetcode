import { readFile } from "node:fs/promises";
import path from "node:path";

/** Shapes written by build_site_data.py at the repo root. */
export type Difficulty = "Easy" | "Medium" | "Hard";

export interface Problem {
  id: string;
  n: number;
  title: string;
  leetcode: number | null;
  difficulty: Difficulty;
  rung: number | null;
  statement: string;
  approach: string;
  time: string | null;
  space: string | null;
  solution: string;
  /** line index within `solution` -> the comment that explains that line */
  notes: Record<string, string>;
  tests: string;
  /** function names in this cell that stress_test.py checks against a reference */
  verified: string[];
  /** LeetCode's own page for this problem, searched by number */
  leetcodeUrl: string | null;
  /** a recording of this solution running on one of its own test cases */
  trace: Trace | null;
}

/**
 * What `trace_solutions.py` recorded: the sequences the solution walks, and a
 * step per executed line saying where each of its pointers was sitting.
 */
export interface Trace {
  call: string;
  rows: { name: string; kind: "text" | "numbers"; values: (string | number)[]; movers: string[] }[];
  steps: { l: number; m: Record<string, number> }[];
}

/** The explainer a notebook opens with, split into its sections. */
export interface About {
  lead: string;
  sections: { heading: string; body: string }[];
}

export interface Pattern {
  id: string;
  slug: string;
  name: string;
  /** the parenthetical from the notebook heading, e.g. "Floyd's Cycle Detection" */
  note: string | null;
  about: About;
  notebook: string;
  problems: Problem[];
}

export interface IndexEntry {
  id: string;
  slug: string;
  name: string;
  note: string | null;
  notebook: string;
  counts: Record<Difficulty, number>;
  verified: number;
}

export interface Index {
  totals: { patterns: number; problems: number; verified: number };
  patterns: IndexEntry[];
}

const DATA = path.join(process.cwd(), "public", "data");

/**
 * Read at build time, not at request time: `output: "export"` means every page
 * is rendered once, here, and shipped as HTML. The JSON in public/ is the same
 * file the client would fetch, so the two can never disagree.
 */
async function read<T>(name: string): Promise<T> {
  return JSON.parse(await readFile(path.join(DATA, name), "utf8")) as T;
}

export const loadIndex = () => read<Index>("index.json");
export const loadPattern = (slug: string) => read<Pattern>(`${slug}.json`);

export const REPO = "https://github.com/shiva-shivanibokka/Core-algorithms-for-Leetcode";

export const TIERS: Difficulty[] = ["Easy", "Medium", "Hard"];
