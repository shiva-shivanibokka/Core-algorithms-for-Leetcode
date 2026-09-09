import Link from "next/link";
import { loadIndex, REPO, TIERS } from "@/lib/data";

export default async function Home() {
  const { totals, patterns } = await loadIndex();
  const withRef = patterns.filter((p) => p.verified > 0).length;

  return (
    <>
      <section className="shell hero">
        <p className="kicker">Core algorithms for LeetCode</p>
        <h1 className="gradient">
          <span>Interview problems,</span>
          <span>filed by the shape of the answer</span>
        </h1>
        <p className="stand">
          Not a pile of solved problems. Thirteen patterns, ninety problems each,
          worked from a warm-up Easy up to something a FAANG onsite would use — and
          every one of them runs, with the tests that prove it sitting next to it.
        </p>

        <div className="tally">
          <div>
            <span className="num mono">{totals.patterns}</span>
            <span className="lbl">patterns</span>
          </div>
          <div>
            <span className="num mono">{totals.problems.toLocaleString()}</span>
            <span className="lbl">problems, all green</span>
          </div>
          <div>
            <span className="num mono">{totals.verified}</span>
            <span className="lbl">also checked against a reference</span>
          </div>
        </div>
      </section>

      <section className="shell">
        <div className="assurance">
          <article>
            <h3>
              <span className="tick" aria-hidden="true" />
              Every cell runs
            </h3>
            <p>
              <code>verify_notebooks.py</code> executes all 1,178 code cells on every
              push. A solution that raises, or whose asserts stop holding, fails the
              build.
            </p>
          </article>
          <article>
            <h3>
              <span className="tick" aria-hidden="true" />
              Every solution is reached
            </h3>
            <p>
              Running cells is not enough. Two problems here once shipped a solution
              the cell never called — one of them a stub — and stayed green for two
              years. Now that fails too.
            </p>
          </article>
          <article>
            <h3>
              <span className="tick" aria-hidden="true" />
              {totals.verified} checked from outside
            </h3>
            <p>
              Asserts written beside a solution only prove it agrees with its author.{" "}
              <code>stress_test.py</code> runs {totals.verified} solutions against
              brute-force references — written from the problem statement, sharing no
              code with the bank — on 200 random inputs each. Every pattern is covered.
            </p>
          </article>
        </div>
      </section>

      <section className="shell">
        <div className="section-head">
          <h2>The thirteen patterns</h2>
          <span className="kicker">40 easy · 30 medium · 20 hard, each</span>
        </div>

        <div className="patterns">
          {patterns.map((p) => {
            const total = TIERS.reduce((sum, t) => sum + p.counts[t], 0);
            return (
              <Link key={p.slug} href={`/p/${p.slug}/`} className="pcard">
                <span className="head">
                  <span className="idx mono">{p.id}</span>
                  <span className="name">{p.name}</span>
                </span>
                <span className="bar" aria-hidden="true">
                  {TIERS.map((t) => (
                    <i
                      key={t}
                      className={t.toLowerCase()}
                      style={{ width: `${(p.counts[t] / total) * 100}%` }}
                    />
                  ))}
                </span>
                {p.note && <span className="aside">{p.note}</span>}
                <span className="counts">
                  {TIERS.map((t) => (
                    <span key={t} className={t.toLowerCase()}>
                      <b>{p.counts[t]}</b> {t.toLowerCase()}
                    </span>
                  ))}
                </span>
                <span className={`ref-line${p.verified ? " has" : ""}`}>
                  {p.verified
                    ? `${p.verified} checked against a reference`
                    : "no independent reference yet"}
                </span>
              </Link>
            );
          })}
        </div>

        <p className="stand" style={{ paddingBottom: "70px", fontSize: "14px" }}>
          All {withRef} patterns have solutions under an independent reference, though not
          evenly: an array problem needs a one-line brute force, while a tree or graph
          problem needs its input built first. The cards say how many rather than
          averaging it away.{" "}
          <a href={`${REPO}/blob/main/stress_test.py`} style={{ color: "var(--cyan)" }}>
            stress_test.py
          </a>
        </p>
      </section>
    </>
  );
}
