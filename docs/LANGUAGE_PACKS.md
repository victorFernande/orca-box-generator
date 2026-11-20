# Pacotes de idioma modulares / Modular language packs

Cada idioma é um arquivo JSON independente em `src/box_studio/locales/`. A lista do seletor, o nome exibido, a identificação do idioma do Orca e a direção do texto vêm desses arquivos. Não é necessário acrescentar o código do idioma a uma lista Python ou JavaScript.

## Adicionar um idioma

1. Copie `en.json` como ponto de partida ou crie um catálogo parcial.
2. Salve, por exemplo, `src/box_studio/locales/nl.json`:

```json
{
  "schema_version": 1,
  "code": "nl",
  "native_name": "Nederlands",
  "direction": "ltr",
  "order": 7,
  "translations": {
    "Model Gallery": "Modellengalerij",
    "Width X": "Breedte X",
    "Save": "Opslaan",
    "Files exported.": "Bestanden geëxporteerd."
  }
}
```

3. Gere os instaladores com `python -B -W error scripts/build_and_install.py --no-install`.
4. Distribua uma das três variantes geradas em `dist/`. Após instalar ou atualizar, reinicie o OrcaSlicer. O novo idioma já aparecerá no seletor.

O build inclui automaticamente todos os arquivos `locales/*.json` válidos no `.py`, no `_any.py` e no wheel. Os dois arquivos Python contêm os catálogos compactados e continuam independentes de arquivos auxiliares. O wheel inclui os JSONs legíveis na pasta do pacote. Não há tradutor online nem nova dependência de execução.

## Formato e compatibilidade

- `schema_version` é o inteiro `1`.
- `code` é um código textual, por exemplo `nl`, `nl-nl` ou `ar-eg`. O host `nl_NL.UTF-8` corresponde primeiro a `nl-nl`, depois a `nl`, conforme os catálogos disponíveis.
- `native_name` é o nome que aparece no seletor.
- `direction` aceita `ltr` ou `rtl`. Campos numéricos e o desenho CAD mantêm orientação própria. Um novo idioma ainda deve passar por revisão visual e editorial.
- `order` define a posição no menu; se omitido, novos catálogos vão após os idiomas com ordem explícita.
- `translations` associa frases de origem em inglês a texto simples. Um catálogo pode ser parcial: frases ausentes usam a origem em inglês. Os textos antigos PT/EN também permanecem como fallback de compatibilidade.

Marcadores como `{height}`, `{size}` e `{path}` precisam ser preservados. Não inclua HTML, JavaScript, nomes pessoais de presets nem traduza identificadores ou valores numéricos. O build rejeita dados inválidos, códigos duplicados, chaves JSON repetidas e marcadores incompatíveis. Na abertura, um catálogo opcional inválido é ignorado sem impedir o uso dos catálogos válidos e do inglês.

Quando a mesma frase precisa de traduções diferentes conforme o controle, use uma chave contextual no próprio JSON. Por exemplo, `ui:sealing::TPU gasket` e `ui:gasketOnly::TPU gasket` podem ter palavras diferentes. A interface tenta a chave contextual e depois a frase simples. Isso preserva os termos anteriores sem criar condições específicas para cada idioma no código.

Catálogos adicionais também podem ficar em `locales/` ao lado de um `.py` instalado, ou na pasta `locales/` do pacote extraído de um wheel; são lidos ao iniciar o processo. Para distribuir o idioma nas próximas instalações e atualizações, inclua o JSON no repositório e gere novamente os instaladores. As instruções acima não alteram a instalação que está aberta.

## Reutilizar nos outros Studios

Gear, Vase e Box usam o mesmo contrato JSON e cópias independentes do módulo `language_packs.py`. Os caminhos equivalentes são `src/gear_studio/locales/` e `src/vase_studio/locales/`. Um catálogo pode conter a união das frases dos três plugins: entradas que a interface não utiliza não afetam o funcionamento. Nenhum plugin importa arquivos do projeto irmão.

## Verification and future installations

Tests add only temporary JSON catalogs, rebuild the actual standalone, `_any.py` and wheel distributions, import each in a fresh process and verify discovery in page and dock. They cover exact regional preference, base-language fallback, partial translations, runtime sidecars, strict build rejection and invalid optional-file isolation. Browser checks exercise the new native selector without modifying a locale allowlist. Synthetic test languages are not shipped as production translations.

The standalone builder embeds compressed JSON data, not executable code. The source and wheel keep readable files. Standard geometry sources, prepared meshes, printing parameters and existing preference storage remain independent of the language-pack mechanism.
