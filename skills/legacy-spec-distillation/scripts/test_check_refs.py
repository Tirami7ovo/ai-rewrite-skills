import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_refs import check  # noqa: E402


class CheckRefsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.pkg, self.repo = root / "pkg", root / "repo"
        (self.repo / "src").mkdir(parents=True)
        (self.repo / "src/app.c").write_text("\n".join(["// x"] * 9 + ["int apply_config(void)", "{", "}"]) + "\n",
                                            encoding="utf-8")
        self.pkg.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def run_check(self, text):
        (self.pkg / "SPEC.md").write_text(text, encoding="utf-8")
        return check(self.pkg, [self.repo])

    def test_defined_and_undefined_ids(self):
        problems = self.run_check("| BR-01 | 结论 |\n### Q-01 问题\n见 BR-01、Q-01、BR-02；P1-REQ-101 不是本包编号\n")
        self.assertEqual([p.split("：")[-1] for p in problems], ["引用了未定义的编号 BR-02"])

    def test_citation_in_range_with_symbol(self):
        self.assertEqual(self.run_check("见 `src/app.c:10#apply_config` 与 `app.c:9-11`\n"), [])

    def test_citation_out_of_range(self):
        problems = self.run_check("见 `app.c:40`\n")
        self.assertTrue(any("超出文件行数" in p for p in problems), problems)

    def test_symbol_drifted(self):
        problems = self.run_check("见 `app.c:2#apply_config`\n")
        self.assertTrue(any("附近找不到符号 apply_config" in p for p in problems), problems)

    def test_missing_file(self):
        problems = self.run_check("见 `gone.c:3`\n")
        self.assertTrue(any("找不到文件 gone.c" in p for p in problems), problems)

    def test_closed_question_needs_decision_on_citing_line(self):
        problems = self.run_check(
            "| DEC-01 | 决定 |\n| BR-09 | 结论 |\n| Q-01 | **已决 DEC-01**：问题 | BR-09 |\n"
            "缓存用满保旧拒新（Q-01，BR-09）\n按目标淘汰最旧（Q-01，DEC-01）\n见 Q-01（已决）\n")
        self.assertEqual([p.split("：", 1)[0] for p in problems], ["SPEC.md:4"])

    def test_markup_around_definition(self):
        problems = self.run_check("| `BR-01` | 结论 |\n| **Q-01** | 问题 |\n见 BR-02、Q-01\n")
        self.assertEqual([p.split("：")[-1] for p in problems], ["引用了未定义的编号 BR-02"])

    def test_rejects_missing_or_empty_package(self):
        (self.pkg / "SPEC.md").write_text("| BR-01 | 结论 |\n", encoding="utf-8")
        empty = Path(self.tmp.name) / "empty"
        empty.mkdir()
        for bad in (self.pkg / "gone", self.pkg / "SPEC.md", empty):
            with self.assertRaises(ValueError):
                check(bad, [])

    def test_rejects_non_utf8_document(self):
        (self.pkg / "SPEC.md").write_bytes("| Q-01 | 已决 DEC-01：问题 |\n".encode("gbk"))
        with self.assertRaises(ValueError):
            check(self.pkg, [])

    def test_citations_skipped_without_repo(self):
        (self.pkg / "SPEC.md").write_text("见 `gone.c:3`\n", encoding="utf-8")
        self.assertEqual(check(self.pkg, []), [])


if __name__ == "__main__":
    unittest.main()
