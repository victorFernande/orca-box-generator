# Verificação completa pela interface / Full UI verification

O runner `scripts/check_box_e2e.cjs` exercita a interface real do Box com Playwright/Chromium e o controlador Python real. A versão 1.2.2 simplifica a galeria para oito modelos padrão, um por estilo, sem acessórios pré-configurados. Este documento descreve o método; avalie o resultado da execução correspondente a cada revisão. Consulte os resultados por revisão no [histórico da CI](https://github.com/victorFernande/orca-box-generator/actions/workflows/ci.yml).

## Escopo

O comando completo percorre os oito estilos e os 8 presets, alterando os controles pela interface. Os testes incluem:

- Seleção dos 8 presets na página e no painel lateral, com prévias reais; exportação STL/3MF de cada preset na página, além de dimensões e controles específicos dos oito estilos.
- Todos os alvos de exportação habilitados para o estilo/configuração de ensaio; opções incompatíveis desabilitadas e rejeições explícitas, sem redução silenciosa de escala. O STL bruto preserva uma peça de 270 mm numa configuração de mesa de 260 mm, enquanto o 3MF automático deve rejeitar essa organização sem criar novo arquivo 3MF. O STL anterior permanece intacto; a pasta não precisa estar vazia. A guarda existente de altura permanece nos dois formatos.
- Movimento observado nas matrizes realmente enviadas ao WebGL, incluindo destravar os fechos antes de levantar a tampa e preservar os eixos das dobradiças. Câmera, materiais, cortes, cotas, malha, rotação e análise visual também são exercitados.
- Torres PCB com inserto/piloto, tipos e faces de recortes, divisórias, dimensões da junta TPU, qualidade e opção de processo. São configurações amostradas, não todas as combinações possíveis.
- Histórico, edição pendente, restaurar, Surpreenda-me, PT/EN, temas, sincronização dos metadados da impressora e criação/carregamento/exclusão de um preset pessoal temporário.
- Abas do painel lateral e um preset de cada estilo no painel, com edição e exportação 3MF.
- Recuperação de uma combinação incompatível de junta/estilo sem apagar silenciosamente os acessórios solicitados.

A abertura Rugged libera os clips antes de girar a tampa. No modo cativo Rugged, base/tampa não são exportadas individualmente; os alvos legítimos de junta e kit continuam separados da montagem. O estojo `clamshell_pip` exporta as duas metades abertas como um objeto com duas cascas. A junta TPU usa a compressão geométrica de 0,15 mm definida no código; a verificação computacional não determina a compressão real do material nem sua vedação.

O kit genérico contém um par base/tampa Lip Snap, uma lingueta de encaixe e o furo da primeira torre configurada, ou uma torre de amostra quando nenhuma foi configurada. Mesmo quando solicitado a partir de outro estilo compatível, ele não reproduz a dobradiça Rugged nem os trilhos Sliding. Não é um certificado de encaixe, tempo de impressão ou desempenho. Caixa aberta, Snap com alavancas, empilhável e estojo articulado exigem ensaios das próprias peças, com parede, folgas e recursos relevantes preservados.

## Arquivos reais e isolamento

`scripts/ui_test_server.py` cria um servidor em `127.0.0.1` numa porta disponível e usa uma pasta temporária privada. Os presets pessoais e os STL/3MF de ensaio são gravados nessa pasta. Nenhum dado do projeto é salvo no código-fonte, em `dist/` ou no armazenamento pessoal do plugin instalado.

A geometria, o controlador, o cache e os exportadores são os mesmos do produto. O transporte nativo para o OrcaSlicer e a abertura de pastas são desabilitados nesse ambiente. O teste de envio exige uma falha honesta de transporte, mesmo quando o 3MF foi realmente escrito; ele não pode declarar que objetos chegaram à mesa.

Cada exportação recebe um manifesto de desenvolvimento com parâmetros, estilo/alvo, nomes de arquivo, tamanhos, hashes e relatório independente. URLs de download usam identificadores cadastrados; não aceitam caminhos arbitrários. Somente os arquivos produzidos na pasta temporária dessa execução podem ser lidos. O runner baixa os bytes e confere tamanho e SHA-256.

`scripts/verify_box_e2e_exports.py` reabre o STL binário ou o ZIP/XML 3MF. Ele compara as coordenadas float32 e os triângulos com a superfície de impressão capturada no controlador. Também confere a prévia entregue à visualização, aplicando as transformações de impressão independentemente. As verificações incluem arestas fechadas/orientadas, ciclos de ligação dos vértices, quantidade de cascas e volumes positivos. No 3MF, incluem nomes/IDs, posição na mesa, altura, ausência de sobreposição dos envelopes de objetos separados e ajustes de processo. Um cache limitado guarda apenas relatórios por hash, sem acumular superfícies em todos os manifestos.

Esses testes não constituem uma prova exata de ausência de toda autointerseção, uma simulação de elasticidade ou uma avaliação de fatiamento. Rejeições de arquivos/configurações e controles negativos do leitor são cobertos por `tests/test_e2e_export_verifier.py`.

Na tampa Sliding real, após confirmar a identidade dos bytes e da superfície, o leitor também exige área de apoio no plano inferior de pelo menos 25% do envelope XY, com tolerância de 0,005 mm. A área e a fração ficam no relatório. O kit Lip Snap não está sujeito a esse critério específico. Uma regressão verifica que uma tampa fechada e orientada, porém apoiada apenas no pequeno dente, é rejeitada. Esse limite geométrico não mede aderência ou qualidade da primeira camada.

## Reproduzir

Requisitos de desenvolvimento: Python 3.12+, NumPy, Node.js e Playwright/Chromium. Playwright é ferramenta de teste, não dependência do plugin. A instalação de ferramentas pode exigir rede; a interface e a geração do produto são offline.

A partir da raiz do repositório, em um terminal POSIX:

```sh
python -m pip install "numpy>=1.26"
TASK_TOOLS="$(mktemp -d)"
npm install --prefix "$TASK_TOOLS" --no-save --package-lock=false playwright@1.62.1
node "$TASK_TOOLS/node_modules/playwright/cli.js" install chromium
export ORCA_PLAYWRIGHT_MODULE="$TASK_TOOLS/node_modules/playwright"
export ORCA_TEST_PYTHON=python
export ORCA_E2E_OUTPUT=test-output/e2e
node scripts/check_box_e2e.cjs
```

Em Linux sem as bibliotecas necessárias ao navegador, use `install --with-deps chromium`, como na CI; a instalação dessas bibliotecas pode exigir permissão de administrador.

No Windows/PowerShell, usando uma instalação existente das ferramentas:

```powershell
$env:ORCA_TEST_PYTHON = (Get-Command python).Source
$env:ORCA_PLAYWRIGHT_MODULE = Join-Path $env:TEMP 'orca-ui-tools/node_modules/playwright'
$env:ORCA_E2E_OUTPUT = 'test-output/e2e'
node scripts/check_box_e2e.cjs
```

Instale o Playwright no diretório indicado antes do comando, ou ajuste `ORCA_PLAYWRIGHT_MODULE` para sua instalação. `ORCA_CHROMIUM_PATH` é opcional e seleciona um executável Chromium já instalado. O interpretador Python selecionado precisa conseguir importar NumPy.

| Variável | Comportamento |
| --- | --- |
| `ORCA_E2E_OUTPUT` | Diretório de relatório e evidências. Sem valor, cria uma pasta temporária. |
| `ORCA_TEST_PYTHON` | Interpretador do backend; padrão `python`. |
| `ORCA_PLAYWRIGHT_MODULE` | Caminho do módulo Playwright; sem valor usa a resolução normal do Node. |
| `ORCA_CHROMIUM_PATH` | Executável opcional; sem valor usa o Chromium do Playwright. |
| `ORCA_E2E_TIMEOUT` | Espera por operação de prévia/exportação, em milissegundos; padrão 240000. Não é o limite total da suíte. |
| `ORCA_E2E_BED_X/Y/Z` | Medidas da impressora sintética em mm; o runner usa 260 em cada eixo por padrão. Não altera um perfil no OrcaSlicer. |
| `ORCA_E2E_SECTIONS` | Padrão completo: `presets,general,styles,features,negative,dock`. Selecionar menos seções produz apenas um diagnóstico parcial. |
| `ORCA_E2E_PRESET_EXPORTS` | Valor `0` desliga as exportações dos presets para diagnóstico. A CI completa mantém o valor `1`. |

O diagnóstico opcional `witness` observa o início da abertura Rugged e não substitui as seções completas. Não há filtro individual por estilo nesta versão do runner.

As regressões de correlação entre pedidos e respostas podem ser executadas sem Playwright com `node scripts/box_e2e_waiter_test.cjs`. Leituras do DOM e das matrizes WebGL servem como observações; as alterações no desenho são feitas pelos controles da interface. O diagnóstico dos pedidos preserva uma cópia dos parâmetros exatamente serializados para o backend.

## Evidências e CI

`report.json` registra verificações, falhas, erros de console, manifestos e hashes dos arquivos. Capturas e matrizes de movimento são gravadas quando previstas pelo teste; `backend.log` registra o processo Python. O runner retorna código diferente de zero quando uma verificação falha. Relatórios parciais não demonstram aprovação da suíte completa.

O encerramento normal solicita `/shutdown`, termina apenas o servidor criado pelo teste e limpa a pasta temporária dos arquivos exportados. As evidências em `ORCA_E2E_OUTPUT` permanecem para revisão; elas não incluem os bytes de todos os modelos. `test-output/` é ignorado pelo Git. Relatórios locais podem mencionar diretórios temporários e devem ser revisados antes de compartilhamento público.

Na CI, a matriz Windows/macOS/Linux executa os testes Python e as regressões Node de correlação. O Linux também executa a comparação visual de template e, em uma etapa independente, o runner E2E completo, reutilizando a instalação do Playwright. A etapa completa pode executar mesmo se a comparação visual anterior falhar, desde que as ferramentas tenham sido instaladas e o job não tenha sido cancelado. A evidência `test-output/e2e/` é preservada por 14 dias no artefato `orca_box_generator-e2e`, inclusive após falhas quando o upload puder executar. Os limites de 90 minutos da etapa e 120 minutos do job são limites de execução, não medições de duração nem promessa de aprovação.

## Aceitação nativa e física

O Chromium isolado não valida instalação, permissões, WebView, WM_COPYDATA/Cocoa/D-Bus ou carregamento dentro do OrcaSlicer real. Esses resultados são separados no [registro de validação](VALIDATION.md). Testes nativos em Windows não demonstram integração nativa macOS/Linux.

Não se infere aprovação de fatiamento, impressão, encaixe físico, esforço de destravamento, vida útil, vedação, carga ou qualidade de pontes a partir do E2E. Uma prévia móvel e uma malha fechada não provam que uma dobradiça sairá livre da impressora. Preserve os perfis e faça ensaios físicos calibrados antes de uso funcional.

## English scope note

The full command uses real browser controls, real Python geometry and real STL/3MF bytes across eight styles, eight standard presets and the enabled targets in the sampled configurations. Native dispatch and folder opening are disabled only in the isolated DEV bridge. Artifact downloads use registered temporary-file IDs; independent readers compare the delivered preview, print snapshot and serialized float32 geometry, then check topology, shell counts, placement and process settings. The report must be assessed for its exact revision and enabled sections. Native application acceptance and physical printing/mating tests remain separate evidence; no completed-run count is asserted here before the final result.
