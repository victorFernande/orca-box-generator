# Generation measurements / Medições de geração

## Version 1.2.3: exact standard presets and faster general computation

The three slow standard cards now load their **complete original surfaces**, not a reduced preview. Nine packaged resources retain every float32 vertex/normal bit and every triangle index from revision `75f3be346516ff7c4be557e9ee05d999dc476a3b`. A committed reference digest fixture checks this identity. Their combined compressed size is 6,488,188 bytes; XOR on float bits and integer deltas are lossless.

Fresh-controller Python measurements on this Windows machine, using the actual 90 × 65 × 35 mm standard cards:

| Standard card | 1.2.2 cold preview | 1.2.3 prepared cold preview | Unchanged triangles |
| --- | ---: | ---: | ---: |
| Screw lid | 13.446 s | 0.301 s | 1,372,384 |
| Rugged pin hinge | 17.562 s | 0.328 s | 1,276,072 |
| Sliding lid | 5.889 s | 0.142 s | 572,422 |

These are controller timings including resource verification/decoding and preview encoding, **not click-to-visible-frame measurements**. The OS file cache was not flushed. Imports, UI creation, transport, JSON/base64 decoding, buffer upload and GPU work add time. The completed GPU-backed Chromium run on Intel UHD 630/D3D11 passed **32/32 measured selections below 2000 ms**, with zero errors. It covered cold and post-tour selection for all eight cards in both page and dock; 32 declared warm-up selections were retained separately. The worst selection was **1431.1 ms**, Screw on a cold page. See the [sanitized measurements and source/resource hashes](performance/1.2.3-standard-selection.json). This is an isolated browser measurement on this machine, not a native Orca or universal hardware guarantee. Startup of Python, Chromium and the UI took 2.11–2.33 s and is not counted as sub-two-second model selection.

| Standard model | Worst measured selection across page/dock, cold/post-tour |
| --- | ---: |
| Snap-fit lid | 0.665 s |
| Screw lid | 1.431 s |
| Rugged hinged | 1.347 s |
| Sliding lid | 0.863 s |
| Open bin with grips | 0.646 s |
| Pivot latch lid | 1.248 s |
| Stackable bin | 0.512 s |
| PIP clamshell | 0.831 s |

The runtime accepts a prepared surface only for the exact manufacturing parameters and current geometry-source fingerprint. Changes to dimensions, clearance, quality, mechanisms or accessories miss this bank and use normal generation/validation. Names, language, theme and export-target metadata can reuse the same canonical surface. Missing, stale or damaged resources also fall back to generation; no UI flag can declare a resource trusted. The standalone bundles embed the resource bytes in Python, not in the initial HTML; the wheel includes them as package data. Only a selected part is decompressed.

The general extractor also runs faster for edited designs: stable numeric XYZ sorting replaces structured row sorting, undirected edges use int64 keys, and layer indices are reused. Resolution, fields, refinement, normals and triangle order are unchanged. Twenty-nine actual surfaces (nineteen preset pieces and ten edited pieces) were compared byte for byte. A separate correction prevents int32 overflow from hiding inverted faces in large-mesh orientation checks. These changes do not promise sub-two-second generation for arbitrary edited or accessory-heavy designs. The selection benchmark runs sequentially after each preceding frame completes; it does not establish a two-second bound while an older custom calculation is still in progress.

The page performs one completed scene draw per accepted mesh reply, reuses shader uniform locations and avoids resizing the caliper canvas unnecessarily. Shader, materials, normals and the exported geometry remain unchanged.

### Measuring selection latency

`scripts/check_box_performance.cjs` measures real preset-card clicks in the isolated page/dock against the real Python backend. Each cold case starts fresh Python/Chromium processes; the explicit fast bootstrap differs from its target, and startup time is reported separately. Two complete preset rounds precede warm measurements and remain in the report. The observer correlates request IDs, complete WebGL index sequences and the actual bound vertex/index buffers tagged by their uploads, rejects an old equal-count frame without the appropriate buffers, waits for a nonblocking GPU fence, and reports two further animation frames. GPU completion is an observation, not proof of physical display presentation or native WebView acceptance.

```console
node scripts/check_box_performance.cjs --self-check
node scripts/check_box_performance.cjs
python -B -W error scripts/benchmark_box.py --styles screw_corner rugged_box sliding_lid --sizes 90x65x35
python -B -W error scripts/benchmark_box.py --styles screw_corner rugged_box sliding_lid --sizes 90x65x35 --ignore-prepared
```

Set `ORCA_TEST_PYTHON`, `ORCA_PLAYWRIGHT_MODULE` and optionally `ORCA_CHROMIUM_PATH` for local development tools. `ORCA_PERF_OUTPUT` selects a private report directory. `ORCA_PERF_GPU=auto` uses the available renderer; `software` explicitly selects SwiftShader. Every report names the actual renderer and whether software rendering was detected. The default target is 2000 ms per measured selection; failure remains a failure, and software/virtual machines are not assumed to meet the same budget. Tests do not install plugins, dispatch native IPC or open the user's project. Native application latency remains a separate measurement.

Decoded resources use the existing 128 MiB mesh LRU and 48 MiB encoded LRU. The three complete surfaces total approximately 92.15 MiB of array data, so both LRUs can evict entries during a full library tour. There is no second decoded cache or background generation of all presets at launch. In a separate standalone-bundle Python process, 24 sequential selections over three library tours stayed within 112.51 MiB accounted mesh data and 45.01 MiB encoded data. Peak resident working set was 209.36 MiB; end-of-tour private committed memory was 358.20, 358.12 and 358.11 MiB. See the [memory observations](performance/1.2.3-python-memory.json); these measure that Python process only, not the browser, GPU or complete Orca application. The compressed embedded strings, transient decoding/JSON/GPU buffers and interpreter/browser memory are additional; the LRU counters are not a total RSS guarantee.

After changing `schema.py`, `mesh_generator.py` or `presets_catalog.py`, rebuild the prepared resources with `python -B -W error scripts/build_preset_meshes.py` before building the distribution. Packaging rejects stale fingerprints or resource hashes. Rebuilding a resource is not permission to alter the approved reference digests without documenting an intentional geometry change.

## Historical measurements

The following measurements use the offline Python controller on Windows, Python 3.12.13 and NumPy 2.5.5. They include real mesh generation and topology validation. They do not measure a physical print or guarantee the same timing on another computer.

## Before the 1.2 changes

The standard 90 × 65 × 35 mm Lip Snap box generated **955,728 triangles** and a **22.94 MB** JSON preview message. Its first preview took **10.043 s** in the recorded baseline. Exporting required another generation (**9.801 s**), and a subsequent preview regenerated again (**9.186 s**), because the single-entry cache distinguished assembly and print orientation.

## Analytic geometry and canonical reuse

Simple Lip Snap shells and the new storage styles use connected contour surfaces instead of a dense tensor grid. Curvature remains tessellated to the declared interface error. Features outside that fast path continue to use the unified implicit CSG surface, so adding complex accessories can increase generation time.

The controller now retains a bounded cache of validated canonical meshes. Print orientation is a pure transformation of those surfaces; preview and export share the same geometry. Encoded preview arrays are also retained, and metadata-only replies reuse the GPU geometry.

Representative local measurements on 2026-11-18:

| Design, outer base dimensions | Cold preview | Print-oriented geometry from cache | Preview after export | Triangles | Preview JSON |
| --- | ---: | ---: | ---: | ---: | ---: |
| Lip Snap, 90 × 65 × 35 mm | 0.201 s | 0.0009 s | 0.0001 s | 2,736 | 0.068 MB |
| Open bin with two hand grips, 90 × 65 × 35 mm | 0.144 s | 0.0006 s | 0.0001 s | 2,584 | 0.064 MB |
| Removable lid and two pivot levers, 90 × 65 × 35 mm | 0.816 s | 0.0022 s | 0.0005 s | 9,928 | 0.242 MB |
| Stackable container with lowered front, 90 × 65 × 35 mm | 0.051 s | 0.0006 s | 0.0001 s | 912 | 0.024 MB |
| Lip Snap, 160 × 95 × 35 mm | 0.153 s | 0.0010 s | 0.0001 s | 2,736 | 0.068 MB |
| Open bin with two hand grips, 160 × 95 × 35 mm | 0.140 s | 0.0007 s | 0.0001 s | 2,584 | 0.064 MB |
| Removable lid and two pivot levers, 160 × 95 × 35 mm | 0.706 s | 0.0026 s | 0.0005 s | 9,928 | 0.242 MB |
| Stackable container with lowered front, 160 × 95 × 35 mm | 0.049 s | 0.0006 s | 0.0001 s | 912 | 0.024 MB |

Stackable-container height includes its lower guide foot. These measurements use plain shells with no added PCB posts, panel cutouts or dividers.

The pivot-lever rows were remeasured on 2026-11-19 after replacing the earlier removable clips. They cover the final base-mounted pivots, closed lid and two levers, including real topology validation. The other rows retain their 2026-11-18 measurements. Do not use timings from the superseded clip geometry as measurements of the lever design.

These are Python-controller timings. Browser message delivery, drawing, file serialization and native application loading add their own time. The print-oriented column is not a full STL/3MF export measurement.

## Equal-half print-in-place case

The original `clamshell_pip` surface includes two captive hinges and connected
pedestals under the bearings and shaft end stops. The two moving shells are
reused in the open 180-degree print pose and exported together as one object.
For this style, the third configured dimension below is **the height of each
half**, not the closed case height or its open print envelope.

| Configured X × Y × half height | Cold preview | Print geometry from cache | Preview after export | Triangles | Preview JSON |
| --- | ---: | ---: | ---: | ---: | ---: |
| 120 × 65 × 14 mm | 0.374 s | 0.0011 s | 0.0002 s | 5,352 | 0.131 MB |
| 90 × 65 × 25 mm | 0.319 s | 0.0012 s | 0.0002 s | 5,352 | 0.131 MB |

These measurements use the same machine and methodology. They do not measure
bridge quality, hinge release force or the time of a physical print.

## Reproduce

```console
python -B -W error scripts/benchmark_box.py --styles lip_snap open_bin snap_latch stackable_bin --sizes 90x65x35 160x95x35
python -B -W error scripts/benchmark_box.py --styles clamshell_pip --sizes 120x65x14 90x65x25
```

Use `--output` to retain the measurements as JSON. The benchmark uses temporary storage and never installs a plugin or sends models to OrcaSlicer.

## Português

As medições incluem geração e validação topológica no controlador Python. As caixas simples passaram a usar superfícies conectadas construídas por contornos, e a exportação reutiliza a malha validada em outra orientação. Modelos com acessórios complexos podem continuar mais demorados por usar a superfície CSG unificada. O tempo do navegador, da gravação do STL/3MF e do carregamento no Orca é adicional; os números acima não são promessa de desempenho em qualquer equipamento.
