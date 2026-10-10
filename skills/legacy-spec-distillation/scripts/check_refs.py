#!/usr/bin/env python3
"""规格包交接检查：编号引用都有定义，代码引用没有越界、符号仍在原处。

    python3 check_refs.py <规格包目录> [--repo <代码仓库> ...]

编号：表格首格或标题里出现的 `前缀-编号`（如 BR-01、EV-C03）视为定义。只检查在本包里
至少定义过一次的前缀，外部文档的编号（如 P1-REQ-101）不受影响。
已关闭问题：定义行写成"已决 <决定编号>：…"的 `Q-…`。其他行引用它时，同一行须注明"已决"
或该决定编号，否则视为写回漏改。
代码引用：反引号里的 `路径:行号`、`路径:起-止`，可带 `#符号`。路径可以只写文件名，
按 --repo 下的文件匹配；不给 --repo 时跳过代码引用检查。
有问题时逐条打印并以 1 退出。
"""

import re
import sys
from pathlib import Path

ID = re.compile(r"(?<![\w-])([A-Z]{1,4}-[A-Z]?\d{1,4})(?![\w-])")
DEFINITION = re.compile(r"^\s*(?:\|\s*|#{1,6}\s+)([A-Z]{1,4}-[A-Z]?\d{1,4})(?![\w-])")
CITATION = re.compile(r"`([^`\s:]+\.[A-Za-z0-9]+):(\d+)(?:[-–](\d+))?(?:#([A-Za-z_]\w*))?`")
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".codegraph", "build"}
NEAR = 3  # 符号允许偏离引用行的行数
CLOSED = "已决"


def prefix(identifier):
    return identifier.rsplit("-", 1)[0] + "-" + "".join(c for c in identifier.rsplit("-", 1)[1] if c.isalpha())


def index_repos(repos):
    files = {}
    for root in repos:
        for path in Path(root).rglob("*"):
            if path.is_file() and not SKIP_DIRS.intersection(path.relative_to(root).parts):
                files.setdefault(path.name, []).append(path)
    return files


def resolve(cited, files):
    name = cited.rsplit("/", 1)[-1]
    return [p for p in files.get(name, []) if p.as_posix().endswith("/" + cited) or cited == name]


def check_citation(match, files, cache):
    cited, start, end, symbol = match.group(1), int(match.group(2)), match.group(3), match.group(4)
    end = int(end) if end else start
    candidates = resolve(cited, files)
    if not candidates:
        return f"找不到文件 {cited}"
    for path in candidates:
        lines = cache.setdefault(path, path.read_text(errors="replace").splitlines())
        if end > len(lines):
            continue
        if symbol is None or any(symbol in line for line in lines[max(0, start - 1 - NEAR):end + NEAR]):
            return None
    if all(end > len(cache[p]) for p in candidates):
        return f"{match.group(0)} 超出文件行数（{max(len(cache[p]) for p in candidates)}）"
    return f"{match.group(0)} 附近找不到符号 {symbol}"


def check(package, repos):
    docs = sorted(Path(package).rglob("*.md"))
    texts = {d: d.read_text(errors="replace").splitlines() for d in docs}
    defined, closed = set(), {}
    for lines in texts.values():
        for line in lines:
            if m := DEFINITION.match(line):
                defined.add(m.group(1))
                if m.group(1).startswith("Q-") and CLOSED in line:
                    decision = re.split(r"[：:|]", line.split(CLOSED, 1)[1], maxsplit=1)[0]
                    closed[m.group(1)] = set(ID.findall(decision))
    prefixes = {prefix(i) for i in defined}
    files = index_repos(repos) if repos else None
    cache, problems = {}, []
    for doc, lines in texts.items():
        for n, line in enumerate(lines, 1):
            where = f"{doc.relative_to(package)}:{n}"
            ids = ID.findall(line)
            head = m.group(1) if (m := DEFINITION.match(line)) else None
            for identifier in ids:
                if prefix(identifier) in prefixes and identifier not in defined:
                    problems.append(f"{where}：引用了未定义的编号 {identifier}")
            for identifier in dict.fromkeys(ids):
                if identifier in closed and identifier != head and CLOSED not in line \
                        and not closed[identifier] & set(ids):
                    problems.append(f"{where}：{identifier} 已关闭，本行仍按未决引用（按决定改写，或注明\"已决\"）")
            if files is not None:
                for match in CITATION.finditer(line):
                    problem = check_citation(match, files, cache)
                    if problem:
                        problems.append(f"{where}：{problem}")
    return problems


def main(argv):
    if not argv or argv[0].startswith("-"):
        sys.exit(__doc__)
    package, repos = Path(argv[0]), []
    rest = argv[1:]
    while rest:
        if rest[0] != "--repo" or len(rest) < 2:
            sys.exit(__doc__)
        repos.append(Path(rest[1]))
        rest = rest[2:]
    problems = check(package, repos)
    for problem in problems:
        print(problem)
    print(f"check_refs：{'发现 %d 处问题' % len(problems) if problems else '通过'}", file=sys.stderr)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
