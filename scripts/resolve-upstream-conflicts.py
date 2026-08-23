#!/usr/bin/env python3
"""
自动解决 linux-PKGBUILD 与 Arch 官方 upstream 合并时的固定冲突。

冲突模式(每次 upstream 更新都会出现,共 3 处,全部在 PKGBUILD):

1. 头部版本区(pkgbase/pkgver/pkgrel)
   - 本地(ours): 保留 pkgbase=linux-legion-audio-fix + 注释
   - upstream:    更新 pkgver/pkgrel(必须采用)
   → 解决: 保留 ours 的 pkgbase 与注释,采用 theirs 的 pkgver/pkgrel

2. b2sums 数组(第 3 个元素)
   - 本地: 旧的 arch patch b2sum + 额外的 'SKIP'(legion patch 的占位)
   - upstream: 新的 arch patch b2sum
   → 解决: 采用 theirs 的 b2sum 值,保留 ours 的 'SKIP' 行

3. sha256sums 数组(第 3 个元素)
   - 同上模式
   → 解决: 同上

用法:
    python3 resolve-upstream-conflicts.py [PKGBUILD 路径, 默认 ./PKGBUILD]
退出码: 0 = 全部冲突已解决; 1 = 存在无法识别的冲突(需人工介入)
"""

import re
import sys

def resolve_pkgbuild(path: str) -> bool:
    with open(path, encoding="utf-8") as f:
        content = f.read()

    # 分割冲突块: <<<<<<< HEAD ... ======= ... >>>>>>> <sha>
    # 用正则匹配完整的冲突块
    conflict_pattern = re.compile(
        r"<<<<<<< HEAD\n(?P<ours>.*?)\n=======\n(?P<theirs>.*?)\n>>>>>>> [^\n]+",
        re.DOTALL,
    )

    unresolved = []

    def resolve(m: re.Match) -> str:
        ours = m.group("ours")
        theirs = m.group("theirs")

        # ---- 冲突块 1: 头部版本区 ----
        # ours 含 pkgbase=linux-legion-audio-fix(或有 # Legion 注释), theirs 含 pkgbase=linux
        if re.search(r"pkgbase\s*=\s*linux-legion-audio-fix", ours) and re.search(
            r"pkgbase\s*=\s*linux\b", theirs
        ):
            # 保留 ours 中所有非 pkgver/pkgrel 的行(pkgbase 注释等)
            ours_keep = [
                line
                for line in ours.splitlines()
                if not re.match(r"^\s*pkgver\s*=", line)
                and not re.match(r"^\s*pkgrel\s*=", line)
            ]
            # 从 theirs 取 pkgver/pkgrel 行
            theirs_ver = [
                line
                for line in theirs.splitlines()
                if re.match(r"^\s*pkgver\s*=", line)
                or re.match(r"^\s*pkgrel\s*=", line)
            ]
            return "\n".join(ours_keep + theirs_ver)

        # ---- 冲突块 2/3: b2sums / sha256sums 数组 ----
        # ours 比 theirs 多一个 'SKIP' 行(legion patch 占位), theirs 是新的哈希值
        # 模式: ours 行数 = theirs 行数 + 1, 且 ours 中恰好有一个 'SKIP' 行
        ours_lines = ours.splitlines()
        theirs_lines = theirs.splitlines()
        ours_skip = [l for l in ours_lines if "'SKIP'" in l]
        if len(ours_lines) == len(theirs_lines) + 1 and len(ours_skip) == 1:
            # 保留 theirs 全部行(新哈希), 并在末尾补回 ours 多余的 SKIP
            return "\n".join(theirs_lines + ours_skip)

        # ---- 无法识别的冲突 ----
        unresolved.append((ours[:80], theirs[:80]))
        return m.group(0)  # 原样保留冲突标记, 供人工处理

    new_content, n = conflict_pattern.subn(resolve, content)

    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)

    if unresolved:
        print(f"[!] 有 {len(unresolved)} 个冲突块无法自动解决, 已保留冲突标记:", file=sys.stderr)
        for ours_head, theirs_head in unresolved:
            print(f"    ours: {ours_head!r}", file=sys.stderr)
            print(f"    theirs: {theirs_head!r}", file=sys.stderr)
        return False

    print(f"[+] 已自动解决 {n} 个冲突块: {path}")
    return True


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "PKGBUILD"
    ok = resolve_pkgbuild(path)
    sys.exit(0 if ok else 1)
