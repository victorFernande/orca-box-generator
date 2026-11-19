# Rugged · SnapLock

Reconstrução paramétrica do mecanismo da referência 3MF fornecida pelo usuário. O arquivo de referência e suas malhas não fazem parte do repositório ou do pacote. Os contornos e superfícies são calculados a partir de medidas; não são triângulos importados.

Parametric reconstruction of the user-supplied 3MF mechanism. The reference file and meshes are excluded from the repository and distribution. Curves and surfaces are calculated from dimensions rather than imported triangles.

## Medidas / Dimensions

| Controle / Parameter | Referência / Reference |
| --- | ---: |
| Corpo externo / Outer body XY | 160 × 95 mm |
| Altura base / Base height | 35 mm |
| Altura tampa / Lid height (`rugged_lid_height`) | 20 mm |
| Altura fechada / Closed height | 55 mm |
| Raio dos cantos / Corner radius | 12 mm |
| Parede e fundos / Walls and floors | 2.5 mm |
| Altura do chanfro / Chamfer height | 10 mm |
| Inclinação do chanfro / Chamfer slope | 30° da vertical / from vertical |
| Folga radial das travas / Latch radial clearance | 0.15 mm |
| Folga radial traseira / Rear radial clearance | 0.125 mm |
| Folga axial traseira / Rear axial clearance | 0.25 mm |

O nome do arquivo menciona 35 mm, a altura da **base**. Tampa, suportes e travas têm envelopes próprios. Largura, profundidade e alturas das duas metades podem ser alteradas dentro dos limites geométricos. Os encaixes conservam seus diâmetros: não escale o conjunto no fatiador para redimensioná-lo.

The filename's 35 mm is the **base** height. Lid, fittings and latches have separate envelopes. Width, depth and both shell heights are independent within geometric limits. Joint diameters remain fixed: resize through the controls rather than scaling the assembly in the slicer.

Aumentar a folga amplia os bolsões das orelhas sem perfurar a parede de apoio. As costas da trava continuam com seu encosto nominal na parede; o ajuste não afasta a trava do corpo. O aro em V também mantém contato nominal, separado das folgas das articulações.

Increasing clearance enlarges the ear recesses while preserving the backing wall. The latch back keeps its nominal seat against that wall; this setting does not move the latch away from the shell. The V rim also retains nominal contact, independently of joint clearances.

## Montagem e abertura / Assembly and opening

1. Imprima as quatro peças separadas: base, tampa e duas travas. Base e tampa apoiam suas faces externas; as travas ficam deitadas na face larga.
2. Encaixe a dobradiça traseira por pressão. Não há pino separado.
3. Monte as duas travas nos apoios da **tampa**, pelos pivôs esféricos superiores.
4. Feche a tampa e engate as linguetas inferiores das travas na base.
5. Para abrir, libere as linguetas e gire as travas; depois levante a tampa. As travas acompanham a tampa.

Print four separate pieces: base, lid and two latches. The shells rest on their exterior faces; the latches lie flat on their broad face. Snap the rear hinge together, then fit each latch's upper spherical pivots into the **lid** sockets. Close the lid and engage the lower flexible catches with the base. Release and rotate both latches before opening the lid; they remain attached to it.

A animação divide a liberação das travas e a abertura da tampa. Ela representa movimentos rígidos, sem simular a deformação das linguetas, força, fadiga ou atrito. Confirme flexibilidade e encaixe com o filamento e a impressora reais.

The animation separates latch release from lid opening. It shows rigid motion without simulating elastic strain, force, fatigue or friction. Physical fit and flexibility require tests with the actual filament and printer.

## Compatibilidade / Compatibility

Este modelo básico não aceita torres, recortes, divisórias, junta TPU ou kit genérico Lip Snap. Recursos incompatíveis geram uma explicação e permanecem nos parâmetros, para o usuário removê-los ou voltar a outro estilo. O estojo `clamshell_pip` continua independente e mantém sua impressão articulada já aberta.

This standard model does not support posts, cutouts, dividers, TPU gaskets or the generic Lip Snap calibration kit. Incompatible requested features remain in the parameters and produce an explanation. Remove them or return to a compatible style. The independent `clamshell_pip` style retains its open print-in-place assembly.

Presets pessoais do Rugged anterior, com esquema 1, são preservados e identificados como legados. Não são convertidos silenciosamente para uma geometria de fabricação diferente. Para usar o novo desenho, selecione **Caixa reforçada · SnapLock** na galeria.

Personal Rugged presets from schema 1 are preserved and identified as legacy. They are not silently converted to different manufacturing geometry. Select **Rugged box · SnapLock** in the gallery to start the new design.

## Verificação / Verification

As quatro superfícies preparadas são idênticas, em V/T, às malhas usadas na comparação visual com a referência privada. As 16 vistas ortográficas usam a mesma câmera e escala em milímetros. A coincidência mínima de silhueta foi **99,7976%**; base e tampa ficaram acima de **99,992%**. A diferença máxima entre os envelopes medidos foi 0,001381 mm na base, 0,002226 mm na tampa e 0,039665 mm nas travas. Esses números descrevem as vistas e envelopes medidos; a reconstrução utiliza curvas próprias e uma triangulação diferente da referência. Veja [método e vínculo dos arquivos](validation/1.3.0-rugged-reference-fit.json).

As verificações geométricas cobrem fechamento, orientação, conexão em uma casca por peça, ligações manifold dos vértices, faces degeneradas, volume, normais, interseções em toda a malha e poses de abertura. A liberação foi verificada em 91 posições e a abertura da tampa em 73 posições, com as travas acompanhando a tampa. As linguetas inferiores precisam flexionar: há até 0,75 mm de engate transitório na região prevista para essa flexão. O aro em V mantém contato nominal. Consulte os [métodos geométricos](validation/1.3.0-rugged-geometry.json) e os resultados da suíte atual em [VALIDATION.md](VALIDATION.md).

A revisão pela interface isolada passou em **211 verificações**, incluindo os oito estilos, página e painel, com **102 ações de exportação** e **145 arquivos** reabertos e conferidos. Uma ação verifica a rejeição esperada de um 3MF acima da mesa. O template passou em 12 layouts e 37 interações. Veja [escopo, resultados e hashes](validation/1.3.0-ui-e2e.json). A medição de seleção do modelo padrão está em [PERFORMANCE.md](PERFORMANCE.md), com os tempos de aquecimento também registrados.

No Orca instalado no Windows, o agente observou a página, as medidas padrão, a liberação das travas e a abertura da tampa, e exportou quatro STL e um 3MF personalizado de 140 × 80 mm, base 40 mm e tampa 20 mm. Os arquivos originais coincidem exatamente com as superfícies de impressão atuais; o 3MF contém quatro objetos apoiados em Z=0, organizados sem sobreposição em mesa de 220 × 220 × 250 mm. **O usuário importou os arquivos na mesa e aprovou o modelo.** A inspeção dos arquivos e essa confirmação manual estão separadas no [relatório nativo](validation/1.3.0-native-export.json). O painel lateral Rugged 1.3 foi verificado no navegador isolado; sua observação nativa específica continua pendente.

Não houve fatiamento ou impressão física. Encaixe, flexibilidade, força e fadiga precisam de ensaio real. A integração nativa macOS/Linux continua pendente.

All four prepared V/T surfaces are byte-identical to the meshes submitted to the private reference comparison. Sixteen orthographic views use identical cameras and millimetre scale: minimum silhouette IoU **99.7976%**, with base/lid above **99.992%**. Maximum envelope differences are 0.001381 / 0.002226 / 0.039665 mm for base / lid / latches. These are view and envelope measurements of an independently triangulated dimensional reconstruction; see the linked reference-fit report.

Geometry checks cover full-mesh intersections, topology, normals, print grounding and mechanism motion (91 latch-release and 73 lid-opening positions). Lower flexures have up to 0.75 mm transient engagement in the intended flexible cam region; V-rim contact is nominal. The isolated real-browser/backend run passed 211 checks, 102 export actions and 145 reopened files, including an intentional oversized-3MF rejection. Template verification passed 12 layouts and 37 interactions. Native Windows page, movement and original-file exports were observed by the agent; Plater import and model approval were confirmed by the user. The original custom 3MF has four exact source objects grounded at Z=0 and separated on a 220 × 220 × 250 mm bed. The specific native Rugged dock, native macOS/Linux sessions and physical printing/fit remain unverified.
