# User manual — Orca Box Studio

## Installation and interface

After installation or an update, close and reopen OrcaSlicer. Check the version and enable **Orca Box Studio** in the plugin manager. The Vase Studio template provides the compact header, printer synchronization, filtered card gallery, paired sliders/numeric fields, feature cards and fixed export footer.

The dock uses **Shape, Features, Print and Presets**, with a compact preview above the controls. Visual material, camera, wireframe and section tools do not change exported surfaces or select a printing filament.

## Design an enclosure

Open the full Gerador de Caixas tab or run the docked panel. Choose one of 15 editable starting designs. PCB presets provide initial envelopes: check the actual board model and revision. All measurements are in millimetres. Width X and depth Y describe the outside base body; height Z is the base-part height. In the stackable style, it includes the foot; for the other styles it runs from the outside bottom to the rim. These are not inside dimensions or the complete envelope including lid, catches and clips. The XY origin is centered on the base; Z=0 is the outside bottom, or the bottom of the foot in the stackable style.

Lip snap includes a locating skirt, a retaining bead and its matching female groove. Rugged adds structural ribs, a hinged lid and two removable spring clips. Sliding uses 45-degree rails, a front insertion opening, a handle and a rear detent. Screw corner provides four integrated corner posts and matching lid clearance holes.

The three storage styles bring the total to seven:

- **Open bin (`open_bin`):** exports only the base. Enable or disable two rounded hand openings and choose left/right or front/back faces. Adjust opening width, opening height and the upper margin. These are wall openings, not external handles. Corner, floor and upper-bridge checks preserve a continuous shell; test hand comfort on a real print. This style has no lid, lid gasket or generic fit kit.
- **Latch lid (`snap_latch`):** a fully removable flat cap and two separately printed front clips. Adjust clip width/thickness, hook retention and lid skirt depth. Seat the lid, install the clips, and release them manually before lifting the lid. The detent requires temporary flexure along the insertion/removal path; the sampled closed positions have clearance. No release force is inferred.

- **Stackable bin (`stackable_bin`):** one open base with a lowered front access and an indexing foot underneath. Adjust access width/drop, foot height and stacking clearance. The full-height side and rear rims provide bearing surfaces. This style exports only the base, without a lid, gasket or generic fit kit.

For the latch lid, the upper face is at `height Z + fit clearance + lid thickness`. The `lid_wall_height` control sets the skirt depth **below** the cap, into the base; it does not add a wall above the lid. The separate print pose places the flat face on the bed with the skirt pointing up. Clips have their own print orientation. Check the arrangement in the slicer; the clip envelope can extend above or beyond the cap.

Fit clearance is measured **per side**, between 0.10 and 0.40 mm. A setting of 0.20 mm gives a 0.40 mm difference between opposite locating widths. It is separate from a post's explicitly defined hole diameter. Lip Snap also has **Snap interference** (`snap_retention`, 0.03–0.30 mm): the radial bead interference that must pass the entry ramp. This is independent of the locating clearance and does not establish safe material strain. Sliding lid thickness follows the rail profile and clearance; the unrelated cap-thickness/skirt controls are hidden for this style.

Simple Lip Snap shells and the storage styles use connected contour surfaces. Complex accessories can still require the implicit CSG surface and take longer; export reuses the validated canonical meshes. See the [reproducible generation measurements](PERFORMANCE.md). Mesh updates run in the background. You can keep editing; the newest design replaces obsolete requests. The page and dock share geometry and user presets. Language and theme remain local viewing preferences.

## Stack different heights

All dimensions are millimetres. In this style, total height `H` includes the foot height `P`. The outside body underside is at `Z=P`; the inside floor is at `Z=P + floor thickness`. The guide foot is solid centrally to support printing. In the assembled stack, the upper body shoulders bear on the lower bin's side/rear rims; the foot indexes into the opening.

A mating family has equal outside X/Y dimensions, corner radius, wall thickness, foot height and stacking clearance. Total height and front access may differ. **Stacking clearance** (`stack_clearance`, 0.10–0.80 mm per side) is independent of the other joint clearance controls. Excess lateral travel encounters the guide/inside wall rather than a free sliding surface.

The upper bin's assembly position is `Z = lower total height − upper foot height`. Combined height is `lower height + upper height − upper foot height`. For example, compatible 60 and 100 mm bins with a 2 mm foot have an upper offset of 58 mm and combined height of 158 mm. This describes the assembly after printing; export and print the individual bins separately.

The tests check three bearing patches and the empty upper bin's mass projection within the support polygon in sampled configurations. They do not establish a load capacity or stability under arbitrary contents. Test the actual material, clearances and load distribution. This is original geometry without a claim of compatibility with third-party organizers.

## PCB supports, ports and partitions

Add PCB supports in the Features area. Drag them in the 2D floor editor or enter exact X/Y positions. Height is measured from the inside floor. Outside diameter, bore diameter and blind depth are editable. The software preserves at least 1.2 mm below a blind bore and checks the lid clearance. Insert dimensions vary by manufacturer: starting M2/M2.5/M3 values are suggestions. M3 pilot mode starts at 2.5 mm; calibrate it for your screw and material.

Panel openings can be placed on the front, back, left or right wall. U measures horizontal position from that face's center; Z measures height from the outside bottom. USB-C and HDMI dimensions are editable passage envelopes. DC uses a circular hole. Slots and hexagons can be repeated into a vent grille. The model checks corner/floor/lid keep-outs and a 1.2 mm bridge between neighbouring openings.

Enter comma-separated divider positions along X or Y. Dividers are united with the floor and sidewalls. A divider that intersects a PCB support is rejected to keep the requested mounting feature usable.

## Inspect and assemble

Drag to orbit, scroll to zoom and use Home to frame the model. The lower slider lifts/slides/rotates the lid. X-ray and axial clipping are inspection tools; they do not alter exported geometry. The preview displays the same generated Python mesh used for manufacturing, with a different pose or print orientation when appropriate.

Remove the Rugged clips before opening. A pin hinge uses a separate removable axle. A captive print-in-place hinge has the axle and retaining ends integrated into the lid. Export **Base + lid** or **Complete set** for this mode: base and lid remain one object containing two closed shells in their assembled positions. The lid spans a substantial cavity above the bed. Assess bridging and removable supports in the slicer, and keep support out of the functional hinge gaps. Print-in-place is **not** promised to be support free. The motion preview is a kinematic check, not a physical strength or print validation.

Enable a perimeter gasket only with a lifting lid and adequate wall width. Export the TPU gasket separately and assign a suitable flexible material in the slicer. The plugin does not claim waterproofing; compression, material and physical sealing require testing.

## Calibrate and manufacture

For the original four styles, the generic compact kit contains a small matching base/lid pair, a bore matching the first configured support (reference M3 when no supports exist) and a snap tongue. Test fit and material flex before printing the finished part. The kit uses a Lip Snap pair and does not reproduce every complete mechanism. Print duration comes from the slicer and depends on the machine/profile.

**Open bin, Latch lid and Stackable bin have no generic fit kit.** First create a smaller configuration with the same wall/floor thickness and clearance. Keep clip dimensions, hook retention and skirt depth when testing the latch style. For stacking, test two heights of the same family while preserving wall/radius, foot and stacking clearance. Export and test the actual pieces. Uniform scaling in the slicer also changes the clearances and is not an equivalent calibration.

Binary STL writes each selected item separately, except the captive assembly, which remains one multi-shell mesh. 3MF preserves item names, assembled captive positions and a collision-free layout on the bed. Oversized parts must be redesigned; the exporter does not silently rescale them.

Send to Plater targets the current running OrcaSlicer instance. Optional mechanical slicing applies four walls, five top/bottom layers and structural infill. Transport success means that the import request was transmitted, not that model loading or slicing has completed. Exported files remain available if dispatch fails.

Windows uses WM_COPYDATA, macOS Cocoa and Linux the session D-Bus protocol. Automated tests use a simulated host and run across platforms. Native validation of version 1.2 remains pending; the preceding version's Windows page/delivery observation is recorded in [validation status](VALIDATION.md). Open a 3MF as a project or use an empty plate; arrange objects when importing into an occupied project. The ten version 1.2 mating tests and five independent stacking tests check sampled paths, contacts and clearance. A clear closed position does not remove the deliberate temporary interference of a snap detent, or establish printed fit. Curved surfaces are tessellated. The shown fit-interface chord-error target does not describe the accuracy of a real printer. Hardware fit, sealing and spring durability require physical calibration.
