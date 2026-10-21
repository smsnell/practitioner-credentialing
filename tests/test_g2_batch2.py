"""Read-only checks of the actual B2 candidate and its sealed B1 predecessor."""

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
B1_SHA256 = "12f14f34275cd712c3ac1551a30e6358cbca67bf1cea51cf053dd12a86a62932"


def read_json(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class ActualBatchTwoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.one = read_json("deliverables/snapshots/batch-01.json")
        cls.two = read_json("deliverables/snapshots/batch-02.json")
        cls.h1 = read_json("deliverables/working/batch-01/history.json")
        cls.h2 = read_json("deliverables/working/batch-02/history.json")
        cls.apps = {row["application_id"]: row for row in cls.two["applications"]}

    def app(self, number):
        return self.apps["APP-2026-" + number]

    def history(self, number):
        return self.h2["applications"]["APP-2026-" + number]

    def assessment(self, number):
        return self.history(number)["assessments"][-1]

    def test_exact_predecessor_hash_and_sealed_b1_unchanged(self):
        path = "deliverables/snapshots/batch-01.json"
        self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), B1_SHA256)
        self.assertEqual(self.two["predecessor"], {"path": path, "sha256": B1_SHA256})
        self.assertEqual(self.two["batch"], 2)
        self.assertEqual(self.two["as_of"], "2026-04-20")

    def test_cumulative_caseload_revisions_decisions_and_no_invented_readiness(self):
        self.assertEqual(len(self.apps), 40)
        self.assertEqual(sum(len(row["revisions"]) for row in self.h2["applications"].values()), 45)
        self.assertEqual(sum(len(row["decisions"]) for row in self.apps.values()), 35)
        for app in self.apps.values():
            with self.subTest(application=app["application_id"]):
                self.assertFalse(app["packet_presentable"])
                self.assertIsNone(app["approval_decision_id"])
                self.assertIsNone(app["activation"])
                self.assertTrue(all(not decision["admitted"] for decision in app["decisions"]))

    def test_prior_public_decisions_and_history_are_exact_prefixes(self):
        prior_apps = {row["application_id"]: row for row in self.one["applications"]}
        for app_id, prior in self.h1["applications"].items():
            current = self.h2["applications"][app_id]
            with self.subTest(application=app_id):
                self.assertEqual(self.apps[app_id]["decisions"][:len(prior_apps[app_id]["decisions"])], prior_apps[app_id]["decisions"])
                for key in ("assessments", "readiness_history", "revisions", "decisions"):
                    self.assertEqual(current[key][:len(prior[key])], prior[key])
                self.assertEqual(current["first_received_date"], prior["first_received_date"])

    def test_referees_carry_across_four_new_revisions(self):
        for number in ("018", "030", "031", "036"):
            assessed = self.assessment(number)
            with self.subTest(application=number):
                self.assertEqual(self.app(number)["revision"], 2)
                self.assertNotIn("two named referees", assessed["intake"]["missing"])
                prior = self.h1["applications"]["APP-2026-" + number]["assessments"][-1]
                self.assertTrue({row["referee_id"] for row in prior["peer_checks"]}.issubset(
                    {row["referee_id"] for row in assessed["peer_checks"]}))

    def test_recorded_intake_deadlines_are_not_reset(self):
        self.assertEqual(self.app("019")["status"], "ineligible-clock-expired")
        notice = self.assessment("019")["intake"]["notices"]
        self.assertEqual([(row["date"], row["due"]) for row in notice], [("2026-02-18", "2026-03-20")])
        self.assertEqual(self.app("018")["status"], "returned-incomplete")
        self.assertTrue(any(row["due"] == "2026-04-05" and row["returned"]
                            for row in self.assessment("018")["intake"]["notices"]))
        conflict = next(row for row in self.assessment("018")["issues"] if row["kind"] == "discrepancy")
        self.assertIn("Harrowgate", conflict["detail"])
        self.assertIn("Silverbeck", conflict["detail"])

    def test_app017_authority_does_not_supply_missing_specific_explanation(self):
        disposition = self.assessment("017")["clinical_dispositions"][0]
        self.assertTrue(disposition["authorized"])
        self.assertEqual(disposition["missing_explanation_dates"], ["2026-02-24"])
        self.assertFalse(disposition["gap_cleared"])
        self.assertEqual(self.app("017")["elements"]["gaps"], "routed-to-clinical-director")

    def test_app032_disposition_retains_high_risk_finding_without_global_readiness(self):
        disposition = self.assessment("032")["clinical_dispositions"][0]
        self.assertTrue(disposition["authorized"])
        self.assertEqual(disposition["ppq_codes"], ["PPQ-2"])
        finding = next(row for row in self.assessment("032")["issues"]
                       if row["kind"] == "finding" and "PPQ-2" in row["detail"])
        self.assertIn(disposition["path"], finding["clinical_disposition_sources"])
        self.assertFalse(self.app("032")["packet_presentable"])

    def test_terminal_sources_are_distinguished_from_offer_to_amend(self):
        self.assertEqual(self.app("028")["status"], "withdrawn")
        self.assertEqual(self.app("029")["status"], "discontinued")
        terminal = self.assessment("029")["clinical_dispositions"][0]
        self.assertTrue(terminal["authorized"])
        self.assertEqual(terminal["terminal"], "discontinued")
        self.assertTrue(any(row["kind"] == "discrepancy" and "recipient conflicts" in row["detail"]
                            for row in self.assessment("029")["issues"]))
        offered = self.assessment("027")["clinical_dispositions"][0]
        self.assertTrue(offered["authorized"] and offered["amendment_offered"])
        self.assertIsNone(offered["terminal"])
        self.assertNotEqual(self.app("027")["status"], "discontinued")
        self.assertTrue(any(row["kind"] == "discrepancy" and "2001-07-15" in row["detail"]
                            and "2009-07-15" in row["detail"] for row in self.assessment("027")["issues"]))

    def test_app030_revised_dates_reconcile_without_rewriting_source_or_verifying_new_entry(self):
        checks = {row["entry_id"]: row for row in self.assessment("030")["entry_checks"]}
        reconciled = checks["ENT-3002"]
        self.assertTrue(reconciled["dates_verified"])
        self.assertFalse(reconciled["unresolved_discrepancy"])
        self.assertEqual(reconciled["accepted_reply_ids"], ["VR-3002"])
        self.assertEqual(reconciled["declared"]["to_date"], "2021-11-30")
        self.assertEqual(reconciled["verification_rows"][0]["outcome"], "confirmed-with-discrepancy")
        self.assertFalse(checks["ENT-3090"]["dates_verified"])
        self.assertEqual(checks["ENT-3090"]["accepted_reply_ids"], [])
        prior = self.h1["applications"]["APP-2026-030"]["assessments"][-1]
        old = next(row for row in prior["entry_checks"] if row["entry_id"] == "ENT-3002")
        self.assertTrue(old["unresolved_discrepancy"])
        self.assertEqual(old["declared"]["to_date"], "2022-08-31")

    def test_app031_licence_resolves_without_filling_other_missing_evidence(self):
        app = self.app("031")
        self.assertEqual(app["revision"], 2)
        self.assertEqual(app["elements"]["licensure"], "resolved")
        self.assertEqual(app["elements"]["education"], "outstanding")
        self.assertEqual(app["elements"]["references"], "outstanding")
        self.assertFalse(app["packet_presentable"])

    def test_app036_conflicting_revision_period_retained_without_future_reply(self):
        assessed = self.assessment("036")
        discrepancy = next(row for row in assessed["issues"] if row["kind"] == "discrepancy")
        self.assertIn("2019–2025", discrepancy["detail"])
        self.assertIn("ENT-3602", discrepancy["detail"])
        self.assertIn("2012-07-16", discrepancy["detail"])
        self.assertNotIn("VR-3604", {row["reply_id"] for row in self.h2["raw_tables"]["verification-replies"]})
        checks = {row["entry_id"]: row for row in assessed["entry_checks"]}
        self.assertEqual(checks["ENT-3602"]["accepted_reply_ids"], [])
        self.assertEqual(checks["ENT-3603"]["accepted_reply_ids"], ["VR-3603"])

    def test_app025_peers_remain_current_at_actual_b2_date_but_have_no_direct_provenance(self):
        peers = self.assessment("025")["peer_checks"]
        self.assertEqual({row["reply"]["signature_date"] for row in peers}, {"2024-05-05", "2024-05-20"})
        self.assertTrue(all(row["eligible"] is True for row in peers))
        self.assertTrue(all(not row["usable"] and not row["provenance_verified"] for row in peers))
        self.assertTrue(all(any("provenance" in failure for failure in row["failures"]) for row in peers))

    def test_gbd039_explicit_condition_dates_retained_but_not_activated(self):
        decision = next(row for row in self.history("039")["decisions"] if row["fields"]["decision_id"] == "GBD-2026-039")
        source = self.h2["raw_documents"][decision["source"]]
        self.assertIn("due 2026-11-30", source)
        self.assertIn("due 2026-06-30", source)
        self.assertEqual({row["due"] for row in decision["conditions"]}, {"2026-11-30", "2026-06-30"})
        self.assertFalse(decision["admitted"])
        self.assertIsNone(self.app("039")["activation"])
        self.assertEqual(self.app("039")["monitored_conditions"], [])

    def test_all_35_refusals_have_one_owned_escalation_without_invented_due_date(self):
        count = 0
        for app in self.apps.values():
            for decision in app["decisions"]:
                count += 1
                matches = [row for row in app["action_queue"]
                           if row["owner"] in {"MSP", "Medical Services Professional"}
                           and decision["decision_id"] in row["item"] and decision["reason"] in row["item"]]
                with self.subTest(decision=decision["decision_id"]):
                    self.assertEqual(len(matches), 1)
                    self.assertIsNone(matches[0]["due"])
        self.assertEqual(count, 35)


if __name__ == "__main__":
    unittest.main()
