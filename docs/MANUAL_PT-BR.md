# Manual — Orca Box Studio

## Instalação e interface

Após instalar ou atualizar, feche e reabra o OrcaSlicer. No gerenciador de plugins, confira a versão e ative **Orca Box Studio**. Abra a aba superior **Gerador de Caixas** ou execute **Orca Box Studio — Painel Lateral**.

O cabeçalho reúne o nome do projeto, a impressora sincronizável, desfazer/refazer, Surpreenda-me, restaurar, idioma e tema. A galeria permite filtrar estilos e presets salvos. Os campos numéricos e sliders alteram o mesmo parâmetro. O rodapé mantém exportação e envio acessíveis enquanto os controles rolam.

No painel lateral, use **Forma, Recursos, Impressão e Presets**. A prévia compacta permanece no topo. Materiais visuais, câmera, malha e cortes não modificam a geometria exportada nem selecionam um filamento para impressão.

## Criar a caixa

1. Abra o Gerador de Caixas no OrcaSlicer ou execute seu painel lateral.
2. Use um dos 15 presets ou mantenha a caixa inicial. Os presets de placas representam envelopes iniciais; compare sua revisão real de ESP32, Arduino ou Raspberry Pi antes de imprimir.
3. Digite as medidas em milímetros: largura X e profundidade Y externas do corpo da base, e altura Z da peça base. No empilhável, essa altura inclui o pé; nos outros estilos, vai do fundo externo até a borda. Ajuste parede, fundo e raio dos cantos. A origem XY fica no centro da base; Z=0 corresponde ao fundo externo, ou à face inferior do pé no empilhável. Tampa, ressaltos e travas podem aumentar o envelope total; os campos não representam o espaço interno.
4. Escolha um dos sete estilos: Lip Snap, Rugged, Sliding, Screw Corner, Caixa aberta, Tampa com travas ou Empilhável. Os estilos de armazenamento são detalhados abaixo.
5. Ajuste a folga **por lado**, de 0,10 a 0,40 mm. Uma folga de 0,20 mm corresponde a uma diferença de 0,40 mm entre duas larguras opostas de referência; não é a folga diametral de um furo de inserto. No Lip Snap, ajuste **Retenção do encaixe** (`snap_retention`, 0,03–0,30 mm) separadamente: ela controla o ressalto radial que precisa vencer a entrada. A folga controla o posicionamento da saia. A rampa facilita a entrada, mas não comprova que o material suporta a flexão solicitada.

As cascas simples Lip Snap e os estilos de armazenamento têm geração por contornos; acessórios complexos podem exigir a superfície CSG e levar mais tempo. A exportação reutiliza as superfícies já validadas. Veja [medições reproduzíveis](PERFORMANCE.md). Você pode continuar editando; pedidos antigos são substituídos pelo último desenho. A aba principal e o painel lateral compartilham o projeto. Idioma e tema são preferências de cada visualização.

## Os sete estilos

- **Lip Snap:** saia de localização, ressalto com entrada gradual e canal correspondente. Ajuste a retenção sem confundi-la com a folga dimensional.
- **Rugged:** dobradiça reforçada e duas travas removíveis; há opção de pino separado ou eixo cativo.
- **Sliding:** tampa inserida pela frente em trilhos de 45°, com lingueta flexível e detente traseiro. A espessura deriva dos trilhos e da folga.
- **Screw Corner:** quatro colunas de canto e furos de passagem na tampa para M2/M2.5/M3; calibre o piloto no material escolhido.
- **Caixa aberta (`open_bin`):** exporta somente a base. Ative ou desative as duas alças e escolha esquerda/direita ou frente/trás. Largura útil, altura útil e margem superior são medidas das aberturas, não de puxadores externos. O sistema preserva os cantos, o fundo e uma ponte superior; confirme o conforto da mão em uma impressão de teste. Não há tampa, junta de tampa ou kit genérico neste estilo.
- **Tampa com travas (`snap_latch`):** exporta base, tampa plana e duas travas separadas na frente. Ajuste largura e espessura das travas, retenção do gancho e profundidade da saia da tampa. Encaixe a tampa, instale as travas e libere-as manualmente antes de levantar a tampa. O detente exige flexão transitória durante montagem/retirada; o modelo fechado possui folga nas regiões amostradas. Isso não é uma estimativa da força de liberação.

- **Empilhável (`stackable_bin`):** base aberta com frente rebaixada e pé inferior de indexação. Ajuste a largura e o rebaixo do acesso frontal, a altura do pé e a folga de empilhamento. A frente permanece mais baixa para acesso; laterais e traseira mantêm o aro de apoio. Há somente uma base exportável, sem tampa, junta ou kit genérico.

Na tampa com travas, a placa superior fica em `altura Z + folga + espessura da tampa`. O controle `lid_wall_height` é a profundidade da saia **para baixo**, dentro da base, e não uma parede acima da tampa. Na impressão separada, a tampa é invertida, com a face plana no leito e a saia para cima. As travas são orientadas separadamente; confira o apoio e as configurações no fatiador. A altura do conjunto com travas pode superar a altura da placa.

## Montar caixas empilháveis

Todas as medidas são em milímetros. Neste estilo, a altura total `H` inclui o pé de altura `P`. A face inferior do corpo fica em `Z=P`, e o piso interno em `Z=P + espessura do fundo`. O pé é sólido na região central para apoiar a impressão; sua função na montagem é indexar dentro da abertura da caixa de baixo. O peso da caixa superior se transmite pelos ombros sobre os aros laterais e traseiro, não por uma peça flutuante com folga vertical.

Para pertencer à mesma família, duas caixas precisam ter largura X, profundidade Y, raio dos cantos, parede, altura do pé e folga de empilhamento iguais. Alturas totais e acessos frontais podem ser diferentes. Use **Folga de empilhamento** (`stack_clearance`, 0,10–0,80 mm por lado), independente da folga Lip/Rugged. O pé cabe na abertura com essa folga; ampliar o deslocamento lateral encontra a parede e ajuda a indexar a posição.

Na montagem, a base da caixa superior fica em `Z = H inferior − P superior`. A altura total do par é `H inferior + H superior − P superior`. Por exemplo, caixas da mesma família com alturas 60 e 100 mm e pé de 2 mm se montam com deslocamento Z de 58 mm e altura total de 158 mm. Essa fórmula descreve a montagem após a impressão; exporte e imprima cada caixa separadamente.

Os testes verificam três áreas de contato e a projeção do centro de massa da caixa vazia dentro dos apoios nas configurações amostradas. Não estabelecem capacidade de carga ou proteção contra tombamento com conteúdo. Faça um teste físico com seu filamento, tolerância e distribuição de carga. A geometria é própria; não há promessa de compatibilidade com organizadores de outros projetos.

## PCB e recortes

Na área de Recursos, adicione torres de PCB e arraste-as no editor 2D. As coordenadas, a altura medida a partir do fundo interno, o diâmetro externo, o diâmetro do furo e sua profundidade ficam disponíveis abaixo. Torna-se necessário deixar ao menos 1,2 mm de fundo cego e espaço suficiente para a tampa. O modo piloto M3 inicia em 2,5 mm; ajuste conforme o parafuso, filamento e ensaio. As dimensões de insertos são sugestões, não padrões universais.

Adicione recortes e escolha frente, trás, esquerda ou direita. U é a posição horizontal no centro da face; Z é a altura a partir do fundo externo. USB-C/HDMI são envelopes de passagem editáveis, DC é circular e a ventilação aceita fendas ou hexágonos. Adicione múltiplos recortes para uma grelha. O sistema rejeita portas que invadam o fundo, os cantos ou a região do encaixe, ou que deixem pontes menores que 1,2 mm entre recortes.

Divisórias são informadas como listas de coordenadas X ou Y, separadas por vírgula. Elas se unem ao fundo e às paredes da base. Uma divisória que atravesse uma torre é rejeitada para preservar o furo e a intenção do projeto.

## Tampa, dobradiça e junta

Use o controle inferior da visualização para abrir, deslizar ou levantar a tampa. Arraste o viewport para orbitar e use a roda para zoom. O modo Raio-X mostra a disposição interna; o corte axial remove uma parte da visualização sem alterar a exportação.

No estilo Rugged, remova as duas travas flexíveis antes da abertura. A dobradiça pode usar pino separado, que é inserido depois da impressão, ou eixo cativo print-in-place. Neste último modo, exporte **Base + tampa** ou **Conjunto completo**: a base e a tampa ficam num objeto conjunto, sem separação automática na mesa. A tampa elevada sobre a cavidade pode precisar de pontes ou suportes. Configure suportes removíveis sem preencher os vãos funcionais da dobradiça. O movimento visual não comprova resistência ou impressão real.

A junta TPU exige um canal compatível e paredes suficientemente largas. Ela não está disponível para a tampa deslizante. Selecione **Junta TPU** e atribua o filamento/material no fatiador; o plugin não transforma PLA em uma peça flexível. Ajuste compressão e material após o teste físico.

## Calibrar e exportar

Nos quatro estilos originais, o kit genérico imprime uma base pequena com encaixe e uma torre que replica o primeiro furo configurado (M3 se não houver torres), a tampa correspondente e uma lingueta de teste. Compare o encaixe, a flexão e o inserto antes de fabricar a caixa final. Esse kit usa um encaixe Lip Snap e não reproduz a dobradiça ou cada mecanismo completo. Seu tempo de impressão depende das configurações da máquina.

**Caixa aberta, Tampa com travas e Empilhável não têm esse kit.** Crie primeiro uma caixa menor com as mesmas espessuras e folgas; para a tampa com travas, mantenha também dimensões e retenção das travas e profundidade da saia. Para o empilhável, teste duas alturas da mesma família, preservando parede, raio, pé e folga de empilhamento. Exporte as peças reais e faça um ensaio de encaixe. Reduzir o conjunto inteiro no fatiador também reduz as folgas e não é uma calibração equivalente.

STL exporta cada item selecionado separadamente, exceto a montagem print-in-place, preservada como objeto de múltiplas cascas. 3MF organiza os itens na mesa e preserva nomes. Peças que não caibam devem ser redimensionadas no projeto; não há escala silenciosa.

Enviar para a mesa usa a instância atual do OrcaSlicer e pode aplicar 4 perímetros, 5 camadas de topo/fundo e preenchimento mecânico. O retorno confirma a transmissão do pedido, e eventuais falhas mantêm os arquivos na pasta de exportação. A versão 1.2 ainda precisa de validação nativa; a suíte usa simulações da API. O histórico de abertura e entrega no Windows da versão anterior está no [registro de validação](VALIDATION.md). Ao abrir um 3MF, use abrir como projeto ou uma mesa vazia; ao importar em um projeto ocupado, organize os objetos antes de fatiar.

## Limites conhecidos

Curvas são tesselações de contornos ou campos geométricos. Os dez testes funcionais de encaixe e os cinco testes independentes de empilhamento da versão 1.2 verificam trajetórias, contato e amostras de folga; ausência de sobreposição fechada nas amostras não elimina a interferência transitória intencional dos detentes, nem comprova o encaixe impresso. O alvo de erro nas interfaces é mostrado no painel, mas contração, fluxo e tolerância mecânica da impressão precisam de calibração. Insertos, portas e envelopes de PCB variam. Vedação e duração das travas não foram homologadas fisicamente. As travas são flexuras removíveis; sua liberação é manual. A opção print-in-place conserva a montagem na exportação e exige avaliação de suporte. Mantenha uma cópia dos projetos pessoais e não os inclua num repositório público.
