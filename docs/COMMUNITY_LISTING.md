# Community listing draft — version 1.2

## Português

**Orca Box Studio — sete estilos de caixas e gabinetes no OrcaSlicer**

Gerador paramétrico offline em PT/EN para OrcaSlicer 2.5.1+, com 15 presets editáveis: tampa por pressão, caixa reforçada com dobradiça, tampa deslizante, quatro parafusos, caixa aberta com duas alças de mão, tampa removível com duas travas separadas e caixa empilhável com acesso frontal. Ajuste as medidas em milímetros, acrescente torres de PCB, divisórias e recortes compatíveis, inspecione a malha WebGL2 e exporte STL/3MF ou transmita um pedido para a mesa.

A folga dimensional e a retenção Lip Snap têm controles separados. A nova tampa com travas é plana, com saia abaixo da placa e detentes de entrada gradual. A exportação reutiliza superfícies validadas; [medições](PERFORMANCE.md) mostram o comportamento das configurações testadas, sem prometer o mesmo tempo em qualquer máquina.

O empilhável tem geometria própria, informada pela [ideia de organização de Techro3D](https://makerworld.com/en/models/2465290-stackable-storage-boxes-containers-by-techro3d). Caixas de alturas diferentes compartilham a família de encaixe quando corpo X/Y, raio, parede, pé e folga coincidem. Não há promessa de encaixe com produtos de terceiros ou capacidade de carga homologada.

Código MIT, Python e NumPy. Os testes locais e as 26 interações no navegador passaram, incluindo cinco testes independentes de empilhamento. A validação dentro do OrcaSlicer da versão 1.2 permanece pendente no [registro de validação](VALIDATION.md). Encaixe impresso, força das travas, conforto das alças, vedação e durabilidade exigem ensaio físico. Caixa aberta, tampa com travas e empilhável não têm kit genérico: teste primeiro as peças reais numa configuração menor. Print-in-place do estilo Rugged exige avaliação de pontes e suportes.

## English

**Orca Box Studio — seven enclosure and storage styles inside OrcaSlicer**

An offline PT/EN parametric generator for OrcaSlicer 2.5.1+, with 15 editable presets: snap lid, rugged hinge, sliding lid, four corner screws, open bin with two hand openings, a removable flat lid with two separate clips, and an open-access stackable bin. Enter custom dimensions in millimetres, add compatible PCB supports, partitions and ports, inspect the WebGL2 surface, then export STL/3MF or transmit an import request to the Plater.

Dimensional clearance and Lip Snap interference have separate controls. The new clip lid has its locating skirt below the cap and progressive detent entries. Export reuses validated surfaces; the [measurements](PERFORMANCE.md) describe tested configurations rather than guaranteed timing on every machine.

The stackable style uses original geometry informed by [Techro3D's storage concept](https://makerworld.com/en/models/2465290-stackable-storage-boxes-containers-by-techro3d). Different heights can share a mating family with equal outside X/Y, radius, wall, foot and stacking clearance. No compatibility with third-party products or certified load capacity is asserted.

MIT licensed, using Python and NumPy. Local verification and 26 browser interactions passed, including five independent stacking tests. Native version 1.2 acceptance remains pending in the [validation record](VALIDATION.md). Printed fit, release force, hand comfort, sealing and durability require physical trials. Open bin, clip lid and stackable bin have no generic fit kit: test the actual parts in a smaller configuration first. Rugged print-in-place assemblies require bridging/support assessment.

This is repository/community copy. No marketplace submission or native/physical approval is implied.
