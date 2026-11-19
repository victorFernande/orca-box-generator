# Orca Box Studio — apresentação para OrcaCloud

**Material da versão 1.2:** oito artes revisadas e descrição bilíngue pronta para copiar. O novo fechamento com alavancas foi verificado na página e no painel lateral do OrcaSlicer 2.5.1 no Windows, com exportação e peças visualmente carregadas na mesa. Consulte o [registro de validação](../VALIDATION.md) para o escopo dos testes e as limitações. A ficha do Box no OrcaCloud não foi criada nem editada nesta entrega.

Quatro artes em **1600 × 900**, cada uma em português e inglês, com **By @VictorFernande** no canto inferior direito. Identidade visual adaptada dos materiais Gear e Vase, preservando os avisos MIT. As peças são geradas pelo próprio Box; os modelos e fotografias das referências externas não são incluídos.

## Descrição pronta

- Campo único do catálogo: [ORCACLOUD_BILINGUAL.md](ORCACLOUD_BILINGUAL.md).
- [Português](ORCACLOUD_PT-BR.md) / [English](ORCACLOUD_EN.md).
- [Prévia com troca de idioma](PREVIEW.html).

Cole o texto bilíngue no campo de descrição do Box no OrcaCloud, confira as imagens e salve. Os oito links usam os PNGs públicos do repositório deste projeto. O material está preparado para essa edição; prepará-lo não cria nem publica uma ficha no OrcaCloud.

## Artes

| Tema | Português | English |
| --- | --- | --- |
| Caixa aberta e alças | [01-box-studio-pt-BR.png](../../assets/marketplace/01-box-studio-pt-BR.png) | [01-box-studio-en.png](../../assets/marketplace/01-box-studio-en.png) |
| Tampa removível e travas | [02-removable-lid-pt-BR.png](../../assets/marketplace/02-removable-lid-pt-BR.png) | [02-removable-lid-en.png](../../assets/marketplace/02-removable-lid-en.png) |
| Container empilhável | [03-stackable-container-pt-BR.png](../../assets/marketplace/03-stackable-container-pt-BR.png) | [03-stackable-container-en.png](../../assets/marketplace/03-stackable-container-en.png) |
| Print-in-place e interface | [04-workspace-export-pt-BR.png](../../assets/marketplace/04-workspace-export-pt-BR.png) | [04-workspace-export-en.png](../../assets/marketplace/04-workspace-export-en.png) |

Os SVGs de mesmo nome mantêm os textos editáveis. As capturas `source-workspace-en.png` e `source-workspace-pt-BR.png` usam o ambiente local de revisão, com impressora genérica e sem arquivos pessoais. As vistas das peças usam as malhas reais e profundidade WebGL2; a vista explodida separa os componentes para mostrar sua construção. Os PNGs em `assets/marketplace/sources/` são renders intermediários transparentes dessas malhas. O SVG mantém o texto editável e incorpora esses renders, sem depender de scripts para ser exibido.

## Reproduzir

Com Python 3.12+, NumPy e Playwright/Chromium de desenvolvimento:

```console
node scripts/capture_marketplace_workspace.cjs
python -B scripts/build_marketplace_artwork.py
node scripts/render_marketplace_artwork.cjs
python -B scripts/build_marketplace_preview.py
```

`ORCA_PLAYWRIGHT_MODULE` e `ORCA_CHROMIUM_PATH` permitem selecionar instalações locais das ferramentas de autoria; elas não são dependências do plugin. O renderizador verifica texto fora do canvas. Confira também o resultado visual antes de substituir as imagens públicas.
