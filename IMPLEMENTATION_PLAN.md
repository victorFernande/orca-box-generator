# Especificação de referência

Este plano registra o escopo original. O comportamento entregue, as tolerâncias e os limites de homologação estão no README e em docs/IMPLEMENTATION_NOTES.md. Tempos de impressão e desempenho são metas, não resultados físicos medidos.

# Orca Box & Enclosure Studio (`orca-box-generator`) — Plano de Implementação Técnica

> **Instrução para a IA que assumir este projeto:**
> Este documento contém a especificação técnica completa, decisões de design alinhadas e o roteiro passo a passo para implementar o plugin nativo **Orca Box & Enclosure Studio** para o **OrcaSlicer 2.5.1+**.
> Use como referência obrigatória os projetos irmãos existentes na pasta:
> - `../orca-gear-generator`
> - `../orca-vase-generator`
> Mantenha 100% de paridade com os padrões de arquitetura, empacotamento e testes desses projetos.

---

## 1. Visão Geral & Escopo

- **Nome do Plugin:** `Orca Box Studio` / `Orca Box & Enclosure Studio`
- **Slug / Diretório:** `orca-box-generator`
- **ID do Plugin (`[tool.orcaslicer.plugin].id`):** `orca-box-studio`
- **Nome do Módulo Python:** `box_studio`
- **Target OS:** Windows (`win32`), macOS (`darwin` arm64/x86_64) e Linux.
- **Ambiente de Execução:** Python `>=3.12` embutido do OrcaSlicer (`C:\Program Files\OrcaSlicer\python\python.exe`) com `numpy>=1.26`. Zero dependências compiladas externas (100% offline).

---

## 2. Decisões de Design (Aprovadas)

1. **4 Estilos Construtivos de Caixa:**
   - **`lip_snap`:** Caixa lisa/chanfrada com encaixe por pressão de perfil perimetral escalonado (*friction/snap lip*).
   - **`rugged_box`:** Caixa reforçada estilo militar/Pelican com nervuras externas de reforço, dobradiças cilíndricas *print-in-place* ou por pino e fechos/travas tipo *clamp clip*.
   - **`sliding_lid`:** Caixa estilo estojo com trilhos chanfrados a 45° autossuportados e trava de final de curso.
   - **`screw_corner`:** Case de eletrônica com 4 colunas de canto para fixação da tampa por parafusos métricos (M2/M2.5/M3).

2. **Acessórios & Hardware Interno:**
   - **Torres de PCB (*Standoffs*):** Coordenadas `(x, y)` customizáveis para montagem de placas, com furos calibrados para *heat-set inserts* de latão (M2, M2.5, M3) ou orifícios piloto para parafusos autoatarraxantes.
   - **Recortes de Painel nas Paredes:** Aberturas analíticas para conectores (USB-C, HDMI, conector DC cilindrico) e grelhas hexagonais/rasgadas de ventilação nas faces selecionadas.
   - **Canal de Vedação TPU (*Gasket*):** Canal perimetral na borda da base/tampa para impressão de junta flexível sob medida.
   - **Divisórias Internas:** Divisórias modulares ajustáveis no eixo X e Y.

3. **Kit Rápido de Calibração FDM (~8 min de impressão):**
   - Amostra física contendo: 1 canto de encaixe base-tampa + 1 torre com furo para inserto térmico + 1 lingueta de trava *snap-fit*.

4. **Presets:** 12 presets curados bilíngues (PT-BR e EN) com tamanhos padrão de placas (ESP32, Raspberry Pi, Arduino), caixas de ferramentas e estojos.

---

## 3. Estrutura de Arquivos do Projeto

```text
orca-box-generator/
├── pyproject.toml                     # Configuração de empacotamento e metadados do OrcaSlicer
├── README.md                          # Manual completo de uso e apresentação
├── LICENSE                            # Licença MIT
├── .gitignore                         # Exclusão de caches e temporários
├── .gitattributes                     # Normalização LF e marcação de binários
├── assets/
│   ├── icon.svg                       # Ícone vetorial da aba (64x64)
│   ├── icon.png                       # Ícone renderizado para marketplace
│   └── icon.jpg                       # Arte de apresentação do estúdio
├── docs/
│   ├── MANUAL_PT-BR.md                # Manual passo a passo em Português
│   ├── MANUAL_EN.md                   # Manual passo a passo em Inglês
│   └── COMMUNITY_LISTING.md           # Textos prontos para GitHub, Reddit e OrcaCloud
├── scripts/
│   └── build_and_install.py           # Empacotador AST PEP 723 single-file + instalador local
├── src/
│   └── box_studio/
│       ├── __init__.py                # Exportações do pacote
│       ├── schema.py                  # Dataclasses de parâmetros e normalização segura
│       ├── mesh_generator.py          # Motor geométrico NumPy 100% 2-manifold estanque
│       ├── exporters.py               # STL binário + OrcaSlicer 3MF multi-objeto com layout 2D
│       ├── presets_catalog.py         # 12 presets curados + persistência JSON do usuário
│       ├── studio_ui.py               # Interface HTML5 + WebGL2 com animação fluida + animação de tampa + editor 2D
│       ├── plugin_main.py             # Bridge nativa @orca.plugin (Pages + Script Dock + IPC WM_COPYDATA)
│       └── icon.svg                   # Cópia do ícone para auto-materialização
├── dist/
│   ├── orca_box_generator.py          # Bundle único PEP 723 com icon.svg auto-materializado
│   ├── orca_box_generator_any.py      # Bundle universal para OrcaCloud
│   └── orca_box_generator-1.0.0-py3-none-any.whl
└── tests/
    ├── test_geometry_manifold.py      # Testes de topologia estanque (Euler-Poincaré, normais)
    ├── test_exporters_and_presets.py  # Teste de 3MF, STL e todos os presets
    └── test_plugin_bundle_and_bridge.py # Testes de empacotamento, importação e bridge
```

---

## 4. Requisitos de Implementação por Módulo

### 4.1 `src/box_studio/schema.py`
- Normalização rigorosa de dimensões: `width_x >= 20.0`, `depth_y >= 20.0`, `height_z >= 10.0`.
- Paredes mínimas (`wall_thickness >= 1.2 mm`, `floor_thickness >= 1.2 mm`).
- Parâmetros da tampa: `style` (`lip_snap`, `rugged_box`, `sliding_lid`, `screw_corner`), `lid_height`, `fit_clearance` (`0.10` a `0.40 mm`), chanfros.
- Dicionário de recortes e lista de torres de fixação (`StandoffSpec`).

### 4.2 `src/box_studio/mesh_generator.py`
- Uso exclusivo de NumPy para coordenadas de vértices e índices de triângulos (`MeshData`).
- **Garantia 2-manifold:** Toda aresta deve pertencer a exatamente duas faces. Nenhuma aresta de borda (*boundary edge*) e nenhuma face degenerada.
- Fechamento de cantos por arcos suaves (seções poligonais discretizadas).
- Subtrações booleanas analíticas para recortes de portas e furos de parafusos sem depender de bibliotecas externas (construção direta das faces de túnel).
- Função `generate_fit_test_kit()` gerando o conjunto de calibração rápida.

### 4.3 `src/box_studio/studio_ui.py`
- WebGL2 puro rodando em canvas offline embutido no WebView do OrcaSlicer.
- Visualização da caixa montada ou explodida (slider de translação $Z$ da tampa ou rotação da dobradiça de `0°` a `180°`).
- Modo Raio-X translúcido para enxergar as torres internas e divisórias.
- Seletor de exportação: `Base + Tampa`, `Apenas Base`, `Apenas Tampa`, `Junta TPU`, `Kit de Calibração`.

### 4.4 `src/box_studio/plugin_main.py`
- Registrar permissão única: `orca.request_permissions(threading=True)`.
- Classe `BoxStudioPageCapability(orca.pages.PagesPluginCapabilityBase)`: Aba superior "Gerador de Caixas".
- Classe `BoxStudioDockCapability(orca.script.ScriptPluginCapabilityBase)`: Painel lateral dockable.
- Auto-materialização do `icon.svg` no diretório de armazenamento local caso o usuário instale apenas o arquivo `.py`.
- Envio direto para o Plater via `WM_COPYDATA` (Windows) e Cocoa `_dispatch_main_q` (macOS), configurando automaticamente 4 voltas de parede, 5 camadas de topo/base e preenchimento mecânico.

### 4.5 `scripts/build_and_install.py`
- Basear no script de [orca-vase-generator/scripts/build_and_install.py](../orca-vase-generator/scripts/build_and_install.py).
- Ler os arquivos em `MODULE_ORDER`, realizar strip de imports relativos, validar sintaxe AST, embutir o bloco `# /// script` PEP 723 e gerar o bundle `dist/orca_box_generator.py`.
- Instalar localmente em `%APPDATA%\OrcaSlicer\orca_plugins\orca_box_generator\`.

---

## 5. Roteiro de Verificação & Testes

Para homologar a implementação:

```powershell
# 1. Compilar o bundle e instalar localmente
& "C:\Program Files\OrcaSlicer\python\python.exe" -B orca-box-generator\scripts\build_and_install.py

# 2. Executar suíte completa de testes com parada em qualquer warning
& "C:\Program Files\OrcaSlicer\python\python.exe" -W error -m unittest discover -s orca-box-generator\tests -v
```

**Critérios de Aprovação:**
- [ ] 100% dos testes passam sem erros nem warnings (`-W error`).
- [ ] Todas as malhas geradas têm topologia estanque fechada ($V - E + F = 2(1-g)$).
- [ ] O bundle único `dist/orca_box_generator.py` carrega standalone sem `src/`.
- [ ] O OrcaSlicer abre o plugin tanto na aba superior quanto no painel lateral.
