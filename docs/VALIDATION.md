# Validation status

## Standard box gallery — 1.2.2, 2026-11-19

The built-in gallery now has eight standard designs, one per existing box style. Board-specific/IoT examples and duplicate accessory variants were removed. No PCB posts, ports, partitions or TPU gasket are enabled in these starting designs. Box geometry and the optional feature controls are unchanged. Personal presets remain separate. The 1.2.1 results below describe the previous seventeen-preset catalog; assess 1.2.2 using its own reports and CI revision.

The targeted local gallery/page/dock run passed 53 checks, with 25 export actions and 35 independently verified files, zero failures and zero console errors. It covered only `presets,general,dock`, not the complete E2E scope. The eight geometry cases and eleven cache/local-edit cases passed with `-B -W error`; standalone bundle/wheel smoke checks and four runner-correlation regressions also passed. Rugged captive export remains covered explicitly through its hinge control in the full runner, without reintroducing an extra preset. Generic-printer PT/EN workspace captures and their fourth presentation image were regenerated for the eight-model catalog. These checks do not constitute new native-application or physical-print acceptance.

## Complete Box E2E review — 1.2.1, 2026-11-19

This revision adds a real-browser/real-backend E2E runner for all eight styles, seventeen presets, enabled export targets, resources, page and dock. It reopens actual STL/3MF bytes and checks them independently against the delivered preview and print snapshot. Native IPC is deliberately disabled only in that development environment. See [reproduction and exact scope](E2E.md); native Windows observations below are separate evidence.

The review found and corrected a Rugged pin bore refilled by the lid-arm union, simultaneous clip/lid motion, individual-half export options for a captive Rugged hinge, nominal TPU contact independent of fit clearance, inaccessible removal of an incompatible gasket after a style change, and hex openings that ignored independent width/height changes. The Rugged animation now removes clips over the first 25% of travel before rotating the lid. Nominal gasket compression is 0.15 mm; it is not a measured seal rating. Sliding now has an upper detent and matching ceiling socket, a broad flat print underside and rear-corner relief; its five new tests and two unchanged legacy precision/retention tests passed without relaxing their original criteria.

A fresh Windows session of OrcaSlicer 2.5.1 loaded models from all eight styles. The table records representative configurations, not every parameter combination or a physical fit test. The earlier Sliding observation was superseded by a fresh rebuild/restart and the corrected native export/import below.

| Native configuration | Observed workflow |
| --- | --- |
| Lip Snap, 92 × 65 × 35 mm | Width edit, native STL/3MF export, base and lid loaded on the Plater. |
| Rugged pin and captive modes, 92 × 65 × 35 mm | Clip-removal/opening phases, native export and Plater loading. The pin mode displayed five separate pieces; captive export preserves the base/lid relationship. |
| Sliding, final corrected 90 × 65 × 35 mm | Closed/open course, native STL/3MF and both pieces loaded on the Plater. The pre-import originals had identical STL/3MF facets, two manifold closed oriented shells, and 5052.989 mm² of lid bed contact (99.786% of its XY envelope, 0.005 mm contact-plane tolerance). |
| Screw Corner, 92 × 65 × 35 mm | Closed preview and exported base/lid with four corner holes loaded. |
| Open bin, 92 × 65 × 42 mm, 48 mm hand openings | Height/grip edits, both openings visible in preview and model loaded. Serialized base independently had one closed oriented shell and Euler −2. |
| Pivot latch lid, 92 × 65 × 42 mm | Release and lift stages; base, lid and two levers loaded. |
| Stackable bin, 92 × 65 × 58 mm, 56 mm front access | Height/access edits and one container loaded. No physical stacking claim. |
| Equal-half PIP, 92 × 65 × 18 mm per half | 36.2 mm closed height, 180°→0° preview, then the preserved open assembly loaded from the closed preview. |

No slicing or printing was performed. Native macOS/Linux loading and physical calibration remain pending. Existing Anycubic acceleration warnings and the dense Rugged model warning are not treated as proof of a geometry defect or as approval to print. Imported project process settings must be reviewed before saving a profile.

The complete local Python run passed **159 tests in 704.989 seconds**, with `-B -W error`, optional Chromium coverage enabled and **no skips**. A subsequent **11-case focused follow-up** checked a two-string PT/EN instruction correction: preserve the exported part orientation rather than telling every lid to be flipped. Geometry and motion code were unchanged by that text follow-up. These counts describe separate runs and are not summed as unique tests. The complete browser-run result belongs to its exact recorded source hashes and CI revision; consult the [CI history](https://github.com/victorFernande/orca-box-generator/actions/workflows/ci.yml) and the change's pull request for completion and artifacts.

The initial complete browser run contained an obsolete negative assertion that expected raw STL to reject a 270 mm-wide part on a 260 mm bed. Existing STL export preserves part coordinates without XY placement, consistently with the reference generators; automatic 3MF export performs the bed-layout check. The corrected assertion requires the actual STL to remain 270 mm with exact facets, then requires 3MF rejection, no new 3MF file and an unchanged design. The existing height guard is unchanged. The earlier full local report retains its failed assertion; it is not relabeled as a passing full run. The complete CI run of the corrected revision is the approval record for that final contract.

The final isolated template/browser run, after the instruction-text correction, passed **12 layouts and 37 interactions**, with zero layout issues or script errors.

The native dock also exercised all four sections, PT/dark, a 120 × 65 mm PIP preset with half height changed to 15 mm, 180°→0°→180° movement, 3MF export and actual loading of the open assembly from the dock. Hex width/height were edited independently to 12 × 6 and 6 × 12 mm on the page; the preview changed and both configurations were exported.

Native application re-saving is not source-byte parity. In a separate inspection, Orca's recenter/save step collapsed one pair of original Rugged PIN vertices separated by approximately 0.00000155 mm, introducing two zero-area triangles in the re-saved base; the re-saved captive file had four. All five original PIN STLs passed strict checks, and corresponding facets located the rounding in Orca's rewritten coordinates. The re-saved Rugged files are explicitly not counted as strict mesh passes. Diagnostic welding recovered the expected closed shells, but no native files were repaired. Original exported-byte verification and native UI/loading acceptance remain distinct evidence.

Earlier validation counts below describe their own historical snapshots.

## Snap lever redesign — 2026-11-19

The current `snap_latch` has two lever latches articulated on the base, replacing the previous removable C-retainers. Four pieces are printed: base, lid and two levers with integral side pins. The pins pressure-fit through chamfered socket mouths. Both levers rotate to 90 degrees before the lid lifts, and stay attached to the base. Pivot diameter, lever width/thickness, hook retention and lid skirt depth remain independently editable within the validated geometric limits.

The independent combined run passed **17/17 tests in 92.129 seconds** with `-B -W error`: ten adapted functional checks and seven new lever checks. They verify sampled closed clearance, actual lid retention/release, pivot-axis purity, radial/axial capture, temporary mounting/cam interference with progressive entry, a real closing stop, accessible grip space and print-layer starts. The large-pin/thin-grip and maximum-clearance counterexamples are covered. Focused actual-triangle checks found no proper crossings or coplanar area overlap in the tested Snap parts; this is not an exact global proof over all legacy geometry or every parameter combination.

The post-freeze isolated browser passed **12 layouts and 37 interactions**, without layout/script errors. Five new checks inspect the actual WebGL model matrices during closed, partial-release, fully released/lid-seated and lifted phases, plus resizing. At 35% of opening both levers are at 90 degrees and the lid has not moved; later travel lifts the lid while keeping the levers on their base pivots.

The **new Snap page passed native geometry/export checks** in a fresh installation of the final geometry on Windows with OrcaSlicer 2.5.1. A 110 × 80 × 40 mm preset showed approximately 51° lever rotation at 20% opening with the lid stationary, 90°/lid still seated at 35%, then 50 mm lid lift at 100% with the levers fixed on the base. A subsequent 160 × 95 × 35 mm configuration with 10 mm skirt and 0.40 mm clearance regenerated. EN/light and PT/dark views were exercised. Native export produced a 3MF and four STL files; delivery to an empty Plater visually confirmed base, lid and both replacement lever objects. The installed bundle matched the distribution, and sibling-plugin/activation-state hashes remained unchanged. No slicing or printing occurred.

### Final rebuilt Windows dock and localization

After a fresh rebuild/restart on 2026-11-19, the **new Snap dock passed** inside OrcaSlicer 2.5.1 on Windows. Space → Speed Dial → Orca Box Studio — Painel Lateral opened the dock. Switching EN→PT immediately translated Padrão, Alvo de erro and the ready-status text without observed geometry regeneration; the displayed mesh was retained. The 110 × 80 × 40 mm preset traversed 0→100% opening. Changing pivot diameter from 3.0 to 3.2 mm regenerated while preserving 100% opening. Resources fields and print instructions were present in Portuguese. Dock 3MF export succeeded, and Send visibly loaded base, lid and two levers as four objects on the Plater with the dock open. This supersedes the three stale labels observed in the earlier page session.

The final focused UI subset passed **28 cases**: one localization, ten visual-template, eleven cache/local-edit and six articulated-case UI/bridge checks. These are focused runs, not additional unique cases to add to a full-suite total.

During closing in an earlier native session, Orca prompted to save the exported project's process settings (four walls, five bottom layers and 35% Gyroid infill). Choosing **Discard** restored the preceding profile without saving over it. No slicing or printing occurred. Review imported process settings and the actual printer profile before printing.

### Storage export correction and full-suite status

The earlier full snapshot completed **134 cases in 573.985 seconds: 133 passed and one errored**. The error was an obsolete storage-export fixture expecting the new four-part Snap, body 160 × 95 × 35 mm, to fit a 220 × 220 mm bed. The pivot/socket envelope and the current conservative arranger's spacing require more room. This was not a successful full run.

The fixture now verifies a 160 × 90 × 35 mm Snap on a 220 × 220 mm bed and 160 × 95 × 35 mm on a 260 × 260 mm bed, with default mating parameters. It also verifies actionable rejection of 160 × 95 × 35 mm on 220 × 220 mm, unchanged source vertices and no invalid output file. All **3 focused storage-export tests passed in 7.842 seconds**. The product packer was unchanged; these are specific verified layouts, not universal minimum beds or an optimum packing proof.

The **complete local run passed 136 tests in 574.594 seconds**, with `-B -W error`, Chromium enabled and **no failures, errors or skips**. It includes the final localization changes and corrected three-case storage-export coverage. Cross-platform results for each revision are available in the [CI run history](https://github.com/victorFernande/orca-box-generator/actions/workflows/ci.yml). Isolated checks of the standalone bundle and unpacked wheel also passed eight actual preview/print-geometry/3MF checks across `open_bin`, `snap_latch`, `stackable_bin` and `clamshell_pip`; the `_any` bundle was byte-identical. The previous Snap native result and older complete-run counts below concern the superseded mechanism. Unchanged styles retain their separately recorded results. Native macOS/Linux integration and physical fitting, release force, fatigue, bridges and load remain untested.

### CI portability follow-up

The 136-case local run above preceded a small platform follow-up. JavaScript test subprocesses now use explicit UTF-8 for input and output, including on Windows legacy locales. The page adapter enforces the reference header's 43 px minimum height so fallback fonts cannot shift the workspace upward. The frozen reference, one-pixel comparison tolerance and dock rules are unchanged. The repeated local browser run passed all 12 layouts and 37 interactions with no issues; full-page header height remained 43 px.

The 44-case focused runner completed in both the normal Windows locale and an emulated CP1252 locale: 43 cases passed and one optional browser case was skipped in each run. That optional case had passed in the 136-case local baseline; the separate complete browser run also verified host-style adaptation and the interface interactions. A legacy-encoding control first reproduced the old Unicode failure, while explicit UTF-8 preserved the round trip of the combining cedilla and the less-than-or-equal symbol. Geometry and motion code did not change in this follow-up. Consult the per-revision CI history for the final cross-platform result.

## Version 1.2 historical baseline before lever redesign — 2026-11-18

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

### Articulated PIP case targeted verification

The post-stacking 89-case and 26-interaction results above are the baseline before adding the articulated case. After adding it and correcting the initial print-layer support geometry, all **8** independent cases in `tests/test_clamshell_mating.py` passed with `-B -W error`.

Both actual float32 halves are connected closed manifold shells, each genus four/Euler minus six, with correct normals and analytic-field/chord agreement. Equal external half height `H` produces a closed body height of `2H + fit_clearance`; both open halves have broad real floor surfaces at Z=0. The pure opening transform matches an independent rotation. Vertex, face-centre and weighted interior-face samples clear the opposite solid in both query directions at **83 poses** from 0 to 180 degrees, including closely spaced endpoint poses. Small axial travel remains clear, while integral end stops prevent larger displacement through the base bores.

Layer-event checks slice actual triangles between vertex-Z events below the body rim. Each positive filled contour must originate at the bed or overlap same-half material below the event. Splitting a previously supported contour is allowed; a new suspended tube/head start is not. The final barrels and lid heads have integral floor pedestals. Short axle bridges remain between supports, so these computational checks do not establish support-free printing or physical hinge release.

The **3** actual export tests passed after this correction: one 3MF object/build transform preserves both open shells and float32 arrays, binary STL rewelds to the same two oriented shells, and an undersized bed rejects the assembly without rearrangement/scaling. The isolated browser run passed **12 layouts and 32 interactions**, with no layout/script issues, before the last label-only patch. The final suite and native record below cover the later verification; targeted counts are not added together as a claimed total.

### Pre-lever local suite and Windows native observations

The full local command with `-B -W error` passed **114 tests in 390.310 seconds with no skips**, including the optional Chromium cascade test. One new gap/HUD label regression was added after that run had imported its tests. The later **17-case focused UI/cache follow-up passed**, including that new regression. Current test discovery is **115 cases**; an exact full 115-case CI result remains pending. The counts describe distinct runs, not 131 unique tests.

The 12-layout/32-interaction browser run preceded that final label-only patch. Focused tests covered the change, and the final native session confirmed the PT/EN labels in the actual application.

**Observed native session: OrcaSlicer 2.5.1 on Windows, final Box 1.2 bundle.** The application was launched fresh after installation. Version/activation were confirmed in the plugin manager; existing activation metadata and the checked hashes of three sibling plugin bundles were preserved. The studio page showed 17 presets. The following operations were visually confirmed:

| Native configuration | Observed result |
| --- | --- |
| Articulated case, 120 × 65 mm, half height changed from 14 to 18 mm | PT/EN, light/dark and 180°→0° opening controls worked; closed height displayed 36.2 mm. Export/delivery while the preview was closed loaded the correct open 180° captive assembly on the Plater. |
| Stackable bin, 140 × 100 mm, height changed from 80 to 100 mm, front access width 85 mm | Regenerated and appeared as the single intended model on the Plater. This was not a physical stacking test. |
| Open bin, height 72 mm, hand-opening width 48 mm | STL export and native Plater loading succeeded; the wall openings were visibly present. |
| Previous removable clip lid, 160 × 95 × 35 mm, skirt depth 10 mm — superseded | Closed preview and 3MF loading succeeded for the former design. This does not validate the replacement base-mounted levers. |
| Dock via Space → Speed Dial → Orca Box → Orca Box Studio — Painel Lateral → Enter | Shape, Features, Print and Presets tabs worked. The short articulated preset began open at 180° with correct gap labels; dock 3MF export and Send to Plater loaded the grouped PIP assembly. |

All 3MF imports in this session were opened **as projects**, keeping them separate from existing models. The native session ended with the PIP assembly on the Plater and the dock open. Visual confirmation establishes actual loading for these observations; the client status correctly continues to report only that an import request was transmitted.

No slicing or physical printing was performed. An acceleration-above-limit warning came from the selected existing Anycubic Kobra 260 × 260 printer profile; the validation session did not alter acceleration settings. Review the actual printer profile and its limit warnings before printing. Native macOS/Linux integration, physical fit, release force, service life, bridge quality and calibration prints remain pending.

### Scope and remaining checks recorded before lever redesign

Version 1.2 has eight styles and seventeen editable presets. `open_bin` exports an open base with optional paired hand openings. `snap_latch` exports a base, flat removable lid and two separate front clips. Its `lid_wall_height` is the skirt depth below the cap; the flat cap top is `height_z + fit_clearance + lid_height`. Body dimensions are external base dimensions in millimetres, not the complete catch/clip envelope or the inside cavity.

Local source, export, packaging and browser checks passed as recorded above, with a 114-case no-skip full run and focused verification of the final added regression. Final Windows page/dock generation, export and Plater loading were observed separately in the native session. The exact current 115-case full CI run remains pending. The earlier version 1.1 Windows observations below are historical; current native evidence comes from the separate version 1.2 session. Live macOS/Linux acceptance, slicing, physical print/fit, grip comfort, inserts, sealing and latch life remain pending.

See [generation measurements](PERFORMANCE.md) for separate timing methodology and limits; the full-run timing above is separate from controller generation timings. The generic fit kit is unavailable for the three storage styles and the articulated case. Test smaller configurations of their actual parts with the same wall thickness, clearance, clip dimensions and retention; uniform mesh scaling changes these values.

For `stackable_bin`, total height includes the foot. Matching outside X/Y, corner radius, wall, foot height and stacking clearance define a family; heights/front access may differ. The assembly offset is `lower.height_z - upper.stack_foot_height`, and combined height is the sum of the two heights minus the upper foot height. Only one base is exported per design.

For `clamshell_pip`, only **Base + lid** and **Complete set** are supported, producing one open two-shell assembly. Individual halves, PCB posts, cutouts, dividers, TPU and the generic kit are rejected. The print envelope is width X, depth `2*depth_y + 2*hinge_separation` and maximum height `height_z + fit_clearance/2 + outer_hinge_radius`. It has no initial front latch. No source-photo assets are included.

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
