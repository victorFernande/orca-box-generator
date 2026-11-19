"""Distribution isolation and installer boundaries for the native Box plugin."""

import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "box_packager_tests", PROJECT_ROOT / "scripts/build_and_install.py"
)
builder = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = builder
spec.loader.exec_module(builder)


class PackagingTests(unittest.TestCase):
    def test_wheel_bytes_do_not_depend_on_builder_platform_zip_defaults(self):
        # The same source release must not change its asset digest merely
        # because ZipInfo otherwise chooses DOS versus Unix producer metadata.
        outputs = []
        for platform in ("win32", "linux", "darwin"):
            with patch.object(zipfile.sys, "platform", platform):
                wheel = builder.build_wheel()
                outputs.append(wheel.read_bytes())
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[0], outputs[2])

    def test_installer_replaces_linked_files_without_overwriting_external_content(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder) / "OrcaSlicer"
            target = base / "orca_plugins" / "orca_box_generator"
            target.mkdir(parents=True)
            external = Path(folder) / "external.txt"
            external.write_text("Keep external content", encoding="utf-8")
            os.link(external, target / "orca_box_generator.py")
            os.link(external, target / "icon.svg")
            source = Path(folder) / "bundle.py"
            source.write_text("# replacement fixture\n", encoding="utf-8")
            with (
                patch.object(builder, "get_orca_base_dir", return_value=base),
                patch.object(builder, "get_install_dir", return_value=target),
            ):
                builder.install_plugin(source)
            self.assertEqual(
                external.read_text(encoding="utf-8"), "Keep external content"
            )
            self.assertEqual(
                (target / "orca_box_generator.py").read_bytes(), source.read_bytes()
            )
            self.assertFalse(
                os.path.samefile(external, target / "orca_box_generator.py")
            )

    def test_bundle_and_wheel_load_without_source_tree(self):
        bundle = builder.build_bundle()
        wheel = builder.build_wheel()
        metadata = builder.extract_pep723_toml(bundle.read_text(encoding="utf-8"))
        self.assertEqual(
            metadata["tool"]["orcaslicer"]["plugin"]["id"], "orca-box-studio"
        )
        self.assertEqual(metadata["requires-python"], ">=3.12")
        self.assertIn(
            "Permission is hereby granted, free of charge",
            bundle.read_text(encoding="utf-8"),
        )
        self.assertEqual(bundle.read_bytes(), builder.DIST_ANY_BUNDLE_PATH.read_bytes())
        builder.verify_bundle_smoke(bundle)
        builder.verify_wheel_smoke(wheel)

    def test_install_preserves_sibling_and_local_install_state(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder) / "OrcaSlicer"
            target = base / "orca_plugins" / "orca_box_generator"
            sibling = base / "orca_plugins" / "existing_plugin"
            target.mkdir(parents=True)
            sibling.mkdir(parents=True)
            state = target / ".install_state.json"
            state.write_text('{"enabled": true}', encoding="utf-8")
            (sibling / "keep.py").write_text("# existing plugin\n", encoding="utf-8")
            source = Path(folder) / "bundle.py"
            source.write_text("# isolated install fixture\n", encoding="utf-8")
            with (
                patch.object(builder, "get_orca_base_dir", return_value=base),
                patch.object(builder, "get_install_dir", return_value=target),
            ):
                self.assertEqual(builder.install_plugin(source), target.resolve())
            self.assertEqual(state.read_text(encoding="utf-8"), '{"enabled": true}')
            self.assertEqual(
                (sibling / "keep.py").read_text(encoding="utf-8"), "# existing plugin\n"
            )
            self.assertEqual(
                (target / "orca_box_generator.py").read_bytes(), source.read_bytes()
            )

    def test_install_rejects_target_outside_dedicated_plugin_folder(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder) / "OrcaSlicer"
            outside = Path(folder) / "unrelated"
            with (
                patch.object(builder, "get_orca_base_dir", return_value=base),
                patch.object(builder, "get_install_dir", return_value=outside),
            ):
                with self.assertRaises(RuntimeError):
                    builder.install_plugin(Path(folder) / "unused.py")
            self.assertFalse(outside.exists())


if __name__ == "__main__":
    unittest.main()
