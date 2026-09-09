import type { Metadata } from "next";
import { notFound } from "next/navigation";
import PatternView from "@/app/components/PatternView";
import { loadIndex, loadPattern } from "@/lib/data";

export async function generateStaticParams() {
  const { patterns } = await loadIndex();
  return patterns.map((p) => ({ slug: p.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const { patterns } = await loadIndex();
  const entry = patterns.find((p) => p.slug === slug);
  if (!entry) return {};
  return {
    title: `${entry.name} · Pattern Bank`,
    description: `${entry.counts.Easy + entry.counts.Medium + entry.counts.Hard} worked ${entry.name} problems, each with its approach, complexity, and the tests that prove it.`,
  };
}

export default async function PatternPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const { patterns } = await loadIndex();
  if (!patterns.some((p) => p.slug === slug)) notFound();
  return <PatternView pattern={await loadPattern(slug)} />;
}
