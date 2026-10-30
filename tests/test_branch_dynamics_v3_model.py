"""v3 응답 모델의 자료형과 계약 검사 연결 확인."""

import copy
import json
import unittest
from pathlib import Path

from pydantic import ValidationError

from schemas.branch_dynamics_v3 import BranchDynamicsV3Response


FIXTURE = Path(__file__).resolve().parent / 'fixtures' / 'branch_dynamics_v3.json'


def load_fixture():
    return json.loads(FIXTURE.read_text())


class BranchDynamicsV3ModelTests(unittest.TestCase):
    def test_design_fixture_round_trips_without_inventing_values(self):
        raw = load_fixture()
        model = BranchDynamicsV3Response.model_validate(raw)
        self.assertEqual(model.model_dump(mode='json', exclude_unset=True), raw)

    def test_required_fields_and_nested_types_are_checked(self):
        raw = load_fixture()
        del raw['branch_dynamics']['branch_strengths']['month']['effective_power']
        with self.assertRaises(ValidationError):
            BranchDynamicsV3Response.model_validate(raw)

        raw = load_fixture()
        raw['branch_dynamics']['pairwise'][0]['adjacent'] = 'unknown'
        with self.assertRaises(ValidationError):
            BranchDynamicsV3Response.model_validate(raw)

    def test_unknown_fields_and_broken_references_are_checked(self):
        raw = load_fixture()
        raw['branch_dynamics']['groups'][0]['invented_power'] = 9.0
        with self.assertRaises(ValidationError):
            BranchDynamicsV3Response.model_validate(raw)

        raw = copy.deepcopy(load_fixture())
        raw['interaction_resolution']['unresolved_interaction_ids'].append(
            'group:trine:unknown')
        with self.assertRaises(ValidationError):
            BranchDynamicsV3Response.model_validate(raw)


if __name__ == '__main__':
    unittest.main()
