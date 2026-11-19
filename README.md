# Orca Box Studio

<p align="center"><img src="assets/icon.jpg" alt="Orca Box Studio — parametric enclosures" width="240"></p>

Estúdio paramétrico offline para **OrcaSlicer 2.5.1+**. A versão 1.2 reúne oito estilos: tampa por pressão, dobradiça reforçada, tampa deslizante, parafusos nos quatro cantos, caixa aberta com alças, tampa removível com dois fechos de alavanca, caixa empilhável com acesso frontal e estojo articulado print-in-place. Interface em português/inglês, temas claro/escuro, aba principal em três colunas e painel lateral.

A interface utiliza o template do **Orca Vase Studio**: cabeçalho compacto, galeria com filtros, cartões de parâmetros, sliders com valores numéricos, ferramentas flutuantes de inspeção e exportação fixa. Veja a [referência visual e sua origem](docs/UI_TEMPLATE.md).

## Recursos

- **Lip snap:** saia de localização com entrada chanfrada, ressalto com rampa e canal correspondente. A retenção do encaixe é ajustada separadamente da folga por lado.
- **Rugged:** nervuras integradas, dobradiça com pino removível ou eixo cativo print-in-place e duas travas flexíveis removíveis. Retire as travas antes de abrir a tampa.
- **Sliding:** trilhos e tampa com perfil a 45°, abertura frontal, puxador e detente traseiro. A espessura útil da tampa deriva do trilho e da folga; os controles de espessura/saia são ocultados neste estilo.
- **Screw corner:** quatro colunas integradas à base e furos correspondentes na tampa, para M2/M2.5/M3.
- **Caixa aberta (`open_bin`):** sem tampa, com duas aberturas de mão arredondadas opcionais nas faces esquerda/direita ou frente/trás. Largura, altura e margem superior das alças são editáveis.
- **Tampa com travas (`snap_latch`):** tampa plana removível e dois fechos de alavanca articulados na base. São quatro peças impressas: base, tampa e duas alavancas com pinos integrados. Monte os pinos nos apoios de encaixe da base; para abrir, gire os dois fechos até 90° e então levante a tampa. Os fechos permanecem presos à base.
- **Empilhável (`stackable_bin`):** base aberta com frente rebaixada, apoio nos dois lados e atrás, e pé de indexação. Caixas da mesma família podem ter alturas diferentes. O pé orienta o encaixe; os ombros da base superior apoiam no aro inferior.
- **Estojo articulado (`clamshell_pip`):** duas metades de mesma profundidade, duas dobradiças cativas com eixos integrados e apoios desde o fundo. Exporta aberto a 180°, com os dois fundos em Z=0, como um objeto de duas cascas. Este estilo inicial não inclui trava frontal.
- Torres de PCB posicionadas pelo editor 2D ou por coordenadas, com diâmetro e profundidade de inserto/piloto editáveis; divisórias nos eixos X/Y; portas USB-C, HDMI, DC e ventilação em fendas ou hexágonos.
- Canal perimetral e junta TPU exportável para tampas que levantam; 17 presets editáveis e biblioteca pessoal salva fora do projeto.
- Visualização WebGL2 da mesma geometria usada na exportação, animação de abertura, raio-X e corte axial. O cálculo do modelo roda em segundo plano; o tempo de regeneração depende das dimensões e dos acessórios.
- Exportação STL binário e 3MF multiobjeto, organização na mesa sem escala automática e envio à instância atual do OrcaSlicer.

## Instalação e uso

Use o arquivo `dist/orca_box_generator.py` ou o wheel em `dist/` em **Plugins → Instalar plugin local**. O ícone se materializa quando necessário. Habilite o plugin e a permissão de execução em segundo plano solicitada.

Para desenvolver ou reconstruir, na raiz deste repositório:

```console
python -B scripts/build_and_install.py --no-install
python -B -W error -m unittest discover -s tests -v
```

Requer Python 3.12+ e NumPy 1.26+. No OrcaSlicer, use o Python embutido, que pode fornecer o NumPy na pasta de pacotes da aplicação. O instalador só copia para a instalação local quando executado **sem** `--no-install`.

Depois de instalar ou atualizar, **feche e reabra o OrcaSlicer** para carregar o novo bundle. Em **Plugins**, confira a versão e ative **Orca Box Studio**. A substituição do arquivo enquanto o aplicativo está aberto não atualiza o plugin que já está em memória.

Abra **Gerador de Caixas** na aba superior. Para o painel lateral, o caminho verificado no OrcaSlicer 2.5.1 no Windows é: na área principal, pressione **Espaço** para abrir o Speed Dial, digite **Orca Box**, selecione **Orca Box Studio — Painel Lateral** e pressione **Enter**. Escolha um preset, ajuste as dimensões e confira os acessórios. Use o kit de calibração nos estilos compatíveis; caixa aberta, tampa com travas, empilhável e estojo articulado exigem ensaio com peças reais de uma configuração menor. Os botões STL/3MF salvam na pasta de exportação privada do plugin; **Abrir pasta de exportação** localiza os arquivos.

## Geometria, tolerâncias e impressão

Todas as medidas são em milímetros. Largura X e profundidade Y definem o corpo externo da base; altura Z define a altura da peça base. No empilhável, ela **inclui o pé**; no estojo articulado, é a altura **de cada metade**; nos outros estilos, vai do fundo externo até a borda. Não são medidas internas nem o envelope completo com tampa, dobradiça, ressaltos e travas. Na tampa com travas, o topo plano fica em `altura Z + folga + espessura da tampa`; `lid_wall_height` define a profundidade da saia **abaixo** dessa placa, sem elevar o topo. As travas podem ultrapassar esse envelope. Confira o conjunto fechado e a organização na mesa antes de imprimir.

Cascas simples Lip Snap, os estilos de armazenamento e o estojo articulado usam superfícies conectadas construídas por contornos. Modelos com acessórios fora desse caminho usam campos geométricos unificados e tetraedros conformes; uniões ocorrem antes da extração da superfície. A exportação reutiliza a malha canônica validada, alterando apenas sua orientação. Veja as [medições e os limites de desempenho](docs/PERFORMANCE.md).

No caminho geral, a grade se refina nas interfaces curvas e nos eventos de altura. O alvo de erro de tesselação é inferior a `min(folga/4, 0,04 mm)` nas interfaces; a interface mostra o alvo em milímetros. Isso não representa a precisão da impressora. Testes verificam topologia, orientação, conectividade, perfis de encaixe e amostras dimensionais. Combinações incompatíveis geram uma explicação e precisam ser corrigidas antes da exportação.

No estilo Rugged com pino, a base é exportada com o fundo para baixo e a tampa invertida. No Rugged **print-in-place**, base e tampa são exportadas como um único objeto com duas cascas fechadas nas posições montadas; o organizador da mesa preserva essa relação. A tampa fica sobre uma grande cavidade: avalie pontes e suportes removíveis no fatiador e mantenha suporte fora das folgas da dobradiça. **Não há promessa de impressão sem suporte para print-in-place.**

Insertos M2/M2.5/M3 têm dimensões que variam entre fabricantes. Os valores iniciais são editáveis, e o kit replica o primeiro furo de torre configurado, ou usa M3 como referência. Paredes e fundo têm mínimo de 1,2 mm. A vedação TPU e a flexão das travas exigem testes físicos com o material escolhido; “caixa com junta” não significa impermeabilidade homologada. O kit genérico é compacto e usa um par Lip Snap, furo e lingueta; não reproduz todos os mecanismos. Não está disponível para caixa aberta, tampa com travas, empilhável ou estojo articulado. Faça primeiro uma configuração menor desses estilos, mantendo espessuras, folgas e medidas de retenção, sem reduzir tudo pela escala do fatiador. O tempo real de impressão vem do fatiador.

## Fechos de alavanca

A prévia mostra duas etapas: primeiro as alavancas giram com a tampa parada; depois a tampa sobe. Ao fechar, assente a tampa e gire os fechos de volta. Os ganchos prendem as abas da tampa; os pivôs pertencem aos apoios da base. Ajuste largura, espessura, retenção do gancho e diâmetro do pivô (`latch_pivot_diameter`, 2,4–4,0 mm). A retenção geométrica e o clique do mecanismo não representam uma força de fechamento homologada.

Preserve a orientação das alavancas exportadas e teste a montagem dos pinos por pressão com o filamento escolhido. O kit genérico não reproduz este mecanismo. As quatro peças precisam caber juntas ao exportar um 3MF do conjunto; se necessário, reduza as dimensões do projeto ou exporte STL e organize a impressão em lotes, sem escalar os encaixes.

## Estojo articulado aberto para imprimir

A altura `H` vale igualmente para base e tampa. Fechado, o corpo tem altura `2H + c`, onde `c` é a folga de fechamento (`fit_clearance`). Aberto, a profundidade do conjunto é `2D + 2s`, com `D` igual à profundidade de cada metade e `s` à separação da dobradiça (`hinge_separation`). A altura máxima de impressão é `H + c/2 + R`, incluindo o raio externo `R` dos tubos da dobradiça; ela supera a altura de uma metade.

A folga PIP (`pip_clearance`, 0,20–0,60 mm) controla os vãos radiais e axiais do mecanismo, separadamente da folga de fechamento. Exporte **Base + tampa** ou **Conjunto completo**: o organizador mantém as duas metades abertas no mesmo objeto. Não separe as cascas para rearranjar. A versão inicial rejeita torres, recortes, divisórias, TPU, kit e exportação de metades isoladas. Eixos e cabeças têm apoios integrados, mas as pontes entre apoios exigem avaliação no fatiador e ensaio físico; não há garantia de impressão sem suporte nem de movimento livre após imprimir.

## Empilhamento

A família de encaixe exige os mesmos X/Y externos, raio dos cantos, espessura de parede, altura do pé e folga de empilhamento (`stack_clearance`). Altura total e acesso frontal podem variar. A folga de empilhamento, de 0,10 a 0,80 mm por lado, é separada da folga dos outros mecanismos. Se o pé da caixa de cima tem altura `P` e a caixa de baixo tem altura total `H`, a montagem desloca a caixa superior em Z por `H − P`; as duas ficam com altura total `H + altura superior − P`. Imprima as caixas separadamente e teste o conjunto antes de usar com carga.

A ideia de armazenamento empilhável com acesso frontal foi informada pela [referência conceitual de Techro3D](https://makerworld.com/en/models/2465290-stackable-storage-boxes-containers-by-techro3d). A implementação paramétrica é própria, sem reutilização de malhas ou elementos visuais da referência. Não há declaração de encaixe com modelos de terceiros nem capacidade de carga homologada.

## Compatibilidade e validação

O envio usa WM_COPYDATA no Windows, Cocoa no macOS e D-Bus de sessão no Linux. A confirmação significa **pedido de importação transmitido**, não confirmação de carregamento nem fatiamento. Se o envio falhar, os arquivos exportados continuam disponíveis.

O novo Snap com alavancas passou em **17 testes independentes** em 92,129 s e no navegador com **12 layouts e 37 interações**. A página e o painel lateral do novo Snap foram verificados no OrcaSlicer 2.5.1 no Windows, incluindo movimento em duas etapas, exportação 3MF, quatro STLs e quatro objetos reais carregados na mesa. A troca EN→PT atualiza os rótulos imediatamente. A suíte local passou em **136 testes em 574,594 s**, com Chromium habilitado e sem falhas, erros ou testes ignorados; inclui as verificações finais de interface e exportação. Os resultados por revisão podem ser consultados no [histórico da CI](https://github.com/victorFernande/orca-box-generator/actions/workflows/ci.yml). A observação nativa anterior do Snap foi superada pela mudança; os resultados Windows dos estilos articulado, empilhável e aberto com alças permanecem registrados. Veja o escopo, os históricos e as pendências no [registro de validação](docs/VALIDATION.md). As amostras verificam ausência de sobreposição permanente no estado fechado e interferência transitória nos detentes. Isso não determina força, deformação admissível, durabilidade nem encaixe físico.

A integração nativa no macOS/Linux permanece pendente. Não houve fatiamento, impressão nem teste físico de encaixe, força, vida útil ou pontes. Revise o perfil da impressora e seus avisos de limites antes de imprimir. O histórico da versão 1.1 foi preservado no registro de validação. Não há publicação automática no OrcaCloud.

O organizador atual considera o envelope completo das quatro peças e pode rejeitar conjuntos que não caibam com seu espaçamento. Para o novo Snap com parâmetros padrão de encaixe, foram verificados corpo de 160 × 90 × 35 mm em mesa de 220 × 220 mm e corpo de 160 × 95 × 35 mm em mesa de 260 × 260 mm. O segundo caso é rejeitado em 220 × 220 mm, sem reduzir a escala; exporte STLs por peça ou ajuste as dimensões.

Ao abrir um 3MF exportado, use a opção de abrir como projeto ou uma mesa vazia. Se importar como geometria em um projeto já ocupado, organize os objetos antes de fatiar: o teste conjunto com Thread mostrou sobreposição com objetos que já estavam na mesa.

Veja [Manual PT-BR](docs/MANUAL_PT-BR.md), [English manual](docs/MANUAL_EN.md), [notas de implementação](docs/IMPLEMENTATION_NOTES.md), [textos de divulgação](docs/COMMUNITY_LISTING.md) e [apresentação e textos PT/EN para catálogo](docs/orcacloud/README.md). Licença [MIT](LICENSE), incluindo os avisos da infraestrutura adaptada de Orca Gear Studio.
