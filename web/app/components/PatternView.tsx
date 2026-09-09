"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import type { Difficulty, Pattern, Problem } from "@/lib/data";
import { formatProse, tokenize } from "@/lib/format";

const TIERS: Difficulty[] = ["Easy", "Medium", "Hard"];

/** How long a line stays alone on screen before the next one arrives. */
const LINE_MS = 190;
/** A line carrying a margin note gets longer, because there is more to read. */
const NOTE_MS = 620;

export default function PatternView({ pattern }: { pattern: Pattern }) {
  const [tier, setTier] = useState<Difficulty | null>(null);
  const [refOnly, setRefOnly] = useState(false);
  const [query, setQuery] = useState("");
  const [openId, setOpenId] = useState<string | null>(null);

  // The open problem lives in the URL, so a solution can be linked to and the
  // browser's back button returns to the list rather than leaving the pattern.
  useEffect(() => {
    const sync = () => setOpenId(decodeURIComponent(location.hash.slice(1)) || null);
    sync();
    addEventListener("hashchange", sync);
    return () => removeEventListener("hashchange", sync);
  }, []);

  const shown = useMemo(() => {
    const q = query.trim().toLowerCase();
    return pattern.problems.filter((p) => {
      if (tier && p.difficulty !== tier) return false;
      if (refOnly && p.verified.length === 0) return false;
      if (!q) return true;
      return (
        p.title.toLowerCase().includes(q) ||
        String(p.leetcode ?? "").includes(q) ||
        p.solution.toLowerCase().includes(q)
      );
    });
  }, [pattern.problems, tier, refOnly, query]);

  const open = openId ? pattern.problems.find((p) => p.id === openId) : undefined;

  if (open) {
    return <ProblemView problem={open} pattern={pattern} />;
  }

  return (
    <div className="shell">
      <p className="crumbs">
        <Link href="/">&larr; All patterns</Link>
      </p>

      <header className="pattern-head">
        <p className="kicker">{pattern.id} · pattern</p>
        <h1 className="gradient">{pattern.name}</h1>
        <p className="sub">
          {pattern.note && <>{pattern.note} &middot; </>}
          {pattern.problems.length} problems ·{" "}
          {TIERS.map((t) => `${pattern.problems.filter((p) => p.difficulty === t).length} ${t.toLowerCase()}`).join(" · ")}{" "}
          · worked in <span className="mono">{pattern.notebook}</span>
        </p>
      </header>

      <div className="controls">
        <button className="chip" aria-pressed={tier === null} onClick={() => setTier(null)}>
          All
        </button>
        {TIERS.map((t) => (
          <button
            key={t}
            className={`chip ${t.toLowerCase()}`}
            aria-pressed={tier === t}
            onClick={() => setTier(tier === t ? null : t)}
          >
            {t}
          </button>
        ))}
        <button
          className="chip ref"
          aria-pressed={refOnly}
          onClick={() => setRefOnly(!refOnly)}
          title="Only the solutions also checked against an independent brute-force reference"
        >
          With a reference
        </button>
        <input
          className="search"
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search title, LeetCode number, or code…"
          aria-label="Search problems"
        />
      </div>

      <div className="rows">
        {shown.map((p) => (
          <button key={p.id} className="prow" onClick={() => { location.hash = p.id; }}>
            <span className={`tier ${p.difficulty.toLowerCase()}`}>
              {p.difficulty[0]}
              {p.rung ?? ""}
            </span>
            <span className="lc mono">{p.leetcode ? `LC ${p.leetcode}` : "—"}</span>
            <span className="title">{p.title}</span>
            <span className="right">
              {p.time && (
                <span className="cx mono" title={p.time}>
                  {p.time}
                </span>
              )}
              {p.verified.length > 0 && <span className="ref-tag">REF</span>}
            </span>
          </button>
        ))}
        {shown.length === 0 && (
          <p className="empty">
            Nothing here matches. {refOnly && "Try turning off “With a reference” — "}
            {refOnly ? "only " : ""}
            {pattern.problems.filter((p) => p.verified.length > 0).length} of this
            pattern&rsquo;s {pattern.problems.length} problems have one.
          </p>
        )}
      </div>
    </div>
  );
}

function ProblemView({ problem, pattern }: { problem: Problem; pattern: Pattern }) {
  const lines = useMemo(() => tokenize(problem.solution), [problem.solution]);
  const notes = problem.notes;
  const noteIndices = useMemo(
    () => Object.keys(notes).map(Number).sort((a, b) => a - b),
    [notes],
  );

  const reduced = useRef(false);
  const [written, setWritten] = useState(0); // how many lines have arrived
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const settle = useCallback(() => {
    clearTimeout(timer.current);
    setWritten(lines.length);
  }, [lines.length]);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" as ScrollBehavior });
    reduced.current = matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced.current) {
      setWritten(lines.length);
      return;
    }
    setWritten(0);
    let i = 0;
    const step = () => {
      i += 1;
      setWritten(i);
      if (i >= lines.length) return;
      timer.current = setTimeout(step, notes[String(i)] ? NOTE_MS : LINE_MS);
    };
    timer.current = setTimeout(step, 260);
    return () => clearTimeout(timer.current);
  }, [problem.id, lines.length, notes]);

  const done = written >= lines.length;

  return (
    <div className="shell problem">
      <div>
        <button className="back" onClick={() => { location.hash = ""; }}>
          &larr; {pattern.name}
        </button>
        <p className="kicker" style={{ marginTop: "14px" }}>
          {problem.difficulty}
          {problem.rung ? ` ${problem.rung}` : ""}
          {problem.leetcode ? ` · LeetCode ${problem.leetcode}` : ""}
        </p>
        <h1 className="gradient">{problem.title}</h1>
        {problem.statement && (
          // formatProse emits paragraphs, so this cannot be a <p>
          <div
            className="statement"
            dangerouslySetInnerHTML={{ __html: formatProse(problem.statement) }}
          />
        )}
      </div>

      {problem.approach && (
        <div className="think">
          <span className="label">The thinking</span>
          <div
            className="body"
            dangerouslySetInnerHTML={{ __html: formatProse(problem.approach) }}
          />
          {(problem.time || problem.space) && (
            <p className="cost">
              {problem.time && `Time ${problem.time}`}
              {problem.time && problem.space && "  ·  "}
              {problem.space && `Space ${problem.space}`}
            </p>
          )}
        </div>
      )}

      <div className="codewrap">
        <div className="codeblock">
          {!done && (
            <button className="skip" onClick={settle}>
              Show it all
            </button>
          )}
          <pre onClick={settle}>
            <code>
              {lines.map((tokens, i) => (
                <span
                  key={i}
                  className={`line${i >= written ? " pending" : ""}${
                    i === written - 1 && !done ? " writing" : ""
                  }`}
                >
                  {tokens.length === 0 ? " " : tokens.map((t, j) => (
                    <span key={j} className={t.cls}>
                      {t.text}
                    </span>
                  ))}
                </span>
              ))}
              <span className={`caret${done ? "" : " on"}`} aria-hidden="true" />
            </code>
          </pre>
        </div>

        <div className="gutter">
          {noteIndices.length === 0 ? (
            <p className="none">No inline notes on this one — the code carries it.</p>
          ) : (
            noteIndices.map((i) => (
              <p
                key={i}
                className={`note${i >= written ? " pending" : ""}`}
                style={{ "--line": i } as React.CSSProperties}
              >
                {notes[String(i)]}
              </p>
            ))
          )}
        </div>
      </div>

      <div className="proof">
        <span className="label">Proved against</span>
        <pre>
          <code>{problem.tests}</code>
        </pre>
        {problem.verified.length > 0 ? (
          <span className="badge">
            ✓ {problem.verified.join(", ")} also checked against a brute-force
            reference on 200 random inputs
          </span>
        ) : (
          <span className="badge plain">
            These cases only — no independent reference for this one yet
          </span>
        )}
      </div>
    </div>
  );
}
