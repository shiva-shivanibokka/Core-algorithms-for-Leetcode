"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { SCENES, type CellStep, type NodeStep, type Step } from "@/lib/scenes";

const STEP_MS = 2100;

/**
 * The pattern's shape, played as a short loop.
 *
 * Two renderers cover all thirteen: a row of cells with pointers and a band,
 * and a set of positioned nodes with edges. Every scene carries a caption per
 * step, so the animation is readable stopped as well as running -- and it can
 * always be stepped by hand.
 */
export default function Visual({ slug }: { slug: string }) {
  const steps = SCENES[slug];
  const [i, setI] = useState(0);
  const [playing, setPlaying] = useState(true);
  const timer = useRef<ReturnType<typeof setInterval> | undefined>(undefined);

  const go = useCallback(
    (d: number) => {
      setPlaying(false);
      setI((n) => (n + d + steps.length) % steps.length);
    },
    [steps.length],
  );

  useEffect(() => {
    if (!playing) return;
    // A hidden tab throttles timers, so a returning visitor would otherwise
    // find the loop stalled halfway through a step.
    const onHide = () => setPlaying(!document.hidden);
    document.addEventListener("visibilitychange", onHide);
    timer.current = setInterval(() => setI((n) => (n + 1) % steps.length), STEP_MS);
    return () => {
      clearInterval(timer.current);
      document.removeEventListener("visibilitychange", onHide);
    };
  }, [playing, steps.length]);

  useEffect(() => {
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) setPlaying(false);
  }, []);

  if (!steps) return null;
  const step = steps[i];

  return (
    <figure className="visual">
      <div className="visual-stage">
        {step.kind === "cells" ? <Cells step={step} /> : <Nodes step={step} />}
      </div>

      <figcaption className="visual-caption">{step.caption}</figcaption>

      <div className="visual-controls">
        <button onClick={() => go(-1)} aria-label="Previous step">
          ‹
        </button>
        <button
          className="play"
          onClick={() => setPlaying((p) => !p)}
          aria-label={playing ? "Pause the animation" : "Play the animation"}
        >
          {playing ? "❚❚" : "▶"}
        </button>
        <button onClick={() => go(1)} aria-label="Next step">
          ›
        </button>
        <span className="visual-dots" aria-hidden="true">
          {steps.map((_, n) => (
            <i key={n} className={n === i ? "on" : ""} />
          ))}
        </span>
        <span className="visual-count">
          step {i + 1} of {steps.length}
        </span>
      </div>
    </figure>
  );
}

function Cells({ step }: { step: CellStep }) {
  const { cells, marks = [], tones, band } = step;
  return (
    <div className="cells" style={{ "--n": cells.length } as React.CSSProperties}>
      {band && (
        <span
          className="cells-band"
          style={
            {
              "--from": band[0],
              "--span": band[1] - band[0] + 1,
            } as React.CSSProperties
          }
        />
      )}
      {cells.map((v, i) => (
        <span key={i} className={`cell ${tones?.[i] ?? "idle"}`}>
          {v}
        </span>
      ))}
      {marks.map((m, n) => (
        <span
          key={n}
          className={`cell-mark ${m.tone ?? "idle"}`}
          style={{ "--at": m.at } as React.CSSProperties}
        >
          <i aria-hidden="true" />
          {m.label}
        </span>
      ))}
    </div>
  );
}

function Nodes({ step }: { step: NodeStep }) {
  const { nodes, edges, directed, marks = [] } = step;
  const at = (id: string) => nodes.find((n) => n.id === id);
  return (
    <svg className="nodes" viewBox="2 6 96 88" preserveAspectRatio="xMidYMid meet">
      {directed && (
        <defs>
          <marker
            id="arrow"
            viewBox="0 0 8 8"
            refX="7"
            refY="4"
            markerWidth="5"
            markerHeight="5"
            orient="auto-start-reverse"
          >
            <path d="M0 0 L8 4 L0 8 z" fill="#4b4570" />
          </marker>
        </defs>
      )}
      {edges.map(([a, b], n) => {
        const p = at(a);
        const q = at(b);
        if (!p || !q) return null;
        // stop the line short of the node so an arrowhead is not buried in it
        const dx = q.x - p.x;
        const dy = q.y - p.y;
        const len = Math.hypot(dx, dy) || 1;
        const r = 7.5;
        return (
          <line
            key={n}
            x1={p.x + (dx / len) * r}
            y1={p.y + (dy / len) * r}
            x2={q.x - (dx / len) * r}
            y2={q.y - (dy / len) * r}
            stroke="#3b3563"
            strokeWidth="0.9"
            markerEnd={directed ? "url(#arrow)" : undefined}
          />
        );
      })}
      {nodes.map((n) => (
        <g key={n.id} className={`node ${n.tone ?? "idle"}`}>
          <circle cx={n.x} cy={n.y} r="7" />
          <text x={n.x} y={n.y} dominantBaseline="central" textAnchor="middle">
            {n.label}
          </text>
        </g>
      ))}
      {marks.map((m, n) => {
        const p = at(m.on);
        if (!p) return null;
        return (
          <text key={n} className="node-mark" x={p.x} y={p.y + 14} textAnchor="middle">
            {m.label}
          </text>
        );
      })}
    </svg>
  );
}

export function hasVisual(slug: string): boolean {
  return Boolean(SCENES[slug]);
}

export type { Step };
