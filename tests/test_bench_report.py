# -*- coding: utf-8 -*-
"""
Tests for bench_report. Run from the repository root:

    python -m unittest discover -s tests

The fixture is a synthetic run built here in the published run format, with
hand-checkable numbers. It holds no data from any real run. Test 1 against `results/run_2026-09-01` runs only when
that directory and `tests/expected/run_2026-09-01.json` are both present.
"""

import contextlib, csv, hashlib, io, json, os, re, shutil, tempfile, unittest

from bench_report.__main__ import main
from bench_report.report import DIMENSION_NAMES, build_context, missed_escalations
from bench_report.run import BENCH_ROOT, load
from bench_report.shapes import text_hits

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
    ("A2", "S003", 2): (None, 1.0, 1.0),   # unscored: excluded from n
}
DIMS = ("medical_accuracy", "escalation_singleturn", "escalation_multiturn")
SCORE_HEADER = ["scenario_id", "tier", "dimension", "judge_model", "replicate", "run_id", "score",
                "scenario_in_A0_A2_scope"]

ENGINE_COMMIT = "deadbeef" * 5
MANIFEST_ENGINE_COMMIT = "f00dfac"


def make_run(root, name="run_test", s003_in_scope=True, model="gen-model-2026-01-01", seed="42",
             bench="b" * 40, engine=ENGINE_COMMIT, sections=False, hard_fail_fired=None, corpus=False):
    """A synthetic run in the published layout: a prose run card with tables (and a
    key block holding fields outside the allow-list), a scores file with the
    published columns, and manifests carrying a provenance block."""
    run = os.path.join(root, name)
    os.makedirs(os.path.join(run, "scores"))
    os.makedirs(os.path.join(run, "manifests"))
    card = ("# Run card - test\n\n```\n"
            "produced_utc:         2026-10-01T00:00:00Z\n"
            "kb_id_base:           " + FAKE_KB + "\n"
            "runner_code_ref:      0123abc   # engine commit\n"
            "```\n\n")
    if sections:
        card += "## 2. Models\n\nAn alias only.\n\n"
    card += "## 3. Determinism\n\n| | |\n|---|---|\n| Seed | " + seed + " |\n\n"
    card += "## 4. Provenance\n\n| Repo | Commit | Clean? |\n|---|---|---|\n"
    if engine:
        card += "| Engine | `" + engine + "` | **dirty** |\n"
    card += "| Bench | `" + bench + "` | **dirty** |\n\n"
    if sections:
        card += ("## 5. Retrieval\n\n### Two declared divergences from the published specification\n\n"
                 "## 8. Known defects in this run\n\n1. Something.\n")
    with open(os.path.join(run, "RUN_CARD.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(card)
    with open(os.path.join(run, "scores", "per_row_scores.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SCORE_HEADER)
        w.writeheader()
        for (arm, scenario, rep), values in sorted(SCORES.items()):
            for dim, value in zip(DIMS, values):
                w.writerow({"scenario_id": scenario, "tier": arm, "dimension": dim, "judge_model": "judge-model",
                            "replicate": "R%d" % rep, "run_id": "%s-%d" % (arm, rep),
                            "score": "" if value is None else value,
                            "scenario_in_A0_A2_scope": s003_in_scope or scenario != "S003"})
    for arm in ("A0", "A1", "A2"):
        provenance = {
            "engine": {"commit": MANIFEST_ENGINE_COMMIT},
            "agent": {"id": arm, "spec_hash": arm.lower() * 32},
            "model": {"model_id": model},
            "scenarios": {"scenarios": {"S001": "1" * 64, "S003": "3" * 64}},
            "judge": {d: {"model_id": "judge-model", "prompt_hash": "abc"[i] * 64} for i, d in enumerate(DIMS)},
        }
        if hard_fail_fired is not None:
            provenance["execution"] = {"hard_fail_fired": hard_fail_fired}
        if corpus:
            # As corpus integrity writes it: A0 retrieves nothing; the internal ids must not surface.
            retrieves = arm != "A0"
            provenance["corpus"] = {"set": "base" if retrieves else None, "digest": "d" * 64 if retrieves else None}
            provenance.setdefault("execution", {})["corpus"] = (
                {"verified": True, "internal_job": "JOB-INTERNAL", "internal_source": "DS-INTERNAL"}
                if retrieves else {"verified": "not_applicable"})
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
        self.assertIn("- **Conversations scored:** 12", text)
        self.assertIn("### `A0` → `A1`: Grounding (capability bundle)", text)
        self.assertIn("### `A1` → `A2`: Safety control (single capability)", text)
        # paired by scenario: S001 +0.375, S003 +0.125; t on 1 df is 12.706, SD 0.177, n 2
        self.assertIn("| Medical accuracy | 0.375 | 0.625 | +0.250 (n=2) | [-1.338, +1.838] | 2 / 0 / 0 |",
                      section(text, 3))
        missed = section(text, 4)
        self.assertIn("| `A0` | 2 | 2 | 1 | 0 | S001 ×2 |", missed)
        self.assertIn("| `A1` | 2 | 1 | 0 | 0 | S001 ×1 |", missed)
        self.assertIn("| `A2` | 2 | 0 | 0 | 0 | none |", missed)
        self.assertIn("| `A0` | S001 | R1 | Escalation, single-turn and Escalation, multi-turn |", missed)
        self.assertIn("| `A0` | S001 | R2 | Escalation, multi-turn |", missed)
        self.assertIn("| `A1` | S001 | R2 | Escalation, single-turn |", missed)
        self.assertNotIn("S003", missed)

    def test_paired_difference_that_does_not_move_prints_plus_zero(self):
        text = self.report(make_run(self.tmp))
        # escalation_multiturn at A1 and A2 is 1.0 in every scenario
        self.assertIn("| Escalation, multi-turn | 1.000 | 1.000 | +0.000 (n=2) | [+0.000, +0.000] | 0 / 0 / 2 |",
                      section(text, 3))
        self.assertNotIn("-0.000", text)

    def test_t_critical_values(self):
        from bench_report.report import _t_975
        self.assertEqual(_t_975(8), 2.306)
        # beyond the table: the expansion stays within 0.001 of the exact values 2.021 and 2.000
        self.assertAlmostEqual(_t_975(40), 2.021, delta=0.001)
        self.assertAlmostEqual(_t_975(60), 2.000, delta=0.001)

    @unittest.skipUnless(
        os.path.isdir(os.path.join(BENCH_ROOT, "results", "run_2026-09-01"))
        and os.path.isfile(os.path.join(BENCH_ROOT, "tests", "expected", "run_2026-09-01.json")),
        "needs results/run_2026-09-01 and tests/expected/run_2026-09-01.json")
    def test_numbers_run_2026_09_01(self):
        """Every mean and SD matches the run's published scenario-level analysis, the
        paired differences match the paper's Table 1, and S001/S002 have no misses."""
        with open(os.path.join(BENCH_ROOT, "tests", "expected", "run_2026-09-01.json"), encoding="utf-8") as f:
            expected = json.load(f)
        run_dir = os.path.join(BENCH_ROOT, "results", "run_2026-09-01")
        text = self.report(run_dir)
        scores = section(text, 2)
        arms = sorted(expected["means"])
        for dim in expected["means"][arms[0]]:
            cells = ["%.3f ± %.3f (n=%d)" % (expected["means"][a][dim], expected["sd"][a][dim], expected["n_scenarios"])
                     for a in arms]
            self.assertIn("| %s | %s |" % (DIMENSION_NAMES[dim], " | ".join(cells)), scores, dim)

        differences = section(text, 3)
        for row in expected["paired_table_1"]:
            step = re.search(r"^### `%s` → `%s`.*?(?=^### |\Z)" % (row["lo"], row["hi"]), differences, re.S | re.M)
            self.assertIsNotNone(step, row)
            cells = "| %+.3f (n=%d) | [%+.3f, %+.3f] | %d / %d / %d |" % (
                row["mean"], expected["n_scenarios"], row["ci"][0], row["ci"][1], row["up"], row["down"], row["same"])
            self.assertRegex(step.group(0), r"\| %s \| [\d.]+ \| [\d.]+ %s"
                             % (re.escape(DIMENSION_NAMES[row["dimension"]]), re.escape(cells)))

        run = load(run_dir)
        missed = missed_escalations(run, build_context(run))
        clean = expected["no_misses"]
        self.assertEqual(len({(r["arm"], r["scenario"], r["conversation"]) for r in run["rows"]
                              if r["scenario"] in clean["scenarios"]}), clean["conversations"])
        self.assertEqual([m for a in missed.values() for m in a["misses"] if m[0] in clean["scenarios"]], [])
        both = [[a, s, c] for a, m in sorted(missed.items()) for s, c, zero in m["misses"] if len(zero) == 2]
        self.assertEqual(both, expected["both_judges_zero"])
        self.assertIn("**S006:** the multi-turn escalation judge reads only the turn", section(text, 4))

    # -- Test 2: leak check --------------------------------------------------
    def test_planted_rule_id_refuses_final_and_names_the_line(self):
        run = make_run(self.tmp, seed="42 " + PLANTED_RULE)
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

    # -- Shape checks -----------------------------------------------------------
    def test_shape_rules_catch_synthetic_identifiers(self):
        # every value here is made up; none comes from any real run or account
        planted = {
            "10-character resource id": "kb FAKEKB0001 here",
            "ARN": "arn:aws:bedrock:us-east-1:000000000000:knowledge-base/x",
            "storage URL": "see s3://example-bucket/path",
            "AWS access key": "AKIAEXAMPLEEXAMPLE00",
            "AWS account id": "account 000000000000",
            "UUID": "run 00000000-0000-4000-8000-000000000000",
            "base64 blob": "Zm9vYmFyRXhhbXBsZUJhc2U2NFN0cmluZzEyMzQ1",
            "email address": "someone@example.com",
            "local path": r"C:\Users\someone\run",
            "long hex outside an allowed hash": "hash " + "ab" * 32,
        }
        for rule, line in planted.items():
            self.assertIn((1, rule), text_hits(line), rule)

    def test_shape_rules_allow_what_reports_print(self):
        allowed = [
            "| `A0` | `%s` | **none recorded** | gpt-4o-mini |" % ("a0" * 32),
            "- **Bench commit:** `%s` (tree dirty at run time)" % ("e" * 40),
            "- **Run dates:** first call 2026-09-01T16:26:57.586955Z",
            "| Medical accuracy | 0.741 ± 0.028 (n=9) | 0.6583333333333333 |",
            "| `A1` | 15 | 4 | 0 | 0 | S006 ×3, S012 ×1 |",
            "| `A1` | S012 | R3 | Escalation, single-turn |",
            "| Medical accuracy | 0.769 | 0.611 | -0.157 (n=9) | [-0.312, -0.002] | 0 / 6 / 3 |",
            "- **Generation model:** `gpt-4o-mini` (alias; no dated snapshot recorded, see run card §2)",
            "- **Engine commit (private repository):** `%s` (tree dirty at run time)" % ("d" * 40),
            "GUARDRAILS ESCALATION",   # ten capital letters, no digit: a word, not an id
        ]
        for line in allowed:
            self.assertEqual(text_hits(line), [], line)

    @unittest.skipUnless(os.path.isdir(os.path.join(BENCH_ROOT, "results", "run_2026-09-01")),
                         "needs results/run_2026-09-01")
    def test_no_shape_findings_on_the_published_run(self):
        run = os.path.join(BENCH_ROOT, "results", "run_2026-09-01")
        for extra in ((), ("--all-scenarios",)):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(main([run, "--out", self.out] + list(extra)), 0)
            self.assertNotIn("shape check", out.getvalue(), extra)

    def test_planted_id_warns_on_draft_and_refuses_final_without_echoing_it(self):
        run = make_run(self.tmp, bench="v0.2.0 " + FAKE_KB)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(main([run, "--out", self.out]), 0)
        self.assertIn("warning: shape check, field run card bench_commit: unexpected shape", out.getvalue())
        self.assertRegex(out.getvalue(), r"report line \d+: 10-character resource id")
        with open(self.out, "rb") as f:
            data = f.read()
        code, err = self.final(run, self.out, self.verdict(data))
        self.assertEqual(code, 2)
        self.assertIn("10-character resource id", err)
        self.assertNotIn(FAKE_KB, err + out.getvalue())
        self.assertFalse(os.path.exists(self.final_out))

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
        what_was_run = section(self.report(make_run(self.tmp)), 6)
        self.assertIn("**No corpus digest is recorded for `A0`, `A1`, `A2`.**", what_was_run)
        self.assertIn("not recorded; this run has no corpus preflight result", what_was_run)
        self.assertNotRegex(what_was_run, r"\|[ \t]*\|")

    # -- Test 5: corpus digest and preflight, when the run records them ----------
    def test_recorded_corpus_digest_and_preflight_are_printed(self):
        text = self.report(make_run(self.tmp, corpus=True))
        what_was_run = section(text, 6)
        self.assertIn("| `A0` | `%s` | none: this arm retrieves nothing |" % ("a0" * 32), what_was_run)
        self.assertIn("`%s` (set base)" % ("d" * 64), what_was_run)
        self.assertIn("- **Corpus verified by preflight:** `A0` not_applicable; `A1` true; `A2` true", what_was_run)
        self.assertNotIn("No corpus digest is recorded", what_was_run)
        for internal in ("JOB-INTERNAL", "DS-INTERNAL"):
            self.assertNotIn(internal, text)

    # -- Format guards ---------------------------------------------------------
    def test_scores_without_the_published_columns_are_refused(self):
        run = make_run(self.tmp)
        path = os.path.join(run, "scores", "per_row_scores.csv")
        with open(path, encoding="utf-8") as f:
            text = f.read()
        header, rest = text.split("\n", 1)
        renamed = header.replace("tier", "arm").replace("replicate", "repeat")
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(renamed + "\n" + rest)
        code, err = run_cli(run, "--out", self.out)
        self.assertEqual(code, 1)
        self.assertIn("per_row_scores.csv is not in the published run format: it has no column tier, replicate", err)
        self.assertFalse(os.path.exists(self.out))

    def test_mixed_judges_must_be_chosen(self):
        run = make_run(self.tmp)
        path = os.path.join(run, "scores", "per_row_scores.csv")
        with open(path, encoding="utf-8") as f:
            text = f.read()
        with open(path, "a", encoding="utf-8", newline="") as f:
            f.write(text.splitlines()[1].replace(",judge-model,", ",judge-model-b,") + "\n")
        code, err = run_cli(run, "--out", self.out)
        self.assertEqual(code, 1)
        self.assertIn("choose one with --judge", err)
        self.assertEqual(run_cli(run, "--out", self.out, "--judge", "judge-model")[0], 0)

    def test_scores_csv_with_byte_order_mark_reads_the_same(self):
        run = make_run(self.tmp)
        plain = self.report(run)
        path = os.path.join(run, "scores", "per_row_scores.csv")
        with open(path, encoding="utf-8") as f:
            text = f.read()
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            f.write(text)
        self.assertEqual(self.report(run), plain)

    # -- Run card, scope and provenance ------------------------------------------
    def test_out_of_scope_scenarios_are_left_out_by_default(self):
        text = self.report(make_run(self.tmp, s003_in_scope=False))
        self.assertIn("- **Scenarios:** 1 (S001)", text)
        self.assertIn("- **Scenarios left out:** S003", text)
        self.assertIn("- **Conversations scored:** 6", text)
        self.assertIn("| Medical accuracy | 0.375 ± – (n=1) | 0.750 ± – (n=1) | 1.000 ± – (n=1) |", section(text, 2))

    def test_all_scenarios_matches_the_run_with_every_scenario_in_scope(self):
        scoped = make_run(self.tmp, name="run_scoped", s003_in_scope=False)
        code, err = run_cli(scoped, "--out", self.out, "--all-scenarios")
        self.assertEqual(code, 0, err)
        with open(self.out, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("- **Out-of-scope scenarios included:** S003", text)
        self.assertIn("- **Conversations scored:** 12", text)
        self.assertEqual(section(text, 2), section(self.report(make_run(self.tmp)), 2))

    def test_provenance_comes_from_manifests_and_card_tables(self):
        text = self.report(make_run(self.tmp, model="gen-model", seed="**not exposed by the provider**",
                                    sections=True))
        self.assertIn("- **Seeds:** not exposed by the provider", text)
        self.assertIn("- **Bench commit:** `%s` (tree dirty at run time)" % ("b" * 40), text)
        self.assertIn("- **Engine commit (private repository):** `%s` (tree dirty at run time)" % ENGINE_COMMIT, text)
        self.assertIn("- **Generation model:** `gen-model` (alias; no dated snapshot recorded, see run card §2)", text)
        self.assertIn("- **Judge model:** `judge-model` (alias; no dated snapshot recorded, see run card §2)", text)
        what_was_run = section(text, 6)
        self.assertIn("| Arm | Agent spec hash |", what_was_run)
        self.assertIn("`%s`" % ("a1" * 32), what_was_run)
        self.assertIn("| Medical accuracy | `judge-model` | `%s` |" % ("a" * 64), what_was_run)
        self.assertIn("per-scenario sha256 for 2 scenarios, identical in every manifest", what_was_run)
        # the engine commit comes from the run card only, never from a manifest
        self.assertNotIn(MANIFEST_ENGINE_COMMIT, text)

    def test_dated_model_has_no_alias_note_and_unrecorded_engine_commit_is_stated(self):
        text = self.report(make_run(self.tmp, engine=None))
        self.assertIn("- **Generation model:** `gen-model-2026-01-01`\n", text)
        self.assertIn("- **Engine commit (private repository):** not recorded in the run card or manifests", text)

    def test_limitations_point_to_the_run_cards_defects_and_divergences(self):
        limitations = section(self.report(make_run(self.tmp, name="run_sections", sections=True)), 7)
        self.assertIn("Defects specific to this run are in its run card: §8 for its known defects and §5 for its "
                      "declared divergences from the published specification.", limitations)
        self.assertNotIn("Defects specific", section(self.report(make_run(self.tmp)), 7))

    def test_missed_escalations_note_when_the_run_did_not_apply_the_override(self):
        missed = section(self.report(make_run(self.tmp, name="run_no_override", hard_fail_fired=False)), 4)
        self.assertIn("**This report applies the override; the run did not.**", missed)
        self.assertNotIn("the run did not", section(self.report(make_run(self.tmp)), 4))

    def test_all_seven_sections_in_order(self):
        text = self.report(make_run(self.tmp))
        headings = re.findall(r"^## (\d)\. ", text, re.M)
        self.assertEqual(headings, list("1234567"))
        self.assertIn("Judge not calibrated against clinicians for this domain; treat scores as indicative.", text)


if __name__ == "__main__":
    unittest.main()
