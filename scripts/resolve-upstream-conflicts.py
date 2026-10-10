#!/usr/bin/env python3
"""
Auto-resolve the recurring merge conflicts between linux-PKGBUILD and the
official Arch Linux upstream kernel PKGBUILD.

Conflict patterns (reappear on every upstream update, 3 hunks, all in PKGBUILD):

1. Header version block (pkgbase/pkgver/pkgrel)
   - ours:   keeps pkgbase=linux-legion-audio-fix + comment
   - theirs: new pkgver/pkgrel (must adopt)
   -> resolution: keep our pkgbase + comment, adopt their pkgver/pkgrel

2. b2sums array (3rd element)
   - ours:   old arch-patch b2sum + extra 'SKIP' (legion patch placeholder)
   - theirs: new arch-patch b2sum
   -> resolution: adopt their b2sum value, keep our 'SKIP' line

3. sha256sums array (3rd element)
   - same pattern as #2
   -> resolution: same as above

Usage:
    python3 resolve-upstream-conflicts.py [PKGBUILD path, default ./PKGBUILD]
Exit code: 0 = all conflicts resolved; 1 = unrecognized conflicts remain (manual intervention required)
"""

import re
import sys

def resolve_pkgbuild(path: str) -> bool:
    with open(path, encoding="utf-8") as f:
        content = f.read()

    # Split conflict hunks: <<<<<<< HEAD ... ======= ... >>>>>>> <sha>
    # Match a full conflict hunk with a regex
    conflict_pattern = re.compile(
        r"<<<<<<< HEAD\n(?P<ours>.*?)\n=======\n(?P<theirs>.*?)\n>>>>>>> [^\n]+",
        re.DOTALL,
    )

    unresolved = []

    def resolve(m: re.Match) -> str:
        ours = m.group("ours")
        theirs = m.group("theirs")

        # ---- Conflict hunk 1: header version block ----
        # ours contains pkgbase=linux-legion-audio-fix (or a # Legion comment),
        # theirs contains pkgbase=linux
        if re.search(r"pkgbase\s*=\s*linux-legion-audio-fix", ours) and re.search(
            r"pkgbase\s*=\s*linux\b", theirs
        ):
            # Keep all our non-pkgver/pkgrel lines (pkgbase, comments, etc.)
            ours_keep = [
                line
                for line in ours.splitlines()
                if not re.match(r"^\s*pkgver\s*=", line)
                and not re.match(r"^\s*pkgrel\s*=", line)
            ]
            # Take pkgver/pkgrel lines from theirs
            theirs_ver = [
                line
                for line in theirs.splitlines()
                if re.match(r"^\s*pkgver\s*=", line)
                or re.match(r"^\s*pkgrel\s*=", line)
            ]
            return "\n".join(ours_keep + theirs_ver)

        # ---- Conflict hunk 2/3: b2sums / sha256sums arrays ----
        # ours has one extra 'SKIP' line (legion patch placeholder), theirs has
        # the new hash value. Pattern: len(ours) == len(theirs) + 1 and ours
        # contains exactly one 'SKIP' line.
        ours_lines = ours.splitlines()
        theirs_lines = theirs.splitlines()
        ours_skip = [l for l in ours_lines if "'SKIP'" in l]
        if len(ours_lines) == len(theirs_lines) + 1 and len(ours_skip) == 1:
            # Keep all their lines (new hashes), append our extra SKIP at the end
            return "\n".join(theirs_lines + ours_skip)

        # ---- Unrecognized conflict ----
        unresolved.append((ours[:80], theirs[:80]))
        return m.group(0)  # leave conflict markers intact for manual handling

    new_content, n = conflict_pattern.subn(resolve, content)

    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)

    if unresolved:
        print(
            f"[!] {len(unresolved)} conflict hunk(s) could not be auto-resolved; "
            f"conflict markers left in place:",
            file=sys.stderr,
        )
        for ours_head, theirs_head in unresolved:
            print(f"    ours: {ours_head!r}", file=sys.stderr)
            print(f"    theirs: {theirs_head!r}", file=sys.stderr)
        return False

    print(f"[+] Auto-resolved {n} conflict hunk(s): {path}")
    return True


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "PKGBUILD"
    ok = resolve_pkgbuild(path)
    sys.exit(0 if ok else 1)
