# Studio interface template / Template da interface

## Português

O Orca Vase Studio é a referência visual escolhida para a interface 1.1 do Box. A base é o template MIT em `src/vase_studio/studio_ui.py`, revisão `a120c70d946a45136b0076a529ff806296b491c4`, do projeto de referência. As medidas, fontes, tokens claros/escuros e componentes são copiados; o conteúdo e as ferramentas correspondem a caixas e gabinetes.

O plugin mantém sua própria cópia do template, incorporada ao bundle e ao wheel. Instalar o gerador de vasos não é necessário. A prévia continua recebendo as malhas Python do Box; o template não substitui o motor geométrico por uma aproximação em JavaScript.

A aba principal usa galeria, controles de forma e editor à esquerda, prévia ao centro e recursos/impressão à direita. O rodapé de exportação permanece acessível. O painel lateral usa uma prévia compacta e as seções Forma, Recursos, Impressão e Presets.

Materiais, câmera, corte, raio-X, malha e cotas são ferramentas de inspeção. Trocar o material visual não troca o filamento no OrcaSlicer. Métricas de superfície não comprovam encaixe físico ou impressão sem suporte. O registro de verificações está em [VALIDATION.md](VALIDATION.md).

## English

Orca Vase Studio is the visual reference selected for the Box 1.1 interface. Its MIT template at `src/vase_studio/studio_ui.py`, revision `a120c70d946a45136b0076a529ff806296b491c4`, supplies the dimensions, typography, light/dark tokens and components. Content and tools describe boxes and enclosures.

This plugin embeds an independent copy in its bundle and wheel; Vase Studio is not a runtime dependency. Preview surfaces still come from the Box Python geometry engine. Visual material selection does not change the slicer's filament. Inspection metrics do not establish physical fit or support-free printing. See [VALIDATION.md](VALIDATION.md) for recorded checks.

## Reproducing browser checks / Reproduzir testes no navegador

Browser tooling is a development dependency only. With Python 3.12+, NumPy and Node.js installed:

```console
npm install --no-save --package-lock=false playwright@1.62.1
npx playwright install chromium
node scripts/check_ui_template.cjs
```

`ORCA_TEST_PYTHON` selects the Python executable; `ORCA_UI_OUTPUT` selects the evidence directory. The runner starts a private localhost backend using temporary storage, blocks native delivery and folder opening, compares the generated interface with frozen Vase measurements, and checks real Python mesh updates and 3MF exports. It writes screenshots and a JSON report outside tracked source by default. This is not a test inside OrcaSlicer.

A suíte Python continua disponível com `python -B -W error -m unittest discover -s tests -v`. No CI, os testes Python rodam nos três sistemas e o navegador isolado roda no Linux. O aplicativo final não utiliza Node.js nem Playwright.
