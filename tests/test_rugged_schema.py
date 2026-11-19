"""SnapLock dimensions, explicit limitations and preservation of personal presets."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from box_studio.schema import normalize_params, validate_params
from box_studio.presets_catalog import BUILTIN_PRESETS, load_user_presets, generate_random_printable_params


class RuggedSchemaTests(unittest.TestCase):
    def test_reference_has_independent_base_and_lid_heights(self):
        p = next(x["params"] for x in BUILTIN_PRESETS if x["id"] == "tool_rugged")
        self.assertEqual(validate_params(p), [])
        self.assertEqual([p[k] for k in ("width_x", "depth_y", "height_z", "rugged_lid_height")], [160, 95, 35, 20])
        changed = normalize_params({**p, "height_z": 45, "rugged_lid_height": 24})
        self.assertEqual(validate_params(changed), [])
        self.assertEqual(changed["height_z"] + changed["rugged_lid_height"], 69)

    def test_old_personal_rugged_presets_are_preserved_and_identified(self):
        original = {"schema_version": 1, "style": "rugged_box", "width_x": 90, "depth_y": 65,
                    "height_z": 35, "hinge_mode": "print_in_place", "cutouts": [{"kind": "usb_c", "z": 15}]}
        before = copy.deepcopy(original)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "presets.json"
            encoded = json.dumps([{"id": "personal", "name": "Old case", "params": original}]).encode()
            path.write_bytes(encoded)
            loaded = load_user_presets(path)
            self.assertEqual(path.read_bytes(), encoded)
        p = normalize_params(loaded[0]["params"])
        self.assertEqual(p["rugged_model"], "legacy")
        self.assertEqual(p["width_x"], 90)
        self.assertTrue(p["cutouts"])
        self.assertIn("saved preset was preserved", " ".join(validate_params(p)))
        self.assertEqual(original, before)
        self.assertEqual(normalize_params(p), p)

    def test_unsupported_features_and_targets_fail_without_discarding_requests(self):
        for changes in ({"standoffs": [{"x": 0, "y": 0}]}, {"cutouts": [{"z": 15}]},
                        {"dividers_x": [0]}, {"dividers_y": [0]}, {"gasket_enabled": True},
                        {"export_target": "gasket"}, {"export_target": "fit_test_kit"}):
            with self.subTest(changes=changes):
                p = normalize_params({"style": "rugged_box", **changes})
                self.assertTrue(validate_params(p))
                for key in changes:
                    self.assertTrue(p[key])

    def test_randomization_is_repeatable_and_preserves_the_mechanism(self):
        p = normalize_params({"style": "rugged_box"})
        for seed in range(12):
            with self.subTest(seed=seed):
                candidate = generate_random_printable_params(p, seed, {"bed_x": 260, "bed_y": 260, "max_z": 260})
                self.assertEqual(candidate, generate_random_printable_params(p, seed, {"bed_x": 260, "bed_y": 260, "max_z": 260}))
                self.assertEqual(validate_params(candidate), [])
                for key in ("style", "rugged_model", "rugged_lid_height", "corner_radius", "wall_thickness", "floor_thickness"):
                    self.assertEqual(candidate[key], p[key])

    def test_wall_floor_and_radius_cannot_invert_the_inner_chamfer(self):
        p = normalize_params({"style": "rugged_box", "wall_thickness": 4,
                              "floor_thickness": 1.5, "corner_radius": 9.1})
        self.assertIn("internal chamfer", " ".join(validate_params(p)))
        p["corner_radius"] = 12
        self.assertEqual(validate_params(p), [])

    def test_randomization_accounts_for_fittings_and_the_inverted_lid(self):
        p = normalize_params({"style": "rugged_box"})
        for seed in range(12):
            candidate = generate_random_printable_params(p, seed, {"bed_x": 260, "bed_y": 260, "max_z": 40})
            self.assertLessEqual(candidate["height_z"] + 4.5, 40)
        with self.assertRaisesRegex(ValueError, "no safe variation"):
            generate_random_printable_params({**p, "rugged_lid_height": 40}, 1, {"bed_x": 260, "bed_y": 260, "max_z": 40})


if __name__ == "__main__":
    unittest.main()
