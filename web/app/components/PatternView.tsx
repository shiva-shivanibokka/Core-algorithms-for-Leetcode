"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import type { Difficulty, Pattern, Problem } from "@/lib/data";
import Visual, { hasVisual } from "@/app/components/Visual";
import { explainSolution } from "@/lib/explain";
import { formatProse, tokenize } from "@/lib/format";

const TIERS: Difficulty[] = ["Easy", "Medium", "Hard"];

/** A line carrying a margin note gets longer, because there is more to read. */
const NOTE_MS = 620;
/** No solution should take longer than this to arrive, however long it is. */
const BUDGET_MS = 2600;
const SLOWEST_MS = 190;
const FASTEST_MS = 80;

/**
 * Pace the reveal to the length of the solution. A fixed delay per line reads
 * well for a twelve-line two-pointer and turns a forty-line DP into a wait, so
 * long solutions arrive faster per line and every one lands inside the budget.
 */
function paceFor(lineCount: number) {
  return Math.min(SLOWEST_MS, Math.max(FASTEST_MS, BUDGET_MS / Math.max(lineCount, 1)));
}

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
        <Link href="/" className="back-link">
          <span className="arrow" aria-hidden="true">&larr;</span>
          All patterns
        </Link>
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

      {pattern.about.sections.length > 0 && (
        <details className="about">
          <summary>
            <span className="caretmark" aria-hidden="true">&#9654;</span>
            How this pattern works
            <span className="hint">
              {pattern.about.sections.map((x) => x.heading).slice(0, 3).join(" · ")}
              {pattern.about.sections.length > 3 ? " …" : ""}
            </span>
          </summary>
          <div className="about-body">
            {pattern.about.sections.map((section) => (
              <section key={section.heading}>
                <h3>{section.heading}</h3>
                <div
                  className="prose"
                  dangerouslySetInnerHTML={{ __html: formatProse(section.body) }}
                />
              </section>
            ))}
          </div>
        </details>
      )}

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
  // The author's comments where they exist, an explanation read off the line
  // where they do not. Roughly two thirds of lines end up with something.
  const explained = useMemo(
    () => explainSolution(problem.solution, notes),
    [problem.solution, notes],
  );
  const noteCount = Object.keys(explained).length;
  const authoredCount = Object.values(explained).filter((n) => !n.derived).length;

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
    const pace = paceFor(lines.length);
    let i = 0;
    const step = () => {
      i += 1;
      setWritten(i);
      if (i >= lines.length) return;
      // Most lines carry a note now, so a note is no longer the exception
      // worth pausing on. Only the author's own comments get the longer beat.
      timer.current = setTimeout(step, explained[i]?.derived === false ? NOTE_MS : pace);
    };
    timer.current = setTimeout(step, 260);

    // A hidden tab throttles timers to about one a second, so someone who
    // switches away mid-reveal comes back to a solution still crawling into
    // place. Finish it instead: they left, the animation has no audience.
    const onHide = () => {
      if (document.hidden) {
        clearTimeout(timer.current);
        setWritten(lines.length);
      }
    };
    document.addEventListener("visibilitychange", onHide);
    return () => {
      clearTimeout(timer.current);
      document.removeEventListener("visibilitychange", onHide);
    };
  }, [problem.id, lines.length, explained]);

  const done = written >= lines.length;

  return (
    <div className="shell problem">
      <div>
        <button
          className="back-link"
          onClick={() => {
            location.hash = "";
          }}
        >
          <span className="arrow" aria-hidden="true">&larr;</span>
          All {pattern.name} problems
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

      <div className="thinkrow">
        {problem.approach && (
          <div className="think">
            <span className="label">The thinking</span>
            <div
              className="body"
              dangerouslySetInnerHTML={{ __html: formatProse(problem.approach) }}
            />
            {(problem.time || problem.space) && (
              <div className="target">
                <span className="lbl">Target</span>
                {problem.time && (
                  <span className="pair">
                    <span className="k">time</span>
                    <span className="v">{problem.time}</span>
                  </span>
                )}
                {problem.space && (
                  <span className="pair">
                    <span className="k">space</span>
                    <span className="v">{problem.space}</span>
                  </span>
                )}
              </div>
            )}
          </div>
        )}
        {hasVisual(pattern.slug) && (
          <div>
            <p className="kicker" style={{ marginBottom: "10px" }}>
              How {pattern.name} moves
            </p>
            <Visual slug={pattern.slug} />
          </div>
        )}
      </div>

      <div className="codegrid">
        <div className="codehead">
          <span className="lbl">The solution, line by line</span>
          {!done && (
            <button className="skip" onClick={settle}>
              Show it all
            </button>
          )}
        </div>
        {/* One grid row per line, so an explanation sits level with the line it
            explains rather than in a list further down the page. */}
        <div className="crows" onClick={settle}>
          {lines.map((tokens, i) => {
            const writing = i === written - 1 && !done;
            const note = explained[i];
            return (
              <div
                key={i}
                className={`crow${i >= written ? " pending" : ""}${writing ? " writing" : ""}`}
              >
                <span className="num" aria-hidden="true">
                  {i + 1}
                </span>
                <code className="ln">
                  {tokens.length === 0 ? " " : tokens.map((t, j) => (
                    <span key={j} className={t.cls}>
                      {t.text}
                    </span>
                  ))}
                  {writing && <span className="caret on" aria-hidden="true" />}
                </code>
                {note && (
                  <span className={`nt${note.derived ? "" : " authored"}`}>{note.text}</span>
                )}
              </div>
            );
          })}
        </div>
        <p className="codefoot">
          {authoredCount > 0 && (
            <>
              <span className="dot authored" aria-hidden="true" /> the author&rsquo;s own
              comments{" "}
            </>
          )}
          <span className="dot" aria-hidden="true" /> the rest read off the code itself.{" "}
          {noteCount} of {lines.length} lines explained.
        </p>
      </div>

      {problem.leetcodeUrl && (
        <div className="actions">
          <a className="leetcode" href={problem.leetcodeUrl} target="_blank" rel="noreferrer">
            Solve it on LeetCode
            <span className="out" aria-hidden="true">&#8599;</span>
          </a>
          <span className="aside">
            Opens LeetCode filtered to problem {problem.leetcode}, so you can write your
            own attempt against the real judge.
          </span>
        </div>
      )}

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
