/**
 * The mark: two pointers converging on a row of cells.
 *
 * It is the first pattern in the bank and the one every other pattern is
 * explained against, so the logo is the idea rather than an abstract glyph --
 * two carets closing on the pair that matches.
 */
export default function Mark({ size = 30 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      role="img"
      aria-label="Pattern Bank"
    >
      <rect x="1" y="1" width="30" height="30" rx="8" fill="url(#mark-bg)" />
      <rect x="1" y="1" width="30" height="30" rx="8" stroke="url(#mark-edge)" />
      {/* the row being searched */}
      <rect x="6.5" y="14.5" width="4" height="4" rx="1" fill="#5eead4" opacity="0.95" />
      <rect x="12" y="14.5" width="4" height="4" rx="1" fill="#5eead4" opacity="0.4" />
      <rect x="17.5" y="14.5" width="4" height="4" rx="1" fill="#a78bfa" opacity="0.4" />
      <rect x="23" y="14.5" width="4" height="4" rx="1" fill="#a78bfa" opacity="0.95" />
      {/* the two pointers, closing inward */}
      <path
        d="M8.5 10.5 L8.5 12.5 M6.9 11.9 L8.5 10.3 L10.1 11.9"
        stroke="#5eead4"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M25 21.5 L25 19.5 M23.4 20.1 L25 21.7 L26.6 20.1"
        stroke="#a78bfa"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <defs>
        <linearGradient id="mark-bg" x1="0" y1="0" x2="32" y2="32">
          <stop stopColor="#1b1636" />
          <stop offset="1" stopColor="#0f0d20" />
        </linearGradient>
        <linearGradient id="mark-edge" x1="0" y1="0" x2="32" y2="32">
          <stop stopColor="#a78bfa" stopOpacity="0.75" />
          <stop offset="1" stopColor="#5eead4" stopOpacity="0.45" />
        </linearGradient>
      </defs>
    </svg>
  );
}
