"""Four supplied B2 dispositions plus narrowly synthetic authority/evidence cases."""

from copy import deepcopy
import csv
from pathlib import Path
import unittest

from credentialing.dispositions import clinical_dispositions
from credentialing.documents import parse_document
from credentialing.io import load_sources
from credentialing.policy import registry


ROOT = Path(__file__).resolve().parents[1]


class DispositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = registry(load_sources(ROOT / "sources"))
        with (ROOT / "inputs/batch-01/applications.csv").open() as stream:
            cls.apps = {row["application_id"]: row for row in csv.DictReader(stream)}
        cls.docs = {}
        with (ROOT / "inputs/batch-02/correspondence.csv").open() as stream:
            for row in csv.DictReader(stream):
                if row["document_path"].startswith("dispositions/"):
                    text = (ROOT / "inputs/batch-02" / row["document_path"]).read_text()
                    cls.docs[row["application_id"]] = parse_document(row["document_path"], text, row)
        assert len(cls.docs) == 4

    def record(self, number, docs=None):
        app_id = f"APP-2026-{number:03d}"
        return clinical_dispositions(self.apps[app_id], docs if docs is not None else list(self.docs.values()), self.reg)[0]

    def explanation(self, when="2026-02-24", start="2019-04-01", end="2019-11-05"):
        text = (f"# Applicant gap explanation\n\n**Date:** {when}\n**Application:** APP-2026-017\n"
                "**Applicant:** Dr. Oskar Lindqvist, MD\n**From:** Dr. Oskar Lindqvist, MD\n"
                f"**Period explained:** {start} to {end}\n\nSynthetic written applicant explanation.\n")
        return parse_document(f"synthetic/{when}-explanation.md", text,
                              {"application_id": "APP-2026-017", "date": when, "direction": "inbound"})

    def test_four_actual_dispositions_have_rostered_authority_and_preserved_prose(self):
        for number in [17, 27, 29, 32]:
            with self.subTest(number=number):
                record = self.record(number)
                doc = self.docs[f"APP-2026-{number:03d}"]
                self.assertTrue(record["authorized"], record["reasons"])
                self.assertEqual(record["reasons"], [])
                self.assertEqual(record["path"], doc["path"])
                self.assertEqual(record["text"], doc["text"])
                self.assertEqual(record["date"], doc["fields"]["date"])
                self.assertTrue(record["topic"])

    def test_affirmative_discontinue_is_terminal_but_do_not_discontinue_is_not(self):
        self.assertEqual(self.record(29)["terminal"], "discontinued")
        offered = self.record(27)
        self.assertIsNone(offered["terminal"])
        self.assertTrue(offered["amendment_offered"])
        self.assertFalse(self.record(29)["amendment_offered"])
        self.assertFalse(self.record(32)["amendment_offered"])

    def test_ppq2_disposition_is_specific_record_not_global_evidence_waiver(self):
        record = self.record(32)
        self.assertEqual(record["ppq_codes"], ["PPQ-2"])
        self.assertTrue(record['ppq_disposition_recorded'])
        self.assertIn("both documents attached", record["text"])
        self.assertFalse(record["gap_cleared"])
        self.assertIsNone(record["terminal"])
        self.assertNotIn("packet_presentable", record)
        self.assertNotIn("approved", record)

    def test_missing_february24_explanation_does_not_invalidate_authority_or_clear_gap(self):
        doc = self.docs["APP-2026-017"]
        record = self.record(17, [doc, self.explanation("2026-02-13")])
        self.assertTrue(record["authorized"])
        self.assertEqual(record["reasons"], [])
        self.assertTrue(record["gap_satisfactory"])
        self.assertEqual(record["gap_period"], ("2019-04-01", "2019-11-05"))
        self.assertEqual(record["required_explanation_dates"], ["2026-02-24"])
        self.assertEqual(record["missing_explanation_dates"], ["2026-02-24"])
        self.assertEqual(record["explanation_paths"], [])
        self.assertTrue(record["evidence_reasons"])
        self.assertFalse(record["gap_cleared"])

    def test_ppq_mention_or_hold_is_not_an_affirmative_disposition(self):
        original = self.docs['APP-2026-032']
        for narrative in ('PPQ-2 remains under review. Do not present the file.',
                          'I have read the PPQ-2 explanation.',
                          'Present the file to the Executive Committee after I complete review.',
                          'Present the file to the Executive Committee with evidence if PPQ-2 is cleared.',
                          'Present the file to the Executive Committee. Do not present the file.'):
            doc = deepcopy(original)
            prefix = doc['text'].split('\nI have read')[0]
            doc['text'] = prefix + '\n' + narrative + '\n\nMarguerite Oyelaran, MD\nClinical Director\n'
            record = self.record(32, [doc])
            self.assertTrue(record['authorized'])
            self.assertEqual(record['ppq_codes'], ['PPQ-2'])
            self.assertFalse(record['ppq_disposition_recorded'])

    def test_exact_named_qualifying_explanation_can_satisfy_recorded_gap_judgment(self):
        explanation = self.explanation()
        record = self.record(17, [self.docs["APP-2026-017"], explanation])
        self.assertTrue(record["gap_cleared"])
        self.assertEqual(record["explanation_paths"], [explanation["path"]])
        self.assertEqual(record["missing_explanation_dates"], [])
        self.assertEqual(record["evidence_reasons"], [])
        self.assertIsNone(record["terminal"])

    def test_explanation_must_cover_every_inclusive_gap_day(self):
        for start, end in [("2019-04-02", "2019-11-05"), ("2019-04-01", "2019-11-04")]:
            with self.subTest(start=start, end=end):
                record = self.record(17, [self.docs["APP-2026-017"], self.explanation(start=start, end=end)])
                self.assertTrue(record["authorized"])
                self.assertFalse(record["gap_cleared"])
        record = self.record(17, [self.docs["APP-2026-017"], self.explanation(start="2019-03-31", end="2019-11-06")])
        self.assertTrue(record["gap_cleared"])

    def test_wrong_person_role_term_or_missing_signature_cannot_authorize_discontinuation(self):
        original = self.docs["APP-2026-029"]
        wrong_name, wrong_role, outside_term, unsigned = [deepcopy(original) for _ in range(4)]
        wrong_name["fields"]["recorded_by"] = "Dr. Someone Else, MD, Clinical Director"
        wrong_role["fields"]["recorded_by"] = "Dr. Marguerite Oyelaran, MD, Committee member"
        outside_term["fields"]["date"] = outside_term["index"]["date"] = "2028-01-01"
        unsigned["text"] = unsigned["text"].rsplit("\nMarguerite Oyelaran, MD", 1)[0]
        for doc in [wrong_name, wrong_role, outside_term, unsigned]:
            with self.subTest(fields=doc["fields"]):
                record = self.record(29, [doc])
                self.assertFalse(record["authorized"])
                self.assertTrue(record["reasons"])
                self.assertIsNone(record["terminal"])

    def test_wrong_applicant_application_or_date_conflict_is_retained_unauthorized(self):
        for field, value in [("applicant", "Dr. Someone Else, MD"), ("application", "APP-OTHER"),
                             ("date", "2026-04-01"), ("date", "2026-02-30")]:
            with self.subTest(field=field, value=value):
                doc = deepcopy(self.docs["APP-2026-029"])
                doc["fields"][field] = value
                record = self.record(29, [doc])
                self.assertFalse(record["authorized"])
                self.assertIsNone(record["terminal"])
                self.assertEqual(record["path"], doc["path"])
                self.assertTrue(record["reasons"])

    def test_signature_claim_header_alone_cannot_substitute_for_footer(self):
        doc = deepcopy(self.docs["APP-2026-032"])
        doc["text"] = doc["text"].replace("\nMarguerite Oyelaran, MD\nClinical Director", "\nDifferent person\nClinical Director")
        self.assertFalse(self.record(32, [doc])["authorized"])

    def test_explanation_identity_direction_and_date_must_match(self):
        base = self.explanation()
        wrong_sender, outbound, wrong_date, wrong_app = [deepcopy(base) for _ in range(4)]
        wrong_sender["fields"]["from"] = "Someone else"
        outbound["index"]["direction"] = "outbound"
        wrong_date["fields"]["date"] = "2026-02-13"
        wrong_app["index"]["application_id"] = "APP-OTHER"
        for explanation in [wrong_sender, outbound, wrong_date, wrong_app]:
            with self.subTest(explanation=explanation):
                record = self.record(17, [self.docs["APP-2026-017"], explanation])
                self.assertFalse(record["gap_cleared"])
                self.assertTrue(record["authorized"])
                self.assertEqual(record["missing_explanation_dates"], ["2026-02-24"])

    def test_negated_or_hypothetical_discontinue_mentions_do_not_create_terminal_result(self):
        original = self.docs["APP-2026-029"]
        for phrase in ["Do not discontinue the application", "If criteria later fail, discontinue the application",
                       'The phrase "Discontinue the application" is not a recorded disposition']:
            with self.subTest(phrase=phrase):
                doc = deepcopy(original)
                doc["text"] = doc["text"].replace("Discontinue the application", phrase)
                self.assertTrue(self.record(29, [doc])["authorized"])
                self.assertIsNone(self.record(29, [doc])["terminal"])

    def test_unauthorized_amendment_offer_is_retained_without_effect(self):
        doc = deepcopy(self.docs["APP-2026-027"])
        doc["fields"]["recorded_by"] = "Dr. Unlisted Person, MD, Clinical Director"
        record = self.record(27, [doc])
        self.assertFalse(record["authorized"])
        self.assertFalse(record["amendment_offered"])
        self.assertIn("Offer the applicant", record["text"])


if __name__ == "__main__":
    unittest.main()
