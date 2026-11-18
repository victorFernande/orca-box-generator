# Validation status

Recorded on 2026-11-18 for version 1.0.0.

All **28** local unittest cases passed with Python 3.12.13, NumPy 2.5.5 and `-B -W error` in 361.37 seconds. A subsequent camera framing adjustment affects only the compact browser layout; geometry algorithms are unchanged. Packaging and browser checks are run again on the final distribution.

## Verification methods

The test suite runs with `python -B -W error -m unittest discover -s tests -v`. It covers the four construction styles, twelve presets, combined PCB supports/ports/dividers, minimum-clearance interfaces, hinge movement, calibration samples, gasket topology, invalid combinations, shared page/dock state and packaging.

Export checks operate on the float32 surface actually written to STL/3MF. They reject nonfinite coordinates, invalid indices, collapsed triangles and layouts exceeding the selected bed or height. Coordinate round-trip checks ensure that 3MF serialization preserves float32 geometry. The installer is tested against a temporary plugin directory, including preservation of sibling plugins and installation state.

Standalone bundle and wheel checks run in separate Python interpreters without the source tree. Importing the wheel package itself must register the plugin entrypoint. Linux transport tests simulate twelve success/failure scenarios and verify unique-owner routing and resource cleanup.

## Independent geometry review

- Default base/lid surfaces for all four styles were closed, consistently oriented and connected, with topology appropriate to their holes.
- The captive-hinge assembly and clips passed vertex-link checks; no vertex with multiple independent link cycles was found in those representative meshes. The sliding lid passed the same check.
- At 0.20 mm configured hinge clearance, the tested actual pin/bore surfaces retained approximately 0.1989 mm radial clearance.
- A sweep of sampled vertices and triangle centers from the actual lid mesh through 73 poses between 0 and 180 degrees found no penetration into the analytic base field at the tested tolerance.
- Print-in-place export preserves the base/lid relationship as one object containing two closed shells, with separate clips. Both STL and 3MF were inspected; the 3MF packer applies a common transform to the assembly.
- Lip and sliding interfaces were sampled at the minimum 0.10 mm configured clearance and checked against their analytic fields.

These checks are computational evidence for the tested dimensions, not a physical print or strength test.

## Interface and performance

Chromium with a local verification bridge renders the actual backend mesh data. Generated JavaScript is syntax checked with Node.js. The interface has full and compact layouts, PT/EN, themes, inspection controls and background regeneration. Results from outdated requests are discarded, and concurrent page/dock requests share a single geometry worker.

Detailed boxes can contain hundreds of thousands to over a million triangles. Regeneration can take several seconds or longer depending on dimensions, features and hardware; a fixed frame rate or regeneration duration is not promised. The displayed curved-interface error is a tessellation target, not printer accuracy.

## Pending validation

Live page/dock activation, permission handling and Plater delivery inside OrcaSlicer remain pending on Windows, macOS and Linux. No native visual validation is claimed by publication. Physical fitting, spring life, inserts, sealing and printing performance also require calibration.

A closed print-in-place lid spans a cavity above the bed. Evaluate bridging and removable supports in the slicer, and avoid filling the functional hinge gaps. Print-in-place does not imply support-free printing. Calibration print duration must come from the selected slicer profile.

The repository CI independently builds and tests the source on Windows, macOS and Linux. Its run history provides the current cross-platform result.
