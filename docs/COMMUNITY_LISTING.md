# Community listing draft — version 1.3.0

## Português

**Orca Box Studio — oito estilos de caixas e gabinetes no OrcaSlicer**

Gerador paramétrico offline em PT/EN para OrcaSlicer 2.5.1+, com 8 presets editáveis: tampa por pressão, caixa reforçada com dobradiça, tampa deslizante, quatro parafusos, caixa aberta com duas alças de mão, tampa removível com dois fechos de alavanca presos à base, caixa empilhável com acesso frontal e estojo articulado print-in-place. Ajuste as medidas em milímetros, acrescente torres de PCB, divisórias e recortes compatíveis, inspecione a malha WebGL2 e exporte STL/3MF ou transmita um pedido para a mesa.

A folga dimensional e a retenção Lip Snap têm controles separados. A tampa com travas é plana, com saia abaixo da placa. São quatro peças impressas: base, tampa e duas alavancas com pinos integrados. Os pinos encaixam nos apoios da base; os fechos giram primeiro e a tampa sobe depois, sem retirar as alavancas. A exportação reutiliza superfícies validadas; [medições](PERFORMANCE.md) mostram o comportamento das configurações testadas, sem prometer o mesmo tempo em qualquer máquina.

O empilhável tem geometria própria, informada pela [ideia de organização de Techro3D](https://makerworld.com/en/models/2465290-stackable-storage-boxes-containers-by-techro3d). Caixas de alturas diferentes compartilham a família de encaixe quando corpo X/Y, raio, parede, pé e folga coincidem. Não há promessa de encaixe com produtos de terceiros ou capacidade de carga homologada.

O estojo articulado tem metades de mesma altura e duas dobradiças cativas. Exporta aberto a 180°, com ambos os fundos na mesa e as duas cascas no mesmo objeto. Tubos e cabeças do eixo têm apoios até o fundo; pontes entre os apoios ainda exigem avaliação de impressão. Este estilo inicial não inclui trava frontal ou acessórios PCB/TPU.

O **Rugged · SnapLock** tem base e tampa profundas com alturas independentes, dobradiça traseira montada por encaixe e duas travas com linguetas flexíveis presas à tampa. São quatro peças sem pino solto; a referência nominal é 160 × 95 mm, com base de 35 mm e tampa de 20 mm. As travas giram antes da abertura da tampa e acompanham seu movimento. Veja [medidas, montagem e limites](RUGGED_SNAPLOCK.md).

Código MIT, Python e NumPy, sem serviços externos durante o uso. Consulte o [registro de validação por versão](VALIDATION.md) e o [histórico da CI](https://github.com/victorFernande/orca-box-generator/actions/workflows/ci.yml). A integração nativa macOS/Linux continua pendente; não houve impressão física. Encaixe impresso, força das travas, conforto das alças, vedação e durabilidade exigem ensaio físico. Rugged, caixa aberta, tampa com travas, empilhável e estojo articulado não têm kit genérico: teste as próprias peças com as dimensões funcionais preservadas. Os estilos print-in-place exigem avaliação de pontes e suportes; não há garantia de impressão sem suporte ou de movimento livre após imprimir.

## English

**Orca Box Studio — eight enclosure and storage styles inside OrcaSlicer**

An offline PT/EN parametric generator for OrcaSlicer 2.5.1+, with 8 standard presets: snap lid, rugged hinge, sliding lid, four corner screws, open bin with two hand openings, a removable flat lid with two base-mounted lever latches, an open-access stackable bin, and a print-in-place articulated case. Enter custom dimensions in millimetres, add compatible PCB supports, partitions and ports, inspect the WebGL2 surface, then export STL/3MF or transmit an import request to the Plater.

Dimensional clearance and Lip Snap interference have separate controls. The lever lid has its locating skirt below the flat cap. Four pieces are printed: base, lid and two levers with integral pins. The pins snap into the base sockets; both latches rotate before the lid lifts, while the levers stay on the base. Export reuses validated surfaces; the [measurements](PERFORMANCE.md) describe tested configurations rather than guaranteed timing on every machine.

The stackable style uses original geometry informed by [Techro3D's storage concept](https://makerworld.com/en/models/2465290-stackable-storage-boxes-containers-by-techro3d). Different heights can share a mating family with equal outside X/Y, radius, wall, foot and stacking clearance. No compatibility with third-party products or certified load capacity is asserted.

The articulated case has equally deep halves and two captive hinges. It exports open at 180 degrees, both floors on the bed and both shells in one object. Barrels and axle heads have integral floor supports; bridges between supports still require print assessment. The initial style has no front latch or PCB/TPU accessories.

**Rugged · SnapLock** has independent deep base/lid heights, a snap-assembled rear hinge and two flexible-finger latches attached to the lid. Four pieces are printed without a separate pin. The nominal reference is 160 × 95 mm, with a 35 mm base and 20 mm lid. The latches rotate before the lid opens and then travel with it. See [dimensions, assembly and limitations](RUGGED_SNAPLOCK.md).

MIT licensed, using Python and NumPy, with no external services during use. See the [versioned validation record](VALIDATION.md) and [CI history](https://github.com/victorFernande/orca-box-generator/actions/workflows/ci.yml). Native macOS/Linux integration remains pending; no physical print test was performed. Printed fit, release force, hand comfort, sealing and durability require physical trials. Rugged, open bin, lever lid, stackable bin and articulated case have no generic fit kit: test their actual parts while preserving the functional dimensions. Print-in-place styles require bridging/support assessment; support-free printing or free movement after printing is not guaranteed.

This is repository/community copy. No marketplace submission or physical certification is implied; the Windows native validation scope is recorded above.
