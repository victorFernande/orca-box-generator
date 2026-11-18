# Implementation and verification notes

## Architecture

Each installation is independent: Python 3.12+, NumPy, inline offline HTML/CSS/JavaScript and WebGL2. The source package and the flattened PEP 723 file expose a single `@orca.plugin` entry point registering a Page and a Script/Dock capability. Infrastructure adapted from Orca Gear Studio retains its MIT notice. No runtime sibling-project dependency, telemetry, CDN or external modeller is required.

The public JSON-compatible parameter API is `normalize_params()` plus `validate_params()`. Mesh functions expose `MeshData`, `generate_box_mesh()`, `generate_fit_test_kit()` and `collect_target_meshes()`. The same boundary arrays feed preview and STL/3MF. `build_part_field()` exposes the analytic solid for geometric tests.

## Surface construction

Analytic signed fields implement rounded boxes, cylinders, slabs, unions and differences. Features join in the field before extraction, rather than being concatenated as intersecting solids. A conforming six-tetrahedron cell decomposition extracts one surface; edge roots are refined against the analytic field. A translated lattice avoids exact iso-node ambiguity. Curved interface neighbourhoods and primitive height events receive local refinement. Extruded height spans use coarse slabs to control cost.

After float32 conversion, only the minimum edges of exactly collinear triangles are collapsed, with a strict 0.002 mm safeguard. Convex coplanar patches can be replaced by fans that preserve every boundary vertex. Concave patches and patches with holes retain their original conforming triangulation. Closed directed edge pairing, connected components, signed volume and geometry-specific Euler characteristic are tested. Euler characteristic is not universally 2: through-bores and hinge barrels change the genus.

The interface chord target is `min(clearance/4, 0.04 mm)`. Tests sample surface errors and functional interfaces; this is separate from printed dimensional accuracy. Very large or highly featured inputs can exceed the grid budget and report a useful error instead of allocating unbounded memory.

## Shared session and native transport

The page and dock share canonical geometry. Each preview viewer retains its response/request ID; identical simultaneous requests share one computation, and stale geometry requests are coalesced. A worker owns its running state, preventing an old callback from clearing a newer worker's flag. Language and theme do not cause geometry broadcasts. Personal presets use atomic file replacement in the plugin's private storage.

Native transports are WM_COPYDATA, Cocoa main-queue file opening and Linux session D-Bus `AnotherInstance`, matched by the current process owner. Linux no-reply delivery confirms transport, not load completion. Export and host preset updates happen off the UI thread. Automatic configuration does not alter the installed printer or filament profiles.

## Functional and physical verification

The suite covers four base/lid styles, twelve presets, posts, panel tunnels, dividers, TPU, the fit kit, snap retention, sampled dimensional error, hinged motion, captive export grouping, standalone bundle/wheel contracts, host-message failures and preview concurrency. A print-in-place export groups base and lid as one multi-shell object, preserving relative coordinates during bed packing. Clips remain separate and are removed before opening.

Automated geometry and API tests do not establish physical printing, waterproofing, insert compatibility or spring durability. Native visual interaction in real Windows/macOS/Linux hosts is a separate pending acceptance step. Publication does not claim those checks have occurred. No automatic OrcaCloud publication is included.

Protocol references: [OrcaSlicer v2.5.1 InstanceCheck.cpp](https://github.com/OrcaSlicer/OrcaSlicer/blob/v2.5.1/src/slic3r/GUI/InstanceCheck.cpp), [host API](https://github.com/OrcaSlicer/OrcaSlicer/wiki/host).
