"""Offline HTML/CSS/WebGL2 workspace. Preview displays the exported Python mesh."""

from __future__ import annotations
import json
from typing import Any

_BOX_HTML = r"""<!doctype html>
<html lang="pt" data-theme="dark">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>Orca Box Studio</title>
    <style>
      :root {
        --bg: #15171b;
        --panel: #1d2026;
        --card: #242830;
        --input: #16181d;
        --border: #313641;
        --text: #eef2f7;
        --muted: #9aa4b4;
        --accent: #00a896;
        --hover: #00bfa5;
        --warn: #ffcf77;
        --error: #ff726e;
        --soft: rgba(0, 191, 165, 0.12);
      }
      [data-theme="light"] {
        --bg: #edf1f6;
        --panel: #fff;
        --card: #f5f7fb;
        --input: #fff;
        --border: #d4dce5;
        --text: #1b222c;
        --muted: #525e6f;
        --accent: #00897b;
        --hover: #00796b;
        --soft: rgba(0, 137, 123, 0.1);
      }
      * {
        box-sizing: border-box;
      }
      html,
      body {
        height: 100%;
        margin: 0;
        overflow: hidden;
      }
      body {
        font:
          12px/1.42 "Segoe UI",
          -apple-system,
          BlinkMacSystemFont,
          Ubuntu,
          sans-serif;
        background: var(--bg);
        color: var(--text);
      }
      button,
      input,
      select,
      textarea {
        font: inherit;
        color: inherit;
      }
      button {
        cursor: pointer;
        border: 1px solid var(--border);
        border-radius: 6px;
        background: var(--card);
        padding: 7px 10px;
      }
      button:hover {
        border-color: var(--accent);
      }
      button:disabled {
        opacity: 0.45;
        cursor: wait;
      }
      button:focus-visible,
      input:focus-visible,
      select:focus-visible {
        outline: 2px solid var(--hover);
        outline-offset: 2px;
      }
      input,
      select,
      textarea {
        width: 100%;
        min-width: 0;
        background: var(--input);
        border: 1px solid var(--border);
        border-radius: 5px;
        padding: 7px;
      }
      input[type="checkbox"] {
        width: auto;
        accent-color: var(--accent);
      }
      input[type="range"] {
        padding: 0;
        accent-color: var(--accent);
      }
      input[type="number"] {
        font-family: Consolas, monospace;
      }
      h1,
      h2,
      h3,
      p {
        margin: 0;
      }
      h1 {
        font-size: 15px;
        font-weight: 650;
      }
      h2 {
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
      }
      h3 {
        font-size: 12px;
      }
      small,
      .muted {
        color: var(--muted);
      }
      .shell {
        height: 100%;
        display: flex;
        flex-direction: column;
      }
      .header {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 12px;
        border-bottom: 1px solid var(--border);
        background: var(--panel);
      }
      .brand-icon {
        width: 34px;
        height: 34px;
        color: var(--hover);
      }
      .brand {
        min-width: 170px;
      }
      .eyebrow {
        font-size: 10px;
        color: var(--accent);
        letter-spacing: 0.13em;
      }
      .design-name {
        max-width: 190px;
      }
      .actions {
        display: flex;
        gap: 5px;
        margin-left: auto;
      }
      .printer {
        border-radius: 20px;
        background: var(--soft);
        color: var(--accent);
        white-space: nowrap;
        font-size: 11px;
      }
      .workspace {
        display: grid;
        grid-template-columns: 286px minmax(300px, 1fr) 258px;
        min-height: 0;
        flex: 1;
      }
      .column {
        min-height: 0;
        overflow-y: auto;
        padding: 10px;
        background: var(--panel);
      }
      .column.left {
        border-right: 1px solid var(--border);
      }
      .column.right {
        border-left: 1px solid var(--border);
      }
      .card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 9px;
        margin-bottom: 10px;
        overflow: hidden;
      }
      .cardhead {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 11px 12px;
        border-bottom: 1px solid var(--border);
      }
      .cardbody {
        padding: 11px 12px;
        display: grid;
        gap: 10px;
      }
      .pair {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 9px;
      }
      .field {
        display: grid;
        gap: 5px;
      }
      .field span {
        font-size: 11px;
        color: var(--muted);
      }
      .check {
        display: flex;
        gap: 7px;
        align-items: center;
      }
      .primary {
        background: var(--accent);
        color: white;
        border-color: var(--accent);
        font-weight: 600;
      }
      .primary:hover {
        background: var(--hover);
      }
      .soft {
        background: var(--soft);
        color: var(--accent);
      }
      .wide {
        width: 100%;
      }
      .viewport {
        position: relative;
        min-height: 220px;
        background: radial-gradient(ellipse at 50% 25%, #29313d, #111318);
        overflow: hidden;
      }
      .viewport canvas {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        touch-action: none;
      }
      .viewport .tag {
        position: absolute;
        top: 15px;
        left: 16px;
        color: #b9c7d5;
        font:
          11px Consolas,
          monospace;
        pointer-events: none;
      }
      .viewport .status {
        position: absolute;
        bottom: 55px;
        left: 16px;
        right: 16px;
        padding: 9px 11px;
        background: rgba(20, 24, 30, 0.9);
        border: 1px solid #35414e;
        border-radius: 6px;
        color: #b9c7d5;
        pointer-events: none;
        white-space: pre-wrap;
      }
      .viewtools {
        position: absolute;
        left: 12px;
        right: 12px;
        bottom: 10px;
        display: flex;
        align-items: center;
        gap: 7px;
      }
      .viewtools button {
        background: rgba(28, 33, 41, 0.9);
        color: #e4edf6;
        border-color: #3a4654;
      }
      .viewtools input {
        flex: 1;
      }
      .viewtools label {
        color: #c3d0dc;
        font-size: 11px;
      }
      .metrics {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
      }
      .metric {
        background: var(--input);
        border: 1px solid var(--border);
        padding: 10px;
        border-radius: 6px;
      }
      .metric b {
        display: block;
        font:
          18px Consolas,
          monospace;
        margin-bottom: 3px;
      }
      .metric span {
        color: var(--muted);
        font-size: 10px;
      }
      .editor {
        width: 100%;
        height: 180px;
        border: 1px solid var(--border);
        border-radius: 6px;
        background: var(--input);
        touch-action: none;
      }
      .feature {
        padding: 8px;
        background: var(--input);
        border: 1px solid var(--border);
        border-radius: 6px;
        display: grid;
        gap: 7px;
      }
      .featuretitle {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 11px;
      }
      .featuretitle button {
        padding: 2px 7px;
        color: var(--error);
      }
      .mini {
        padding: 4px 7px;
        font-size: 11px;
      }
      .tabs {
        display: flex;
        padding: 7px 10px;
        gap: 5px;
        border-bottom: 1px solid var(--border);
        background: var(--panel);
      }
      .tab {
        flex: 1;
        font-size: 11px;
      }
      .tab.active {
        background: var(--soft);
        border-color: var(--accent);
        color: var(--accent);
      }
      .preset-list {
        max-height: 210px;
        overflow-y: auto;
        display: grid;
        gap: 5px;
      }
      .preset {
        width: 100%;
        text-align: left;
        padding: 8px;
      }
      .preset small {
        display: block;
        font-size: 10px;
      }
      .help {
        font-size: 11px;
        color: var(--muted);
        line-height: 1.6;
      }
      .error {
        color: var(--error);
      }
      .footer {
        padding: 5px 12px;
        font-size: 10px;
        color: var(--muted);
        border-top: 1px solid var(--border);
        display: flex;
        justify-content: space-between;
      }
      .badge {
        font:
          10px Consolas,
          monospace;
        color: var(--accent);
        background: var(--soft);
        padding: 2px 5px;
        border-radius: 3px;
      }
      .section-hidden {
        display: none !important;
      }
      .dock .workspace {
        display: flex;
        flex-direction: column;
      }
      .dock .viewport {
        height: 280px;
        flex: none;
        order: -1;
      }
      .dock .column {
        overflow: visible;
        border: 0 !important;
      }
      .dock .workspace {
        overflow: auto;
        display: block;
      }
      .dock .header {
        flex-wrap: wrap;
      }
      .dock .brand {
        min-width: 130px;
      }
      .dock .printer {
        display: none;
      }
      .dock .design-name {
        max-width: 140px;
      }
      .dock .right {
        padding-top: 0;
      }
      .dock .footer {
        display: none;
      }
      .dock .column.left {
        padding-bottom: 0;
      }
      ::-webkit-scrollbar {
        width: 6px;
      }
      ::-webkit-scrollbar-thumb {
        background: var(--border);
        border-radius: 9px;
      }
      @media (max-width: 1050px) {
        .workspace {
          grid-template-columns: 260px minmax(260px, 1fr) 220px;
        }
        .printer {
          display: none;
        }
      }
      @media (max-width: 760px) {
        .workspace {
          grid-template-columns: 230px minmax(200px, 1fr);
        }
        .right {
          grid-column: 1/-1;
          display: flex;
          gap: 10px;
          max-height: 220px;
        }
        .right .card {
          flex: 1;
          min-width: 190px;
        }
        .header {
          flex-wrap: wrap;
        }
        .design-name {
          max-width: 130px;
        }
      }

      .dock-views {
        display: none;
        gap: 6px;
        padding: 7px 10px;
        background: var(--panel);
        border-bottom: 1px solid var(--border);
      }
      .dock .dock-views {
        display: flex;
      }
      .dock-views button {
        flex: 1;
      }
      .dock-views button.active {
        background: var(--soft);
        border-color: var(--accent);
        color: var(--accent);
      }
      .dock .workspace {
        display: flex;
        flex-direction: column;
        overflow: hidden;
      }
      .dock .column {
        flex: 1;
        overflow-y: auto;
        min-height: 0;
      }
      .dock[data-dock-view="3d"] .column {
        display: none;
      }
      .dock[data-dock-view="3d"] .viewport {
        height: auto;
        flex: 1;
        min-height: 200px;
      }
      .dock[data-dock-view="parameters"] .viewport,
      .dock[data-dock-view="parameters"] .right {
        display: none;
      }
      .dock[data-dock-view="export"] .viewport,
      .dock[data-dock-view="export"] .left {
        display: none;
      }
      .dock:not([data-dock-view="parameters"]) .tabs {
        display: none;
      }
    </style>
  </head>
  <body>
    <div class="shell">
      <header class="header">
        <svg class="brand-icon" viewBox="0 0 40 40" fill="none">
          <path
            d="M4 14 20 6 36 14 20 22ZM4 14V29L20 37 36 29V14M20 22V37"
            stroke="currentColor"
            stroke-width="1.5"
          />
          <path d="M4 8 20 1 36 8" stroke="#ffcf77" stroke-width="1.5" />
        </svg>
        <div class="brand">
          <div class="eyebrow">PARAMETRIC ENCLOSURES</div>
          <h1>Orca Box Studio</h1>
        </div>
        <input
          class="design-name"
          id="name"
          aria-label="Design name"
          maxlength="80"
        /><button
          class="printer"
          id="sync"
          title="Sincronizar impressora / Sync printer"
        >
          ● <span id="printer">OrcaSlicer</span> ↻
        </button>
        <div class="actions">
          <button id="undo" title="Desfazer / Undo">↶</button
          ><button id="redo" title="Refazer / Redo">↷</button
          ><button id="reset" title="Restaurar / Reset">↺</button
          ><button id="lang">PT</button
          ><button id="theme" title="Tema / Theme">☾</button>
        </div>
      </header>
      <nav class="dock-views" aria-label="Dock sections">
        <button data-dock-view-button="parameters" data-i="parameters">
          Parâmetros</button
        ><button class="active" data-dock-view-button="3d">3D</button
        ><button data-dock-view-button="export" data-i="export">
          Exportar
        </button>
      </nav>
      <nav class="tabs">
        <button class="tab active" data-tab="shape" data-i="shape">Caixa</button
        ><button class="tab" data-tab="features" data-i="features">
          Acessórios</button
        ><button class="tab" data-tab="presets" data-i="presets">
          Presets
        </button>
      </nav>
      <main class="workspace">
        <aside class="column left">
          <section data-section="shape">
            <div class="card">
              <div class="cardhead">
                <h2 data-i="construction">Construção</h2>
                <span class="badge">mm</span>
              </div>
              <div class="cardbody">
                <label class="field"
                  ><span data-i="style">Estilo de caixa</span
                  ><select id="style">
                    <option value="lip_snap">Lip snap · pressão / snap</option>
                    <option value="rugged_box">
                      Rugged · dobradiça / hinged
                    </option>
                    <option value="sliding_lid">
                      Sliding · deslizante / sliding
                    </option>
                    <option value="screw_corner">
                      Screw corner · parafusos / screws
                    </option>
                  </select></label
                >
                <div class="pair">
                  <label class="field"
                    ><span data-i="width">Largura X</span
                    ><input
                      data-p="width_x"
                      type="number"
                      min="20"
                      max="350"
                      step="1" /></label
                  ><label class="field"
                    ><span data-i="depth">Profundidade Y</span
                    ><input
                      data-p="depth_y"
                      type="number"
                      min="20"
                      max="350"
                      step="1"
                  /></label>
                </div>
                <div class="pair">
                  <label class="field"
                    ><span data-i="height">Altura Z</span
                    ><input
                      data-p="height_z"
                      type="number"
                      min="10"
                      max="250"
                      step="1" /></label
                  ><label class="field"
                    ><span data-i="radius">Raio de canto</span
                    ><input
                      data-p="corner_radius"
                      type="number"
                      min=".8"
                      max="30"
                      step=".2"
                  /></label>
                </div>
                <div class="pair">
                  <label class="field"
                    ><span data-i="wall">Parede</span
                    ><input
                      data-p="wall_thickness"
                      type="number"
                      min="1.2"
                      max="12"
                      step=".2" /></label
                  ><label class="field"
                    ><span data-i="floor">Fundo</span
                    ><input
                      data-p="floor_thickness"
                      type="number"
                      min="1.2"
                      max="12"
                      step=".2"
                  /></label>
                </div>
                <div class="pair">
                  <label class="field"
                    ><span data-i="lid">Espessura tampa</span
                    ><input
                      data-p="lid_height"
                      type="number"
                      min="1.2"
                      max="12"
                      step=".2" /></label
                  ><label class="field"
                    ><span data-i="clearance">Folga por lado</span
                    ><input
                      data-p="fit_clearance"
                      type="number"
                      min=".10"
                      max=".40"
                      step=".01"
                  /></label>
                </div>
                <label class="field"
                  ><span data-i="lip">Profundidade de encaixe</span
                  ><input
                    data-p="lip_depth"
                    type="number"
                    min="3"
                    max="10"
                    step=".5" /></label
                ><label class="field rugged"
                  ><span data-i="hinge">Dobradiça</span
                  ><select id="hinge_mode">
                    <option value="pin">Pino removível / removable pin</option>
                    <option value="print_in_place">
                      Cativa · print-in-place
                    </option>
                  </select></label
                ><label class="field rugged"
                  ><span data-i="pin">Diâmetro do pino</span
                  ><input
                    data-p="hinge_pin_diameter"
                    type="number"
                    min="2"
                    max="6"
                    step=".2" /></label
                ><label class="field screw"
                  ><span data-i="screw">Parafuso de canto</span
                  ><select id="screw_size">
                    <option>M2</option>
                    <option>M2.5</option>
                    <option>M3</option>
                  </select></label
                ><label class="field"
                  ><span data-i="quality">Resolução da superfície</span
                  ><select id="quality">
                    <option value="standard">Standard</option>
                    <option value="fine">Fine</option>
                  </select></label
                >
              </div>
            </div>
            <div class="card">
              <div class="cardhead"><h2 data-i="sealing">Vedação TPU</h2></div>
              <div class="cardbody">
                <label class="check"
                  ><input type="checkbox" id="gasket_enabled" /><span
                    data-i="enableGasket"
                    >Canal perimetral e junta</span
                  ></label
                >
                <div class="pair">
                  <label class="field"
                    ><span data-i="gasketWidth">Largura do canal</span
                    ><input
                      data-p="gasket_width"
                      type="number"
                      min=".6"
                      max="2"
                      step=".1" /></label
                  ><label class="field"
                    ><span data-i="gasketDepth">Profundidade do canal</span
                    ><input
                      data-p="gasket_depth"
                      type="number"
                      min=".5"
                      max="2"
                      step=".1"
                  /></label>
                </div>
                <p class="help" data-i="gasketHelp">
                  Exporte a junta separadamente e selecione TPU no fatiador.
                  Vedação física requer teste.
                </p>
              </div>
            </div>
          </section>
          <section data-section="features" class="section-hidden">
            <div class="card">
              <div class="cardhead">
                <h2 data-i="pcb">Placa & posicionamento</h2>
                <button id="addPost" class="mini">+ PCB</button>
              </div>
              <div class="cardbody">
                <canvas
                  class="editor"
                  id="plan"
                  width="500"
                  height="330"
                  aria-label="Editor de posição de torres / Standoff placement editor"
                ></canvas>
                <p class="help" data-i="planHelp">
                  Arraste as torres no desenho. Origem no centro; X para a
                  direita, Y para trás. Cotas são editáveis abaixo.
                </p>
                <div id="posts"></div>
              </div>
            </div>
            <div class="card">
              <div class="cardhead">
                <h2 data-i="ports">Recortes de painel</h2>
                <button class="mini" id="addPort">+ USB-C</button>
              </div>
              <div class="cardbody">
                <div id="ports"></div>
                <p class="help" data-i="portHelp">
                  Recortes são atravessamentos reais. Preserve cantos, fundo e
                  encaixe. Dimensões de conectores são pontos de partida
                  editáveis.
                </p>
              </div>
            </div>
            <div class="card">
              <div class="cardhead"><h2 data-i="dividers">Divisórias</h2></div>
              <div class="cardbody">
                <label class="field"
                  ><span data-i="dividerX"
                    >Posições X, separadas por vírgula</span
                  ><input id="dividers_x" placeholder="-20, 20" /></label
                ><label class="field"
                  ><span data-i="dividerY"
                    >Posições Y, separadas por vírgula</span
                  ><input id="dividers_y" placeholder="0"
                /></label>
              </div>
            </div>
          </section>
          <section data-section="presets" class="section-hidden">
            <div class="card">
              <div class="cardhead">
                <h2 data-i="library">Biblioteca de projetos</h2>
                <span class="badge">12</span>
              </div>
              <div class="cardbody preset-list" id="presets"></div>
            </div>
            <div class="card">
              <div class="cardhead">
                <h2 data-i="mine">Meus presets</h2>
                <button class="mini" id="savePreset" data-i="save">
                  Salvar
                </button>
              </div>
              <div class="cardbody preset-list" id="userPresets"></div>
            </div>
            <p class="help" data-i="presetHelp">
              Envelopes de placas são referências. Confira o modelo e a revisão
              da sua PCB antes de perfurar ou imprimir.
            </p>
          </section>
        </aside>
        <section class="viewport">
          <canvas
            id="gl"
            aria-label="Pré-visualização 3D / 3D preview"
          ></canvas>
          <div class="tag">
            BOX / ENCLOSURE STUDIO <span id="viewLabel">ASSEMBLY</span>
          </div>
          <div class="status" id="status" role="status" aria-live="polite">
            Preparando visualização / Preparing preview…
          </div>
          <div class="viewtools">
            <button id="home" title="Enquadrar / Fit view">⌂</button
            ><button id="play" title="Animar tampa / Animate lid">▶</button
            ><label for="open" data-i="open">Abrir</label
            ><input
              id="open"
              type="range"
              min="0"
              max="100"
              value="25"
              aria-label="Abertura da tampa / Lid opening"
            /><span id="openValue" style="color: #bcc9d7; font: 11px Consolas"
              >25%</span
            >
          </div>
        </section>
        <aside class="column right">
          <div class="card">
            <div class="cardhead">
              <h2 data-i="inspection">Inspeção</h2>
              <span class="badge">LIVE MESH</span>
            </div>
            <div class="cardbody">
              <div class="metrics">
                <div class="metric">
                  <b id="volume">—</b><span data-i="volume">Volume · cm³</span>
                </div>
                <div class="metric">
                  <b id="triangles">—</b
                  ><span data-i="triangles">Triângulos</span>
                </div>
              </div>
              <label class="check"
                ><input id="xray" type="checkbox" /><span data-i="xray"
                  >Raio-X · componentes internos</span
                ></label
              ><label class="field"
                ><span data-i="cut">Corte axial de inspeção</span
                ><input id="cut" type="range" min="0" max="100" value="0"
              /></label>
              <p class="help" id="surface"></p>
              <p class="help" data-i="sameMesh">
                Visualização e exportação usam a mesma geometria Python. Curvas
                são tesselações; a atualização do modelo acontece em segundo
                plano.
              </p>
            </div>
          </div>
          <div class="card">
            <div class="cardhead"><h2 data-i="manufacture">Fabricação</h2></div>
            <div class="cardbody">
              <select
                id="target"
                aria-label="Peças para exportação / Export parts"
              >
                <option value="base_and_lid" data-i="both">Base + tampa</option>
                <option value="base_only" data-i="baseOnly">Apenas base</option>
                <option value="lid_only" data-i="lidOnly">Apenas tampa</option>
                <option value="gasket" data-i="gasketOnly">Junta TPU</option>
                <option value="fit_test_kit" data-i="kit">
                  Kit de calibração
                </option>
                <option value="full_suite" data-i="full">
                  Conjunto completo
                </option></select
              ><button class="primary wide job" id="send" data-i="send">
                Enviar para a mesa
              </button>
              <div class="pair">
                <button class="job" id="stl">STL ↓</button
                ><button class="job" id="mf">3MF ↓</button>
              </div>
              <label class="check"
                ><input id="auto_configure_slicer" type="checkbox" /><span
                  data-i="auto"
                  >Aplicar fatiamento mecânico</span
                ></label
              ><button id="folder" class="wide" data-i="folder">
                Abrir pasta de exportação
              </button>
              <p class="help" data-i="printHelp">
                Base com fundo na mesa; tampa invertida. Faça o kit de encaixe
                antes da peça final. O tempo depende da impressora e do perfil.
              </p>
              <p class="help" id="pipNote"></p>
            </div>
          </div>
        </aside>
      </main>
      <footer class="footer">
        <span>Orca Box Studio 1.0.0 · NumPy / WebGL2 · Offline</span
        ><span data-i="gesture">Arraste para orbitar · roda para zoom</span>
      </footer>
    </div>
    <script>
      const INITIAL = __BOX_CONTEXT__;
      (() => {
        "use strict";
        const $ = (id) => document.getElementById(id),
          clone = (o) => JSON.parse(JSON.stringify(o));
        let p = clone(INITIAL.params),
          lang = INITIAL.lang || p.lang || "pt",
          theme = INITIAL.theme || "dark",
          tab = "shape",
          history = [],
          future = [],
          meshes = [],
          serial = 0,
          latest = 0,
          timer = null,
          playing = false,
          angle = 25,
          drag = null;
        const texts = {
          pt: {
            shape: "Caixa",
            features: "Acessórios",
            presets: "Presets",
            construction: "Construção",
            style: "Estilo de caixa",
            width: "Largura X",
            depth: "Profundidade Y",
            height: "Altura Z",
            radius: "Raio de canto",
            wall: "Parede",
            floor: "Fundo",
            lid: "Espessura tampa",
            clearance: "Folga por lado",
            lip: "Profundidade de encaixe",
            hinge: "Dobradiça",
            pin: "Diâmetro do pino",
            screw: "Parafuso de canto",
            quality: "Resolução da superfície",
            sealing: "Vedação TPU",
            enableGasket: "Canal perimetral e junta",
            gasketWidth: "Largura do canal",
            gasketDepth: "Profundidade do canal",
            gasketHelp:
              "Exporte a junta separadamente e selecione TPU no fatiador. Vedação física requer teste.",
            pcb: "Placa & posicionamento",
            planHelp:
              "Arraste as torres. Origem no centro; X para a direita, Y para trás. Cotas editáveis abaixo.",
            ports: "Recortes de painel",
            portHelp:
              "Atravessamentos reais. Preserve cantos, fundo e encaixe. Dimensões de conectores são pontos de partida editáveis.",
            dividers: "Divisórias",
            dividerX: "Posições X, separadas por vírgula",
            dividerY: "Posições Y, separadas por vírgula",
            library: "Biblioteca de projetos",
            mine: "Meus presets",
            save: "Salvar",
            presetHelp:
              "Envelopes de placas são referências. Confira o modelo e a revisão da sua PCB.",
            open: "Abrir",
            inspection: "Inspeção",
            volume: "Volume · cm³",
            triangles: "Triângulos",
            xray: "Raio-X · componentes internos",
            cut: "Corte axial de inspeção",
            sameMesh:
              "Visualização e exportação usam a mesma geometria Python. Curvas são tesselações; atualização em segundo plano.",
            manufacture: "Fabricação",
            both: "Base + tampa",
            baseOnly: "Apenas base",
            lidOnly: "Apenas tampa",
            gasketOnly: "Junta TPU",
            kit: "Kit de calibração",
            full: "Conjunto completo",
            send: "Enviar para a mesa",
            auto: "Aplicar fatiamento mecânico",
            folder: "Abrir pasta de exportação",
            printHelp:
              "Base com fundo na mesa; tampa invertida. Imprima o kit de encaixe antes da peça final. Tempo depende da impressora e do perfil.",
            gesture: "Arraste para orbitar · roda para zoom",
            generating: "Gerando malha… você pode continuar editando.",
            ready: "Malha atualizada · pronta para inspecionar.",
            noHost:
              "Pré-visualização de interface. Abra o plugin no OrcaSlicer para gerar malhas.",
            pip: "Print-in-place: conjunto montado. Avalie pontes/suportes removíveis sob a tampa, sem preencher as folgas da dobradiça. Retire as travas para abrir.",
            delete: "Remover",
            heightPost: "Altura torre",
            outer: "Ø externo",
            hole: "Ø furo",
            holeDepth: "Prof. furo",
            insert: "Inserto",
            pilot: "Piloto",
            face: "Face",
            kind: "Tipo",
            front: "Frente",
            back: "Trás",
            left: "Esquerda",
            right: "Direita",
          },
          en: {
            shape: "Enclosure",
            features: "Features",
            presets: "Presets",
            construction: "Construction",
            style: "Enclosure style",
            width: "Width X",
            depth: "Depth Y",
            height: "Height Z",
            radius: "Corner radius",
            wall: "Wall",
            floor: "Floor",
            lid: "Lid thickness",
            clearance: "Clearance per side",
            lip: "Locating skirt depth",
            hinge: "Hinge",
            pin: "Pin diameter",
            screw: "Corner screw",
            quality: "Surface resolution",
            sealing: "TPU gasket",
            enableGasket: "Perimeter channel and gasket",
            gasketWidth: "Channel width",
            gasketDepth: "Channel depth",
            gasketHelp:
              "Export the gasket separately and select TPU in the slicer. Physical sealing requires testing.",
            pcb: "PCB & placement",
            planHelp:
              "Drag standoffs. Centered origin; X right, Y back. Exact coordinates remain editable below.",
            ports: "Panel cutouts",
            portHelp:
              "Real through-openings. Preserve corners, floor and lid interface. Connector dimensions are editable starting points.",
            dividers: "Dividers",
            dividerX: "X positions, comma separated",
            dividerY: "Y positions, comma separated",
            library: "Design library",
            mine: "My presets",
            save: "Save",
            presetHelp:
              "PCB envelopes are references. Check your actual board model and revision.",
            open: "Open",
            inspection: "Inspection",
            volume: "Volume · cm³",
            triangles: "Triangles",
            xray: "X-ray · internal components",
            cut: "Axial inspection cut",
            sameMesh:
              "Preview and export share the Python geometry. Curves are tessellated; model updates run in the background.",
            manufacture: "Manufacture",
            both: "Base + lid",
            baseOnly: "Base only",
            lidOnly: "Lid only",
            gasketOnly: "TPU gasket",
            kit: "Fit calibration kit",
            full: "Complete set",
            send: "Send to Plater",
            auto: "Apply mechanical slicing",
            folder: "Open export folder",
            printHelp:
              "Base on its floor; lid flipped onto the cap. Print the fit kit first. Print time depends on printer and profile.",
            gesture: "Drag to orbit · wheel to zoom",
            generating: "Generating mesh… you can keep editing.",
            ready: "Mesh updated · ready to inspect.",
            noHost:
              "Interface preview. Open this plugin in OrcaSlicer to generate meshes.",
            pip: "Print-in-place: assembled set. Assess bridging/removable support below the lid without filling hinge gaps. Remove clips before opening.",
            delete: "Remove",
            heightPost: "Post height",
            outer: "Outer Ø",
            hole: "Hole Ø",
            holeDepth: "Hole depth",
            insert: "Insert",
            pilot: "Pilot",
            face: "Face",
            kind: "Type",
            front: "Front",
            back: "Back",
            left: "Left",
            right: "Right",
          },
        };
        const tr = (k) => texts[lang][k] || k;
        function send(m) {
          if (window.orca && typeof window.orca.postMessage === "function") {
            window.orca.postMessage(m);
            return true;
          }
          if (window.chrome?.webview) {
            window.chrome.webview.postMessage(m);
            return true;
          }
          return false;
        }
        function status(s, error = false) {
          $("status").textContent = s;
          $("status").style.borderColor = error ? "#ff726e" : "#35414e";
          $("status").style.color = error ? "#ff9b97" : "#b9c7d5";
        }
        texts.pt.parameters = "Parâmetros";
        texts.en.parameters = "Parameters";
        texts.pt.export = "Exportar";
        texts.en.export = "Export";
        document.querySelectorAll("[data-dock-view-button]").forEach(
          (button) =>
            (button.onclick = () => {
              document.body.dataset.dockView = button.dataset.dockViewButton;
              document
                .querySelectorAll("[data-dock-view-button]")
                .forEach((other) =>
                  other.classList.toggle("active", other === button),
                );
              render();
              drawPlan();
            }),
        );
        function translate() {
          document.documentElement.lang = lang;
          document.documentElement.dataset.theme = theme;
          $("lang").textContent = lang.toUpperCase();
          $("theme").textContent = theme === "dark" ? "☾" : "☀";
          document
            .querySelectorAll("[data-i]")
            .forEach((e) => (e.textContent = tr(e.dataset.i)));
          presets();
          features();
          drawPlan();
        }
        function snapshot() {
          history.push(clone(p));
          if (history.length > 40) history.shift();
          future = [];
          buttons();
        }
        function buttons() {
          $("undo").disabled = !history.length;
          $("redo").disabled = !future.length;
        }
        function setDesign(next, remember = true) {
          if (remember) snapshot();
          p = clone(next);
          sync();
          requestPreview();
        }
        function sync() {
          for (const k of ["lid_height", "lip_depth"])
            document
              .querySelector("[data-p=" + k + "]")
              .closest("label").style.display =
              p.style === "sliding_lid" ? "none" : "grid";
          $("name").value = p.name;
          document
            .querySelectorAll("[data-p]")
            .forEach((e) => (e.value = p[e.dataset.p]));
          for (const key of ["style", "hinge_mode", "screw_size", "quality"])
            $(key).value = p[key];
          for (const key of ["gasket_enabled", "auto_configure_slicer"])
            $(key).checked = p[key];
          $("dividers_x").value = p.dividers_x.join(", ");
          $("dividers_y").value = p.dividers_y.join(", ");
          $("target").value = p.export_target;
          document
            .querySelectorAll(".rugged")
            .forEach(
              (e) =>
                (e.style.display = p.style === "rugged_box" ? "grid" : "none"),
            );
          document
            .querySelectorAll(".screw")
            .forEach(
              (e) =>
                (e.style.display =
                  p.style === "screw_corner" ? "grid" : "none"),
            );
          $("pipNote").textContent =
            p.style === "rugged_box" && p.hinge_mode === "print_in_place"
              ? tr("pip")
              : "";
          features();
          drawPlan();
          buttons();
          render();
        }
        function requestPreview() {
          clearTimeout(timer);
          const request_id = ++serial;
          latest = request_id;
          timer = setTimeout(() => {
            status(tr("generating"));
            p.lang = lang;
            p.theme = theme;
            if (!send({ type: "preview", params: p, request_id }))
              status(tr("noHost"));
          }, 350);
        }
        function change(key, value) {
          snapshot();
          p[key] = value;
          sync();
          requestPreview();
        }
        document
          .querySelectorAll("[data-p]")
          .forEach((e) =>
            e.addEventListener("change", () =>
              change(e.dataset.p, Number(e.value)),
            ),
          );
        for (const key of ["style", "hinge_mode", "screw_size", "quality"])
          $(key).onchange = () => change(key, $(key).value);
        for (const key of ["gasket_enabled", "auto_configure_slicer"])
          $(key).onchange = () => change(key, $(key).checked);
        for (const key of ["dividers_x", "dividers_y"])
          $(key).onchange = () =>
            change(
              key,
              $(key)
                .value.split(",")
                .map((s) => s.trim())
                .filter(Boolean)
                .map(Number)
                .filter(Number.isFinite),
            );
        $("name").onchange = () => change("name", $("name").value);
        $("target").onchange = () => change("export_target", $("target").value);
        $("undo").onclick = () => {
          if (!history.length) return;
          future.push(clone(p));
          p = history.pop();
          sync();
          requestPreview();
        };
        $("redo").onclick = () => {
          if (!future.length) return;
          history.push(clone(p));
          p = future.pop();
          sync();
          requestPreview();
        };
        $("reset").onclick = () => setDesign(INITIAL.params);
        $("lang").onclick = () => {
          lang = lang === "pt" ? "en" : "pt";
          translate();
          sync();
        };
        $("theme").onclick = () => {
          theme = theme === "dark" ? "light" : "dark";
          translate();
        };
        $("sync").onclick = () => send({ type: "sync_printer" });
        $("folder").onclick = () => send({ type: "open_exports_folder" });
        document.addEventListener("keydown", (e) => {
          if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
            e.preventDefault();
            (e.shiftKey ? $("redo") : $("undo")).click();
          }
        });
        document.querySelectorAll("[data-tab]").forEach(
          (b) =>
            (b.onclick = () => {
              tab = b.dataset.tab;
              document
                .querySelectorAll("[data-tab]")
                .forEach((x) => x.classList.toggle("active", x === b));
              document
                .querySelectorAll("[data-section]")
                .forEach((x) =>
                  x.classList.toggle(
                    "section-hidden",
                    x.dataset.section !== tab,
                  ),
                );
              drawPlan();
            }),
        );
        function presets() {
          const list = $("presets");
          list.replaceChildren();
          (INITIAL.presets || []).forEach((s) => {
            const b = document.createElement("button");
            b.className = "preset";
            b.textContent = lang === "pt" ? s.name_pt : s.name_en;
            const small = document.createElement("small");
            small.textContent = `${s.params.width_x} × ${s.params.depth_y} × ${s.params.height_z} mm · ${s.params.style}`;
            b.append(small);
            b.onclick = () => setDesign(s.params);
            list.append(b);
          });
          const user = $("userPresets");
          user.replaceChildren();
          (INITIAL.user_presets || []).forEach((s) => {
            const row = document.createElement("div");
            row.className = "pair";
            const b = document.createElement("button");
            b.textContent = s.name;
            b.onclick = () => setDesign(s.params);
            const del = document.createElement("button");
            del.textContent = "×";
            del.title = tr("delete");
            del.onclick = () =>
              send({ type: "delete_preset", preset_id: s.id });
            row.append(b, del);
            user.append(row);
          });
        }
        $("savePreset").onclick = () =>
          send({ type: "save_preset", params: p, name: p.name });
        function fieldInput(label, value, onchange, step = ".1") {
          const lab = document.createElement("label");
          lab.className = "field";
          const span = document.createElement("span");
          span.textContent = label;
          const inp = document.createElement("input");
          inp.type = "number";
          inp.step = step;
          inp.value = value;
          inp.onchange = () => onchange(Number(inp.value));
          lab.append(span, inp);
          return lab;
        }
        function selectInput(label, value, values, onchange) {
          const lab = document.createElement("label");
          lab.className = "field";
          const span = document.createElement("span");
          span.textContent = label;
          const sel = document.createElement("select");
          values.forEach(([v, text]) => {
            const opt = document.createElement("option");
            opt.value = v;
            opt.textContent = text;
            sel.append(opt);
          });
          sel.value = value;
          sel.onchange = () => onchange(sel.value);
          lab.append(span, sel);
          return lab;
        }
        function featureChange(list, index, key, value) {
          snapshot();
          p[list][index][key] = value;
          drawPlan();
          requestPreview();
        }
        function features() {
          const posts = $("posts");
          posts.replaceChildren();
          p.standoffs.forEach((s, i) => {
            const card = document.createElement("div");
            card.className = "feature";
            const head = document.createElement("div");
            head.className = "featuretitle";
            head.textContent = `PCB ${i + 1}`;
            const del = document.createElement("button");
            del.textContent = "×";
            del.onclick = () => {
              snapshot();
              p.standoffs.splice(i, 1);
              sync();
              requestPreview();
            };
            head.append(del);
            card.append(head);
            const pairs = [
              ["X", "x", "Y", "y"],
              [tr("heightPost"), "height", tr("outer"), "outer_diameter"],
              [tr("hole"), "hole_diameter", tr("holeDepth"), "hole_depth"],
            ];
            pairs.forEach(([a, ka, b, kb]) => {
              const row = document.createElement("div");
              row.className = "pair";
              row.append(
                fieldInput(a, s[ka], (v) =>
                  featureChange("standoffs", i, ka, v),
                ),
                fieldInput(b, s[kb], (v) =>
                  featureChange("standoffs", i, kb, v),
                ),
              );
              card.append(row);
            });
            const row = document.createElement("div");
            row.className = "pair";
            row.append(
              selectInput(
                tr("insert"),
                s.insert,
                [
                  ["M2", "M2"],
                  ["M2.5", "M2.5"],
                  ["M3", "M3"],
                ],
                (v) => {
                  featureChange("standoffs", i, "insert", v);
                },
              ),
              selectInput(
                "Modo / Mode",
                s.mode,
                [
                  ["insert", tr("insert")],
                  ["pilot", tr("pilot")],
                ],
                (v) => {
                  featureChange("standoffs", i, "mode", v);
                  p.standoffs[i].hole_diameter =
                    v === "pilot"
                      ? { M2: 1.6, "M2.5": 2.1, M3: 2.5 }[s.insert] || 2.5
                      : { M2: 3.2, "M2.5": 3.8, M3: 4.2 }[s.insert] || 4.2;
                  features();
                },
              ),
            );
            card.append(row);
            posts.append(card);
          });
          const ports = $("ports");
          ports.replaceChildren();
          p.cutouts.forEach((s, i) => {
            const card = document.createElement("div");
            card.className = "feature";
            const head = document.createElement("div");
            head.className = "featuretitle";
            head.textContent = `${tr("ports")} ${i + 1}`;
            const del = document.createElement("button");
            del.textContent = "×";
            del.onclick = () => {
              snapshot();
              p.cutouts.splice(i, 1);
              sync();
              requestPreview();
            };
            head.append(del);
            card.append(head);
            const row = document.createElement("div");
            row.className = "pair";
            row.append(
              selectInput(
                tr("face"),
                s.face,
                ["front", "back", "left", "right"].map((x) => [x, tr(x)]),
                (v) => featureChange("cutouts", i, "face", v),
              ),
              selectInput(
                tr("kind"),
                s.kind,
                [
                  ["usb_c", "USB-C"],
                  ["hdmi", "HDMI"],
                  ["dc", "DC Ø8"],
                  ["slot", "Slot"],
                  ["hex", "Hex"],
                ],
                (v) => {
                  snapshot();
                  const spec = {
                    usb_c: [10, 4, "rounded"],
                    hdmi: [16, 7, "rounded"],
                    dc: [8, 8, "circle"],
                    slot: [20, 3, "rounded"],
                    hex: [6, 6, "hex"],
                  }[v];
                  Object.assign(s, {
                    kind: v,
                    width: spec[0],
                    height: spec[1],
                    shape: spec[2],
                  });
                  features();
                  requestPreview();
                },
              ),
            );
            card.append(row);
            for (const pair of [
              [
                ["U", "u"],
                ["Z", "z"],
              ],
              [
                [tr("width"), "width"],
                [tr("height"), "height"],
              ],
            ]) {
              const r = document.createElement("div");
              r.className = "pair";
              pair.forEach(([label, key]) =>
                r.append(
                  fieldInput(label, s[key], (v) =>
                    featureChange("cutouts", i, key, v),
                  ),
                ),
              );
              card.append(r);
            }
            ports.append(card);
          });
        }
        $("addPost").onclick = () => {
          snapshot();
          p.standoffs.push({
            x: 0,
            y: 0,
            height: 8,
            outer_diameter: 7,
            hole_diameter: 4.2,
            hole_depth: 5,
            insert: "M3",
            mode: "insert",
          });
          sync();
          requestPreview();
        };
        $("addPort").onclick = () => {
          snapshot();
          p.cutouts.push({
            face: "front",
            kind: "usb_c",
            shape: "rounded",
            u: 0,
            z: Math.max(8, p.height_z / 2),
            width: 10,
            height: 4,
          });
          sync();
          requestPreview();
        };
        function drawPlan() {
          const canvas = $("plan"),
            c = canvas.getContext("2d"),
            w = canvas.width,
            h = canvas.height;
          c.clearRect(0, 0, w, h);
          const s = Math.min((w - 45) / p.width_x, (h - 45) / p.depth_y);
          const cx = w / 2,
            cy = h / 2;
          c.strokeStyle = theme === "dark" ? "#627282" : "#9baaba";
          c.lineWidth = 2;
          c.strokeRect(
            cx - (p.width_x * s) / 2,
            cy - (p.depth_y * s) / 2,
            p.width_x * s,
            p.depth_y * s,
          );
          c.strokeStyle = "#36444f";
          c.lineWidth = 1;
          c.beginPath();
          c.moveTo(10, cy);
          c.lineTo(w - 10, cy);
          c.moveTo(cx, 10);
          c.lineTo(cx, h - 10);
          c.stroke();
          c.fillStyle = "#8b9aa8";
          c.font = "13px Consolas";
          c.fillText("X →", w - 50, cy - 5);
          c.fillText("Y ↑", cx + 6, 18);
          p.dividers_x.forEach((x) => {
            c.strokeStyle = "#00a896";
            c.beginPath();
            c.moveTo(cx + x * s, cy - (p.depth_y * s) / 2);
            c.lineTo(cx + x * s, cy + (p.depth_y * s) / 2);
            c.stroke();
          });
          p.dividers_y.forEach((y) => {
            c.beginPath();
            c.moveTo(cx - (p.width_x * s) / 2, cy - y * s);
            c.lineTo(cx + (p.width_x * s) / 2, cy - y * s);
            c.stroke();
          });
          p.standoffs.forEach((q, i) => {
            c.fillStyle = "#00a896";
            c.beginPath();
            c.arc(
              cx + q.x * s,
              cy - q.y * s,
              (q.outer_diameter * s) / 2,
              0,
              Math.PI * 2,
            );
            c.fill();
            c.fillStyle = theme === "dark" ? "#16181d" : "#fff";
            c.beginPath();
            c.arc(
              cx + q.x * s,
              cy - q.y * s,
              (q.hole_diameter * s) / 2,
              0,
              Math.PI * 2,
            );
            c.fill();
            c.fillStyle = "#ffcf77";
            c.fillText(String(i + 1), cx + q.x * s + 8, cy - q.y * s - 8);
          });
        }
        $("plan").onpointerdown = (e) => {
          const r = $("plan").getBoundingClientRect(),
            x = ((e.clientX - r.left) * 500) / r.width,
            y = ((e.clientY - r.top) * 330) / r.height,
            s = Math.min(455 / p.width_x, 285 / p.depth_y);
          const i = p.standoffs.findIndex(
            (q) =>
              Math.hypot(x - (250 + q.x * s), y - (165 - q.y * s)) <
              Math.max(12, (q.outer_diameter * s) / 2),
          );
          if (i >= 0) {
            snapshot();
            drag = i;
            $("plan").setPointerCapture(e.pointerId);
          }
        };
        $("plan").onpointermove = (e) => {
          if (drag === null) return;
          const r = $("plan").getBoundingClientRect(),
            s = Math.min(455 / p.width_x, 285 / p.depth_y);
          p.standoffs[drag].x =
            Math.round(
              ((((e.clientX - r.left) * 500) / r.width - 250) / s) * 10,
            ) / 10;
          p.standoffs[drag].y =
            Math.round(
              ((165 - ((e.clientY - r.top) * 330) / r.height) / s) * 10,
            ) / 10;
          drawPlan();
        };
        $("plan").onpointerup = () => {
          if (drag !== null) {
            drag = null;
            features();
            requestPreview();
          }
        };
        function busy(on) {
          document.querySelectorAll(".job").forEach((b) => (b.disabled = on));
        }
        function manufacture(type, format) {
          p.export_target = $("target").value;
          p.lang = lang;
          busy(true);
          status(tr("generating"));
          if (
            !send({ type, format, params: p, export_target: p.export_target })
          ) {
            busy(false);
            status(tr("noHost"));
          }
        }
        $("send").onclick = () => manufacture("send_to_plater", "3mf");
        $("stl").onclick = () => manufacture("export_file", "stl");
        $("mf").onclick = () => manufacture("export_file", "3mf");
        function receive(raw) {
          let m = raw?.data ?? raw;
          try {
            if (typeof m === "string") m = JSON.parse(m);
          } catch (_) {
            return;
          }
          if (!m || typeof m !== "object") return;
          if (m.type === "design_changed") {
            p = clone(m.params);
            sync();
            requestPreview();
            return;
          }
          if (m.type === "init_state") {
            if (m.host) {
              INITIAL.host = m.host;
              $("printer").textContent =
                `${m.host.printer_name} · ${m.host.nozzle_mm}mm`;
            }
            if (m.user_presets) {
              INITIAL.user_presets = m.user_presets;
              presets();
            }
            return;
          }
          if (m.type === "presets_result") {
            INITIAL.user_presets = m.user_presets;
            presets();
            return;
          }
          if (m.type === "preview_result") {
            if (m.request_id && m.request_id !== latest) return;
            if (!m.ok) {
              status(m.message, true);
              return;
            }
            p = clone(m.params);
            INITIAL.hinge = m.hinge;
            loadMeshes(m.meshes);
            $("volume").textContent = m.volume_cm3.toFixed(1);
            $("triangles").textContent =
              (
                m.meshes.reduce((s, x) => s + x.triangle_count, 0) / 1000
              ).toFixed(0) + "k";
            const err = Math.max(...m.meshes.map((x) => x.interface_error_mm));
            $("surface").textContent =
              (lang === "pt"
                ? "Alvo de erro nas interfaces curvas ≤ "
                : "Curved interface chord-error target ≤ ") +
              err.toFixed(3) +
              " mm";
            status(tr("ready"));
            sync();
            return;
          }
          if (m.type === "action_result") {
            busy(false);
            status(m.message || String(m.ok), !m.ok);
          }
        }
        window.addEventListener("message", receive);
        if (window.chrome?.webview)
          window.chrome.webview.addEventListener("message", receive);
        if (window.orca?.onMessage) window.orca.onMessage(receive);
        window.receiveBoxMessage = receive;
        // WebGL2: arrays are the exact mesh arrays supplied by the Python exporter.
        let gl = $("gl").getContext("webgl2", { antialias: true, alpha: true }),
          program = null,
          yaw = -0.75,
          pitch = 0.68,
          zoom = 1,
          orbit = null;
        function shader(type, source) {
          const s = gl.createShader(type);
          gl.shaderSource(s, source);
          gl.compileShader(s);
          if (!gl.getShaderParameter(s, gl.COMPILE_STATUS))
            throw Error(gl.getShaderInfoLog(s));
          return s;
        }
        function initializeGL() {
          if (!gl) {
            status(
              "WebGL2 indisponível / unavailable. Export remains available.",
              true,
            );
            return;
          }
          program = gl.createProgram();
          gl.attachShader(
            program,
            shader(
              gl.VERTEX_SHADER,
              `#version 300 es\nprecision highp float;in vec3 position;in vec3 normal;uniform mat4 vp;uniform mat4 model;out vec3 n;out vec3 world;void main(){vec4 w=model*vec4(position,1.0);world=w.xyz;n=mat3(model)*normal;gl_Position=vp*w;}`.replaceAll(
                "\\n",
                "\n",
              ),
            ),
          );
          gl.attachShader(
            program,
            shader(
              gl.FRAGMENT_SHADER,
              `#version 300 es\nprecision highp float;in vec3 n;in vec3 world;uniform vec4 color;uniform float cut;out vec4 outColor;void main(){if(world.x>cut)discard;vec3 N=normalize(n);if(!gl_FrontFacing)N=-N;float diffuse=.35+.65*max(0.0,dot(N,normalize(vec3(-.4,-.7,1.0))));outColor=vec4(color.rgb*diffuse,color.a);}`.replaceAll(
                "\\n",
                "\n",
              ),
            ),
          );
          gl.linkProgram(program);
          if (!gl.getProgramParameter(program, gl.LINK_STATUS))
            throw Error(gl.getProgramInfoLog(program));
          gl.enable(gl.DEPTH_TEST);
          gl.enable(gl.BLEND);
          gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
        }
        function decode(s, ctor) {
          const b = atob(s),
            a = new Uint8Array(b.length);
          for (let i = 0; i < b.length; i++) a[i] = b.charCodeAt(i);
          return new ctor(a.buffer);
        }
        function loadMeshes(items) {
          if (!gl) return;
          meshes.forEach((m) => {
            gl.deleteBuffer(m.pb);
            gl.deleteBuffer(m.nb);
            gl.deleteBuffer(m.ib);
            gl.deleteVertexArray(m.vao);
          });
          meshes = items.map((item) => {
            const pos = decode(item.vertices, Float32Array),
              tri = decode(item.triangles, Uint32Array),
              norm = new Float32Array(pos.length);
            for (let i = 0; i < tri.length; i += 3) {
              let a = tri[i] * 3,
                b = tri[i + 1] * 3,
                c = tri[i + 2] * 3;
              const ux = pos[b] - pos[a],
                uy = pos[b + 1] - pos[a + 1],
                uz = pos[b + 2] - pos[a + 2],
                vx = pos[c] - pos[a],
                vy = pos[c + 1] - pos[a + 1],
                vz = pos[c + 2] - pos[a + 2];
              const nx = uy * vz - uz * vy,
                ny = uz * vx - ux * vz,
                nz = ux * vy - uy * vx;
              for (const j of [a, b, c]) {
                norm[j] += nx;
                norm[j + 1] += ny;
                norm[j + 2] += nz;
              }
            }
            for (let i = 0; i < norm.length; i += 3) {
              const l = Math.hypot(norm[i], norm[i + 1], norm[i + 2]) || 1;
              norm[i] /= l;
              norm[i + 1] /= l;
              norm[i + 2] /= l;
            }
            const vao = gl.createVertexArray();
            gl.bindVertexArray(vao);
            const pb = gl.createBuffer();
            gl.bindBuffer(gl.ARRAY_BUFFER, pb);
            gl.bufferData(gl.ARRAY_BUFFER, pos, gl.STATIC_DRAW);
            const loc = gl.getAttribLocation(program, "position");
            gl.enableVertexAttribArray(loc);
            gl.vertexAttribPointer(loc, 3, gl.FLOAT, false, 0, 0);
            const nb = gl.createBuffer();
            gl.bindBuffer(gl.ARRAY_BUFFER, nb);
            gl.bufferData(gl.ARRAY_BUFFER, norm, gl.STATIC_DRAW);
            const nl = gl.getAttribLocation(program, "normal");
            gl.enableVertexAttribArray(nl);
            gl.vertexAttribPointer(nl, 3, gl.FLOAT, false, 0, 0);
            const ib = gl.createBuffer();
            gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ib);
            gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, tri, gl.STATIC_DRAW);
            return { ...item, vao, pb, nb, ib, count: tri.length };
          });
          render();
        }
        const I = () =>
          new Float32Array([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]);
        function mult(a, b) {
          const c = new Float32Array(16);
          for (let col = 0; col < 4; col++)
            for (let row = 0; row < 4; row++)
              for (let k = 0; k < 4; k++)
                c[col * 4 + row] += a[k * 4 + row] * b[col * 4 + k];
          return c;
        }
        function translateM(x, y, z) {
          const m = I();
          m[12] = x;
          m[13] = y;
          m[14] = z;
          return m;
        }
        function rotateX(a) {
          const m = I();
          m[5] = Math.cos(a);
          m[6] = Math.sin(a);
          m[9] = -Math.sin(a);
          m[10] = Math.cos(a);
          return m;
        }
        function normalize(v) {
          const l = Math.hypot(...v) || 1;
          return v.map((x) => x / l);
        }
        function cross(a, b) {
          return [
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0],
          ];
        }
        function dot(a, b) {
          return a.reduce((s, x, i) => s + x * b[i], 0);
        }
        function camera(aspect) {
          const size =
              (Math.max(p.width_x, p.depth_y, p.height_z) * 1.8) /
              (zoom * Math.max(0.1, Math.min(1, aspect))),
            target = [0, 0, p.height_z * 0.52],
            eye = [
              size * Math.cos(yaw) * Math.cos(pitch),
              size * Math.sin(yaw) * Math.cos(pitch),
              target[2] + size * Math.sin(pitch),
            ],
            z = normalize(eye.map((x, i) => x - target[i])),
            x = normalize(cross([0, 0, 1], z)),
            y = cross(z, x),
            v = new Float32Array([
              x[0],
              y[0],
              z[0],
              0,
              x[1],
              y[1],
              z[1],
              0,
              x[2],
              y[2],
              z[2],
              0,
              -dot(x, eye),
              -dot(y, eye),
              -dot(z, eye),
              1,
            ]),
            f = 1 / Math.tan(Math.PI / 7),
            near = 0.1,
            far = 5000,
            pr = new Float32Array([
              f / aspect,
              0,
              0,
              0,
              0,
              f,
              0,
              0,
              0,
              0,
              (far + near) / (near - far),
              -1,
              0,
              0,
              (2 * far * near) / (near - far),
              0,
            ]);
          return mult(pr, v);
        }
        function render() {
          if (!gl || !program) return;
          const cv = $("gl"),
            r = cv.getBoundingClientRect(),
            dpr = Math.min(devicePixelRatio || 1, 1.7);
          cv.width = Math.max(1, Math.round(r.width * dpr));
          cv.height = Math.max(1, Math.round(r.height * dpr));
          gl.viewport(0, 0, cv.width, cv.height);
          gl.depthMask(true);
          gl.clearColor(0, 0, 0, 0);
          gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
          gl.depthMask(!$("xray").checked);
          gl.useProgram(program);
          gl.uniformMatrix4fv(
            gl.getUniformLocation(program, "vp"),
            false,
            camera(cv.width / cv.height),
          );
          gl.uniform1f(
            gl.getUniformLocation(program, "cut"),
            $("cut").value === "0"
              ? 10000
              : p.width_x / 2 - (p.width_x * Number($("cut").value)) / 100,
          );
          for (const m of meshes) {
            let model = I();
            const opening = Number($("open").value) / 100;
            if (m.part === "lid") {
              if (p.style === "rugged_box") {
                const hinge = INITIAL.hinge || {
                  y: p.depth_y / 2 + 5,
                  z: p.height_z - 4,
                };
                model = mult(
                  translateM(0, hinge.y, hinge.z),
                  mult(
                    rotateX(-opening * Math.PI),
                    translateM(0, -hinge.y, -hinge.z),
                  ),
                );
              } else if (p.style === "sliding_lid")
                model = translateM(0, -opening * (p.depth_y + 10), 0);
              else model = translateM(0, 0, opening * 50);
            }
            if (m.part.startsWith("clip"))
              model = translateM(0, -opening * 15, 0);
            const color =
              m.part === "lid"
                ? [1, 0.74, 0.34]
                : m.part === "gasket"
                  ? [0.7, 0.62, 1]
                  : m.part === "pin"
                    ? [0.35, 0.63, 1]
                    : m.part.startsWith("clip")
                      ? [0.65, 0.78, 0.86]
                      : [0, 0.72, 0.61];
            gl.uniform4fv(gl.getUniformLocation(program, "color"), [
              ...color,
              $("xray").checked ? 0.42 : 1,
            ]);
            gl.uniformMatrix4fv(
              gl.getUniformLocation(program, "model"),
              false,
              model,
            );
            gl.bindVertexArray(m.vao);
            gl.drawElements(gl.TRIANGLES, m.count, gl.UNSIGNED_INT, 0);
          }
        }
        $("gl").onpointerdown = (e) => {
          orbit = [e.clientX, e.clientY];
          $("gl").setPointerCapture(e.pointerId);
        };
        $("gl").onpointermove = (e) => {
          if (!orbit) return;
          yaw -= (e.clientX - orbit[0]) * 0.008;
          pitch = Math.max(
            0.08,
            Math.min(1.5, pitch + (e.clientY - orbit[1]) * 0.008),
          );
          orbit = [e.clientX, e.clientY];
          render();
        };
        $("gl").onpointerup = () => (orbit = null);
        $("gl").onwheel = (e) => {
          e.preventDefault();
          zoom = Math.max(
            0.35,
            Math.min(4, zoom * Math.exp(-e.deltaY * 0.001)),
          );
          render();
        };
        $("home").onclick = () => {
          zoom = 1;
          yaw = -0.75;
          pitch = 0.68;
          render();
        };
        $("open").oninput = () => {
          $("openValue").textContent = $("open").value + "%";
          render();
        };
        $("xray").onchange = render;
        $("cut").oninput = render;
        $("play").onclick = () => {
          playing = !playing;
          $("play").textContent = playing ? "Ⅱ" : "▶";
          if (playing) requestAnimationFrame(tick);
        };
        function tick(t) {
          if (!playing) return;
          $("open").value = 50 - 50 * Math.cos(t * 0.0007);
          $("openValue").textContent = Math.round($("open").value) + "%";
          render();
          requestAnimationFrame(tick);
        }
        window.addEventListener("resize", render);
        document.addEventListener("visibilitychange", () => {
          if (document.hidden) {
            playing = false;
            $("play").textContent = "▶";
          }
        });
        if (INITIAL.mode === "dock") {
          document.body.classList.add("dock");
          document.body.dataset.dockView = "3d";
        }
        try {
          initializeGL();
        } catch (e) {
          status(String(e), true);
        }
        translate();
        sync();
        if (INITIAL.host)
          $("printer").textContent =
            `${INITIAL.host.printer_name} · ${INITIAL.host.nozzle_mm}mm`;
        if (INITIAL.meshes) loadMeshes(INITIAL.meshes);
        else requestPreview();
      })();
    </script>
  </body>
</html>
"""


def get_studio_html(
    mode: str = "page", initial_context: dict[str, Any] | None = None
) -> str:
    from .schema import normalize_params
    from .presets_catalog import BUILTIN_PRESETS

    ctx = dict(initial_context or {})
    ctx.setdefault("params", normalize_params())
    ctx.setdefault("presets", BUILTIN_PRESETS)
    ctx["mode"] = mode
    payload = (
        json.dumps(ctx, ensure_ascii=False, separators=(",", ":"))
        .replace("</", "<\\/")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
    return _BOX_HTML.replace("__BOX_CONTEXT__", payload)
