# Manual — Orca Box Studio

## Instalação e interface

Após instalar ou atualizar, feche e reabra o OrcaSlicer. No gerenciador de plugins, confira a versão **1.4.1** e ative **Orca Box Studio**. Abra a aba superior **Box Studio**.

Para abrir o painel lateral no caminho verificado no Windows com OrcaSlicer 2.5.1:

1. Na área principal do OrcaSlicer, pressione **Espaço** para abrir o Speed Dial.
2. Digite **Orca Box** e selecione **Orca Box Studio — Painel Lateral**.
3. Pressione **Enter**. O painel oferece **Forma, Recursos, Impressão e Presets**.

O cabeçalho reúne o nome do projeto, a impressora sincronizável, desfazer/refazer, Surpreenda-me, restaurar, idioma e tema. A galeria permite filtrar estilos e presets salvos. Os campos numéricos e sliders alteram o mesmo parâmetro. O rodapé mantém exportação e envio acessíveis enquanto os controles rolam.

No painel lateral, use **Forma, Recursos, Impressão e Presets**. A prévia compacta permanece no topo. Materiais visuais, câmera, malha e cortes não modificam a geometria exportada nem selecionam um filamento para impressão.

## Criar a caixa

1. Abra o Box Studio no OrcaSlicer ou execute seu painel lateral.
2. Escolha um dos oito modelos padrão, um por estilo, ou mantenha a caixa inicial. A galeria não inclui presets de IoT nem acessórios de eletrônica pré-configurados. Comece pelas medidas e pelo funcionamento da caixa.
3. Digite as medidas em milímetros: largura X e profundidade Y externas do corpo da base, e altura Z da peça base. No empilhável, essa altura inclui o pé; no estojo articulado, ela é a altura de cada metade; nos outros estilos, vai do fundo externo até a borda. Ajuste parede, fundo e raio dos cantos. A origem XY fica no centro da base; Z=0 corresponde ao fundo externo, ou à face inferior do pé no empilhável. Tampa, ressaltos e travas podem aumentar o envelope total; os campos não representam o espaço interno.
4. Escolha um dos oito estilos: Lip Snap, Rugged, Sliding, Screw Corner, Caixa aberta, Tampa com travas, Empilhável ou Estojo articulado. Os estilos de armazenamento são detalhados abaixo.
5. Ajuste a folga **por lado**, de 0,10 a 0,40 mm nos estilos comuns. No Rugged, o intervalo é 0,10–0,30 mm para os encaixes das articulações, preservando o encosto da trava e o contato nominal do aro em V. Uma folga de 0,20 mm corresponde a uma diferença de 0,40 mm entre duas larguras opostas de referência; não é a folga diametral de um furo de inserto. No Lip Snap, ajuste **Retenção do encaixe** (`snap_retention`, 0,03–0,30 mm) separadamente: ela controla o ressalto radial que precisa vencer a entrada. A folga controla o posicionamento da saia. A rampa facilita a entrada, mas não comprova que o material suporta a flexão solicitada.

As cascas simples Lip Snap e os estilos de armazenamento têm geração por contornos; acessórios complexos podem exigir a superfície CSG e levar mais tempo. A exportação reutiliza as superfícies já validadas. Veja [medições reproduzíveis](PERFORMANCE.md). Você pode continuar editando; pedidos antigos são substituídos pelo último desenho. A aba principal e o painel lateral compartilham o projeto. Idioma e tema são preferências de cada visualização.

## Os oito estilos

- **Lip Snap:** saia de localização, ressalto com entrada gradual e canal correspondente. Ajuste a retenção sem confundi-la com a folga dimensional.
- **Rugged · SnapLock:** base e tampa profundas com alturas independentes, dobradiça traseira de encaixe e duas travas articuladas na tampa. São quatro peças sem pinos soltos. Veja [medidas e montagem](RUGGED_SNAPLOCK.md).
- **Sliding:** tampa inserida pela frente em trilhos de 45°, com lingueta flexível e detente traseiro. A espessura deriva dos trilhos e da folga.
- **Screw Corner:** quatro colunas de canto e furos de passagem na tampa para M2/M2.5/M3; calibre o piloto no material escolhido.
- **Caixa aberta (`open_bin`):** exporta somente a base. Ative ou desative as duas alças e escolha esquerda/direita ou frente/trás. Largura útil, altura útil e margem superior são medidas das aberturas, não de puxadores externos. O sistema preserva os cantos, o fundo e uma ponte superior; confirme o conforto da mão em uma impressão de teste. Não há tampa, junta de tampa ou kit genérico neste estilo.
- **Tampa com travas (`snap_latch`):** exporta quatro peças: base, tampa plana e duas alavancas com pinos integrados. As alavancas são montadas nos apoios da base e ficam articuladas nela; os ganchos prendem as abas da tampa. Gire os dois fechos para abrir e depois retire a tampa. Ajuste largura e espessura da alavanca, retenção do gancho, diâmetro do pivô e profundidade da saia da tampa. A passagem pelo clique exige flexão transitória; o estado fechado tem folga nas regiões verificadas. Isso não estima a força necessária no material impresso.

- **Empilhável (`stackable_bin`):** base aberta com frente rebaixada e pé inferior de indexação. Ajuste a largura e o rebaixo do acesso frontal, a altura do pé e a folga de empilhamento. A frente permanece mais baixa para acesso; laterais e traseira mantêm o aro de apoio. Há somente uma base exportável, sem tampa, junta ou kit genérico.

- **Estojo articulado (`clamshell_pip`):** duas metades de mesma profundidade e duas dobradiças com eixos cativos integrados. A prévia abre de 0 a 180°. A exportação mantém as metades abertas a 180°, com ambos os fundos na mesa, em um único objeto com duas cascas. Não há trava frontal neste estilo inicial.

Na tampa com travas, a placa superior fica em `altura Z + folga + espessura da tampa`. O controle `lid_wall_height` é a profundidade da saia **para baixo**, dentro da base, e não uma parede acima da tampa. Na impressão separada, a tampa é invertida, com a face plana no leito e a saia para cima. As travas são orientadas separadamente; confira o apoio e as configurações no fatiador. A altura do conjunto com travas pode superar a altura da placa.

## Montar e abrir os fechos de alavanca

Imprima a base, a tampa e as duas alavancas na orientação exportada. Cada alavanca tem os pinos do pivô integrados. Sem a tampa no caminho, alinhe esses pinos com as bocas chanfradas dos dois apoios frontais correspondentes e pressione a alavanca em direção à base para encaixar. As bocas retêm os pinos radialmente; o corpo entre os apoios limita a saída lateral. Teste o ajuste antes de montar o segundo fecho e preserve as áreas flexíveis.

O controle **Diâmetro do pivô** (`latch_pivot_diameter`, 2,4–4,0 mm) muda os pinos e suas sedes. A retenção do gancho é outra dimensão, não uma regulagem de força. Pivô, espessura, folga e largura precisam de espaço suficiente na frente da base; combinações incompatíveis são rejeitadas. O cubo/pinos possuem faces planas para apoiar a impressão das alavancas. Avalie adesão, pontes e suportes no fatiador; não há promessa de impressão sem suporte.

O controle de abertura segue a operação real: primeiro os dois fechos giram até 90°, com a tampa parada; depois a tampa sobe e os fechos permanecem na base. Na montagem física, abra ambos os fechos antes de retirar a tampa. Para fechar, assente a tampa e gire as alavancas para prender suas abas. Não puxe os fechos para fora da base como parte da abertura normal.

O mecanismo inclui entrada gradual e clique angular. Esse contato transitório é separado da folga em repouso; não se deve interpretar ausência de colisão fechada como garantia de encaixe, força ou durabilidade impressa. Faça uma amostra menor preservando pivô, folgas e espessuras. Se as quatro peças não couberem juntas no 3MF, use um projeto menor ou exporte STL para imprimir em lotes. Não reduza os encaixes pela escala do fatiador.

## Imprimir o estojo articulado

**Altura de cada metade** é a altura externa `H` tanto da base quanto da tampa; a tampa não usa o controle de espessura dos outros estilos. O fundo e a parede têm espessuras próprias, iguais nas duas metades. A altura fechada do corpo é `2H + c`, com `c` igual à folga de fechamento (`fit_clearance`). Use a inspeção de movimento para avaliar a disposição, sem confundir a animação com teste físico.

A **Folga PIP** (`pip_clearance`, 0,20–0,60 mm) é o vão axial/radial entre eixo e tubos. A **Separação da dobradiça** (`hinge_separation`, 4–12 mm) afasta o eixo do corpo; valores incompatíveis com o raio são rejeitados. A largura X e a profundidade Y continuam representando uma metade. O envelope aberto para imprimir tem largura X, profundidade `2 × Y + 2 × separação` e altura máxima `H + folga de fechamento/2 + raio externo da dobradiça`. Os tubos ficam acima da borda; confira esse envelope na impressora.

Escolha **Base + tampa** ou **Conjunto completo**. A exportação forma um objeto de duas cascas, abertas e cativas, com os dois fundos em Z=0. Preserve essa relação na mesa; separar/reorganizar as cascas compromete a dobradiça. Os eixos e suas cabeças pertencem à tampa, com pedestais que chegam ao fundo. Há pontes curtas entre os apoios do eixo. Avalie-as no fatiador, mantenha suporte fora dos vãos funcionais e faça uma impressão de teste. Não há garantia de impressão sem suporte, desencravamento automático ou movimento livre depois de imprimir.

Este estilo inicial não aceita torres de PCB, recortes, divisórias, junta TPU, kit genérico ou metades exportadas isoladamente. Os parâmetros incompatíveis são preservados e geram erro; ajuste-os ou use outro estilo. Não há teste de força, vida útil ou carga da dobradiça.

## Montar caixas empilháveis

Todas as medidas são em milímetros. Neste estilo, a altura total `H` inclui o pé de altura `P`. A face inferior do corpo fica em `Z=P`, e o piso interno em `Z=P + espessura do fundo`. O pé é sólido na região central para apoiar a impressão; sua função na montagem é indexar dentro da abertura da caixa de baixo. O peso da caixa superior se transmite pelos ombros sobre os aros laterais e traseiro, não por uma peça flutuante com folga vertical.

Para pertencer à mesma família, duas caixas precisam ter largura X, profundidade Y, raio dos cantos, parede, altura do pé e folga de empilhamento iguais. Alturas totais e acessos frontais podem ser diferentes. Use **Folga de empilhamento** (`stack_clearance`, 0,10–0,80 mm por lado), independente da folga Lip/Rugged. O pé cabe na abertura com essa folga; ampliar o deslocamento lateral encontra a parede e ajuda a indexar a posição.

Na montagem, a base da caixa superior fica em `Z = H inferior − P superior`. A altura total do par é `H inferior + H superior − P superior`. Por exemplo, caixas da mesma família com alturas 60 e 100 mm e pé de 2 mm se montam com deslocamento Z de 58 mm e altura total de 158 mm. Essa fórmula descreve a montagem após a impressão; exporte e imprima cada caixa separadamente.

Os testes verificam três áreas de contato e a projeção do centro de massa da caixa vazia dentro dos apoios nas configurações amostradas. Não estabelecem capacidade de carga ou proteção contra tombamento com conteúdo. Faça um teste físico com seu filamento, tolerância e distribuição de carga. A geometria é própria; não há promessa de compatibilidade com organizadores de outros projetos.

## PCB e recortes

Na área de Recursos, adicione torres de PCB e arraste-as no editor 2D. As coordenadas, a altura medida a partir do fundo interno, o diâmetro externo, o diâmetro do furo e sua profundidade ficam disponíveis abaixo. Torna-se necessário deixar ao menos 1,2 mm de fundo cego e espaço suficiente para a tampa. O modo piloto M3 inicia em 2,5 mm; ajuste conforme o parafuso, filamento e ensaio. As dimensões de insertos são sugestões, não padrões universais.

Adicione recortes e escolha frente, trás, esquerda ou direita. U é a posição horizontal no centro da face; Z é a altura a partir do fundo externo. USB-C/HDMI são envelopes de passagem editáveis, DC é circular e a ventilação aceita fendas ou hexágonos. A largura e a altura do hexágono definem o envelope completo em cada eixo de forma independente; proporções diferentes podem alongar o hexágono, sem manter um hexágono regular. Adicione múltiplos recortes para uma grelha. O sistema rejeita portas que invadam o fundo, os cantos ou a região do encaixe, ou que deixem pontes menores que 1,2 mm entre recortes.

Divisórias são informadas como listas de coordenadas X ou Y, separadas por vírgula. Elas se unem ao fundo e às paredes da base. Uma divisória que atravesse uma torre é rejeitada para preservar o furo e a intenção do projeto.

## Tampa, dobradiça e junta

Use o controle inferior da visualização para abrir, deslizar ou levantar a tampa. Arraste o viewport para orbitar e use a roda para zoom. O modo Raio-X mostra a disposição interna; o corte axial remove uma parte da visualização sem alterar a exportação.

No Rugged SnapLock, as travas ficam presas à tampa. Solte as linguetas inferiores e gire as travas antes de abrir. A animação usa os primeiros 25% para girar as travas, depois abre a dobradiça traseira com as travas acompanhando a tampa. Exporte as quatro peças separadas para montar após a impressão: base pelo fundo, tampa invertida e travas deitadas na face larga. Não há pino solto nem modo print-in-place neste estilo. O estojo articulado continua sendo um estilo separado. A prévia não simula flexão nem comprova resistência ou encaixe físico.

A junta TPU exige um canal compatível e paredes suficientemente largas. Ela não está disponível para a tampa deslizante. Selecione **Junta TPU** e atribua o filamento/material no fatiador; o plugin não transforma PLA em uma peça flexível. A junta acompanha a folga de fechamento e prevê 0,15 mm de compressão nominal: seu topo fica 0,15 mm acima do apoio da tampa na montagem rígida. Isso não determina pressão ou vedação reais. Ao mudar para Sliding, caixa aberta ou empilhável com a junta marcada, a opção permanece visível e pode ser desmarcada para corrigir a incompatibilidade; torres e recortes solicitados não são apagados silenciosamente. Teste o dimensionamento e o material fisicamente.

No Sliding, o dente de retenção fica acima da placa e a orientação de exportação mantém apoio amplo na face inferior plana; os cantos traseiros têm alívio no caminho nominal de entrada. O detente ainda exige flexão transitória. Essa geometria não é uma aprovação de aderência, força, fatiamento ou encaixe impresso.

## Calibrar e exportar

Nos estilos compatíveis, o kit genérico imprime uma base pequena com encaixe e uma torre que replica o primeiro furo configurado (M3 se não houver torres), a tampa correspondente e uma lingueta de teste. Compare o encaixe, a flexão e o inserto antes de fabricar a caixa final. Esse kit usa um encaixe Lip Snap e não reproduz os trilhos Sliding ou cada mecanismo completo. Seu tempo de impressão depende das configurações da máquina.

**Rugged, Caixa aberta, Tampa com travas, Empilhável e Estojo articulado não têm esse kit.** Crie primeiro uma caixa menor com as mesmas espessuras e folgas, respeitando os limites do estilo; para o Rugged, preserve os diâmetros dos encaixes e teste suas quatro peças. Para a tampa com travas, mantenha também dimensões e retenção das travas e profundidade da saia. Para o empilhável, teste duas alturas da mesma família, preservando parede, raio, pé e folga de empilhamento. Para o estojo articulado, teste um conjunto menor mantendo folgas, eixo e separação compatíveis. Exporte as peças reais e faça um ensaio de encaixe. Reduzir o conjunto inteiro no fatiador também reduz as folgas e não é uma calibração equivalente.

STL exporta cada item selecionado separadamente, exceto a montagem print-in-place, preservada como objeto de múltiplas cascas. Ele mantém as medidas solicitadas e não faz organização XY na mesa ativa; uma peça pode ser mais larga que essa mesa. A conferência existente de altura continua valendo nos dois formatos. Organize os STLs e escolha uma impressora compatível antes de fabricar. 3MF organiza os itens na mesa e preserva nomes. O organizador considera os envelopes completos e mantém espaçamento entre as peças. No Snap com parâmetros padrão de encaixe, um corpo de 160 × 90 × 35 mm passou em mesa de 220 × 220 mm; 160 × 95 × 35 mm passou em 260 × 260 mm e foi rejeitado em 220 × 220 mm. Isso descreve o organizador atual, não um limite geométrico universal. Exporte STLs por peça ou ajuste as dimensões no projeto; não há escala silenciosa.

Enviar para a mesa usa a instância atual do OrcaSlicer e pode aplicar 4 perímetros, 5 camadas de topo/fundo e preenchimento mecânico. O retorno confirma a transmissão do pedido, e eventuais falhas mantêm os arquivos na pasta de exportação. Os resultados Windows deste parágrafo são históricos da versão 1.2.0; consulte o [registro de validação](VALIDATION.md) para a revisão 1.2.1. A versão 1.2 anterior a este redesenho foi verificada dentro do OrcaSlicer 2.5.1 no Windows, na página e no painel lateral, incluindo carregamento visual do 3MF na mesa. A página e o painel lateral do novo Snap com alavancas foram verificados no Windows, com operação em duas etapas, exportação e base/tampa/duas alavancas visualmente carregadas na mesa. No painel lateral, alterar o diâmetro do pivô de 3,0 para 3,2 mm preservou a abertura em 100%; a troca EN→PT atualizou os rótulos imediatamente. O teste anterior do Snap não substitui essa nova observação. Os testes automatizados também usam simulações da API; a integração nativa macOS/Linux continua pendente. O [registro de validação](VALIDATION.md) separa esses resultados e o histórico anterior. Ao abrir um 3MF, use abrir como projeto ou uma mesa vazia; ao importar em um projeto ocupado, organize os objetos antes de fatiar.

A validação nativa não executou fatiamento nem impressão. Revise o perfil real da impressora e os avisos de limites antes de imprimir. Na sessão de teste, um aviso de aceleração acima do limite veio do perfil já existente; as acelerações não foram alteradas durante a validação. Ao fechar o projeto exportado, o Orca ofereceu salvar seus ajustes de processo; escolher **Descartar** restaurou o perfil anterior, sem sobrescrevê-lo. Revise os ajustes do 3MF antes de salvar um perfil ou imprimir.

O método de reprodução e o escopo da verificação completa pela interface estão em [E2E](E2E.md). Os resultados atuais ficam no [registro de validação](VALIDATION.md); os totais anteriores não são uma aprovação antecipada da revisão 1.2.1.

## Limites conhecidos

No histórico da versão 1.2.0, a suíte local passou em 136 testes em 574,594 s, com Chromium habilitado e sem falhas, erros ou testes ignorados. Esse resultado computacional não substitui a calibração física; os resultados por revisão estão no [histórico da CI](https://github.com/victorFernande/orca-box-generator/actions/workflows/ci.yml).

Curvas são tesselações de contornos ou campos geométricos. O redesenho Snap passou em 17 testes independentes, incluindo as dez verificações funcionais adaptadas e sete verificações novas de pivô/alavanca. Os cinco testes de empilhamento e oito do estojo articulado permanecem evidência dos estilos correspondentes. São verificações de trajetórias, contato, topologia e eventos de início de material; ausência de sobreposição fechada nas amostras não elimina a interferência transitória intencional dos detentes, nem comprova o encaixe impresso. O alvo de erro nas interfaces é mostrado no painel, mas contração, fluxo e tolerância mecânica da impressão precisam de calibração. Insertos, portas e envelopes de PCB variam. Vedação e duração das travas não foram homologadas fisicamente. A liberação das travas é manual; no Snap com alavancas, elas permanecem presas aos pivôs da base. A opção print-in-place conserva a montagem na exportação e exige avaliação de suporte. Mantenha uma cópia dos projetos pessoais e não os inclua num repositório público.
