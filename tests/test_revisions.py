import copy
import unittest

from credentialing.revisions import assess_revision, verified_role


class RevisionTests(unittest.TestCase):
    def setUp(self):
        self.old = {"entry_id": "ENT-1", "application_id": "APP-1", "revision": "1",
                    "organization": "Hospital A", "role": "Staff Physician",
                    "supervisor": "Dr A", "contact_name": "Office A",
                    "contact_email": "a@example.invalid", "from_date": "2019-01-01", "to_date": ""}
        self.entry = dict(self.old, revision="2")
        self.reply = {"reply_id": "VR-1", "application_id": "APP-1", "entry_id": "ENT-1",
                      "attester_organization": "Hospital A", "received_from": "Medical staff office — Hospital A",
                      "verified_credential": "Employment — Staff Physician",
                      "requested_date": "2025-01-01", "received_date": "2025-01-15"}

    def assess(self):
        return assess_revision(self.entry, [self.old], self.reply)

    def test_unchanged_and_contact_only_can_reuse(self):
        self.assertEqual(self.assess(), {"changed_fields": {}, "missing_facts": [], "conflicts": []})
        self.entry.update(contact_name="Office B", contact_email="b@example.invalid")
        result = self.assess()
        self.assertEqual(set(result["changed_fields"]), {"contact_name", "contact_email"})
        self.assertEqual(result["missing_facts"], [])
        self.assertEqual(result["conflicts"], [])

    def test_changed_organization_old_source_conflicts(self):
        self.entry["organization"] = "Hospital B"
        result = self.assess()
        self.assertEqual(result["conflicts"][0]["verified"], "Hospital A")
        self.assertEqual(result["conflicts"][0]["declared"], "Hospital B")

    def test_changed_organization_equivalent_name_is_not_employer_proof(self):
        self.entry["organization"] = "Hospital B"
        self.reply.update(attester_organization="Independent CVO", received_from="Independent CVO")
        self.assertEqual(self.assess()["missing_facts"][0]["field"], "organization")

    def test_changed_role_requires_actual_role(self):
        self.entry["role"] = "Department Chair"
        result = self.assess()
        self.assertEqual(result["conflicts"][0]["field"], "role")
        self.assertEqual(result["conflicts"][0]["verified"], "Staff Physician")
        self.reply["verified_credential"] = "Employment verified"
        self.assertEqual(self.assess()["missing_facts"][0]["field"], "role")

    def test_changed_supervisor_is_not_attester_or_contact(self):
        self.entry["supervisor"] = "Dr B"
        self.reply.update(attester_name="Dr B", notes="Dr B signed this reply.")
        self.assertEqual(self.assess()["missing_facts"][0]["field"], "supervisor")
        self.reply["verified_supervisor"] = "Dr B"
        self.assertEqual(self.assess()["missing_facts"], [])
        self.assertEqual(self.assess()["conflicts"], [])

    def test_old_request_can_verify_revised_facts(self):
        self.entry.update(organization="Hospital B", role="Department Chair", supervisor="Dr B")
        self.reply.update(attester_organization="Hospital B", received_from="Medical staff office — Hospital B",
                          verified_credential="Employment — Department Chair", verified_supervisor="Dr B")
        result = self.assess()
        self.assertEqual(result["missing_facts"], [])
        self.assertEqual(result["conflicts"], [])
        self.assertEqual(result["changed_fields"]["role"]["evidence"][0]["source_ref"], "verification-replies.csv#VR-1")

    def test_explicit_role_does_not_silently_override_conflicting_credential(self):
        self.entry["role"] = "Department Chair"
        self.reply["verified_role"] = "Department Chair"
        self.assertEqual(self.assess()["conflicts"][0]["verified"], "Staff Physician")

    def test_training_role_can_follow_clear_credential_label(self):
        self.old["role"] = "Internal Medicine Residency"
        self.entry["role"] = "Family Medicine Residency"
        self.reply["verified_credential"] = "Residency — Family Medicine"
        self.assertEqual(self.assess()["conflicts"], [])
        self.assertEqual(self.assess()["missing_facts"], [])

    def test_verified_role_extraction_is_explicit_and_unambiguous(self):
        for credential, expected in (("Degree — Doctor of Medicine", "doctor of medicine"),
                ("Residency — Family Medicine", "family medicine residency"),
                ("Fellowship — Cardiovascular Disease", "cardiovascular disease fellowship"),
                ("Internship — Rotating Internship", "rotating internship"),
                ("Employment — Staff Physician", "staff physician"),
                ("Employment verified", None)):
            with self.subTest(credential=credential):
                self.assertEqual(verified_role({"verified_credential": credential}), expected)
        self.assertEqual(verified_role({"verified_role": "  Department   CHAIR "}), "department chair")
        self.assertIsNone(verified_role({"verified_role": "Chair", "verified_credential": "Employment — Staff Physician"}))

    def test_dates_remain_for_callers_date_comparison(self):
        self.entry["from_date"] = "2020-01-01"
        result = self.assess()
        self.assertIn("from_date", result["changed_fields"])
        self.assertEqual(result["conflicts"], [])
        self.assertEqual(result["missing_facts"], [])

    def test_same_application_and_entry_only_and_future_excluded(self):
        middle = dict(self.old, revision="2", role="Department Chair")
        self.entry.update(revision="3", role="Department Chair")
        histories = [middle, dict(self.old, application_id="OTHER", revision="2"),
                     dict(self.old, revision="4"), dict(self.old, entry_id="OTHER", revision="2")]
        self.assertEqual(assess_revision(self.entry, histories, self.reply)["changed_fields"], {})

    def test_later_contact_revision_cannot_hide_earlier_unsupported_role_change(self):
        middle = dict(self.old, revision="2", role="Department Chair")
        self.entry.update(revision="3", role="Department Chair", contact_name="Office B")
        result = assess_revision(self.entry, [self.old, middle], self.reply)
        self.assertEqual(result["conflicts"][0]["field"], "role")
        self.assertEqual(result["changed_fields"]["role"]["previous_revision"], 1)
        self.reply["verified_credential"] = "Employment — Department Chair"
        self.assertEqual(assess_revision(self.entry, [self.old, middle], self.reply)["conflicts"], [])

    def test_inputs_are_not_mutated_and_initial_entry_is_not_revision_hold(self):
        original = copy.deepcopy((self.entry, self.old, self.reply))
        self.assess()
        self.assertEqual((self.entry, self.old, self.reply), original)
        self.assertEqual(assess_revision(self.entry, [], self.reply)["missing_facts"], [])


if __name__ == "__main__":
    unittest.main()
