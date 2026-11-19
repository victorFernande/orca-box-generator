# Generation measurements / Medições de geração

## Compactação e memória da revisão final 1.3.0

O banco preparado passou de **34.427.046 para 15.910.205 bytes (−53,8%)**, com oito peças em sete arquivos. A compactação agrupa planos de bytes antes do DEFLATE, conservando os preditores XOR de float32 e diferenças de índices. A segunda trava referencia o recurso da primeira com uma translação float32 cuja reconstrução é comprovada pelo hash original de seus vértices. Os **24 hashes V/T/N** continuam idênticos aos da revisão aprovada, assim como dimensões, volumes, topologia e orçamento de erro dos modelos padrão. Um decoder independente verificou esses mesmos dados, sem chamar o carregador do produto nem gerar CAD. A correção posterior da ponta exata da dobradiça altera somente uma das sete fontes geométricas; o [novo vínculo de fonte](../docs/validation/1.3.0-decimal-hinge.json) foi aprovado após reconstruir as oito peças e conferir novamente os 24 hashes originais, sem editar a referência aprovada.

Na comparação final de três processos isolados por caso, a importação do bundle `d2ef9c58…`, incluindo NumPy, teve mediana de **3759,0 → 1970,9 ms**. O pico de working set desse processo passou de **229,76 → 135,43 MiB**. A nova importação variou de 1926,9 a 2233,3 ms; são processos Python nesta máquina com cache de arquivos não esvaziado, não a abertura nativa do Orca ou uma garantia para outros computadores. As observações anteriores do bundle `33023595…` permanecem identificadas separadamente no relatório.

No Chromium isolado, quatro cargas Rugged intercaladas com três caixas abertas mantiveram os dados realmente desenhados bit a bit idênticos. Remover o texto base64 retido reduziu o heap após GC em aproximadamente **76,34 MB por WebView**. A comparação exata de índices/normais permitiu compartilhar apenas esses buffers: os arrays CPU retidos passaram de **57.256.332 para 43.728.324 bytes**, e os buffers GL únicos solicitados de **82.703.676 para 62.411.640 bytes**. Posições e identificadores de material permanecem individuais. Esses valores descrevem categorias diferentes e não devem ser somados como economia física total.

Com wireframe ligado, os buffers GL únicos passaram de **159.045.324 para 111.697.272 bytes**. Ao desligar, a revisão final retorna a **62.411.640 bytes**, liberando todos os buffers de arestas; a revisão anterior os retinha até trocar a malha. Trocas repetidas não deixaram buffers órfãos ou erros GL no ensaio. A contagem de bytes GL é uma medição das alocações pedidas, não da memória física do driver/GPU, e o teste não mede FPS sustentado.

Compactação não torna a geometria decodificada menor. No carregador final, a mediana de três leituras do Rugged completo foi 601 ms; a referência privada do decoder anterior foi 604 ms. O Screw base teve 139 contra 95 ms e aproximadamente 5,6 MiB adicionais de pico incremental no decoder. Não se afirma redução de tempo ou de pico de memória em todas as etapas. O transporte da prévia ainda contém a superfície completa, e um cálculo personalizado ativo pode atrasar a próxima seleção. Veja [evidência, hashes, amostras e escopos separados](performance/1.3.0-package-memory-optimization.json).

The final revision reduces the prepared bank by 53.8%, preserving every approved V/T/N byte. It releases retained preview transport strings, shares only bit-identical GPU normals/indices and CPU indices, and frees wire buffers when disabled. Independent decoding and actual bound-render-input hashes verify surface identity. Python import, post-GC browser heap, CPU arrays and requested GL buffer bytes are separate measurements, not native-Orca startup, physical GPU memory or sustained-FPS guarantees.

### Seleção dos modelos na revisão final

Com os artefatos finais `d2ef9c58…` / `057e3c8a…` e fonte geométrica `f35120b6…`, a rodada completa passou nas **32 seleções medidas e nas 32 seleções de aquecimento abaixo de 2000 ms**. O pior tempo medido foi **1881,7 ms**, Rugged na página em seleção fria; os outros três casos Rugged foram 1627,4 ms na página após duas voltas e 1680,9 / 1633,3 ms no painel. Todos os tempos, inclusive aquecimentos, parâmetros, buffers realmente usados e hashes das fontes/recursos/artefatos estão no [relatório final completo](performance/1.3.0-optimized-standard-selection.json).

| Modelo padrão | Pior seleção medida |
| --- | ---: |
| Lip Snap | 296,3 ms |
| Screw Corner | 896,8 ms |
| Rugged SnapLock | 1881,7 ms |
| Sliding | 529,3 ms |
| Open bin | 313,8 ms |
| Lever latch | 880,0 ms |
| Stackable | 214,3 ms |
| PIP clamshell | 479,4 ms |

O ensaio usa o controlador real com Chromium isolado e GPU Intel UHD 630/D3D11, incluindo a sequência completa de índices, buffers correlacionados e fence da GPU. São pedidos sequenciais concluídos, sem esvaziar o cache do sistema operacional. Não mede o WebView nativo, uma fila já ocupada com extração personalizada ou FPS sustentado. A redução de pacote/memória não implica que toda seleção tenha ficado mais rápida que a revisão anterior; ambas as rodadas estão preservadas. As medições abaixo pertencem aos snapshots anteriores.

## Snapshot anterior do Rugged SnapLock 1.3.0 — 2026-11-19

A geometria Rugged foi substituída. A rodada final com GPU Intel UHD 630/D3D11 passou nas **32 seleções medidas abaixo de 2000 ms**, incluindo primeira seleção em processos novos e seleção após duas voltas pela galeria, na página e no painel. O pior tempo medido foi **1748,3 ms**, Rugged no painel após as duas voltas. A caixa completa manteve seus 3.180.902 triângulos, incluindo as duas travas. Veja [relatório completo, hashes e método](performance/1.3.0-standard-selection.json).

As **32 seleções de aquecimento também estão no relatório**. Duas seleções Rugged no painel demoraram 2212,8 e 2048,5 ms. Portanto, o resultado não significa que qualquer clique será sempre inferior a dois segundos. O ensaio usa Chromium isolado com o controlador real; não mede a latência do WebView nativo do Orca, o tempo de inicialização dos processos ou uma fila com outro cálculo pesado ainda em andamento. O cache de arquivos do sistema operacional não foi esvaziado.

| Modelo padrão / Standard model | Pior seleção medida / Worst measured selection |
| --- | ---: |
| Lip Snap | 279.9 ms |
| Screw Corner | 763.1 ms |
| Rugged SnapLock | 1748.3 ms |
| Sliding | 446.2 ms |
| Open bin | 295.9 ms |
| Lever latch | 780.7 ms |
| Stackable | 215.8 ms |
| PIP clamshell | 480.3 ms |

Escolher um projeto completo não espera mais o atraso de 350 ms usado para agrupar edições de sliders. Os arquivos preparados mantêm todos os bits de V/T/N; o decoder reconstrói os dados no próprio buffer e verifica seus hashes. As duas travas compartilham somente os índices e normais imutáveis cujos hashes são idênticos; as coordenadas continuam independentes. O controlador é o dono dessas referências, sem um segundo cache global de arrays. Não houve redução de triângulos ou alteração dos materiais/normais da prévia.

A revisão mantém o limite de 128 MiB para malhas, amplia a prévia codificada para 96 MiB e inclui caches locais das travas (48 MiB, até duas entradas) e apoios frontais (8 MiB). Os limites somam 280 MiB de contabilização, incluindo referências compartilhadas contadas mais de uma vez; não limitam a memória total do processo, navegador ou GPU. Em um processo Python isolado usando o pacote-fonte, três voltas e 24 seleções ficaram dentro dos quatro limites. A memória privada no fim das voltas foi aproximadamente 423,56 / 423,58 / 423,58 MiB; o pico de working set chegou a 312,41 MiB após também exercitar os caches locais. Veja [memória, limites e hashes](performance/1.3.0-python-memory.json). O ensaio não mede a memória do bundle dentro do Orca nem da GPU/navegador.

Reprodução: `python -B -W error scripts/check_box_memory.py --output test-output/memory.json` e o comando de benchmark de seleção abaixo. Mudanças em qualquer uma das sete dependências em `_PRESET_DEPENDENCIES` exigem reconstruir o banco antes da distribuição. Alterar a altura da tampa ou a folga das articulações pode exigir nova extração das travas e levar dezenas de segundos; a meta de seleção padrão não abrange toda edição personalizada.

The final hardware-backed run passed 32/32 measured standard-card selections below two seconds, worst 1748.3 ms. All 32 declared warm-ups remain visible; two exceeded the target (2212.8 and 2048.5 ms). These are isolated Chromium/controller observations on this machine, not a native-WebView or universal timing guarantee. Full geometry and all V/T/N bits are retained. The three-tour memory report covers a fresh Python process importing the source package, separately from browser/GPU and native Orca memory. The 1.2.3 results below describe the previous Rugged design.

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
