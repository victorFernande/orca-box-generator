# User manual — Orca Box Studio

## Installation and interface

After installation or an update, close and reopen OrcaSlicer. Check version **1.2.1** and enable **Orca Box Studio** in the plugin manager. Open the full **Gerador de Caixas** tab.

The verified dock route on Windows with OrcaSlicer 2.5.1 is:

1. From the main OrcaSlicer workspace, press **Space** to open Speed Dial.
2. Type **Orca Box** and select **Orca Box Studio — Painel Lateral**.
3. Press **Enter**. The dock offers **Shape, Features, Print and Presets**.

The Vase Studio template provides the compact header, printer synchronization, filtered card gallery, paired sliders/numeric fields, feature cards and fixed export footer.

The dock uses **Shape, Features, Print and Presets**, with a compact preview above the controls. Visual material, camera, wireframe and section tools do not change exported surfaces or select a printing filament.

## Design an enclosure

Open the full Gerador de Caixas tab or run the docked panel. Choose one of 17 editable starting designs. PCB presets provide initial envelopes: check the actual board model and revision. All measurements are in millimetres. Width X and depth Y describe the outside base body; height Z is the base-part height. In the stackable style, it includes the foot; in the articulated case, it is the height of each half; for the other styles it runs from the outside bottom to the rim. These are not inside dimensions or the complete envelope including lid, catches and clips. The XY origin is centered on the base; Z=0 is the outside bottom, or the bottom of the foot in the stackable style.

Lip snap includes a locating skirt, a retaining bead and its matching female groove. Rugged adds structural ribs, a hinged lid and two removable spring clips. Sliding uses 45-degree rails, a front insertion opening, a handle and a rear detent. Screw corner provides four integrated corner posts and matching lid clearance holes.

Three storage styles and the articulated case bring the total to eight:

- **Open bin (`open_bin`):** exports only the base. Enable or disable two rounded hand openings and choose left/right or front/back faces. Adjust opening width, opening height and the upper margin. These are wall openings, not external handles. Corner, floor and upper-bridge checks preserve a continuous shell; test hand comfort on a real print. This style has no lid, lid gasket or generic fit kit.
- **Latch lid (`snap_latch`):** four printed parts: base, flat lid and two levers with integral pivot pins. The levers mount in the base sockets and stay articulated to it; their hooks retain the lid tabs. Rotate both latches open before removing the lid. Adjust lever width/thickness, hook retention, pivot diameter and lid skirt depth. The click requires temporary flexure while the sampled closed state has clearance; no printed release force is inferred.

- **Stackable bin (`stackable_bin`):** one open base with a lowered front access and an indexing foot underneath. Adjust access width/drop, foot height and stacking clearance. The full-height side and rear rims provide bearing surfaces. This style exports only the base, without a lid, gasket or generic fit kit.

- **Articulated case (`clamshell_pip`):** two equally deep halves with two integral captive-axle hinges. Inspection opens from 0 to 180°. Export preserves both halves open at 180°, floors on the same bed plane, as one object containing two closed shells. This initial style has no front latch.

For the latch lid, the upper face is at `height Z + fit clearance + lid thickness`. The `lid_wall_height` control sets the skirt depth **below** the cap, into the base; it does not add a wall above the lid. The separate print pose places the flat face on the bed with the skirt pointing up. Clips have their own print orientation. Check the arrangement in the slicer; the clip envelope can extend above or beyond the cap.

Fit clearance is measured **per side**, between 0.10 and 0.40 mm. A setting of 0.20 mm gives a 0.40 mm difference between opposite locating widths. It is separate from a post's explicitly defined hole diameter. Lip Snap also has **Snap interference** (`snap_retention`, 0.03–0.30 mm): the radial bead interference that must pass the entry ramp. This is independent of the locating clearance and does not establish safe material strain. Sliding lid thickness follows the rail profile and clearance; the unrelated cap-thickness/skirt controls are hidden for this style.

Simple Lip Snap shells and the storage styles use connected contour surfaces. Complex accessories can still require the implicit CSG surface and take longer; export reuses the validated canonical meshes. See the [reproducible generation measurements](PERFORMANCE.md). Mesh updates run in the background. You can keep editing; the newest design replaces obsolete requests. The page and dock share geometry and user presets. Language and theme remain local viewing preferences.

## Assemble and operate the lever latches

Print the base, lid and two levers in their exported orientation. Each lever has integral pivot pins. With the lid out of the way, align the pins with the chamfered mouths of the matching front sockets and press the lever toward the base to seat it. The socket mouths retain the pins radially, while the body between the sockets limits axial withdrawal. Test one latch before fitting the other and preserve the flexible regions.

**Pivot diameter** (`latch_pivot_diameter`, 2.4–4.0 mm) changes the pins and sockets. Hook retention is a separate dimension, not a force setting. Pivot size, thickness, clearance and width need enough space at the front of the base; incompatible combinations are rejected. Flat hub/pin faces support the exported lever print pose. Assess bed adhesion, bridges and supports in the slicer; support-free printing is not guaranteed.

The opening control follows the mechanism: both levers first rotate to 90 degrees with the lid stationary; then the lid lifts while the levers remain on the base. Physically open both latches before taking off the lid. To close it, seat the lid and turn the levers back over its tabs. Pulling the levers off the base is not part of normal opening.

Progressive entry and an angular click cause deliberate transient contact, separate from neutral closed clearance. This does not establish printed fit, release force or service life. Print a smaller trial while preserving pivot, clearances and thicknesses. If all four parts do not fit one 3MF layout, reduce the project dimensions or export STL and print in batches; do not scale down the mating geometry in the slicer.

## Print the articulated case

**Height of each half** is the external height `H` of both the base and lid. This lid does not use the shallow-cap thickness control from the other styles. Floor and wall thicknesses apply equally to both halves. Closed body height is `2H + c`, where `c` is the closing gap (`fit_clearance`). The motion preview does not establish physical movement after printing.

**PIP clearance** (`pip_clearance`, 0.20–0.60 mm) is the radial/axial clearance of the hinge. **Hinge separation** (`hinge_separation`, 4–12 mm) moves the axis away from the body; incompatible radius/separation combinations are rejected. Width X and depth Y still describe one half. The open print envelope has width X, depth `2 × Y + 2 × separation` and maximum height `H + closing gap/2 + outer hinge radius`. Barrels extend above the rim; check this envelope against the printer.

Select **Base + lid** or **Complete set**. Both halves export open as one captive two-shell object, with both outside floors at Z=0. Preserve that relationship when placing it on the bed; splitting/rearranging the shells breaks the hinge placement. Axles and end heads belong to the lid and have integral pedestals down to its floor. Short axle bridges remain between supports. Inspect them in the slicer, keep support out of functional clearances and print a test assembly. Support-free printing, automatic release and free movement after printing are not guaranteed.

The initial style rejects PCB supports, ports, partitions, TPU gasket, the generic fit kit and individual-half exports. Incompatible requested parameters remain present and produce an error; adjust them or choose another style. Hinge load, force and service life have not been physically tested.

## Stack different heights

All dimensions are millimetres. In this style, total height `H` includes the foot height `P`. The outside body underside is at `Z=P`; the inside floor is at `Z=P + floor thickness`. The guide foot is solid centrally to support printing. In the assembled stack, the upper body shoulders bear on the lower bin's side/rear rims; the foot indexes into the opening.

A mating family has equal outside X/Y dimensions, corner radius, wall thickness, foot height and stacking clearance. Total height and front access may differ. **Stacking clearance** (`stack_clearance`, 0.10–0.80 mm per side) is independent of the other joint clearance controls. Excess lateral travel encounters the guide/inside wall rather than a free sliding surface.

The upper bin's assembly position is `Z = lower total height − upper foot height`. Combined height is `lower height + upper height − upper foot height`. For example, compatible 60 and 100 mm bins with a 2 mm foot have an upper offset of 58 mm and combined height of 158 mm. This describes the assembly after printing; export and print the individual bins separately.

The tests check three bearing patches and the empty upper bin's mass projection within the support polygon in sampled configurations. They do not establish a load capacity or stability under arbitrary contents. Test the actual material, clearances and load distribution. This is original geometry without a claim of compatibility with third-party organizers.

## PCB supports, ports and partitions

Add PCB supports in the Features area. Drag them in the 2D floor editor or enter exact X/Y positions. Height is measured from the inside floor. Outside diameter, bore diameter and blind depth are editable. The software preserves at least 1.2 mm below a blind bore and checks the lid clearance. Insert dimensions vary by manufacturer: starting M2/M2.5/M3 values are suggestions. M3 pilot mode starts at 2.5 mm; calibrate it for your screw and material.

Panel openings can be placed on the front, back, left or right wall. U measures horizontal position from that face's center; Z measures height from the outside bottom. USB-C and HDMI dimensions are editable passage envelopes. DC uses a circular hole. Slots and hexagons can be repeated into a vent grille. Hexagon width and height independently define its complete envelope on each axis; unequal proportions may stretch the six-sided shape rather than preserve a regular hexagon. The model checks corner/floor/lid keep-outs and a 1.2 mm bridge between neighbouring openings.

Enter comma-separated divider positions along X or Y. Dividers are united with the floor and sidewalls. A divider that intersects a PCB support is rejected to keep the requested mounting feature usable.

## Inspect and assemble

Drag to orbit, scroll to zoom and use Home to frame the model. The lower slider lifts/slides/rotates the lid. X-ray and axial clipping are inspection tools; they do not alter exported geometry. The preview displays the same generated Python mesh used for manufacturing, with a different pose or print orientation when appropriate.

Remove the Rugged clips before opening. The animation uses the first 25% of the control to move both clips out by 15 mm while the lid stays closed, then rotates the lid from 0 to 180 degrees. A pin hinge uses a separate removable axle. A captive print-in-place hinge has the axle and retaining ends integrated into the lid. Export **Base + lid** or **Complete set** for this mode: base and lid remain one object containing two closed shells in their assembled positions. Individual base/lid exports are blocked in this mode; compatible gasket and kit targets remain independent. The lid spans a substantial cavity above the bed. Assess bridging and removable supports in the slicer, and keep support out of the functional hinge gaps. Print-in-place is **not** promised to be support free. The motion preview is a kinematic check, not a physical strength or print validation.

Enable a perimeter gasket only with a lifting lid and adequate wall width. Export the TPU gasket separately and assign a suitable flexible material in the slicer. The gasket follows closing clearance and has 0.15 mm nominal geometric compression: its top lies 0.15 mm above the lid land in the rigid assembly. This does not establish actual pressure or sealing. Switching to Sliding, open bin or stackable bin with the gasket enabled keeps the checkbox visible so it can be unchecked to recover; requested PCB supports and cutouts are not silently deleted. Material and physical sealing require testing.

Sliding places the detent tooth above the plate, leaving a broad flat underside in the exported print pose. Rear corners have relief along the nominal insertion path. The detent still requires temporary flexure; this geometry is not an adhesion, force, slicing or printed-fit acceptance.

## Calibrate and manufacture

For the original four styles, the generic compact kit contains a small matching base/lid pair, a bore matching the first configured support (reference M3 when no supports exist) and a snap tongue. Test fit and material flex before printing the finished part. The kit uses a Lip Snap pair and does not reproduce the Rugged hinge or Sliding rails, or every complete mechanism. Print duration comes from the slicer and depends on the machine/profile.

**Open bin, Latch lid, Stackable bin and Articulated case have no generic fit kit.** First create a smaller configuration with the same wall/floor thickness and clearance. Keep clip dimensions, hook retention and skirt depth when testing the latch style. For stacking, test two heights of the same family while preserving wall/radius, foot and stacking clearance. For the articulated case, test a smaller pair with compatible clearance, axle and separation settings. Export and test the actual pieces. Uniform scaling in the slicer also changes the clearances and is not an equivalent calibration.

Binary STL writes each selected item separately, except the captive assembly, which remains one multi-shell mesh. 3MF preserves item names, assembled captive positions and a collision-free layout on the bed. Automatic 3MF placement rejects parts that do not fit the selected bed; the exporter does not silently rescale them. STL does not apply XY bed placement: it preserves each part's requested dimensions, even when wider than the active bed. The existing print-height guard still applies to both formats. Arrange raw STL parts and select a printer that can manufacture them.

Send to Plater targets the current running OrcaSlicer instance. Optional mechanical slicing applies four walls, five top/bottom layers and structural infill. Transport success means that the import request was transmitted, not that model loading or slicing has completed. Exported files remain available if dispatch fails.

The following Windows observations are historical version 1.2.0 evidence; consult the [validation record](VALIDATION.md) for revision 1.2.1. Windows uses WM_COPYDATA, macOS Cocoa and Linux the session D-Bus protocol. Automated tests use a simulated host and run across platforms. Version 1.2 before this redesign was verified inside OrcaSlicer 2.5.1 on Windows in both the page and dock, including visual confirmation of exported models loaded on the Plater. The new lever Snap page and dock were verified on Windows, including two-stage operation, export and base/lid/two levers visually loaded on the Plater. In the dock, changing pivot diameter from 3.0 to 3.2 mm preserved 100% opening, and EN→PT immediately updated the labels. The preceding Snap test does not replace this new observation. Native macOS/Linux validation remains pending. See [validation status](VALIDATION.md) for the scope and earlier history. Open a 3MF as a project or use an empty plate; arrange objects when importing into an occupied project. For the current conservative arranger with default mating parameters, a 160 × 90 × 35 mm Snap body passed on a 220 × 220 mm bed; 160 × 95 × 35 mm passed on 260 × 260 mm and was rejected on 220 × 220 mm without scaling or changing the meshes. Export separate STLs or adjust project dimensions when the complete four-part layout is rejected. These are tested layouts, not universal size limits. The native session did not slice or print. Review the selected printer profile and limit warnings before printing. An acceleration-above-limit warning in the test session came from an existing profile; validation did not change acceleration settings. Closing the exported project prompted Orca to save its process settings; choosing **Discard** restored the preceding profile without overwriting it. Review imported process settings before saving a profile or printing. The historical version 1.2.0 local suite passed 136 tests in 574.594 seconds with Chromium enabled and no failures, errors or skips. This computational result does not replace physical calibration; see the [CI run history](https://github.com/victorFernande/orca-box-generator/actions/workflows/ci.yml) for each revision's cross-platform result. The lever Snap redesign passed 17 independent checks, comprising the ten adapted functional checks and seven new pivot/lever checks. The five stacking and eight articulated-case tests remain evidence for their respective styles. These check sampled paths, contacts, topology and print material-start events. A clear closed position does not remove the deliberate temporary interference of a snap detent, or establish printed fit. Curved surfaces are tessellated. The shown fit-interface chord-error target does not describe the accuracy of a real printer. Hardware fit, sealing and spring durability require physical calibration. See [E2E reproduction and scope](E2E.md) for the complete UI method, and the [validation record](VALIDATION.md) for current results; the earlier totals are not an advance acceptance of revision 1.2.1.
