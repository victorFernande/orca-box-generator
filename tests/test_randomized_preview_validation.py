"""Random candidates must survive the actual preview before becoming shared state."""

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from box_studio.plugin_main import BoxStudioController
from box_studio.schema import normalize_params


class RandomizedPreviewValidationTests(unittest.TestCase):
    def test_host_retries_rejected_surface_before_updating_shared_design(self):
        controller = BoxStudioController()
        original = controller.current_params()
        accepted = []

        def geometry(params, **kwargs):
            self.assertEqual(controller.current_params(), original)
            accepted.append(params)
            if len(accepted) == 1:
                raise ValueError("base: invalid surface topology")
            self.assertTrue(kwargs["assembled"])
            self.assertEqual(kwargs["target"], params["export_target"])
            return []

        messages = []
        with patch.object(controller, "_geometry", side_effect=geometry):
            controller.handle_message({"type": "randomize", "seed": 42}, messages.append)
        self.assertEqual(len(accepted), 2)
        self.assertTrue(messages[-1]["ok"])
        self.assertEqual(controller.current_params(), accepted[-1])
        self.assertNotEqual(accepted[0], accepted[1])

    def test_all_rejected_candidates_leave_current_design_unchanged(self):
        controller = BoxStudioController()
        original = controller.current_params()
        messages = []
        with patch.object(controller, "_geometry", side_effect=ValueError("invalid topology")) as geometry:
            controller.handle_message({"type": "randomize", "seed": 42}, messages.append)
        self.assertFalse(messages[-1]["ok"])
        self.assertEqual(controller.current_params(), original)
        self.assertEqual(geometry.call_count, 8)

    def test_unexpected_generation_errors_are_not_silently_retried(self):
        controller = BoxStudioController()
        messages = []
        with patch.object(controller, "_geometry", side_effect=RuntimeError("unexpected")) as geometry:
            controller.handle_message({"type": "randomize", "seed": 42}, messages.append)
        self.assertFalse(messages[-1]["ok"])
        self.assertEqual(geometry.call_count, 1)
        self.assertIn("unexpected", messages[-1]["message"])

    def test_observed_ci_seeds_produce_real_preview_and_reuse_approved_geometry(self):
        cases = (
            (2850159178, dict(style="rugged_box", width_x=162, depth_y=96,
                height_z=36, wall_thickness=2.5, floor_thickness=2.5,
                rugged_lid_height=22, corner_radius=12, fit_clearance=0.15)),
            (3957100624, dict(style="open_bin", width_x=92, depth_y=66,
                height_z=36, handle_faces="front_back", handle_width=35,
                handle_height=10, handle_top_margin=7)),
        )
        for seed, values in cases:
            with self.subTest(seed=seed):
                controller = BoxStudioController()
                messages = []
                params = normalize_params(values)
                with patch.object(controller, "read_host_context", return_value={
                    "bed_x": 260, "bed_y": 260, "max_z": 260,
                }):
                    controller.handle_message({"type": "randomize", "seed": seed,
                        "params": params}, messages.append)
                self.assertTrue(messages[-1]["ok"], messages[-1])
                candidate = messages[-1]["params"]
                self.assertEqual(candidate["style"], params["style"])
                approved = controller._geometry(candidate, assembled=True,
                    target=candidate["export_target"])
                self.assertTrue(approved)
                with patch("box_studio.plugin_main.generate_box_mesh",
                           side_effect=AssertionError("Approved geometry must be cached")):
                    preview = controller._preview_payload(candidate)
                self.assertTrue(preview["meshes"])


if __name__ == "__main__":
    unittest.main()
