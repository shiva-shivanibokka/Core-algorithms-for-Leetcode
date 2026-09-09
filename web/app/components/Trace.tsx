"use client";

import { useCallback, useEffect, useRef, useState } from "react";
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
  const last = trace.steps.length - 1;

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

  return (
    <div className="trace">
      <div className="trace-head">
        <span className="lbl">Watch it run</span>
        <code className="trace-call">{trace.call}</code>
      </div>

      <div className="trace-rows">
        {trace.rows.map((row) => (
          <div key={row.name} className="trace-row">
            <span className="rowname mono">{row.name}</span>
            <div
              className={`cells ${row.kind}`}
              style={{ "--n": row.values.length } as React.CSSProperties}
            >
              {row.values.map((v, n) => {
                const on = row.movers.filter((m) => step?.m[m] === n);
                return (
                  <span key={n} className={`cell${on.length ? " live" : ""}`}>
                    {row.kind === "text" && v === " " ? "␣" : String(v)}
                  </span>
                );
              })}
              {row.movers.map((m, n) => {
                const at = step?.m[m];
                if (at === undefined) return null;
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
