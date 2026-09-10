"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Trace as Recording } from "@/lib/data";

const STEP_MS = 900;

/**
 * Replay of this solution running on one of its own test cases.
 *
 * Nothing here is drawn from a description of the pattern: the row is the
 * input the test actually passed, the markers are where the solution's own
 * pointers were sitting, and the step reports which line was executing. The
 * line is handed back up so the code below can light up in time with it, which
 * is the whole point — you watch the pointer move and see which line moved it.
 */
export default function Trace({
  trace,
  onLine,
}: {
  trace: Recording;
  onLine: (line: number | null) => void;
}) {
  const [i, setI] = useState(0);
  const [playing, setPlaying] = useState(false);
  const timer = useRef<ReturnType<typeof setInterval> | undefined>(undefined);
  const last = Math.max(0, trace.steps.length - 1);

  useEffect(() => {
    setI(0);
    setPlaying(false);
  }, [trace]);

  useEffect(() => {
    onLine(trace.steps[i]?.l ?? null);
  }, [i, trace, onLine]);

  useEffect(() => () => onLine(null), [onLine]);

  useEffect(() => {
    if (!playing) return;
    // A hidden tab throttles timers to about one a second, which would leave
    // someone returning to the page halfway through a step.
    const onHide = () => {
      if (document.hidden) setPlaying(false);
    };
    document.addEventListener("visibilitychange", onHide);
    timer.current = setInterval(() => {
      setI((n) => {
        if (n >= last) {
          setPlaying(false);
          return n;
        }
        return n + 1;
      });
    }, STEP_MS);
    return () => {
      clearInterval(timer.current);
      document.removeEventListener("visibilitychange", onHide);
    };
  }, [playing, last]);

  const go = useCallback(
    (d: number) => {
      setPlaying(false);
      setI((n) => Math.min(last, Math.max(0, n + d)));
    },
    [last],
  );

  const step = trace.steps[i];

  // A changing row is replayed by applying every step's writes up to here.
  // Cheaper than storing a full snapshot per step, and it makes "what changed
  // on this step" fall out for free.
  const { state, justWritten } = useMemo(() => {
    const current: Record<string, (string | number)[]> = {};
    for (const row of trace.rows) {
      if (row.kind === "state") current[row.name] = [...row.values];
    }
    let written: Record<string, Set<number>> = {};
    for (let n = 0; n <= i && n < trace.steps.length; n += 1) {
      written = {};
      for (const [name, cells] of Object.entries(trace.steps[n].d ?? {})) {
        if (!current[name]) continue;
        written[name] = new Set();
        for (const [idx, value] of Object.entries(cells)) {
          current[name][Number(idx)] = value;
          written[name].add(Number(idx));
        }
      }
    }
    return { state: current, justWritten: written };
  }, [trace, i]);

  return (
    <div className="trace">
      <div className="trace-head">
        <span className="lbl">Watch it run</span>
        <code className="trace-call">{trace.call}</code>
      </div>

      <div className="trace-rows">
        {trace.rows.map((row) => (
          <div key={row.name} className="trace-row">
            <span className="rowname mono">
              {row.name}
              {row.kind === "state" && <em>changes</em>}
            </span>
            <div
              className={`cells ${row.kind}`}
              style={
                {
                  "--n": row.values.length,
                  // the labels stack under the row, so the box has to be told
                  // how many tiers to leave space for
                  "--tiers": row.movers.length,
                } as React.CSSProperties
              }
            >
              {(row.kind === "state" ? state[row.name] ?? row.values : row.values).map(
                (v, n) => {
                  const pointed = row.movers.some((m) => step?.m[m] === n);
                  const wrote = justWritten[row.name]?.has(n);
                  return (
                    <span
                      key={n}
                      className={`cell${pointed ? " live" : ""}${wrote ? " wrote" : ""}`}
                    >
                      {row.kind === "text" && v === " " ? "␣" : String(v)}
                    </span>
                  );
                },
              )}
              {row.movers.map((m, n) => {
                const at = step?.m[m];
                // One slot past either end is meaningful and drawn: `right =
                // len(nums)` is an exclusive bound, and a pointer that has run
                // off the front sits at -1. Anything further out is no longer
                // pointing at this row, so it is not drawn at all.
                if (at === undefined || at < -1 || at > row.values.length) return null;
                return (
                  <span
                    key={m}
                    className="cell-mark live"
                    style={{ "--at": at, "--tier": n } as React.CSSProperties}
                  >
                    <i aria-hidden="true" />
                    {m}
                  </span>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <div className="trace-controls">
        <button onClick={() => go(-1)} disabled={i === 0} aria-label="Previous step">
          ‹
        </button>
        <button
          className="play"
          onClick={() => {
            if (i >= last) setI(0);
            setPlaying((p) => !p);
          }}
          aria-label={playing ? "Pause" : "Play"}
        >
          {playing ? "❚❚" : "▶"}
        </button>
        <button onClick={() => go(1)} disabled={i >= last} aria-label="Next step">
          ›
        </button>
        <input
          className="scrub"
          type="range"
          min={0}
          max={last}
          value={i}
          onChange={(e) => {
            setPlaying(false);
            setI(Number(e.target.value));
          }}
          aria-label="Step through the run"
        />
        <span className="trace-count mono">
          line {(step?.l ?? 0) + 1} · step {i + 1}/{trace.steps.length}
        </span>
      </div>
    </div>
  );
}
