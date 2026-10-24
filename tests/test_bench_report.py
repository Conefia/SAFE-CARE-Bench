# -*- coding: utf-8 -*-
"""
Tests for bench_report. Run from the repository root:

    python -m unittest discover -s tests

The fixture is a synthetic run built here, with hand-checkable numbers. It holds
no data from any real run. Test 1 against `results/run_2026-09-01` runs only when
that directory and `tests/expected/run_2026-09-01.json` are both present.
"""

import contextlib, csv, io, json, os, re, shutil, sys, tempfile, unittest

from bench_report.__main__ import main
from bench_report.run import BENCH_ROOT

PLANTED_RULE = "RULE-ESC-017"
FAKE_KB = "FAKEKB0001"

# (arm, scenario, repeat) -> medical_accuracy, escalation_singleturn, escalation_multiturn
# S001 declares escalation_expected: true; S003 declares false.
SCORES = {
    ("A0", "S001", 1): (0.50, 0.0, 0.0),   # missed
    ("A0", "S001", 2): (0.25, 1.0, 0.0),   # missed (either dimension at 0)
    ("A0", "S003", 1): (0.50, 1.0, 1.0),
    ("A0", "S003", 2): (0.25, 0.0, 1.0),   # 0 where none expected: not a missed escalation
    ("A1", "S001", 1): (0.75, 1.0, 1.0),
    ("A1", "S001", 2): (0.75, 0.0, 1.0),   # missed
    ("A1", "S003", 1): (0.50, 1.0, 1.0),
    ("A1", "S003", 2): (0.50, 1.0, 1.0),
    ("A2", "S001", 1): (1.00, 1.0, 1.0),
    ("A2", "S001", 2): (1.00, 1.0, 1.0),
    ("A2", "S003", 1): (0.75, 1.0, 1.0),
    ("A2", "S003", 2): (None, 1.0, 1.0),   # unparseable: excluded from n
}
DIMS = ("medical_accuracy", "escalation_singleturn", "escalation_multiturn")


def make_run(root, corpus_digest=True, bench_version="v0.2.0-test"):
    run = os.path.join(root, "run_test")
    os.makedirs(os.path.join(run, "scores"))
    os.makedirs(os.path.join(run, "manifests"))
    with open(os.path.join(run, "RUN_CARD.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# RUN_CARD - test\n\n```\n"
                "run_id:               run_test\n"
                "produced_utc:         2026-10-01T00:00:00Z\n"
                "agent_model_id:       gen-model-2026-01-01\n"
                "judge_1_model_id:     judge-model-2026-01-01\n"
                "judge_prompt_sha256:  " + "a" * 64 + "\n"
                "seed:                 42\n"
                "bench_version:        " + bench_version + "\n"
                "kb_id_base:           " + FAKE_KB + "\n"
                "runner_code_ref:      0123abc   # engine commit\n"
                "```\n")
    header = ["run_id", "arm_id", "config_sha256", "agent_model_id", "scenario_id", "conversation_id",
              "dimension", "judge_id", "judge_pass", "score_normalised", "parse_ok"]
    if corpus_digest:
        header.insert(3, "corpus_manifest_sha256")
    with open(os.path.join(run, "scores", "per_row_scores.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        for (arm, scenario, rep), values in sorted(SCORES.items()):
            for dim, value in zip(DIMS, values):
                for judge_pass in ("1", "2"):
                    row = {"run_id": "run_test", "arm_id": arm, "config_sha256": arm.lower() * 32,
                           "agent_model_id": "gen-model-2026-01-01", "scenario_id": scenario,
                           "conversation_id": "%s_%s_R%02d" % (arm, scenario, rep), "dimension": dim,
                           "judge_id": "J1", "judge_pass": judge_pass,
                           # pass 2 holds values that would move every mean if it leaked in
                           "score_normalised": "" if value is None else (value if judge_pass == "1" else 0.123),
                           "parse_ok": "False" if value is None else "True"}
                    if corpus_digest:
                        row["corpus_manifest_sha256"] = "not_applicable" if arm == "A0" else "c" * 64
                    w.writerow(row)
    for arm, start, end in (("A0", "2026-09-01T10:00:00Z", "2026-09-01T11:00:00Z"),
                            ("A2", "2026-09-01T09:00:00Z", "2026-09-01T12:00:00Z")):
        with open(os.path.join(run, "manifests", "%s_R01.manifest.json" % arm), "w", encoding="utf-8") as f:
            json.dump({"run_id": arm, "started_at": start, "finished_at": end}, f)
    return run


def run_cli(*args):
    err, out = io.StringIO(), io.StringIO()
    with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
        code = main(list(args))
    return code, err.getvalue()


def section(text, number):
    m = re.search(r"^## %d\. .*?(?=^## |\Z)" % number, text, re.S | re.M)
    return m.group(0)


class ReportTests(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.out = os.path.join(self.tmp, "report.md")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def report(self, run):
        code, err = run_cli(run, "--out", self.out)
        self.assertEqual(code, 0, err)
        with open(self.out, encoding="utf-8") as f:
            return f.read()

    def deny_list(self, *entries):
        path = os.path.join(self.tmp, "deny.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("# private deny list\n" + "\n".join(entries) + "\n")
        return path

    def ip_scan(self, exit_code):
        return '"%s" -c "import sys; sys.exit(%d)"' % (sys.executable, exit_code)

    # -- Test 1: numbers -----------------------------------------------------
    def test_numbers_synthetic(self):
        text = self.report(make_run(self.tmp))
        scores = section(text, 2)
        self.assertIn("| Medical accuracy | 0.375 ± 0.144 (n=4) | 0.625 ± 0.144 (n=4) | 0.917 ± 0.144 (n=3) |", scores)
        self.assertNotIn("0.123", text)
        self.assertIn("### `A0` → `A1`: Grounding (capability bundle)", text)
        self.assertIn("### `A1` → `A2`: Safety control (single capability)", text)
        self.assertIn("| Medical accuracy | 0.375 (n=4) | 0.625 (n=4) | +0.250 |", text)
        missed = section(text, 4)
        self.assertIn("| `A0` | 2 | 2 | 0 | S001 ×2 |", missed)
        self.assertIn("| `A1` | 2 | 1 | 0 | S001 ×1 |", missed)
        self.assertIn("| `A2` | 2 | 0 | 0 | none |", missed)

    @unittest.skipUnless(
        os.path.isdir(os.path.join(BENCH_ROOT, "results", "run_2026-09-01"))
        and os.path.isfile(os.path.join(BENCH_ROOT, "tests", "expected", "run_2026-09-01.json")),
        "needs results/run_2026-09-01 and tests/expected/run_2026-09-01.json")
    def test_numbers_run_2026_09_01(self):
        """Every mean and missed-escalation count matches the run card and the paper."""
        with open(os.path.join(BENCH_ROOT, "tests", "expected", "run_2026-09-01.json"), encoding="utf-8") as f:
            expected = json.load(f)
        text = self.report(os.path.join(BENCH_ROOT, "results", "run_2026-09-01"))
        for arm, dims in expected["means"].items():
            for dim, value in dims.items():
                self.assertRegex(text, re.escape("%.3f" % value), "%s %s" % (arm, dim))
        for arm, count in expected["missed"].items():
            self.assertRegex(section(text, 4), r"\| `%s` \| \d+ \| %d \|" % (re.escape(arm), count))

    # -- Test 2: leak check --------------------------------------------------
    def test_planted_rule_id_refuses_final_and_names_the_line(self):
        run = make_run(self.tmp, bench_version="v0.2.0 " + PLANTED_RULE)
        draft = self.report(run)
        draft_line = next(i for i, l in enumerate(draft.splitlines(), 1) if PLANTED_RULE in l)
        os.remove(self.out)
        code, err = run_cli(run, "--out", self.out, "--final",
                            "--deny-list", self.deny_list(PLANTED_RULE), "--ip-scan", self.ip_scan(0))
        self.assertEqual(code, 2)
        self.assertRegex(err, r"report line \d+ matches deny-list entry on line 2")
        self.assertNotIn(PLANTED_RULE, err)
        self.assertFalse(os.path.exists(self.out))
        self.assertFalse(os.path.exists(self.out + ".unchecked"))
        reported = int(re.search(r"report line (\d+)", err).group(1))
        self.assertEqual(reported, draft_line - 2)   # the final report has no two-line DRAFT banner

    def test_failed_ip_scan_refuses_final(self):
        code, err = run_cli(make_run(self.tmp), "--out", self.out, "--final",
                            "--deny-list", self.deny_list(PLANTED_RULE), "--ip-scan", self.ip_scan(1))
        self.assertEqual(code, 2)
        self.assertIn("ip-scan failed", err)
        self.assertFalse(os.path.exists(self.out))
        self.assertFalse(os.path.exists(self.out + ".unchecked"))

    def test_final_fails_closed_without_checks(self):
        run = make_run(self.tmp)
        for args in ((), ("--deny-list", self.deny_list(PLANTED_RULE)), ("--ip-scan", self.ip_scan(0))):
            code, err = run_cli(run, "--out", self.out, "--final", *args)
            self.assertEqual(code, 2, args)
            self.assertFalse(os.path.exists(self.out))

    def test_deny_list_inside_repo_is_refused(self):
        code, err = run_cli(make_run(self.tmp), "--out", self.out, "--final",
                            "--deny-list", os.path.join(BENCH_ROOT, "README.md"), "--ip-scan", self.ip_scan(0))
        self.assertEqual(code, 2)
        self.assertIn("outside the public bench repository", err)

    def test_clean_final_is_written_without_draft_banner(self):
        code, err = run_cli(make_run(self.tmp), "--out", self.out, "--final",
                            "--deny-list", self.deny_list(PLANTED_RULE), "--ip-scan", self.ip_scan(0))
        self.assertEqual(code, 0, err)
        with open(self.out, encoding="utf-8") as f:
            self.assertNotIn("DRAFT", f.read())

    def test_card_fields_outside_allow_list_never_reach_the_report(self):
        text = self.report(make_run(self.tmp))
        self.assertNotIn(FAKE_KB, text)
        self.assertNotIn("0123abc", text)
        self.assertNotIn(self.tmp, text)

    # -- Test 3: same input ---------------------------------------------------
    def test_same_input_gives_byte_identical_reports(self):
        run = make_run(self.tmp)
        second = os.path.join(self.tmp, "again.md")
        self.assertEqual(run_cli(run, "--out", self.out)[0], 0)
        self.assertEqual(run_cli(run, "--out", second)[0], 0)
        with open(self.out, "rb") as a, open(second, "rb") as b:
            self.assertEqual(a.read(), b.read())

    # -- Test 4: missing digest -----------------------------------------------
    def test_missing_corpus_digest_is_stated_not_blank(self):
        what_was_run = section(self.report(make_run(self.tmp, corpus_digest=False)), 6)
        self.assertIn("**No corpus digest is recorded for `A0`, `A1`, `A2`.**", what_was_run)
        self.assertIn("not recorded; this run has no corpus preflight result", what_was_run)
        self.assertNotRegex(what_was_run, r"\|[ \t]*\|")

    def test_recorded_corpus_digest_is_shown(self):
        what_was_run = section(self.report(make_run(self.tmp)), 6)
        self.assertIn("not applicable (no retrieval)", what_was_run)
        self.assertIn("`%s`" % ("c" * 64), what_was_run)
        self.assertNotIn("No corpus digest", what_was_run)

    # -- Format guards ---------------------------------------------------------
    def test_mixed_judges_must_be_chosen(self):
        run = make_run(self.tmp)
        path = os.path.join(run, "scores", "per_row_scores.csv")
        with open(path, encoding="utf-8") as f:
            text = f.read()
        with open(path, "a", encoding="utf-8", newline="") as f:
            f.write(text.splitlines()[1].replace(",J1,", ",J2,") + "\n")
        code, err = run_cli(run, "--out", self.out)
        self.assertEqual(code, 1)
        self.assertIn("choose one with --judge", err)
        self.assertEqual(run_cli(run, "--out", self.out, "--judge", "J1")[0], 0)

    def test_all_seven_sections_in_order(self):
        text = self.report(make_run(self.tmp))
        headings = re.findall(r"^## (\d)\. ", text, re.M)
        self.assertEqual(headings, list("1234567"))
        self.assertIn("Judge not calibrated against clinicians for this domain; treat scores as indicative.", text)


if __name__ == "__main__":
    unittest.main()
