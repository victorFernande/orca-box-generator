# Validation status

## Version 1.2 verification — 2026-11-18

### Confirmed independent functional subset

All **10** tests in `tests/test_functional_mating.py` passed locally with Python 3.12 and `-B -W error`. This is a targeted functional subset, not the count or result of the full version 1.2 suite. It verifies:

- Lip Snap interference exposed as `snap_retention`, independently of locating clearance, with a progressive axial entry ramp.
- No permanent Rugged clip overlap in the sampled closed configurations at 0.10/0.20/0.40 mm clearance.
- Sliding detent clearance when closed and a geometric barrier during withdrawal.
- Open-bin hand openings on both selectable face pairs, preserved grip bridges/floor, one connected shell and genus-two topology for the two-hole bin.
- The removable lid plus two front clips: actual float32 mesh edge orientation, connectivity, single-cycle vertex links and agreement with the analytic field/chord budget; sampled closed clearance; progressive clip entry; temporary detent interference during withdrawal; vertical lid retention with clips installed and removal after they are released.

Additional independent mesh checks passed for high hook retention and minimum clip thickness, and for a larger open bin and a bin with handles disabled. These are computational samples, not an exhaustive proof over every input or an elastic-contact simulation. A clear closed state and deliberate transient snap interference are separate requirements. No release force, allowable strain, material durability or printed fit was measured.

### Confirmed stacking subset and earlier full-suite baseline

All **5** independent tests in `tests/test_stackable_mating.py` passed with `-B -W error`. Two unequal heights, also with different front-access/floor dimensions, have actual finite bearing patches on the lower left/right/rear rims and upper underside. The empty upper mesh's mass projection lies inside the three-contact polygon. Actual mesh/field samples verify no penetration at the aligned pose, during vertical insertion or within-clearance lateral movement; the guide and shoulders oppose excess lateral/downward movement. Incompatible families are rejected. Mesh connectivity, oriented edges, manifold vertex links and field/chord agreement were checked, with additional extreme-parameter cases passing.

These tests do not establish load capacity, friction, material strength or stability under arbitrary contents. The new mesh, tests and visual presentation are original, without redistribution of reference meshes/assets or a compatibility claim with third-party organizers.

Before the stackable addition, the complete local version 1.2 suite passed **75** tests in **318.569 seconds**. Its browser run passed **12 layouts and 22 interactions**. Those results are preserved as the pre-stacking baseline.

### Post-stacking local verification

The complete run with `-B -W error` completed **89 cases in 333.878 seconds**, with **88 passing and one optional Chromium cascade case skipped** because its browser environment was not enabled for that command. The final theme-adapter subset was then run with Chromium enabled: **3/3 passed**, including that previously skipped case.

After the final style-specific print-help change, the UI/cache/local-edit subset passed **11/11**, and the final independent stacking subset passed **5/5**. These focused follow-ups cover the final files; their counts are not additional unique tests to add to the full-run count.

The isolated browser run passed **12 layouts and 26 interactions**, with zero layout or script errors. A final 26-interaction run after the print-help change also passed. It exercises the real Python meshes, changes the stacking foot/clearance/front opening, exports a single-piece stacking 3MF and restores lid controls when switching styles. Both standalone bundles and the wheel passed isolated import/registration and wheel RECORD verification. These checks do not control OrcaSlicer.

### Current scope and remaining checks

Version 1.2 has seven styles and fifteen editable presets. `open_bin` exports an open base with optional paired hand openings. `snap_latch` exports a base, flat removable lid and two separate front clips. Its `lid_wall_height` is the skirt depth below the cap; the flat cap top is `height_z + fit_clearance + lid_height`. Body dimensions are external base dimensions in millimetres, not the complete catch/clip envelope or the inside cavity.

Local source, export, packaging and isolated-browser checks after adding `stackable_bin` passed as recorded above. Native version 1.2 page/dock acceptance, regeneration, export and Plater loading remain pending. The earlier version 1.1 Windows observations below do not validate the changed mechanisms or current native bundle. Live macOS/Linux acceptance, slicing, physical print/fit, grip comfort, inserts, sealing and latch life remain pending.

See [generation measurements](PERFORMANCE.md) for separate timing methodology and limits; no complete-suite timing is asserted here. The generic fit kit is unavailable for the three storage styles. Test smaller configurations of their actual parts with the same wall thickness, clearance, clip dimensions and retention; uniform mesh scaling changes these values.

For `stackable_bin`, total height includes the foot. Matching outside X/Y, corner radius, wall, foot height and stacking clearance define a family; heights/front access may differ. The assembly offset is `lower.height_z - upper.stack_foot_height`, and combined height is the sum of the two heights minus the upper foot height. Only one base is exported per design.

The version 1.0 and 1.1 records below are preserved as historical evidence.

## Version 1.1.0 verification — 2026-11-18

A native session in **OrcaSlicer 2.5.1 on Windows** opened the Box and Thread studio pages, generated their real geometry, exported 3MF files and sent import requests through WM_COPYDATA. The base and lid from each plugin were then visually confirmed on the Plater. This observation goes beyond the transport acknowledgement; the plugin's status message itself still reports only that an import request was sent.

The native session used version 1.1.0 **before the final native-theme adapters**. The final adapters and final dock layout have not yet been verified inside OrcaSlicer. Live integration inside macOS and Linux remains pending. No slicing, physical printing, mating-fit, strength or sealing validation was performed.

During the shared session, the Thread 3MF was imported as geometry into a project already containing Box objects, and the objects overlapped. Open the exported 3MF as a project, or use an empty plate; when adding it to an existing plate, arrange the objects before slicing.

Automated geometry, UI, transport and packaging checks are recorded separately from that native observation. The final complete Box suite was still running when this entry was written; no final test count is asserted here. The earlier results below remain historical records.

## Version 1.0.0 historical baseline

Recorded on 2026-11-18 for version 1.0.0.

All **28** local unittest cases passed with Python 3.12.13, NumPy 2.5.5 and `-B -W error` in 361.37 seconds. A subsequent camera framing adjustment affects only the compact browser layout; geometry algorithms are unchanged. Packaging and browser checks are run again on the final distribution.

### Verification methods

The test suite runs with `python -B -W error -m unittest discover -s tests -v`. It covers the four construction styles, twelve presets, combined PCB supports/ports/dividers, minimum-clearance interfaces, hinge movement, calibration samples, gasket topology, invalid combinations, shared page/dock state and packaging.

Export checks operate on the float32 surface actually written to STL/3MF. They reject nonfinite coordinates, invalid indices, collapsed triangles and layouts exceeding the selected bed or height. Coordinate round-trip checks ensure that 3MF serialization preserves float32 geometry. The installer is tested against a temporary plugin directory, including preservation of sibling plugins and installation state.

Standalone bundle and wheel checks run in separate Python interpreters without the source tree. Importing the wheel package itself must register the plugin entrypoint. Linux transport tests simulate twelve success/failure scenarios and verify unique-owner routing and resource cleanup.

### Independent geometry review

- Default base/lid surfaces for all four styles were closed, consistently oriented and connected, with topology appropriate to their holes.
- The captive-hinge assembly and clips passed vertex-link checks; no vertex with multiple independent link cycles was found in those representative meshes. The sliding lid passed the same check.
- At 0.20 mm configured hinge clearance, the tested actual pin/bore surfaces retained approximately 0.1989 mm radial clearance.
- A sweep of sampled vertices and triangle centers from the actual lid mesh through 73 poses between 0 and 180 degrees found no penetration into the analytic base field at the tested tolerance.
- Print-in-place export preserves the base/lid relationship as one object containing two closed shells, with separate clips. Both STL and 3MF were inspected; the 3MF packer applies a common transform to the assembly.
- Lip and sliding interfaces were sampled at the minimum 0.10 mm configured clearance and checked against their analytic fields.

These checks are computational evidence for the tested dimensions, not a physical print or strength test.

### Interface and performance

Chromium with a local verification bridge renders the actual backend mesh data. Generated JavaScript is syntax checked with Node.js. The interface has full and compact layouts, PT/EN, themes, inspection controls and background regeneration. Results from outdated requests are discarded, and concurrent page/dock requests share a single geometry worker.

Detailed boxes can contain hundreds of thousands to over a million triangles. Regeneration can take several seconds or longer depending on dimensions, features and hardware; a fixed frame rate or regeneration duration is not promised. The displayed curved-interface error is a tessellation target, not printer accuracy.

### Pending validation recorded for version 1.0.0

Live page/dock activation, permission handling and Plater delivery inside OrcaSlicer remain pending on Windows, macOS and Linux. No native visual validation is claimed by publication. Physical fitting, spring life, inserts, sealing and printing performance also require calibration.

A closed print-in-place lid spans a cavity above the bed. Evaluate bridging and removable supports in the slicer, and avoid filling the functional hinge gaps. Print-in-place does not imply support-free printing. Calibration print duration must come from the selected slicer profile.

The repository CI independently builds and tests the source on Windows, macOS and Linux. Its run history provides the current cross-platform result.
