# Idiomas / Languages — 1.4.0

O menu do cabeçalho oferece Português, English, Español, Italiano, Français, Deutsch e 日本語 na aba principal e no painel lateral. Todos os textos e fontes de sistema são locais; o plugin não consulta serviços de tradução nem baixa fontes.

Na primeira abertura, o plugin reconhece o idioma informado pelo OrcaSlicer, incluindo variantes como `it_IT`, `es-MX` e `ja_JP`. Idiomas não suportados usam inglês. A escolha manual é gravada atomicamente em `ui_preferences.json` na pasta de dados do plugin e prevalece nas próximas aberturas e sincronizações de impressora. Uma mudança avisa a outra vista aberta. A troca não recalcula geometria, limpa o histórico nem altera valores numéricos.

O catálogo cobre os controles, ajuda, materiais, nomes dos oito modelos internos, inspeção e mensagens comuns de conclusão. Nomes de projetos e presets pessoais, nomes de impressoras, caminhos, extensões e valores numéricos permanecem como foram fornecidos. Diagnósticos técnicos vindos do gerador ou do sistema podem manter o texto original em português/inglês; mensagens desconhecidas são preservadas integralmente. Os campos numéricos mantêm o formato existente, com ponto decimal, e as unidades continuam em milímetros. As traduções editoriais ainda podem receber ajustes de falantes nativos.

A preferência de idioma é separada dos parâmetros de fabricação. O campo legado `params.lang` continua em `pt`/`en` para os nomes internos de peças e exportações; o contexto da interface e a preferência aceitam os sete idiomas. Essa separação mantém os sete arquivos fonte do banco preparado e todos os recursos geométricos aprovados inalterados, inclusive seus hashes. A interface não reescreve textos arbitrários do documento nem nomes do usuário.

## Verification

The native selector covers seven bundled locales in page and dock, light and dark themes. The isolated browser test exercises 28 combinations, persistent choice, printer synchronization, cross-view updates, unchanged numeric values and geometry request counts, personal names and actual independently reopened STL/3MF exports. Catalog tests require full coverage of the owned UI dictionary and parameter labels, equal placeholder sets and no empty translations. These checks run in CI after the isolated browser is installed.

Language switching never initiates a mesh request. The original standard geometry source fingerprint, prepared resource bytes and geometry fixtures remain unchanged. This update does not repeat physical fit tests or establish native macOS/Linux compatibility; see [validation](VALIDATION.md). Existing package/memory measurements refer to 1.3.0 and remain historical evidence, not new timing guarantees for every language or machine.

Run locally without controlling an installed slicer:

```text
python -B -W error -m unittest discover -s tests -p test_offline_languages.py -v
node scripts/check_offline_languages.cjs
python -B -W error scripts/build_and_install.py --no-install
```

The browser script requires an isolated Playwright installation via `ORCA_PLAYWRIGHT_MODULE` and optionally `ORCA_BROWSER_EXECUTABLE` and `ORCA_TEST_PYTHON`. These are developer test settings, not runtime dependencies.
