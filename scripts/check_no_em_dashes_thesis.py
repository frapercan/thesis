#!/usr/bin/env python3
"""Guard script: fail if any publishable prose in the thesis contains em-dashes.

Scans chapters/, frontmatter/, and appendix/ for:
  - ASCII double-hyphen used as an em-dash: --
  - Unicode em-dash: — (—)

Skips content inside:
  - \\begin{verbatim}...\\end{verbatim}
  - \\begin{lstlisting}...\\end{lstlisting}
  - Inline \\texttt{...} spans (CLI flags such as --flag)
  - Math environments: $...$, \\[...\\], \\begin{equation}, \\begin{align}, etc.
  - Line comments: % ...

Exit code 0  = clean
Exit code 1  = one or more violations found (printed to stdout)
"""

import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Directories relative to the script's parent (repo root)
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
SCAN_DIRS = ["chapters", "frontmatter", "appendix"]

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Block environments to strip before scanning prose
_BLOCK_ENV_RE = re.compile(
    r"\\begin\{(verbatim|lstlisting|equation\*?|align\*?|gather\*?|multline\*?|"
    r"displaymath|math)\}.*?\\end\{\1\}",
    re.DOTALL,
)

# Inline \texttt{...} — strip the whole span
_TEXTTT_RE = re.compile(r"\\texttt\{[^{}]*\}", re.DOTALL)

# Inline math $...$ (non-greedy, no nested $)
_INLINE_MATH_RE = re.compile(r"\$[^$]+?\$")

# Display math \[...\]
_DISPLAY_MATH_RE = re.compile(r"\\\[.*?\\\]", re.DOTALL)

# Line comments: everything from % to end of line
# (does not handle escaped \% — acceptable for our purposes)
_COMMENT_RE = re.compile(r"(?<!\\)%.*$", re.MULTILINE)

# Targets
_ASCII_EMDASH_RE = re.compile(r"--")
_UNICODE_EMDASH_RE = re.compile("—")  # —


def _strip_exempt(text: str) -> str:
    """Remove code/math/comment spans from *text*, replacing with spaces."""
    text = _BLOCK_ENV_RE.sub(lambda m: " " * len(m.group(0)), text)
    text = _DISPLAY_MATH_RE.sub(lambda m: " " * len(m.group(0)), text)
    text = _TEXTTT_RE.sub(lambda m: " " * len(m.group(0)), text)
    text = _INLINE_MATH_RE.sub(lambda m: " " * len(m.group(0)), text)
    text = _COMMENT_RE.sub(lambda m: " " * len(m.group(0)), text)
    return text


def _check_file(path: Path) -> list[str]:
    """Return a list of violation messages for *path*."""
    raw = path.read_text(encoding="utf-8")
    prose = _strip_exempt(raw)

    violations: list[str] = []

    # Re-split prose by lines so we can report line numbers
    raw_lines = raw.splitlines()
    prose_lines = prose.splitlines()

    for lineno, (raw_line, prose_line) in enumerate(
        zip(raw_lines, prose_lines), start=1
    ):
        for m in _ASCII_EMDASH_RE.finditer(prose_line):
            violations.append(
                f"{path}:{lineno}: ASCII em-dash '--' in prose: {raw_line.strip()!r}"
            )
        for m in _UNICODE_EMDASH_RE.finditer(prose_line):
            violations.append(
                f"{path}:{lineno}: Unicode em-dash '—' in prose: {raw_line.strip()!r}"
            )

    return violations


def main() -> int:
    all_violations: list[str] = []

    for dirname in SCAN_DIRS:
        scan_path = ROOT / dirname
        if not scan_path.exists():
            continue
        for tex_file in sorted(scan_path.rglob("*.tex")):
            all_violations.extend(_check_file(tex_file))

    if all_violations:
        print("ERROR: em-dash violations found in thesis prose:\n")
        for v in all_violations:
            print(" ", v)
        print(
            f"\nTotal: {len(all_violations)} violation(s). "
            "Replace with comma, semicolon, parentheses, or a single hyphen."
        )
        return 1

    print("OK: no em-dashes found in thesis prose.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
