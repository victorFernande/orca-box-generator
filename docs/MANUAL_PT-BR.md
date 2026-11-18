# Manual — Orca Box Studio

## Criar a caixa

1. Abra o Gerador de Caixas no OrcaSlicer ou execute seu painel lateral.
2. Use um dos 12 presets ou mantenha a caixa inicial. Os presets de placas representam envelopes iniciais; compare sua revisão real de ESP32, Arduino ou Raspberry Pi antes de imprimir.
3. Defina largura X, profundidade Y e altura Z externas. Ajuste parede, fundo e raio dos cantos. A origem XY fica no centro da base; Z=0 corresponde ao fundo externo.
4. Escolha o estilo. Lip snap usa um ressalto na saia da tampa e um canal na base. Rugged usa dobradiça e travas. Sliding usa trilhos laterais e inserção pela frente. Screw corner usa quatro parafusos.
5. Ajuste a folga **por lado**, de 0,10 a 0,40 mm. Uma folga de 0,20 mm corresponde a uma diferença de 0,40 mm entre duas larguras opostas de referência; não é a folga diametral de um furo de inserto.

A pré-visualização pode levar alguns segundos, especialmente com nervuras, furos e interfaces pequenas. Você pode continuar editando; pedidos antigos são substituídos pelo último desenho. A aba principal e o painel lateral compartilham o projeto. Idioma e tema são preferências de cada visualização.

## PCB e recortes

Na aba Acessórios, adicione torres de PCB e arraste-as no editor 2D. As coordenadas, a altura medida a partir do fundo interno, o diâmetro externo, o diâmetro do furo e sua profundidade ficam disponíveis abaixo. Torna-se necessário deixar ao menos 1,2 mm de fundo cego e espaço suficiente para a tampa. O modo piloto M3 inicia em 2,5 mm; ajuste conforme o parafuso, filamento e ensaio. As dimensões de insertos são sugestões, não padrões universais.

Adicione recortes e escolha frente, trás, esquerda ou direita. U é a posição horizontal no centro da face; Z é a altura a partir do fundo externo. USB-C/HDMI são envelopes de passagem editáveis, DC é circular e a ventilação aceita fendas ou hexágonos. Adicione múltiplos recortes para uma grelha. O sistema rejeita portas que invadam o fundo, os cantos ou a região do encaixe, ou que deixem pontes menores que 1,2 mm entre recortes.

Divisórias são informadas como listas de coordenadas X ou Y, separadas por vírgula. Elas se unem ao fundo e às paredes da base. Uma divisória que atravesse uma torre é rejeitada para preservar o furo e a intenção do projeto.

## Tampa, dobradiça e junta

Use o controle inferior da visualização para abrir, deslizar ou levantar a tampa. Arraste o viewport para orbitar e use a roda para zoom. O modo Raio-X mostra a disposição interna; o corte axial remove uma parte da visualização sem alterar a exportação.

No estilo Rugged, remova as duas travas flexíveis antes da abertura. A dobradiça pode usar pino separado, que é inserido depois da impressão, ou eixo cativo print-in-place. Neste último modo, exporte **Base + tampa** ou **Conjunto completo**: a base e a tampa ficam num objeto conjunto, sem separação automática na mesa. A tampa elevada sobre a cavidade pode precisar de pontes ou suportes. Configure suportes removíveis sem preencher os vãos funcionais da dobradiça. O movimento visual não comprova resistência ou impressão real.

A junta TPU exige um canal compatível e paredes suficientemente largas. Ela não está disponível para a tampa deslizante. Selecione **Junta TPU** e atribua o filamento/material no fatiador; o plugin não transforma PLA em uma peça flexível. Ajuste compressão e material após o teste físico.

## Calibrar e exportar

O kit imprime uma base pequena com encaixe e uma torre que replica o primeiro furo configurado (M3 se não houver torres), a tampa correspondente e uma lingueta de teste. Compare o encaixe, a flexão e o inserto antes de fabricar a caixa final. Seu tempo de impressão depende das configurações da máquina.

STL exporta cada item selecionado separadamente, exceto a montagem print-in-place, preservada como objeto de múltiplas cascas. 3MF organiza os itens na mesa e preserva nomes. Peças que não caibam devem ser redimensionadas no projeto; não há escala silenciosa.

Enviar para a mesa usa a instância atual do OrcaSlicer e pode aplicar 4 perímetros, 5 camadas de topo/fundo e preenchimento mecânico. O retorno confirma a transmissão do pedido, e eventuais falhas mantêm os arquivos na pasta de exportação. A integração nativa precisa de homologação em cada sistema; a suíte usa simulações da API.

## Limites conhecidos

Curvas e recortes são tesselações de campos geométricos. O alvo de erro nas interfaces é mostrado no painel, mas contração, fluxo e tolerância mecânica da impressão precisam de calibração. Insertos, portas e envelopes de PCB variam. Vedação e duração das travas não foram homologadas fisicamente. As travas são flexuras removíveis; sua liberação é manual. A opção print-in-place conserva a montagem na exportação e exige avaliação de suporte. Mantenha uma cópia dos projetos pessoais e não os inclua num repositório público.
