# Generation measurements / Medições de geração

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
| Removable lid and two clips, 90 × 65 × 35 mm | 0.148 s | 0.0013 s | 0.0001 s | 2,680 | 0.067 MB |
| Stackable container with lowered front, 90 × 65 × 35 mm | 0.051 s | 0.0006 s | 0.0001 s | 912 | 0.024 MB |
| Lip Snap, 160 × 95 × 35 mm | 0.153 s | 0.0010 s | 0.0001 s | 2,736 | 0.068 MB |
| Open bin with two hand grips, 160 × 95 × 35 mm | 0.140 s | 0.0007 s | 0.0001 s | 2,584 | 0.064 MB |
| Removable lid and two clips, 160 × 95 × 35 mm | 0.152 s | 0.0016 s | 0.0001 s | 2,680 | 0.067 MB |
| Stackable container with lowered front, 160 × 95 × 35 mm | 0.049 s | 0.0006 s | 0.0001 s | 912 | 0.024 MB |

Stackable-container height includes its lower guide foot. These measurements use plain shells with no added PCB posts, panel cutouts or dividers.

These are Python-controller timings. Browser message delivery, drawing, file serialization and native application loading add their own time. The print-oriented column is not a full STL/3MF export measurement.

## Reproduce

```console
python -B -W error scripts/benchmark_box.py --styles lip_snap open_bin snap_latch stackable_bin --sizes 90x65x35 160x95x35
```

Use `--output` to retain the measurements as JSON. The benchmark uses temporary storage and never installs a plugin or sends models to OrcaSlicer.

## Português

As medições incluem geração e validação topológica no controlador Python. As caixas simples passaram a usar superfícies conectadas construídas por contornos, e a exportação reutiliza a malha validada em outra orientação. Modelos com acessórios complexos podem continuar mais demorados por usar a superfície CSG unificada. O tempo do navegador, da gravação do STL/3MF e do carregamento no Orca é adicional; os números acima não são promessa de desempenho em qualquer equipamento.
