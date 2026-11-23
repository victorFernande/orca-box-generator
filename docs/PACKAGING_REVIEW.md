# Packaging review — 2026-11-23

Version 1.4.3 compresses only the offline Studio HTML/CSS/JavaScript literal
in both standalone bundles. The restored UTF-8 document is byte-identical;
Python bridge code remains readable. No runtime package is added.

The bundle decreases from 21,824,597 to 21,697,538 bytes (0.58%). Most of its
size is the approved SnapLock mesh data, already stored losslessly. Further
compression experiments were rejected because they increased decode time
or size. No decimation, coordinate rounding or geometry changes were applied.
This is a download-size improvement, not a claim of faster mesh generation.

Validation: 258 baseline Python tests passed (one skipped), followed by seven
targeted packaging/resource tests, standalone/universal/wheel smoke checks
and page/dock browser interactions. Run Python checks with `-B -W error`.
The new regression checks restore the document and compare the entire module
AST, so executable code outside that literal must remain unchanged.

Windows OrcaSlicer 2.5.1: page presets, open-bin 3MF export, full-resolution
SnapLock preview and base-only 3MF export passed; dock preset selection and
stackable-bin STL export passed. The full SnapLock set was correctly rejected
on the selected 220 × 220 mm bed; export parts separately or use a larger bed.
The compact header and preview diagnostics remain crowded at narrow widths.
No physical print or macOS/Linux application validation was performed.
