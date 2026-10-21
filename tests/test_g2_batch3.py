"""Read-only actual B3 checks and explicitly synthetic disposition controls."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

from credentialing.dispositions import clinical_dispositions
from credentialing.dates import peer_current
from credentialing.documents import indexed_documents, parse_document
from credentialing.io import load_batch, load_sources
from credentialing.policy import registry


ROOT = Path(__file__).resolve().parents[1]
B2_SHA256 = "9fb37f39bbe58cb36a144d2c381d2b1c41c49208af81932f8bd4ef7c83e11cf5"


def read_json(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class ActualBatchThreeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.two = read_json("deliverables/snapshots/batch-02.json")
        cls.three = read_json("deliverables/snapshots/batch-03.json")
        cls.h2 = read_json("deliverables/working/batch-02/history.json")
        cls.h3 = read_json("deliverables/working/batch-03/history.json")
        cls.apps = {row["application_id"]: row for row in cls.three["applications"]}

    def app(self, number):
        return self.apps["APP-2026-" + number]

    def assessment(self, number):
        return self.h3["applications"]["APP-2026-" + number]["assessments"][-1]

    def test_sealed_predecessor_and_cumulative_inventory(self):
        path = "deliverables/snapshots/batch-02.json"
        self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), B2_SHA256)
        self.assertEqual(self.three["predecessor"], {"path": path, "sha256": B2_SHA256})
        self.assertEqual((self.three["batch"], self.three["as_of"]), (3, "2026-05-18"))
        self.assertEqual(len(self.apps), 40)
        self.assertEqual(sum(len(row["revisions"]) for row in self.h3["applications"].values()), 46)
        self.assertEqual(sum(len(row["decisions"]) for row in self.apps.values()), 56)
        self.assertTrue(all(not row["packet_presentable"] and row["approval_decision_id"] is None
                            and row["activation"] is None for row in self.apps.values()))

    def test_entire_b2_history_and_public_decisions_remain_exact_prefixes(self):
        prior_apps = {row["application_id"]: row for row in self.two["applications"]}
        for app_id, old in self.h2["applications"].items():
            current = self.h3["applications"][app_id]
            with self.subTest(application=app_id):
                for field in ("assessments", "readiness_history", "decisions", "revisions"):
                    self.assertEqual(current[field][:len(old[field])], old[field])
                self.assertEqual(current["first_received_date"], old["first_received_date"])
                self.assertEqual(self.apps[app_id]["decisions"][:len(prior_apps[app_id]["decisions"])], prior_apps[app_id]["decisions"])

    def test_all_refusals_have_one_msp_action_without_invented_deadline(self):
        count = 0
        for app in self.apps.values():
            for decision in app["decisions"]:
                count += 1
                with self.subTest(decision=decision["decision_id"]):
                    self.assertFalse(decision["admitted"])
                    actions = [row for row in app["action_queue"]
                               if row["owner"] in {"MSP", "Medical Services Professional"}
                               and decision["decision_id"] in row["item"] and decision["reason"] in row["item"]]
                    self.assertEqual(len(actions), 1)
                    self.assertIsNone(actions[0]["due"])
        self.assertEqual(count, 56)

    def test_app015_review_retains_restriction_and_original_no_as_separate_discrepancy(self):
        app, assessed = self.app("015"), self.assessment("015")
        self.assertEqual(app["revision"], 1)
        declared = [row for row in self.h3["raw_tables"]["application-disclosures"]
                    if row["application_id"] == app["application_id"] and row["question_code"] == "PPQ-1"]
        self.assertEqual([(row["revision"], row["answer"]) for row in declared], [("1", "No")])
        disposition = next(row for row in assessed["clinical_dispositions"] if "Licensure finding" in row["topic"])
        self.assertTrue(disposition["authorized"])
        self.assertTrue(disposition["licensure_review_recorded"])
        self.assertEqual(set(disposition["finding_sources"]), {
            "letters/2026-03-04_board-action_APP-2026-015.md",
            "letters/2026-04-20_confirm-disclosure-reply_APP-2026-015.md"})
        findings = [row for row in assessed["issues"] if row["element"] == "licensure" and row["kind"] == "finding"]
        self.assertTrue(findings)
        self.assertTrue(all(row["owner"] == "Medical Services Professional" for row in findings))
        self.assertTrue(all(disposition["path"] in row["clinical_disposition_sources"] for row in findings))
        discrepancies = [row for row in assessed["issues"] if row["element"] == "licensure" and row["kind"] == "discrepancy"]
        self.assertTrue(discrepancies)
        self.assertTrue(all(row["owner"] == "Applicant" for row in discrepancies))
        self.assertEqual(app["elements"]["licensure"], "outstanding")
        self.assertFalse(app["packet_presentable"])

    def test_app025_one_peer_stale_one_current_both_still_lack_direct_provenance(self):
        peers = {row["reply_id"]: row for row in self.assessment("025")["peer_checks"]}
        self.assertEqual(peers["RR-2500"]["reply"]["signature_date"], "2024-05-05")
        self.assertFalse(peers["RR-2500"]["eligible"])
        self.assertTrue(any("not current" in text for text in peers["RR-2500"]["failures"]))
        self.assertEqual(peers["RR-2501"]["reply"]["signature_date"], "2024-05-20")
        self.assertTrue(peers["RR-2501"]["eligible"])
        self.assertTrue(all(not row["usable"] and not row["provenance_verified"] for row in peers.values()))

    def test_app027_family_medicine_revision_replaces_wait_for_old_amendment(self):
        app, assessed = self.app("027"), self.assessment("027")
        self.assertEqual(app["revision"], 2)
        self.assertEqual(assessed["application"]["discipline"], "Family Medicine")
        requested = [row["privilege_code"] for row in self.h3["raw_tables"]["privilege-requests"]
                     if row["application_id"] == app["application_id"] and row["revision"] == "2"]
        self.assertEqual(requested, ["PRIV-FM"])
        self.assertFalse(any("await applicant choice" in row["detail"] for row in assessed["issues"]))
        self.assertNotEqual(app["status"], "discontinued")
        self.assertFalse(app["packet_presentable"])

    def test_late_verification_stays_on_changed_entry_and_period_conflict_remains(self):
        checks = {row["entry_id"]: row for row in self.assessment("036")["entry_checks"]}
        self.assertNotIn("VR-3604", checks["ENT-3603"]["accepted_reply_ids"])
        late = next(row for row in checks["ENT-3602"]["verification_rows"] if row["reply_id"] == "VR-3604")
        self.assertEqual(late["entry_id"], "ENT-3602")
        self.assertEqual((late["verified_from"], late["verified_to"]), ("2012-07-16", "2019-08-31"))
        self.assertFalse(any(row["reply_id"] == "VR-3604" for row in checks["ENT-3603"]["verification_rows"]))
        self.assertTrue(any(row["kind"] == "discrepancy" and "2019–2025" in row["detail"]
                            and "ENT-3602" in row["detail"] for row in self.assessment("036")["issues"]))

    def test_missing_specific_explanation_and_other_source_conflicts_remain(self):
        disposition = self.assessment("017")["clinical_dispositions"][0]
        self.assertEqual(disposition["missing_explanation_dates"], ["2026-02-24"])
        self.assertFalse(disposition["gap_cleared"])
        self.assertEqual(self.app("017")["elements"]["gaps"], "routed-to-clinical-director")
        self.assertTrue(any(row["kind"] == "discrepancy" and "Harrowgate" in row["detail"]
                            and "Silverbeck" in row["detail"] for row in self.assessment("018")["issues"]))
        self.assertTrue(any(row["kind"] == "discrepancy" and "recipient conflicts" in row["detail"]
                            for row in self.assessment("029")["issues"]))
        self.assertEqual((self.app("028")["status"], self.app("029")["status"]), ("withdrawn", "discontinued"))

    def test_new_inbound_name_conflict_and_prior_outbound_conflict_are_preserved(self):
        documents = self.h3["raw_documents"]
        path = next(path for path in documents if path.startswith("letters/2026-04-24_") and "APP-2026-034" in path)
        source = (ROOT / "inputs/batch-03" / path).read_text(encoding="utf-8-sig")
        self.assertEqual(documents[path], source)
        self.assertIn("**From:** Dr. Ingrid Solheim, MD", source)
        self.assertIn("**Applicant:** Dr. Ingrid Lindholm, MD", source)
        self.assertTrue(source.rstrip().endswith("Ingrid Lindholm, MD"))
        prior_issues = self.h2["applications"]["APP-2026-034"]["assessments"][-1]["issues"]
        self.assertTrue(any(row["kind"] == "discrepancy" for row in prior_issues))
        self.assertTrue(any(row["kind"] == "discrepancy" for row in self.assessment("034")["issues"]))

    def test_stale_peer_letter_boundary_wording_is_retained_without_overriding_inclusive_rule(self):
        documents = self.h3["raw_documents"]
        path = next(path for path in documents if path.startswith("letters/2026-05-14_") and "APP-2026-025" in path)
        source = (ROOT / "inputs/batch-03" / path).read_text(encoding="utf-8-sig")
        self.assertEqual(documents[path], source)
        self.assertIn("stopped being current on 2026-05-05", source)
        self.assertTrue(peer_current("2024-05-05", "2026-05-05"))
        self.assertFalse(peer_current("2024-05-05", "2026-05-06"))


class LicensureDispositionControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        one, three = load_batch(ROOT / "inputs/batch-01"), load_batch(ROOT / "inputs/batch-03")
        cls.app = next(row for row in one["tables"]["applications"] if row["application_id"] == "APP-2026-015")
        cls.docs = [row for row in indexed_documents(one) + indexed_documents(three)
                    if row["index"]["application_id"] == cls.app["application_id"]]
        cls.reg = registry(load_sources(ROOT / "sources"))

    def test_synthetic_missing_dated_support_cannot_establish_review(self):
        for omitted in ("letters/2026-03-04_board-action_APP-2026-015.md",
                        "letters/2026-04-20_confirm-disclosure-reply_APP-2026-015.md"):
            docs = [row for row in self.docs if row["path"] != omitted]
            with self.subTest(omitted=omitted):
                record = clinical_dispositions(self.app, docs, self.reg)[0]
                self.assertTrue(record["authorized"])
                self.assertFalse(record["licensure_review_recorded"])
                self.assertTrue(record["evidence_reasons"])
                self.assertNotIn(omitted, record["finding_sources"])

    def test_synthetic_unauthorized_director_cannot_establish_review(self):
        original = deepcopy(self.docs)
        docs = []
        for row in self.docs:
            if row["path"].startswith("dispositions/"):
                text = row["text"].replace("Marguerite Oyelaran", "Unlisted Reviewer")
                docs.append(parse_document("synthetic/unauthorized-disposition.md", text, deepcopy(row["index"])))
            else:
                docs.append(row)
        record = clinical_dispositions(self.app, docs, self.reg)[0]
        self.assertFalse(record["authorized"])
        self.assertFalse(record["licensure_review_recorded"])
        self.assertTrue(record["reasons"])
        self.assertEqual(self.docs, original)


if __name__ == "__main__":
    unittest.main()
