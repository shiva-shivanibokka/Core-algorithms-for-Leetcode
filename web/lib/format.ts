/** Pure helpers shared by server and client components. */

export type Token = { text: string; cls?: "kw" | "str" | "num" | "com" | "fn" };

const KEYWORDS = new Set([
  "and", "as", "assert", "break", "class", "continue", "def", "del", "elif", "else",
  "except", "False", "finally", "for", "from", "global", "if", "import", "in", "is",
  "lambda", "None", "nonlocal", "not", "or", "pass", "raise", "return", "True", "try",
  "while", "with", "yield",
]);

const NAME = /[A-Za-z_][A-Za-z0-9_]*/y;
const NUMBER = /\d+(?:\.\d+)?/y;

/**
 * Tokenise one line of Python, carrying triple-quoted strings across lines.
 *
 * Deliberately small: enough to tell a comment from a string from a keyword,
 * which is all the reader needs. Anything it does not recognise comes back as
 * plain text rather than being guessed at.
 */
export function tokenizeLine(
  line: string,
  openQuote: string | null,
): { tokens: Token[]; openQuote: string | null } {
  const tokens: Token[] = [];
  let i = 0;
  let open = openQuote;
  let plain = "";

  const flush = () => {
    if (plain) tokens.push({ text: plain });
    plain = "";
  };

  // A triple-quoted string carried over from an earlier line runs until it closes.
  if (open) {
    const end = line.indexOf(open);
    if (end === -1) return { tokens: [{ text: line, cls: "str" }], openQuote: open };
    tokens.push({ text: line.slice(0, end + open.length), cls: "str" });
    i = end + open.length;
    open = null;
  }

  while (i < line.length) {
    const ch = line[i];

    if (ch === "#") {
      flush();
      tokens.push({ text: line.slice(i), cls: "com" });
      return { tokens, openQuote: null };
    }

    if (ch === '"' || ch === "'") {
      flush();
      const triple = line.slice(i, i + 3);
      if (triple === ch.repeat(3)) {
        const end = line.indexOf(triple, i + 3);
        if (end === -1) {
          tokens.push({ text: line.slice(i), cls: "str" });
          return { tokens, openQuote: triple };
        }
        tokens.push({ text: line.slice(i, end + 3), cls: "str" });
        i = end + 3;
        continue;
      }
      let j = i + 1;
      while (j < line.length && line[j] !== ch) j += line[j] === "\\" ? 2 : 1;
      tokens.push({ text: line.slice(i, Math.min(j + 1, line.length)), cls: "str" });
      i = j + 1;
      continue;
    }

    NAME.lastIndex = i;
    const name = NAME.exec(line);
    if (name) {
      flush();
      const word = name[0];
      const isDef = /\bdef\s+$/.test(line.slice(0, i)) || /\bclass\s+$/.test(line.slice(0, i));
      tokens.push({
        text: word,
        cls: isDef ? "fn" : KEYWORDS.has(word) ? "kw" : undefined,
      });
      i += word.length;
      continue;
    }

    NUMBER.lastIndex = i;
    const num = NUMBER.exec(line);
    if (num) {
      flush();
      tokens.push({ text: num[0], cls: "num" });
      i += num[0].length;
      continue;
    }

    plain += ch;
    i += 1;
  }

  flush();
  return { tokens, openQuote: open };
}

export function tokenize(code: string): Token[][] {
  let open: string | null = null;
  return code.split("\n").map((line) => {
    const result = tokenizeLine(line, open);
    open = result.openQuote;
    return result.tokens;
  });
}

const escapeHtml = (s: string) =>
  s.replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c] as string);

/**
 * The notebooks' markdown, reduced to the four things they actually use:
 * bold, inline code, italics, and dash bullets. Escaped first, so a heading
 * that happens to contain a `<` is text and not markup.
 */
export function formatProse(markdown: string): string {
  const inline = (s: string) =>
    escapeHtml(s)
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, "<em>$1</em>");

  const html: string[] = [];
  let list: string[] = [];

  const closeList = () => {
    if (list.length) html.push(`<ul>${list.map((li) => `<li>${li}</li>`).join("")}</ul>`);
    list = [];
  };

  for (const raw of markdown.split("\n")) {
    const line = raw.trim();
    if (!line) {
      closeList();
      continue;
    }
    const bullet = line.match(/^[-*]\s+(.*)$/);
    if (bullet) {
      list.push(inline(bullet[1]));
    } else {
      closeList();
      html.push(`<p>${inline(line)}</p>`);
    }
  }
  closeList();
  return html.join("");
}
