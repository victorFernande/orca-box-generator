# Community listing draft — version 1.2

## Português

**Orca Box Studio — oito estilos de caixas e gabinetes no OrcaSlicer**

Gerador paramétrico offline em PT/EN para OrcaSlicer 2.5.1+, com 17 presets editáveis: tampa por pressão, caixa reforçada com dobradiça, tampa deslizante, quatro parafusos, caixa aberta com duas alças de mão, tampa removível com dois fechos de alavanca presos à base, caixa empilhável com acesso frontal e estojo articulado print-in-place. Ajuste as medidas em milímetros, acrescente torres de PCB, divisórias e recortes compatíveis, inspecione a malha WebGL2 e exporte STL/3MF ou transmita um pedido para a mesa.

A folga dimensional e a retenção Lip Snap têm controles separados. A tampa com travas é plana, com saia abaixo da placa. São quatro peças impressas: base, tampa e duas alavancas com pinos integrados. Os pinos encaixam nos apoios da base; os fechos giram primeiro e a tampa sobe depois, sem retirar as alavancas. A exportação reutiliza superfícies validadas; [medições](PERFORMANCE.md) mostram o comportamento das configurações testadas, sem prometer o mesmo tempo em qualquer máquina.

O empilhável tem geometria própria, informada pela [ideia de organização de Techro3D](https://makerworld.com/en/models/2465290-stackable-storage-boxes-containers-by-techro3d). Caixas de alturas diferentes compartilham a família de encaixe quando corpo X/Y, raio, parede, pé e folga coincidem. Não há promessa de encaixe com produtos de terceiros ou capacidade de carga homologada.

O estojo articulado tem metades de mesma altura e duas dobradiças cativas. Exporta aberto a 180°, com ambos os fundos na mesa e as duas cascas no mesmo objeto. Tubos e cabeças do eixo têm apoios até o fundo; pontes entre os apoios ainda exigem avaliação de impressão. Este estilo inicial não inclui trava frontal ou acessórios PCB/TPU.

Código MIT, Python e NumPy. O redesenho dos fechos passou em 17 testes independentes e no navegador com 12 layouts e 37 interações. A página e o painel lateral do novo Snap foram verificados no Windows com movimento em duas etapas, geração, exportação e quatro peças visualmente carregadas na mesa. Os rótulos mudam imediatamente entre EN/PT. A suíte local final passou em 136 testes em 574,594 s, com Chromium habilitado e sem falhas, erros ou testes ignorados; os resultados por revisão estão no [histórico da CI](https://github.com/victorFernande/orca-box-generator/actions/workflows/ci.yml). O teste nativo do Snap anterior foi superado pela mudança; os resultados dos estilos que não mudaram estão preservados. Consulte o [registro de validação](VALIDATION.md). A integração nativa macOS/Linux continua pendente; não houve fatiamento ou impressão. Encaixe impresso, força das travas, conforto das alças, vedação e durabilidade exigem ensaio físico. Caixa aberta, tampa com travas, empilhável e estojo articulado não têm kit genérico: teste primeiro as peças reais numa configuração menor. Os estilos print-in-place exigem avaliação de pontes e suportes; não há garantia de impressão sem suporte ou de movimento livre após imprimir.

## English

**Orca Box Studio — eight enclosure and storage styles inside OrcaSlicer**

An offline PT/EN parametric generator for OrcaSlicer 2.5.1+, with 17 editable presets: snap lid, rugged hinge, sliding lid, four corner screws, open bin with two hand openings, a removable flat lid with two base-mounted lever latches, an open-access stackable bin, and a print-in-place articulated case. Enter custom dimensions in millimetres, add compatible PCB supports, partitions and ports, inspect the WebGL2 surface, then export STL/3MF or transmit an import request to the Plater.

Dimensional clearance and Lip Snap interference have separate controls. The lever lid has its locating skirt below the flat cap. Four pieces are printed: base, lid and two levers with integral pins. The pins snap into the base sockets; both latches rotate before the lid lifts, while the levers stay on the base. Export reuses validated surfaces; the [measurements](PERFORMANCE.md) describe tested configurations rather than guaranteed timing on every machine.

The stackable style uses original geometry informed by [Techro3D's storage concept](https://makerworld.com/en/models/2465290-stackable-storage-boxes-containers-by-techro3d). Different heights can share a mating family with equal outside X/Y, radius, wall, foot and stacking clearance. No compatibility with third-party products or certified load capacity is asserted.

The articulated case has equally deep halves and two captive hinges. It exports open at 180 degrees, both floors on the bed and both shells in one object. Barrels and axle heads have integral floor supports; bridges between supports still require print assessment. The initial style has no front latch or PCB/TPU accessories.

MIT licensed, using Python and NumPy. The lever redesign passed 17 independent tests and the browser with 12 layouts and 37 interactions. The new Snap page and dock were verified on Windows with two-stage movement, generation, export and four parts visually loaded on the Plater. Labels switch immediately between EN/PT. The final local suite passed 136 tests in 574.594 seconds with Chromium enabled and no failures, errors or skips; see the [CI run history](https://github.com/victorFernande/orca-box-generator/actions/workflows/ci.yml) for each revision's cross-platform result. The previous native Snap observation was superseded by the redesign; results for unchanged styles are retained. See the [validation record](VALIDATION.md). Native macOS/Linux integration remains pending; no slicing or printing was performed. Printed fit, release force, hand comfort, sealing and durability require physical trials. Open bin, clip lid, stackable bin and articulated case have no generic fit kit: test the actual parts in a smaller configuration first. Print-in-place styles require bridging/support assessment; support-free printing or free movement after printing is not guaranteed.

This is repository/community copy. No marketplace submission or physical certification is implied; the Windows native validation scope is recorded above.
