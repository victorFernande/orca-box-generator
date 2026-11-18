# User manual — Orca Box Studio

## Design an enclosure

Open the full Gerador de Caixas tab or run the docked panel. Choose one of 12 editable starting designs. PCB presets provide initial envelopes: check the actual board model and revision. Width X, depth Y and height Z are outside dimensions. The XY origin is centered on the base; Z=0 is the outside bottom.

Lip snap includes a locating skirt, a retaining bead and its matching female groove. Rugged adds structural ribs, a hinged lid and two removable spring clips. Sliding uses 45-degree rails, a front insertion opening, a handle and a rear detent. Screw corner provides four integrated corner posts and matching lid clearance holes.

Fit clearance is measured **per side**, between 0.10 and 0.40 mm. A setting of 0.20 mm gives a 0.40 mm difference between opposite locating widths. It is separate from a post's explicitly defined hole diameter. Sliding lid thickness follows the rail profile and clearance; the unrelated cap-thickness/skirt controls are hidden for this style.

Mesh updates run in the background and can take several seconds. You can keep editing; the newest design replaces obsolete requests. The page and dock share geometry and user presets. Language and theme remain local viewing preferences.

## PCB supports, ports and partitions

Add PCB supports on the Features tab. Drag them in the 2D floor editor or enter exact X/Y positions. Height is measured from the inside floor. Outside diameter, bore diameter and blind depth are editable. The software preserves at least 1.2 mm below a blind bore and checks the lid clearance. Insert dimensions vary by manufacturer: starting M2/M2.5/M3 values are suggestions. M3 pilot mode starts at 2.5 mm; calibrate it for your screw and material.

Panel openings can be placed on the front, back, left or right wall. U measures horizontal position from that face's center; Z measures height from the outside bottom. USB-C and HDMI dimensions are editable passage envelopes. DC uses a circular hole. Slots and hexagons can be repeated into a vent grille. The model checks corner/floor/lid keep-outs and a 1.2 mm bridge between neighbouring openings.

Enter comma-separated divider positions along X or Y. Dividers are united with the floor and sidewalls. A divider that intersects a PCB support is rejected to keep the requested mounting feature usable.

## Inspect and assemble

Drag to orbit, scroll to zoom and use Home to frame the model. The lower slider lifts/slides/rotates the lid. X-ray and axial clipping are inspection tools; they do not alter exported geometry. The preview displays the same generated Python mesh used for manufacturing, with a different pose or print orientation when appropriate.

Remove the Rugged clips before opening. A pin hinge uses a separate removable axle. A captive print-in-place hinge has the axle and retaining ends integrated into the lid. Export **Base + lid** or **Complete set** for this mode: base and lid remain one object containing two closed shells in their assembled positions. The lid spans a substantial cavity above the bed. Assess bridging and removable supports in the slicer, and keep support out of the functional hinge gaps. Print-in-place is **not** promised to be support free. The motion preview is a kinematic check, not a physical strength or print validation.

Enable a perimeter gasket only with a lifting lid and adequate wall width. Export the TPU gasket separately and assign a suitable flexible material in the slicer. The plugin does not claim waterproofing; compression, material and physical sealing require testing.

## Calibrate and manufacture

The compact kit contains a small matching base/lid pair, a bore matching the first configured support (reference M3 when no supports exist) and a snap tongue. Test fit and material flex before printing the finished part. Print duration comes from the slicer and depends on the machine/profile.

Binary STL writes each selected item separately, except the captive assembly, which remains one multi-shell mesh. 3MF preserves item names, assembled captive positions and a collision-free layout on the bed. Oversized parts must be redesigned; the exporter does not silently rescale them.

Send to Plater targets the current running OrcaSlicer instance. Optional mechanical slicing applies four walls, five top/bottom layers and structural infill. Transport success means that the import request was transmitted, not that model loading or slicing has completed. Exported files remain available if dispatch fails.

Windows uses WM_COPYDATA, macOS Cocoa and Linux the session D-Bus protocol. Automated tests use a simulated host and run across platforms; native visual integration still needs validation in each operating system. Curved surfaces are tessellated. The shown fit-interface chord-error target does not describe the accuracy of a real printer. Hardware fit, sealing and spring durability require physical calibration.
