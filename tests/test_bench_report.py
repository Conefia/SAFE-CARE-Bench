# -*- coding: utf-8 -*-
"""
Tests for bench_report. Run from the repository root:

    python -m unittest discover -s tests

The fixture is a synthetic run built here, with hand-checkable numbers. It holds
no data from any real run. Test 1 against `results/run_2026-09-01` runs only when
that directory and `tests/expected/run_2026-09-01.json` are both present.
"""

import contextlib, csv, hashlib, io, json, os, re, shutil, tempfile, unittest

from bench_report.__main__ import main
from bench_report.report import DIMENSION_NAMES
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


ENGINE_COMMIT = "deadbeef" * 5


def make_published_run(root):
    """The same scores in the published layout: tier/replicate columns, a scope column,
    a prose run card with tables, and manifests carrying a provenance block. S003 is
    marked out of scope."""
    run = os.path.join(root, "run_published")
    os.makedirs(os.path.join(run, "scores"))
    os.makedirs(os.path.join(run, "manifests"))
    with open(os.path.join(run, "RUN_CARD.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("# Run card - test\n\n## Determinism\n\n| | |\n|---|---|\n"
                "| Seed | **not exposed by the provider** |\n\n## Provenance\n\n"
                "| Repo | Commit | Clean? |\n|---|---|---|\n"
                "| Engine | `" + ENGINE_COMMIT + "` | **dirty** |\n"
                "| Bench | `" + "b" * 40 + "` | **dirty** |\n")
    header = ["scenario_id", "tier", "dimension", "judge_model", "replicate", "run_id", "score",
              "scenario_in_A0_A2_scope"]
    with open(os.path.join(run, "scores", "per_row_scores.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header)
        w.writeheader()
        for (arm, scenario, rep), values in sorted(SCORES.items()):
            for dim, value in zip(DIMS, values):
                if value is None:
                    continue
                w.writerow({"scenario_id": scenario, "tier": arm, "dimension": dim, "judge_model": "judge-model",
                            "replicate": "R%d" % rep, "run_id": "%s-%d" % (arm, rep), "score": value,
                            "scenario_in_A0_A2_scope": scenario != "S003"})
    for arm in ("A0", "A1", "A2"):
        provenance = {
            "engine": {"commit": ENGINE_COMMIT[:7]},
            "agent": {"id": arm, "spec_hash": arm.lower() * 32},
            "model": {"model_id": "gen-model"},
            "scenarios": {"scenarios": {"S001": "1" * 64, "S003": "3" * 64}},
            "execution": {"hard_fail_fired": False},
            "judge": {d: {"model_id": "judge-model", "prompt_hash": d[0] * 64} for d in DIMS},
        }
        with open(os.path.join(run, "manifests", "%s_R1_manifest.json" % arm), "w", encoding="utf-8") as f:
            json.dump({"run_id": arm, "started_at": "2026-09-01T10:00:00Z", "finished_at": "2026-09-01T11:00:00Z",
                       "provenance": provenance}, f)
        with open(os.path.join(run, "manifests", "%s_R1_summary.json" % arm), "w", encoding="utf-8") as f:
            json.dump({"mean": 0.5}, f)
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
        self.out = os.path.join(self.tmp, "report.draft.md")
        self.final_out = os.path.join(self.tmp, "report.md")

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

    def draft(self, run):
        """Write a draft, return (draft path, its bytes)."""
        code, err = run_cli(run, "--out", self.out)
        self.assertEqual(code, 0, err)
        with open(self.out, "rb") as f:
            return self.out, f.read()

    def verdict(self, draft_bytes, **overrides):
        """A verdict that clears `draft_bytes`, with any field overridden."""
        fields = dict(ip_check_verdict="1", report_sha256=hashlib.sha256(draft_bytes).hexdigest(),
                      report_file=os.path.basename(self.out), checked_by="Test Checker",
                      checked_utc="2026-10-27T12:00:00Z", ip_check_commit="e" * 40,
                      item_1="PASS", item_2="PASS", item_3="N/A", item_4="PASS", item_5="PASS",
                      item_6="N/A", item_7="PASS", bottom_line="SAFE TO PUSH")
        fields.update(overrides)
        path = os.path.join(self.tmp, "report.draft.md.verdict")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write("".join("%s: %s\n" % kv for kv in fields.items() if kv[1] is not None))
        return path

    def final(self, run, draft, verdict, deny=None):
        return run_cli(run, "--final", "--draft", draft, "--verdict", verdict, "--out", self.final_out,
                       "--deny-list", deny or self.deny_list(PLANTED_RULE))

    # -- Test 1: numbers -----------------------------------------------------
    def test_numbers_synthetic(self):
        text = self.report(make_run(self.tmp))
        scores = section(text, 2)
        # scenario means first: A2 is S001 1.00 and S003 0.75 (its second repeat is unscored)
        self.assertIn("| Medical accuracy | 0.375 ± 0.000 (n=2) | 0.625 ± 0.177 (n=2) | 0.875 ± 0.177 (n=2) |", scores)
        self.assertNotIn("0.123", text)
        self.assertIn("- **Conversations scored:** 12", text)
        self.assertIn("### `A0` → `A1`: Grounding (capability bundle)", text)
        self.assertIn("### `A1` → `A2`: Safety control (single capability)", text)
        self.assertIn("| Medical accuracy | 0.375 (n=2) | 0.625 (n=2) | +0.250 |", text)
        missed = section(text, 4)
        self.assertIn("| `A0` | 2 | 2 | 0 | S001 ×2 |", missed)
        self.assertIn("| `A1` | 2 | 1 | 0 | S001 ×1 |", missed)
        self.assertIn("| `A2` | 2 | 0 | 0 | none |", missed)

    @unittest.skipUnless(
        os.path.isdir(os.path.join(BENCH_ROOT, "results", "run_2026-09-01"))
        and os.path.isfile(os.path.join(BENCH_ROOT, "tests", "expected", "run_2026-09-01.json")),
        "needs results/run_2026-09-01 and tests/expected/run_2026-09-01.json")
    def test_numbers_run_2026_09_01(self):
        """Every mean and SD matches the run's published scenario-level analysis."""
        with open(os.path.join(BENCH_ROOT, "tests", "expected", "run_2026-09-01.json"), encoding="utf-8") as f:
            expected = json.load(f)
        text = self.report(os.path.join(BENCH_ROOT, "results", "run_2026-09-01"))
        scores = section(text, 2)
        arms = sorted(expected["means"])
        for dim in expected["means"][arms[0]]:
            cells = ["%.3f ± %.3f (n=%d)" % (expected["means"][a][dim], expected["sd"][a][dim], expected["n_scenarios"])
                     for a in arms]
            self.assertIn("| %s | %s |" % (DIMENSION_NAMES[dim], " | ".join(cells)), scores, dim)
        for arm, count in expected["missed"].items():
            self.assertRegex(section(text, 4), r"\| `%s` \| \d+ \| %d \|" % (re.escape(arm), count))

    # -- Test 2: leak check --------------------------------------------------
    def test_planted_rule_id_refuses_final_and_names_the_line(self):
        run = make_run(self.tmp, bench_version="v0.2.0 " + PLANTED_RULE)
        draft, data = self.draft(run)
        draft_line = next(i for i, l in enumerate(data.decode("utf-8").splitlines(), 1) if PLANTED_RULE in l)
        code, err = self.final(run, draft, self.verdict(data))
        self.assertEqual(code, 2)
        self.assertIn("report line %d matches deny-list entry on line 2" % draft_line, err)
        self.assertNotIn(PLANTED_RULE, err)
        self.assertFalse(os.path.exists(self.final_out))

    def test_clean_final_is_the_checked_draft_byte_for_byte(self):
        run = make_run(self.tmp)
        draft, data = self.draft(run)
        code, err = self.final(run, draft, self.verdict(data))
        self.assertEqual(code, 0, err)
        with open(self.final_out, "rb") as f:
            self.assertEqual(f.read(), data)
        self.assertNotIn(b"DRAFT", data)

    def test_cleared_item_counts_as_pass(self):
        run = make_run(self.tmp)
        draft, data = self.draft(run)
        code, err = self.final(run, draft, self.verdict(data, item_2="PASS (cleared by Yassen 2026-10-27)"))
        self.assertEqual(code, 0, err)

    def test_verdict_that_does_not_clear_the_draft_refuses(self):
        run = make_run(self.tmp)
        draft, data = self.draft(run)
        cases = {
            "stale hash": (dict(report_sha256="0" * 64), "does not match the verdict"),
            "do not push": (dict(item_5="FAIL", bottom_line="DO NOT PUSH"), "item_5 is FAIL"),
            "needs human": (dict(item_4="NEEDS HUMAN"), "item_4 is NEEDS HUMAN"),
            "other file": (dict(report_file="other.draft.md"), "the verdict is for other.draft.md"),
        }
        for name, (fields, message) in cases.items():
            code, err = self.final(run, draft, self.verdict(data, **fields))
            self.assertEqual(code, 2, name)
            self.assertIn(message, err, name)
            self.assertFalse(os.path.exists(self.final_out), name)

    def test_verdict_missing_who_when_or_commit_refuses(self):
        run = make_run(self.tmp)
        draft, data = self.draft(run)
        for key in ("checked_by", "checked_utc", "ip_check_commit"):
            code, err = self.final(run, draft, self.verdict(data, **{key: None}))
            self.assertEqual(code, 2, key)
            self.assertIn("verdict is missing: %s" % key, err)
        code, err = self.final(run, draft, self.verdict(data, ip_check_commit="abc123"))
        self.assertEqual(code, 2)
        self.assertIn("ip_check_commit is not in the expected form", err)

    def test_draft_edited_after_the_check_refuses(self):
        run = make_run(self.tmp)
        draft, data = self.draft(run)
        verdict = self.verdict(data)
        with open(draft, "ab") as f:
            f.write(b"edited\n")
        code, err = self.final(run, draft, verdict)
        self.assertEqual(code, 2)
        self.assertIn("not what this run renders", err)
        self.assertFalse(os.path.exists(self.final_out))

    def test_final_fails_closed_without_checks(self):
        run = make_run(self.tmp)
        draft, data = self.draft(run)
        verdict, deny = self.verdict(data), self.deny_list(PLANTED_RULE)
        for args in (("--verdict", verdict, "--deny-list", deny),
                     ("--draft", draft, "--deny-list", deny),
                     ("--draft", draft, "--verdict", verdict)):
            env = os.environ.pop("SAFE_CARE_DENY_LIST", None)
            try:
                code, err = run_cli(run, "--final", "--out", self.final_out, *args)
            finally:
                if env is not None:
                    os.environ["SAFE_CARE_DENY_LIST"] = env
            self.assertEqual(code, 2, args)
            self.assertFalse(os.path.exists(self.final_out))

    def test_deny_list_or_verdict_inside_repo_is_refused(self):
        run = make_run(self.tmp)
        draft, data = self.draft(run)
        inside = os.path.join(BENCH_ROOT, "README.md")
        for verdict, deny in ((self.verdict(data), inside), (inside, None)):
            code, err = self.final(run, draft, verdict, deny)
            self.assertEqual(code, 2)
            self.assertIn("outside the public bench repository", err)

    def test_draft_needs_a_draft_name_and_final_a_published_one(self):
        run = make_run(self.tmp)
        code, err = run_cli(run, "--out", self.final_out)
        self.assertEqual(code, 1)
        self.assertIn("must end in .draft.md", err)
        draft, data = self.draft(run)
        code, err = run_cli(run, "--final", "--draft", draft, "--verdict", self.verdict(data), "--out", draft,
                            "--deny-list", self.deny_list(PLANTED_RULE))
        self.assertEqual(code, 2)
        self.assertIn("must be the published name", err)

    def test_card_fields_outside_allow_list_never_reach_the_report(self):
        text = self.report(make_run(self.tmp))
        self.assertNotIn(FAKE_KB, text)
        self.assertNotIn("0123abc", text)
        self.assertNotIn(self.tmp, text)

    # -- Test 3: same input ---------------------------------------------------
    def test_same_input_gives_byte_identical_reports(self):
        run = make_run(self.tmp)
        second = os.path.join(self.tmp, "again.draft.md")
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

    def test_scores_csv_with_byte_order_mark_reads_the_same(self):
        run = make_run(self.tmp)
        plain = self.report(run)
        path = os.path.join(run, "scores", "per_row_scores.csv")
        with open(path, encoding="utf-8") as f:
            text = f.read()
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            f.write(text)
        self.assertEqual(self.report(run), plain)

    # -- Published run format ---------------------------------------------------
    def test_published_format_leaves_out_of_scope_scenarios_by_default(self):
        text = self.report(make_published_run(self.tmp))
        self.assertIn("- **Scenarios:** 1 (S001)", text)
        self.assertIn("- **Scenarios left out:** S003", text)
        self.assertIn("- **Conversations scored:** 6", text)
        self.assertIn("| Medical accuracy | 0.375 ± – (n=1) | 0.750 ± – (n=1) | 1.000 ± – (n=1) |", section(text, 2))

    def test_all_scenarios_matches_the_synthetic_run(self):
        code, err = run_cli(make_published_run(self.tmp), "--out", self.out, "--all-scenarios")
        self.assertEqual(code, 0, err)
        with open(self.out, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("- **Out-of-scope scenarios included:** S003", text)
        self.assertIn("- **Conversations scored:** 12", text)
        self.assertEqual(section(text, 2), section(self.report(make_run(self.tmp)), 2))

    def test_published_provenance_comes_from_manifests_and_card_tables(self):
        text = self.report(make_published_run(self.tmp))
        self.assertIn("- **Seeds:** not exposed by the provider", text)
        self.assertIn("- **Bench commit:** %s (tree dirty at run time)" % ("b" * 40), text)
        self.assertIn("- **Generation model:** `gen-model`", text)
        what_was_run = section(text, 6)
        self.assertIn("`%s`" % ("a1" * 32), what_was_run)
        self.assertIn("| Medical accuracy | `judge-model` | `%s` |" % ("m" * 64), what_was_run)
        self.assertIn("per-scenario sha256 for 2 scenarios, identical in every manifest", what_was_run)
        self.assertNotIn("deadbee", text)

    def test_missed_escalations_note_when_the_run_did_not_apply_the_override(self):
        missed = section(self.report(make_published_run(self.tmp)), 4)
        self.assertIn("**This report applies the override; the run did not.**", missed)
        self.assertNotIn("the run did not", section(self.report(make_run(self.tmp)), 4))

    def test_all_seven_sections_in_order(self):
        text = self.report(make_run(self.tmp))
        headings = re.findall(r"^## (\d)\. ", text, re.M)
        self.assertEqual(headings, list("1234567"))
        self.assertIn("Judge not calibrated against clinicians for this domain; treat scores as indicative.", text)


if __name__ == "__main__":
    unittest.main()
