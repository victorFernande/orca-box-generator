# Implementation and verification notes — version 1.2

## Architecture and parameter contract

Each installation is independent: Python 3.12+, NumPy, inline offline HTML/CSS/JavaScript and WebGL2. The source package and flattened PEP 723 file expose one `@orca.plugin` entry point registering a Page and Script/Dock capability. Infrastructure adapted from Orca Gear Studio retains its MIT notice. No runtime sibling-project dependency, telemetry, CDN or external modeller is required.

The JSON-compatible parameter boundary is `normalize_params()` plus `validate_params()`. Mesh APIs expose `MeshData`, `generate_box_mesh()`, `generate_fit_test_kit()` and `collect_target_meshes()`. `build_part_field()` exposes the analytic solid for independent membership/clearance checks. Seven styles and fifteen editable starting presets are available: `lip_snap`, `rugged_box`, `sliding_lid`, `screw_corner`, `open_bin`, `snap_latch` and `stackable_bin`.

All dimensions are millimetres. `width_x` and `depth_y` describe the external base body; `height_z` is the outside floor-to-rim height for the non-stacking styles; in `stackable_bin` it is the total base-part height including the indexing foot. They are not cavity dimensions or the complete assembled envelope. Hinges, catches and clips can project beyond the body. For `snap_latch`, the flat cap top is `height_z + fit_clearance + lid_height`; `lid_wall_height` defines its skirt depth below the cap, not walls above it. The independent clip envelope can extend further.

`fit_clearance` is a dimensional gap per side. Lip Snap `snap_retention` is separate radial bead interference; its entry profile is progressively chamfered. Storage `latch_retention`, clip width and clip thickness control a different mechanism and do not estimate release force. `open_bin` can create two capsule-shaped hand openings on either left/right or front/back faces; their dimensions and upper margin are independent controls. It has no lid. `snap_latch` uses a removable flat cap and two separate front clips with ramped detent nibs and matching catch sockets. Release the clips before lifting the lid.

## Stacking contract

`stackable_bin` is an original open-access body with a solid central guide foot and load-bearing shoulders. `height_z` includes `stack_foot_height` (1–5 mm); the body underside is at the foot height and the inside floor at foot height plus `floor_thickness`. `stack_clearance` (0.10–0.80 mm per side) is independent of `fit_clearance`. `front_access_width` and `front_access_drop` lower the central front while retaining the full-height side/rear rims. Only the base is exported.

`stacking_pose_z(lower, upper)` validates both designs and their mating family: equal `width_x`, `depth_y`, `corner_radius`, `wall_thickness`, `stack_foot_height` and `stack_clearance` within the implementation tolerance. Heights and front-access parameters may differ. It returns `lower.height_z - upper.stack_foot_height`. That places the upper body's shoulders on the lower U rim, with its guide entering the cavity. Combined height is `lower.height_z + upper.height_z - upper.stack_foot_height`. This describes the physical assembly, not a request to print an assembled stack.

Five independent tests in `tests/test_stackable_mating.py` passed. Actual mesh faces supply finite upward/downward contact patches on both sides and the rear, with the empty upper mesh's mass projection inside the contact triangle. Samples check both directions for penetration along the assembly pose, vertical insertion and within-clearance lateral offsets; further downward movement or excess lateral movement encounters the supporting/indexing surfaces. Different heights/front accesses and incompatible-family rejection are covered. Additional extreme-radius, foot-height and clearance mesh checks passed. This is geometric evidence without a load rating, friction model or arbitrary-content tipping guarantee.

The general idea was informed by [Techro3D's stackable storage containers](https://makerworld.com/en/models/2465290-stackable-storage-boxes-containers-by-techro3d). The parameterized surfaces and tests here are original; no source mesh or visual asset is reused, and no mating compatibility with the reference products is asserted.

## Surface construction and reuse

Simple Lip Snap shells and the three storage styles use connected contour surfaces. Rounded corners retain a chord-error budget; capsule handle tunnels, catch surfaces and extruded clip contours share their boundary vertices. The fast path is checked against the same analytic solid used for the general field model. An attached feature is not represented by an overlapping closed mesh inside the base.

Inputs outside that path use analytic signed fields for rounded boxes, cylinders, slabs, unions and differences. Features join before extraction. A conforming six-tetrahedron decomposition extracts the surface, with roots refined against the field. A translated lattice avoids exact iso-node ambiguity; curved interfaces and primitive height events receive refinement. Extruded height spans use coarse slabs where applicable.

In that general path, float32 degeneracies are addressed by collapsing only minimum edges of collinear triangles, with a 0.002 mm safeguard. Convex coplanar patches can be replaced by fans preserving their boundary; concave patches and holes retain conforming triangulation. Directed edge pairing, connectivity, volume and appropriate Euler characteristic are checked. Euler characteristic is not universally two: the open bin with two hand openings has genus two and Euler characteristic minus two.

The interface chord target is `min(fit_clearance/4, 0.04 mm)`. Field samples on actual float32 vertices and triangle interiors check the geometric approximation; this is separate from printer accuracy. The general grid budget rejects excessive inputs rather than allocating without a bound. Complex accessories can still be slower than simple contour shells; see [generation measurements](PERFORMANCE.md).

The controller retains validated canonical part meshes in a byte-bounded cache. `orient_mesh_for_print()` transforms copies, allowing preview and export to reuse the same surfaces. Encoded preview arrays are also cached. Identical in-flight requests share a computation, and stale preview requests are coalesced. These changes remove orientation-only regeneration without promising a fixed latency for every model or host.

## Functional verification

Ten independent tests in `tests/test_functional_mating.py` passed with `-B -W error`. They check separate Lip retention/clearance and an axial lead-in; absence of permanent closed Rugged clip overlap in the sampled configurations; a Sliding detent barrier; and the new storage mechanisms. The latter checks include actual connected float32 meshes, opposite directed edges, manifold vertex links, field/chord parity, hand openings with genus-two topology, neutral closed clip clearance, progressive clip entry, a temporary withdrawal barrier, vertical lid retention with clips installed, and lid removal after releasing them.

A watertight mesh alone does not establish an operative joint. Closed-state clearance is distinct from deliberately transient interference during snap insertion/removal. These checks sample geometric paths and solids; they do not model elastic deformation, contact force, friction, fatigue or print shrinkage. Physical fitting, material selection, insert compatibility, grip comfort, sealing and spring durability require printed trials.

The generic fit kit is unavailable for `open_bin`, `snap_latch` and `stackable_bin`. It uses a small Lip Snap pair, a bore and a tongue, so it is not a calibration surrogate for every mechanism. Test a smaller configuration of the actual storage parts while retaining thicknesses, clearances, clip dimensions and retention; uniformly scaling an exported mesh changes the fit too.

## Shared session and native transport

The page and dock share canonical geometry and private user presets, while language and theme remain viewing preferences. A worker owns its running state, preventing an older callback from clearing a newer worker flag. Presets use atomic file replacement in private storage. Native transport uses WM_COPYDATA on Windows, Cocoa main-queue file opening on macOS and the Linux session D-Bus instance service with unique-owner routing. Transport acknowledgement means request transmitted, not that loading or slicing completed. Export and host-preset updates run off the UI thread; automatic configuration does not modify installed printer/filament profiles.

The post-stacking full run completed 89 cases without failures in 333.878 seconds; its optional browser-cascade case was then enabled and passed separately. Final focused UI/cache and theme checks also passed after the print-help update. Twelve browser layouts and 26 interactions passed, followed by the same 26 interactions on the final UI. Live native version 1.2 acceptance remains pending; see [validation status](VALIDATION.md). Earlier Windows page/generation/export/delivery observations belong to version 1.1 and remain historical evidence. No version 1.2 native, slicing or physical-print approval is inferred from them. No automatic OrcaCloud publication is included.

Protocol references: [OrcaSlicer v2.5.1 InstanceCheck.cpp](https://github.com/OrcaSlicer/OrcaSlicer/blob/v2.5.1/src/slic3r/GUI/InstanceCheck.cpp), [host API](https://github.com/OrcaSlicer/OrcaSlicer/wiki/host).
