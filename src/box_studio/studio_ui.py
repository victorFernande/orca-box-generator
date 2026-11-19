"""Canonical offline Orca Studio interface; MIT reference styling and real Python meshes."""

from __future__ import annotations
import copy
import json
from typing import Any
from .schema import normalize_params
from .presets_catalog import BUILTIN_PRESETS

_BOX_HTML = r"""<!doctype html>
<html lang="__INITIAL_LANG__" data-theme="__INITIAL_THEME__">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Orca Box Studio</title>
    <style>
:root,
[data-theme="dark"] {
  --bg-app: #16181c;
  --bg-panel: #1e2026;
  --bg-card: #252830;
  --bg-card-hover: #2c303a;
  --bg-input: #17191e;
  --bg-viewport-top: #232730;
  --bg-viewport-bot: #121418;
  --bg-hud: rgba(24, 27, 33, 0.86);
  --border-subtle: #313640;
  --border-strong: #414856;
  --text-main: #eef2f6;
  --text-muted: #9aa3b2;
  --text-dim: #6e7787;
  --orca-accent: #00a896;
  --orca-accent-hover: #00bfa5;
  --orca-accent-soft: rgba(0, 191, 165, 0.15);
  --orca-accent-border: rgba(0, 191, 165, 0.48);
  --status-ok: #00c853;
  --status-warn: #ffb300;
  --status-crit: #ff5252;
  --shadow-soft: 0 8px 24px rgba(0, 0, 0, 0.35);
  --radius-sm: 6px;
  --radius-md: 9px;
  --radius-lg: 12px;
  --font-sans: var(--orca-font, "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, Ubuntu, sans-serif);
  --font-mono: "Cascadia Code", Consolas, "SFMono-Regular", monospace;
}

[data-theme="light"] {
  --bg-app: #eef2f6;
  --bg-panel: #ffffff;
  --bg-card: #f5f7fa;
  --bg-card-hover: #eaeff5;
  --bg-input: #ffffff;
  --bg-viewport-top: #dde4ec;
  --bg-viewport-bot: #c7d1dc;
  --bg-hud: rgba(255, 255, 255, 0.90);
  --border-subtle: #d5dce4;
  --border-strong: #b8c3cf;
  --text-main: #1c222b;
  --text-muted: #556070;
  --text-dim: #7b8696;
  --orca-accent: #00897b;
  --orca-accent-hover: #00796b;
  --orca-accent-soft: rgba(0, 137, 123, 0.12);
  --orca-accent-border: rgba(0, 137, 123, 0.45);
  --status-ok: #1b9e4b;
  --status-warn: #d98200;
  --status-crit: #d93025;
  --shadow-soft: 0 8px 24px rgba(15, 25, 40, 0.10);
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body {
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: var(--bg-app);
  color: var(--text-main);
  font-family: var(--font-sans);
  font-size: 12.5px;
  line-height: 1.4;
  user-select: none;
  -webkit-font-smoothing: antialiased;
}

::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: var(--border-strong);
  border-radius: 99px;
}
::-webkit-scrollbar-thumb:hover {
  background: var(--orca-accent);
}

button, input, select {
  font-family: inherit;
  font-size: inherit;
  color: inherit;
}

.studio-shell {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
}

/* Header Bar */
.studio-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 7px 12px;
  background: var(--bg-panel);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
  z-index: 20;
}

.brand-group {
  display: flex;
  align-items: center;
  gap: 9px;
  min-width: 0;
  flex: 1 1 auto;
}

.brand-logo {
  width: 26px;
  height: 26px;
  border-radius: 7px;
  background: linear-gradient(135deg, #00bfa5 0%, #00796b 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 191, 165, 0.30);
}

.brand-titles {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.brand-name-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.brand-title {
  font-weight: 700;
  font-size: 13.5px;
  letter-spacing: 0.2px;
  white-space: nowrap;
}

.design-name-input {
  background: var(--bg-input);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 3px 8px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-main);
  width: 165px;
  transition: border-color 0.15s;
}
.design-name-input:focus {
  outline: none;
  border-color: var(--orca-accent);
}

.printer-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 11px;
  border-radius: 99px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  color: var(--text-muted);
  font-size: 11px;
  white-space: nowrap;
  max-width: min(560px, 56vw);
  min-width: 0;
  flex: 0 1 auto;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s, color 0.15s;
}
.printer-pill:hover {
  border-color: var(--orca-accent-border);
  background: var(--bg-card-hover);
  color: var(--text-main);
}
.printer-pill:active {
  transform: translateY(1px);
}

.printer-pill-text {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  min-width: 0;
  overflow: hidden;
}

.printer-pill-name {
  min-width: 0;
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 600;
  color: var(--text-main);
}

.printer-pill-specs {
  flex-shrink: 0;
  white-space: nowrap;
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 10.6px;
}

.printer-pill-sync {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11.5px;
  line-height: 1;
  color: var(--orca-accent-hover);
  margin-left: 1px;
  transition: transform 0.38s ease;
}
[data-theme="light"] .printer-pill-sync {
  color: var(--orca-accent);
}
.printer-pill.syncing .printer-pill-sync {
  transform: rotate(360deg);
}

.printer-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--orca-accent-hover);
  flex-shrink: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 5px;
  flex-shrink: 0;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 5px 10px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
  background: var(--bg-card);
  color: var(--text-main);
  font-weight: 600;
  font-size: 11.5px;
  cursor: pointer;
  transition: background 0.14s, border-color 0.14s, transform 0.08s;
  white-space: nowrap;
}
.btn:hover:not(:disabled) {
  background: var(--bg-card-hover);
  border-color: var(--border-strong);
}
.btn:active:not(:disabled) {
  transform: translateY(1px);
}
.btn:disabled {
  opacity: 0.42;
  cursor: not-allowed;
}

.btn-icon {
  padding: 5px 7px;
}

.btn-accent {
  background: linear-gradient(135deg, var(--orca-accent) 0%, #00897b 100%);
  border-color: transparent;
  color: #ffffff;
}
.btn-accent:hover:not(:disabled) {
  background: linear-gradient(135deg, var(--orca-accent-hover) 0%, var(--orca-accent) 100%);
  border-color: transparent;
}

.btn-soft {
  background: var(--orca-accent-soft);
  border-color: var(--orca-accent-border);
  color: var(--orca-accent-hover);
}
[data-theme="light"] .btn-soft {
  color: var(--orca-accent);
}
.btn-soft:hover:not(:disabled) {
  background: var(--orca-accent);
  color: #ffffff;
}

/* Main Workspace Grid */
.studio-workspace {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 332px minmax(340px, 1fr) 364px;
  overflow: hidden;
}

.col-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--bg-panel);
  overflow: hidden;
}
.col-left {
  border-right: 1px solid var(--border-subtle);
}
.col-right {
  border-left: 1px solid var(--border-subtle);
}

.col-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* Dock Mode Navigation Tabs (hidden in wide page mode) */
.dock-tabs {
  display: none;
  background: var(--bg-panel);
  border-bottom: 1px solid var(--border-subtle);
  padding: 4px 6px;
  gap: 4px;
  flex-shrink: 0;
}

.dock-tab-btn {
  flex: 1;
  padding: 6px 4px;
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  text-align: center;
  transition: all 0.14s;
}
.dock-tab-btn:hover {
  color: var(--text-main);
  background: var(--bg-card);
}
.dock-tab-btn.active {
  background: var(--orca-accent-soft);
  border-color: var(--orca-accent-border);
  color: var(--orca-accent-hover);
}
[data-theme="light"] .dock-tab-btn.active {
  color: var(--orca-accent);
}

/* Cards & Sections */
.studio-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}

.card-title {
  font-size: 11.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.55px;
  color: var(--text-main);
  display: flex;
  align-items: center;
  gap: 6px;
}

.card-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 99px;
  background: var(--orca-accent-soft);
  color: var(--orca-accent-hover);
}
[data-theme="light"] .card-badge {
  color: var(--orca-accent);
}

/* Presets Grid */
.preset-filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.filter-chip {
  padding: 3px 7px;
  font-size: 10.5px;
  font-weight: 600;
  border-radius: 99px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-input);
  color: var(--text-muted);
  cursor: pointer;
}
.filter-chip.active {
  background: var(--orca-accent);
  border-color: var(--orca-accent);
  color: #ffffff;
}

.presets-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
  max-height: 205px;
  overflow-y: auto;
  padding-right: 2px;
}

.preset-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 6px 7px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
  background: var(--bg-panel);
  cursor: pointer;
  transition: border-color 0.14s, background 0.14s;
  text-align: left;
}
.preset-card:hover {
  background: var(--bg-card-hover);
  border-color: var(--border-strong);
}
.preset-card.active {
  border-color: var(--orca-accent-hover);
  background: var(--orca-accent-soft);
}

.preset-thumb {
  width: 30px;
  height: 36px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preset-meta {
  min-width: 0;
  flex: 1;
}

.preset-name {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-main);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.preset-sub {
  font-size: 9.8px;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.preset-del-btn {
  position: absolute;
  top: 3px;
  right: 3px;
  width: 17px;
  height: 17px;
  border-radius: 4px;
  border: none;
  background: rgba(255, 82, 82, 0.16);
  color: var(--status-crit);
  font-size: 11px;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
.preset-del-btn:hover {
  background: var(--status-crit);
  color: #ffffff;
}

.save-preset-bar {
  display: none;
  gap: 5px;
  align-items: center;
  padding-top: 4px;
  border-top: 1px dashed var(--border-subtle);
}
.save-preset-bar.open {
  display: flex;
}
.save-preset-input {
  flex: 1;
  min-width: 0;
  background: var(--bg-input);
  border: 1px solid var(--orca-accent-border);
  border-radius: var(--radius-sm);
  padding: 4px 7px;
  font-size: 11.5px;
}

/* Segmented Mode Switch */
.seg-group {
  display: flex;
  background: var(--bg-input);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 2px;
  gap: 2px;
}

.seg-btn {
  flex: 1;
  padding: 5px 6px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.14s;
}
.seg-btn.active {
  background: var(--orca-accent);
  color: #ffffff;
}

/* 2D Curve Canvas Box */
.curve-editor-wrap {
  position: relative;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
  background: var(--bg-input);
  overflow: hidden;
}

#curve-canvas {
  display: block;
  width: 100%;
  height: 220px;
  cursor: crosshair;
  touch-action: none;
}

.curve-overlay-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 8px;
  background: var(--bg-panel);
  border-top: 1px solid var(--border-subtle);
  font-size: 10.5px;
  color: var(--text-muted);
}

.curve-coord-readout {
  font-family: var(--font-mono);
  font-size: 10.5px;
  color: var(--orca-accent-hover);
}
[data-theme="light"] .curve-coord-readout {
  color: var(--orca-accent);
}

.curve-hint {
  font-size: 10.2px;
  color: var(--text-dim);
}

/* Slider Controls */
.ctrl-row {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.ctrl-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}

.ctrl-label {
  font-size: 11.3px;
  color: var(--text-muted);
  font-weight: 500;
}

.ctrl-val-wrap {
  display: flex;
  align-items: center;
  gap: 3px;
}

.ctrl-num {
  width: 58px;
  background: var(--bg-input);
  border: 1px solid var(--border-subtle);
  border-radius: 4px;
  padding: 2px 5px;
  text-align: right;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-main);
}
.ctrl-num:focus {
  outline: none;
  border-color: var(--orca-accent);
}

.ctrl-unit {
  font-size: 10px;
  color: var(--text-dim);
  min-width: 18px;
}

input[type="range"].orca-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 5px;
  border-radius: 99px;
  background: var(--border-strong);
  outline: none;
  cursor: pointer;
}
input[type="range"].orca-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 13px;
  height: 13px;
  border-radius: 50%;
  background: var(--orca-accent-hover);
  border: 2px solid #ffffff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.4);
  cursor: grab;
  transition: transform 0.1s;
}
input[type="range"].orca-slider::-webkit-slider-thumb:hover {
  transform: scale(1.15);
}

/* Toggle Switch */
.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.toggle-switch {
  position: relative;
  display: inline-block;
  width: 34px;
  height: 18px;
  flex-shrink: 0;
}
.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}
.toggle-track {
  position: absolute;
  inset: 0;
  background: var(--border-strong);
  border-radius: 99px;
  cursor: pointer;
  transition: background 0.18s;
}
.toggle-track::before {
  content: "";
  position: absolute;
  width: 14px;
  height: 14px;
  left: 2px;
  top: 2px;
  border-radius: 50%;
  background: #ffffff;
  transition: transform 0.18s;
}
.toggle-switch input:checked + .toggle-track {
  background: var(--orca-accent);
}
.toggle-switch input:checked + .toggle-track::before {
  transform: translateX(16px);
}

/* Texture Accordion Layer Cards */
.tex-card {
  background: var(--bg-panel);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  overflow: hidden;
  transition: border-color 0.15s;
}
.tex-card.enabled {
  border-color: var(--orca-accent-border);
}

.tex-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 7px 9px;
  background: var(--bg-card);
  cursor: pointer;
}
.tex-card.enabled .tex-head {
  background: var(--orca-accent-soft);
}

.tex-title-wrap {
  display: flex;
  align-items: center;
  gap: 7px;
  font-weight: 600;
  font-size: 12px;
}

.tex-chevron {
  font-size: 10px;
  color: var(--text-muted);
  transition: transform 0.15s;
}
.tex-card.expanded .tex-chevron {
  transform: rotate(90deg);
}

.tex-body {
  display: none;
  padding: 8px 9px 10px;
  border-top: 1px solid var(--border-subtle);
  flex-direction: column;
  gap: 7px;
}
.tex-card.expanded .tex-body {
  display: flex;
}

/* Center 3D Viewport */
.viewport-col {
  position: relative;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  background: radial-gradient(circle at 50% 32%, var(--bg-viewport-top) 0%, var(--bg-viewport-bot) 100%);
  overflow: hidden;
}

#gl-canvas {
  width: 100%;
  height: 100%;
  display: block;
  touch-action: none;
  cursor: grab;
}
#gl-canvas:active {
  cursor: grabbing;
}

#vp-caliper-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: block;
  pointer-events: none;
  z-index: 5;
}

/* Wall Thickness Quick Presets & Perimeter Hint */
.wall-preset-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 1px;
}

.wall-chip {
  flex: 1;
  min-width: 48px;
  padding: 3px 5px;
  border-radius: 5px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-input);
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 10.2px;
  font-weight: 600;
  cursor: pointer;
  text-align: center;
  transition: all 0.14s;
}
.wall-chip:hover {
  color: var(--text-main);
  border-color: var(--border-strong);
  background: var(--bg-card-hover);
}
.wall-chip.active {
  background: var(--orca-accent-soft);
  border-color: var(--orca-accent-hover);
  color: var(--orca-accent-hover);
}
[data-theme="light"] .wall-chip.active {
  color: var(--orca-accent);
  border-color: var(--orca-accent);
}

.wall-perim-hint {
  font-size: 10.4px;
  color: var(--orca-accent-hover);
  font-family: var(--font-mono);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  padding: 3px 7px;
  border-radius: 5px;
  background: var(--orca-accent-soft);
  border: 1px solid var(--orca-accent-border);
}
[data-theme="light"] .wall-perim-hint {
  color: var(--orca-accent);
}

/* Floating Viewport Overlays */
.vp-toolbar-left {
  position: absolute;
  top: 10px;
  left: 10px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 5px;
  max-width: calc(100% - 252px);
  z-index: 10;
}

.vp-glass {
  background: var(--bg-hud);
  backdrop-filter: blur(8px);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-soft);
}

.vp-select {
  background: var(--bg-hud);
  color: var(--text-main);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 5px 8px;
  font-size: 11.5px;
  font-weight: 600;
  cursor: pointer;
}

.vp-chip {
  padding: 5px 8px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-subtle);
  background: var(--bg-hud);
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.vp-chip:hover {
  color: var(--text-main);
  border-color: var(--border-strong);
}
.vp-chip.active {
  background: var(--orca-accent);
  border-color: var(--orca-accent);
  color: #ffffff;
}
.vp-chip-xray {
  border-color: var(--orca-accent-border);
  color: var(--text-main);
}
.vp-chip-xray.active {
  background: linear-gradient(135deg, #00bfa5 0%, #ff8f00 130%);
  border-color: transparent;
  color: #ffffff;
  box-shadow: 0 2px 10px rgba(0, 191, 165, 0.35);
}

.spiral-mode-banner {
  display: none;
  position: absolute;
  top: 48px;
  left: 10px;
  max-width: calc(100% - 256px);
  padding: 5px 10px;
  font-size: 10.6px;
  font-weight: 600;
  line-height: 1.3;
  z-index: 12;
  border-left: 3px solid var(--orca-accent-hover);
  color: var(--text-main);
  pointer-events: none;
}
.spiral-mode-banner.visible {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.spiral-mode-banner.warn {
  border-left-color: var(--status-warn);
  background: rgba(45, 34, 14, 0.90);
}
[data-theme="light"] .spiral-mode-banner.warn {
  background: rgba(255, 245, 224, 0.94);
}

.vp-cam-bar {
  position: absolute;
  bottom: 56px;
  left: 10px;
  display: flex;
  gap: 4px;
  z-index: 10;
}

.vp-cut-bar {
  position: absolute;
  bottom: 10px;
  left: 10px;
  right: 10px;
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 6px 10px;
  z-index: 10;
}

.vp-cut-modes {
  display: inline-flex;
  background: var(--bg-input);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  padding: 2px;
  gap: 2px;
  flex-shrink: 0;
}

.vp-cut-mode-btn {
  padding: 3px 7px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--text-muted);
  font-size: 10.5px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.14s;
}
.vp-cut-mode-btn:hover {
  color: var(--text-main);
}
.vp-cut-mode-btn.active {
  background: var(--orca-accent);
  color: #ffffff;
}

.vp-cut-label {
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
  color: var(--text-muted);
}

/* Printability HUD */
.vp-hud-right {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 236px;
  padding: 9px 11px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  z-index: 10;
}

.hud-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 10.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-muted);
}

.hud-status-pill {
  padding: 1px 7px;
  border-radius: 99px;
  font-size: 10px;
  font-weight: 700;
}
.hud-status-pill.ok {
  background: rgba(0, 200, 83, 0.18);
  color: var(--status-ok);
}
.hud-status-pill.warn {
  background: rgba(255, 179, 0, 0.20);
  color: var(--status-warn);
}
.hud-status-pill.crit {
  background: rgba(255, 82, 82, 0.22);
  color: var(--status-crit);
}

.hud-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 5px 8px;
}

.hud-metric {
  display: flex;
  flex-direction: column;
}
.hud-metric-k {
  font-size: 9.8px;
  color: var(--text-dim);
}
.hud-metric-v {
  font-family: var(--font-mono);
  font-size: 11.2px;
  font-weight: 600;
  color: var(--text-main);
}

.hud-warnings {
  display: flex;
  flex-direction: column;
  gap: 3px;
  max-height: 92px;
  overflow-y: auto;
}

.hud-warn-item {
  font-size: 10.2px;
  padding: 3px 6px;
  border-radius: 4px;
  background: rgba(255, 179, 0, 0.13);
  border-left: 2px solid var(--status-warn);
  color: var(--text-main);
}
.hud-warn-item.crit {
  background: rgba(255, 82, 82, 0.15);
  border-left-color: var(--status-crit);
}

.heatmap-legend {
  display: none;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  padding-top: 4px;
  border-top: 1px solid var(--border-subtle);
  color: var(--text-muted);
}
.heatmap-legend.visible {
  display: flex;
}
.legend-swatch {
  width: 9px;
  height: 9px;
  border-radius: 2px;
  display: inline-block;
}

.bed-alert-banner {
  display: none;
  position: absolute;
  top: 52px;
  left: 50%;
  transform: translateX(-50%);
  padding: 6px 12px 6px 14px;
  border-radius: 99px;
  background: rgba(213, 0, 0, 0.90);
  color: #ffffff;
  font-weight: 700;
  font-size: 11.5px;
  box-shadow: 0 4px 16px rgba(213, 0, 0, 0.45);
  z-index: 15;
  pointer-events: auto;
  white-space: nowrap;
}
.bed-alert-banner.visible {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.bed-fit-btn {
  padding: 2px 9px;
  border-radius: 99px;
  border: 1px solid rgba(255, 255, 255, 0.65);
  background: rgba(255, 255, 255, 0.18);
  color: #ffffff;
  font-size: 10.5px;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.14s;
}
.bed-fit-btn:hover {
  background: rgba(255, 255, 255, 0.32);
}

/* Right Action Footer */
.action-footer {
  padding: 10px;
  background: var(--bg-panel);
  border-top: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  gap: 7px;
  flex-shrink: 0;
}

.btn-hero {
  width: 100%;
  padding: 10px 14px;
  font-size: 13px;
  font-weight: 700;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, #00bfa5 0%, #00897b 100%);
  color: #ffffff;
  border: none;
  box-shadow: 0 4px 14px rgba(0, 191, 165, 0.32);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: filter 0.15s, transform 0.08s;
}
.btn-hero:hover:not(:disabled) {
  filter: brightness(1.07);
}
.btn-hero:active:not(:disabled) {
  transform: translateY(1px);
}
.btn-hero:disabled {
  opacity: 0.55;
  cursor: wait;
}

.export-btn-row {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 6px;
}

.helper-note {
  font-size: 10.5px;
  color: var(--text-muted);
  background: var(--bg-input);
  border-left: 2px solid var(--orca-accent);
  padding: 5px 7px;
  border-radius: 0 4px 4px 0;
}

.helper-note.warn {
  border-left-color: var(--status-warn);
  background: rgba(255, 179, 0, 0.10);
}

/* Toast Notification */
.toast-banner {
  position: fixed;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%) translateY(20px);
  opacity: 0;
  pointer-events: none;
  padding: 8px 16px;
  border-radius: var(--radius-md);
  background: var(--bg-card);
  border: 1px solid var(--orca-accent);
  color: var(--text-main);
  font-size: 12px;
  font-weight: 600;
  box-shadow: var(--shadow-soft);
  transition: opacity 0.2s, transform 0.2s;
  z-index: 999;
  max-width: 90vw;
}
.toast-banner.visible {
  opacity: 1;
  transform: translateX(-50%) translateY(0);
}
.toast-banner.error {
  border-color: var(--status-crit);
}

/* ============================================================================
   COMPACT SIDE-DOCK MODE (`data-mode="dock"` or narrow viewports <= 960px)
   ============================================================================ */
body[data-mode="dock"] .printer-pill,
body[data-mode="dock"] .brand-title {
  display: none;
}

body[data-mode="dock"] .design-name-input {
  width: 118px;
}

body[data-mode="dock"] .studio-workspace {
  display: flex;
  flex-direction: column;
}

body[data-mode="dock"] .viewport-col {
  order: -1;
  height: 245px;
  flex-shrink: 0;
  border-bottom: 1px solid var(--border-subtle);
}

body[data-mode="dock"] .vp-hud-right {
  width: 172px;
  padding: 5px 7px;
  gap: 3px;
}
body[data-mode="dock"] .hud-warnings,
body[data-mode="dock"] .spiral-mode-banner {
  display: none;
}
body[data-mode="dock"] .vp-cam-bar {
  display: none;
}
body[data-mode="dock"] .vp-cut-bar {
  padding: 4px 6px;
  bottom: 6px;
  gap: 4px;
}
body[data-mode="dock"] .vp-cut-mode-btn {
  padding: 2px 5px;
  font-size: 9.8px;
}

body[data-mode="dock"] .dock-tabs {
  display: flex;
  order: 0;
}

body[data-mode="dock"] .col-left,
body[data-mode="dock"] .col-right {
  border: none;
  flex: 1;
  min-height: 0;
}

body[data-mode="dock"] .col-right .action-footer {
  display: none;
}

.dock-global-footer {
  display: none;
}
body[data-mode="dock"] .dock-global-footer {
  display: flex;
}

body[data-mode="dock"][data-dock-tab="shape"] .col-right {
  display: none;
}
body[data-mode="dock"][data-dock-tab="shape"] #card-presets {
  display: none;
}

body[data-mode="dock"][data-dock-tab="presets"] .col-right {
  display: none;
}
body[data-mode="dock"][data-dock-tab="presets"] #card-silhouette,
body[data-mode="dock"][data-dock-tab="presets"] #card-resolution {
  display: none;
}
body[data-mode="dock"][data-dock-tab="presets"] .presets-grid {
  max-height: none;
}

body[data-mode="dock"][data-dock-tab="textures"] .col-left {
  display: none;
}
body[data-mode="dock"][data-dock-tab="textures"] #card-print-mode,
body[data-mode="dock"][data-dock-tab="textures"] #card-gardening {
  display: none;
}

body[data-mode="dock"][data-dock-tab="print"] .col-left {
  display: none;
}
body[data-mode="dock"][data-dock-tab="print"] #card-envelope,
body[data-mode="dock"][data-dock-tab="print"] #card-textures {
  display: none;
}

@media (max-width: 960px) {
  .printer-pill {
    display: none;
  }
  .studio-workspace {
    grid-template-columns: 280px minmax(260px, 1fr) 300px;
  }
}
</style>
    <style>
      /* Preserve the reference page height when fallback font metrics differ. */
      body[data-mode="page"] .studio-header {
        min-height: 43px;
      }
      .box-select {
        width: 100%;
        max-width: 100%;
      }
      .box-pair {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 7px;
      }
      .box-feature {
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-sm);
        padding: 7px;
        display: flex;
        flex-direction: column;
        gap: 7px;
      }
      .box-feature-title {
        display: flex;
        align-items: center;
        justify-content: space-between;
      }
      .box-feature .ctrl-num {
        max-width: 100%;
      }
      .box-feature .ctrl-row {
        display: flex;
        flex-direction: column;
        gap: 4px;
      }
      .box-feature-title button {
        padding: 1px 6px;
      }
      .section-hidden {
        display: none;
      }
      .box-style-controls[hidden] { display: none; }
      .box-status-error {
        color: var(--status-crit);
      }
    </style>
    <style id="orca-box-host-adapter">
      /* Orca's late, bare element defaults must not replace the studio tokens.
         Keep this adapter separate from the unchanged canonical design sheet. */
      html[data-theme],
      html[data-theme] body {
        background: var(--bg-app);
        color: var(--text-main);
        font-family: var(--font-sans);
        font-size: 12.5px;
        line-height: 1.4;
      }
      html[data-theme="dark"] {
        --orca-accent: #00a896;
        color-scheme: dark;
      }
      html[data-theme="light"] {
        --orca-accent: #00897b;
        color-scheme: light;
      }
      html[data-theme] :is(h1, h2, h3, h4, h5, h6),
      html[data-theme] .brand-title,
      html[data-theme] .tex-title-wrap {
        color: var(--text-main);
      }
      html[data-theme] :is(input, select, textarea) {
        color: var(--text-main);
      }
      html[data-theme] input[type="range"].orca-slider {
        border: 0;
        padding: 0;
        min-height: 0;
        box-shadow: none;
      }
      html[data-theme] .toggle-switch input {
        border: 0;
        padding: 0;
        min-width: 0;
        min-height: 0;
      }
    </style>
  </head>
  <body data-mode="__INITIAL_MODE__" data-dock-tab="shape">
    <div class="studio-shell">
      <header class="studio-header">
        <div class="brand-group">
          <div class="brand-logo" title="Orca Box Studio">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="m3 8 9-5 9 5-9 5Zm0 0v10l9 5 9-5V8M12 13v10" />
            </svg>
          </div>
          <div class="brand-titles">
            <div class="brand-name-row">
              <span class="brand-title">Orca Box Studio</span>
              <input
                id="name"
                class="design-name-input"
                type="text"
                maxlength="80"
                value="Caixa de projeto"
                aria-label="Design Name"
              />
            </div>
          </div>
          <button
            id="sync"
            type="button"
            class="printer-pill"
            title="Clique para sincronizar impressora ativa do OrcaSlicer"
          >
            <span class="printer-dot"></span>
            <span id="printer-pill-text" class="printer-pill-text">
              <span id="printer-pill-name" class="printer-pill-name"
                >Generic 3D Printer</span
              >
              <span id="printer-pill-specs" class="printer-pill-specs"
                >· 220×220×250 mm · 0.4mm</span
              >
            </span>
            <span
              id="printer-pill-sync"
              class="printer-pill-sync"
              aria-hidden="true"
              >↻</span
            >
          </button>
        </div>

        <div class="header-actions">
          <button id="undo" class="btn btn-icon" title="Undo (Ctrl+Z)" disabled>
            ↶
          </button>
          <button id="redo" class="btn btn-icon" title="Redo (Ctrl+Y)" disabled>
            ↷
          </button>
          <button id="btn-randomize" class="btn btn-soft">
            <span>🎲</span>
            <span data-i18n="btn_surprise">Surpreenda-me</span>
          </button>
          <button id="reset" class="btn btn-icon" title="Reset">↺</button>
          <button id="lang" class="btn btn-icon" title="Português / English">
            PT
          </button>
          <button id="theme" class="btn btn-icon" title="Dark / Light">
            ☾
          </button>
        </div>
      </header>

      <nav class="dock-tabs" aria-label="Studio Sections">
        <button class="dock-tab-btn active" data-tab="shape" data-i18n="shape">
          Forma</button
        ><button class="dock-tab-btn" data-tab="textures" data-i18n="features">
          Recursos</button
        ><button class="dock-tab-btn" data-tab="print" data-i18n="manufacture">
          Impressão</button
        ><button class="dock-tab-btn" data-tab="presets" data-i18n="presets">
          Presets
        </button>
      </nav>
      <main class="studio-workspace">
        <section class="col-panel col-left">
          <div class="col-scroll">
            <div id="card-presets" class="studio-card">
              <div class="card-head">
                <span class="card-title" data-i18n="sec_presets"
                  >sec_presets</span
                ><button
                  id="btn-toggle-save-preset"
                  class="btn btn-soft"
                  style="padding: 2px 8px; font-size: 10.5px"
                  data-i18n="btn_save_preset"
                >
                  + Salvar
                </button>
              </div>
              <div id="save-preset-bar" class="save-preset-bar">
                <input
                  id="inp-save-preset-name"
                  class="save-preset-input"
                  type="text"
                  maxlength="64"
                /><button
                  id="savePreset"
                  class="btn btn-accent"
                  data-i18n="save"
                >
                  Salvar
                </button>
              </div>
              <div id="preset-filters" class="preset-filter-row">
                <button
                  class="filter-chip active"
                  data-cat="all"
                  data-i18n="cat_all"
                >
                  Todos</button
                ><button class="filter-chip" data-cat="lip_snap">Snap</button
                ><button class="filter-chip" data-cat="rugged_box">
                  Rugged</button
                ><button class="filter-chip" data-cat="sliding_lid">
                  Sliding</button
                ><button class="filter-chip" data-cat="screw_corner">
                  Screw</button
                ><button class="filter-chip" data-cat="open_bin" data-i18n="openBin">Caixa aberta</button
                ><button class="filter-chip" data-cat="snap_latch" data-i18n="snapLatch">Travas</button
                ><button class="filter-chip" data-cat="stackable_bin" data-i18n="stackableBin">Empilhável</button
                ><button class="filter-chip" data-cat="clamshell_pip" data-i18n="clamshellPip">Articulado PIP</button
                ><button
                  class="filter-chip"
                  data-cat="user"
                  data-i18n="cat_user"
                >
                  Meus
                </button>
              </div>
              <div id="presets-grid" class="presets-grid"></div>
            </div>
            <div id="card-silhouette" class="studio-card">
              <div class="card-head">
                <span class="card-title" data-i18n="construction"
                  >construction</span
                ><span id="poly-badge" class="card-badge">BOX</span>
              </div>
              <label class="ctrl-row"
                ><span class="ctrl-label" data-i18n="style">style</span
                ><select id="style" class="vp-select box-select">
                  <option value="lip_snap">Lip Snap</option>
                  <option value="rugged_box">Rugged Box</option>
                  <option value="sliding_lid">Sliding Lid</option>
                  <option value="screw_corner">Screw Corner</option>
                  <option value="open_bin" data-i18n="openBin">Caixa aberta</option>
                  <option value="snap_latch" data-i18n="snapLatch">Tampa com travas</option>
                  <option value="stackable_bin" data-i18n="stackableBin">Caixa empilhável</option>
                  <option value="clamshell_pip" data-i18n="clamshellPip">Estojo articulado PIP</option>
                </select></label
              >
              <div data-slider="width_x" class="ctrl-row">
                <label class="ctrl-top"
                  ><span
                    class="ctrl-label"
                    data-pt="Largura X"
                    data-en="Width X"
                    >Largura X</span
                  ><span class="ctrl-val-wrap"
                    ><input
                      class="ctrl-num"
                      data-p="width_x"
                      type="number"
                      min="20"
                      max="350"
                      step="1"
                    /><span class="ctrl-unit">mm</span></span
                  ></label
                ><input
                  class="orca-slider"
                  data-param-range="width_x"
                  type="range"
                  min="20"
                  max="350"
                  step="1"
                />
              </div>
              <div data-slider="depth_y" class="ctrl-row">
                <label class="ctrl-top"
                  ><span
                    class="ctrl-label"
                    data-pt="Profundidade Y"
                    data-en="Depth Y"
                    >Profundidade Y</span
                  ><span class="ctrl-val-wrap"
                    ><input
                      class="ctrl-num"
                      data-p="depth_y"
                      type="number"
                      min="20"
                      max="350"
                      step="1"
                    /><span class="ctrl-unit">mm</span></span
                  ></label
                ><input
                  class="orca-slider"
                  data-param-range="depth_y"
                  type="range"
                  min="20"
                  max="350"
                  step="1"
                />
              </div>
              <div data-slider="height_z" class="ctrl-row">
                <label class="ctrl-top"
                  ><span
                    class="ctrl-label"
                    data-pt="Altura Z"
                    data-en="Height Z"
                    >Altura Z</span
                  ><span class="ctrl-val-wrap"
                    ><input
                      class="ctrl-num"
                      data-p="height_z"
                      type="number"
                      min="10"
                      max="250"
                      step="1"
                    /><span class="ctrl-unit">mm</span></span
                  ></label
                ><input
                  class="orca-slider"
                  data-param-range="height_z"
                  type="range"
                  min="10"
                  max="250"
                  step="1"
                />
              </div>
              <div data-slider="corner_radius" class="ctrl-row">
                <label class="ctrl-top"
                  ><span
                    class="ctrl-label"
                    data-pt="Raio de canto"
                    data-en="Corner radius"
                    >Raio de canto</span
                  ><span class="ctrl-val-wrap"
                    ><input
                      class="ctrl-num"
                      data-p="corner_radius"
                      type="number"
                      min="0.8"
                      max="30"
                      step="0.2"
                    /><span class="ctrl-unit">mm</span></span
                  ></label
                ><input
                  class="orca-slider"
                  data-param-range="corner_radius"
                  type="range"
                  min="0.8"
                  max="30"
                  step="0.2"
                />
              </div>
              <div class="ctrl-row">
                <div class="ctrl-top">
                  <span class="ctrl-label" data-i18n="open">Abrir</span
                  ><span class="ctrl-val-wrap"
                    ><span id="openValue" class="ctrl-num">25%</span></span
                  >
                </div>
                <input
                  id="open"
                  class="orca-slider"
                  type="range"
                  min="0"
                  max="100"
                  value="25"
                />
              </div>
              <div class="curve-editor-wrap">
                <canvas id="curve-canvas" width="500" height="330"></canvas>
                <div class="curve-overlay-bar">
                  <span id="curve-coord-readout" class="curve-coord-readout"
                    >X/Y · mm</span
                  ><button
                    id="addPost"
                    class="btn"
                    style="padding: 2px 6px; font-size: 10px"
                  >
                    + PCB
                  </button>
                </div>
              </div>
              <div class="curve-hint" data-i18n="planHelp"></div>
            </div>
            <div id="card-resolution" class="studio-card">
              <div class="card-head">
                <span class="card-title" data-i18n="quality">quality</span>
              </div>
              <label class="ctrl-row"
                ><span class="ctrl-label" data-i18n="quality">quality</span
                ><select id="quality" class="vp-select box-select">
                  <option value="standard" data-i18n="qualityStandard">Standard</option>
                  <option value="fine" data-i18n="qualityFine">Fine</option>
                </select></label
              >
              <p id="surface" class="helper-note"></p>
            </div>
          </div>
        </section>
        <section class="viewport-col">
          <canvas id="gl-canvas"></canvas>
          <canvas id="vp-caliper-canvas"></canvas>

          <!-- Top-Left Material & View Controls -->
          <div class="vp-toolbar-left">
            <select id="sel-material" class="vp-select" aria-label="Material">
              <option value="emerald_silk" data-i18n="mat_emerald">
                Seda Esmeralda Orca
              </option>
              <option value="terracotta" data-i18n="mat_terracotta">
                Cerâmica Terracota
              </option>
              <option value="matte_ceramic" data-i18n="mat_white">
                Porcelana Branca Mate
              </option>
              <option value="copper_bronze" data-i18n="mat_copper">
                Bronze Cobre Escovado
              </option>
              <option value="xray" data-i18n="mat_xray">
                🔬 Raio-X / Parede (Translúcido)
              </option>
              <option value="heatmap" data-i18n="mat_heatmap">
                Mapa de Overhang (°)
              </option>
            </select>
            <button id="xray" class="vp-chip vp-chip-xray" data-i18n="vp_xray">
              🔬 Raio-X / Parede
            </button>
            <button
              id="btn-vp-calipers"
              class="vp-chip"
              data-i18n="vp_calipers"
            >
              📏 Cotas mm
            </button>
            <button id="btn-vp-heatmap" class="vp-chip" data-i18n="vp_heatmap">
              🔥 Overhang
            </button>
            <button id="btn-vp-wire" class="vp-chip" data-i18n="vp_wire">
              ⌗ Malha
            </button>
            <button id="play" class="vp-chip" title="Animate lid">▶</button>
            <button id="btn-vp-spin" class="vp-chip" title="Auto-Rotate">
              ⟳
            </button>
          </div>

          <!-- Out-of-bed live warning -->
          <div id="bed-alert-banner" class="bed-alert-banner">
            <span>⚠</span>
            <span id="bed-alert-text"
              >Dimensões excedem o volume da impressora!</span
            >
            <button
              id="btn-fit-to-printer"
              style="display: none"
              type="button"
              class="bed-fit-btn"
              data-i18n="btn_fit_printer"
            >
              Ajustar à Mesa
            </button>
          </div>

          <!-- Top-Right Live Printability & Dimensions HUD -->
          <aside id="vp-hud-right" class="vp-hud-right vp-glass">
            <div class="hud-title-row">
              <span data-i18n="hud_title">Printabilidade</span>
              <span id="hud-status-pill" class="hud-status-pill ok">OK</span>
            </div>
            <div class="hud-grid">
              <div class="hud-metric">
                <span class="hud-metric-k" data-i18n="hud_wall_floor"
                  >Parede / Fundo</span
                >
                <span id="hud-wall-floor" class="hud-metric-v">—</span>
              </div>
              <div class="hud-metric">
                <span class="hud-metric-k" data-i18n="hud_mouth_hole"
                  >Folga por lado</span
                >
                <span id="hud-clearance" class="hud-metric-v">—</span>
              </div>
              <div class="hud-metric">
                <span class="hud-metric-k" data-i18n="hud_dims"
                  >Dimensões (mm)</span
                >
                <span id="hud-dims" class="hud-metric-v">—</span>
              </div>
              <div class="hud-metric">
                <span class="hud-metric-k" data-i18n="hud_overhang"
                  >Overhang Máx</span
                >
                <span id="hud-overhang" class="hud-metric-v">—</span>
              </div>
              <div class="hud-metric">
                <span class="hud-metric-k" data-i18n="hud_weight"
                  >Volume sólido</span
                >
                <span id="volume" class="hud-metric-v">—</span>
              </div>
              <div class="hud-metric">
                <span class="hud-metric-k" data-i18n="hud_Tris"
                  >Triângulos</span
                >
                <span id="triangles" class="hud-metric-v">—</span>
              </div>
            </div>
            <div id="xray-legend" class="heatmap-legend">
              <span
                ><i class="legend-swatch" style="background: #0fd6c2"></i
                ><span data-i18n="leg_outer">Externa</span></span
              >
              <span
                ><i class="legend-swatch" style="background: #ff8c38"></i
                ><span data-i18n="leg_inner">Cavidade &amp; Fundo</span></span
              >
            </div>
            <div id="heatmap-legend" class="heatmap-legend">
              <span
                ><i class="legend-swatch" style="background: #00c853"></i
                >≤45°</span
              >
              <span
                ><i class="legend-swatch" style="background: #ffb300"></i
                >45–55°</span
              >
              <span
                ><i class="legend-swatch" style="background: #ff3d00"></i
                >&gt;55°</span
              >
            </div>
            <div
              id="status"
              class="helper-note"
              role="status"
              aria-live="polite"
            ></div>
            <div id="hud-warnings" class="hud-warnings"></div>
          </aside>

          <!-- Camera Preset Pills -->
          <div class="vp-cam-bar">
            <button class="vp-chip" data-cam="iso">Iso</button>
            <button class="vp-chip" data-cam="front" data-i18n="cam_front">
              Frente
            </button>
            <button class="vp-chip" data-cam="top" data-i18n="cam_top">
              Topo
            </button>
            <button class="vp-chip" data-cam="bottom" data-i18n="cam_bottom">
              Base
            </button>
            <button
              class="vp-chip"
              id="home"
              data-cam="fit"
              data-i18n="cam_fit"
            >
              Enquadrar
            </button>
          </div>

          <!-- Bottom Dual Section Inspector Slider (Vertical Profile Y + Horizontal Plan Slice Z) -->
          <div class="vp-cut-bar vp-glass">
            <div
              class="vp-cut-modes"
              role="group"
              aria-label="Section Cut Mode"
            >
              <button
                id="btn-cut-mode-y"
                class="vp-cut-mode-btn active"
                data-i18n="vp_cut_y"
              >
                ✂ Corte Vertical (Perfil Y)
              </button>
              <button
                id="btn-cut-mode-z"
                class="vp-cut-mode-btn"
                data-i18n="vp_cut_z"
              >
                💿 Fatia Horizontal Z (Planta 5%–100%)
              </button>
            </div>
            <input
              id="cut"
              class="orca-slider"
              type="range"
              min="0"
              max="100"
              step="1"
              value="0"
            />
            <span
              id="lbl-cross-cut"
              class="ctrl-num"
              style="width: 62px; text-align: center"
              >Off</span
            >
            <button
              id="btn-cut-half"
              class="btn"
              style="padding: 3px 7px; font-size: 10.5px"
            >
              50%
            </button>
            <button
              id="btn-cut-off"
              class="btn"
              style="padding: 3px 7px; font-size: 10.5px"
            >
              Off
            </button>
          </div>
        </section>

        <section class="col-panel col-right">
          <div class="col-scroll">
            <div id="card-print-mode" class="studio-card">
              <div class="card-head">
                <span class="card-title" data-i18n="wall">wall</span
                ><span id="wall-mode-badge" class="card-badge">mm</span>
              </div>
              <div data-slider="wall_thickness" class="ctrl-row">
                <label class="ctrl-top"
                  ><span class="ctrl-label" data-pt="Parede" data-en="Wall"
                    >Parede</span
                  ><span class="ctrl-val-wrap"
                    ><input
                      class="ctrl-num"
                      data-p="wall_thickness"
                      type="number"
                      min="1.2"
                      max="12"
                      step="0.2"
                    /><span class="ctrl-unit">mm</span></span
                  ></label
                ><input
                  class="orca-slider"
                  data-param-range="wall_thickness"
                  type="range"
                  min="1.2"
                  max="12"
                  step="0.2"
                />
              </div>
              <div data-slider="floor_thickness" class="ctrl-row">
                <label class="ctrl-top"
                  ><span class="ctrl-label" data-pt="Fundo" data-en="Floor"
                    >Fundo</span
                  ><span class="ctrl-val-wrap"
                    ><input
                      class="ctrl-num"
                      data-p="floor_thickness"
                      type="number"
                      min="1.2"
                      max="12"
                      step="0.2"
                    /><span class="ctrl-unit">mm</span></span
                  ></label
                ><input
                  class="orca-slider"
                  data-param-range="floor_thickness"
                  type="range"
                  min="1.2"
                  max="12"
                  step="0.2"
                />
              </div>
              <div data-slider="lid_height" class="ctrl-row">
                <label class="ctrl-top"
                  ><span
                    class="ctrl-label"
                    data-pt="Espessura da tampa"
                    data-en="Lid thickness"
                    >Espessura da tampa</span
                  ><span class="ctrl-val-wrap"
                    ><input
                      class="ctrl-num"
                      data-p="lid_height"
                      type="number"
                      min="1.2"
                      max="12"
                      step="0.2"
                    /><span class="ctrl-unit">mm</span></span
                  ></label
                ><input
                  class="orca-slider"
                  data-param-range="lid_height"
                  type="range"
                  min="1.2"
                  max="12"
                  step="0.2"
                />
              </div>
              <div data-slider="fit_clearance" class="ctrl-row">
                <label class="ctrl-top"
                  ><span
                    class="ctrl-label"
                    data-pt="Folga por lado"
                    data-en="Clearance per side"
                    >Folga por lado</span
                  ><span class="ctrl-val-wrap"
                    ><input
                      class="ctrl-num"
                      data-p="fit_clearance"
                      type="number"
                      min="0.1"
                      max="0.4"
                      step="0.01"
                    /><span class="ctrl-unit">mm</span></span
                  ></label
                ><input
                  class="orca-slider"
                  data-param-range="fit_clearance"
                  type="range"
                  min="0.1"
                  max="0.4"
                  step="0.01"
                />
              </div>
              <div id="wall-preset-chips" class="wall-preset-row">
                <button class="wall-chip" data-wall-preset="1.2">1.2 mm</button
                ><button class="wall-chip" data-wall-preset="2.4">2.4 mm</button
                ><button class="wall-chip" data-wall-preset="4">4 mm</button
                ><button class="wall-chip" data-wall-preset="8">8 mm</button>
              </div>
              <div id="wall-perim-hint" class="wall-perim-hint"></div>
            </div>
            <div id="card-textures" class="studio-card">
              <div class="card-head">
                <span class="card-title" data-i18n="features">features</span>
              </div>
              <div class="tex-card expanded">
                <div class="tex-head">
                  <span class="tex-title-wrap" data-i18n="pcb">PCB</span>
                </div>
                <div class="tex-body" id="posts"></div>
              </div>
              <div class="tex-card expanded">
                <div class="tex-head">
                  <span class="tex-title-wrap" data-i18n="ports">Recortes</span
                  ><button
                    id="addPort"
                    class="btn btn-soft"
                    style="padding: 2px 6px"
                  >
                    + USB-C
                  </button>
                </div>
                <div class="tex-body" id="ports"></div>
              </div>
              <div class="tex-card expanded">
                <div class="tex-head">
                  <span class="tex-title-wrap" data-i18n="dividers"
                    >Divisórias</span
                  >
                </div>
                <div class="tex-body">
                  <label class="ctrl-row"
                    ><span class="ctrl-label" data-i18n="dividerX"></span
                    ><input
                      id="dividers_x"
                      class="save-preset-input"
                      placeholder="-20, 20" /></label
                  ><label class="ctrl-row"
                    ><span class="ctrl-label" data-i18n="dividerY"></span
                    ><input
                      id="dividers_y"
                      class="save-preset-input"
                      placeholder="0"
                  /></label>
                </div>
              </div>
            </div>
            <div id="card-envelope" class="studio-card">
              <div class="card-head">
                <span class="card-title" data-i18n="connections">Encaixes & alças</span>
              </div>
              <div data-slider="lip_depth" class="ctrl-row">
                <label class="ctrl-top"
                  ><span
                    class="ctrl-label"
                    data-pt="Profundidade de encaixe"
                    data-en="Locating skirt depth"
                    >Profundidade de encaixe</span
                  ><span class="ctrl-val-wrap"
                    ><input
                      class="ctrl-num"
                      data-p="lip_depth"
                      type="number"
                      min="3"
                      max="10"
                      step="0.5"
                    /><span class="ctrl-unit">mm</span></span
                  ></label
                ><input
                  class="orca-slider"
                  data-param-range="lip_depth"
                  type="range"
                  min="3"
                  max="10"
                  step="0.5"
                />
              </div>
              <div class="rugged">
                <label class="ctrl-row"
                  ><span class="ctrl-label" data-i18n="hinge">hinge</span
                  ><select id="hinge_mode" class="vp-select box-select">
                    <option value="pin">Pino / Pin</option>
                    <option value="print_in_place">Print-in-place</option>
                  </select></label
                >
                <p id="rugged-motion-phase" class="helper-note" aria-live="polite" hidden></p>
              </div>
                <div data-slider="hinge_pin_diameter" class="ctrl-row">
                  <label class="ctrl-top"
                    ><span
                      class="ctrl-label"
                      data-pt="Diâmetro do pino"
                      data-en="Pin diameter"
                      >Diâmetro do pino</span
                    ><span class="ctrl-val-wrap"
                      ><input
                        class="ctrl-num"
                        data-p="hinge_pin_diameter"
                        type="number"
                        min="2"
                        max="6"
                        step="0.2"
                      /><span class="ctrl-unit">mm</span></span
                    ></label
                  ><input
                    class="orca-slider"
                    data-param-range="hinge_pin_diameter"
                    type="range"
                    min="2"
                    max="6"
                    step="0.2"
                  />
                </div>

              <div class="screw">
                <label class="ctrl-row"
                  ><span class="ctrl-label" data-i18n="screw">screw</span
                  ><select id="screw_size" class="vp-select box-select">
                    <option value="M2">M2</option>
                    <option value="M2.5">M2.5</option>
                    <option value="M3">M3</option>
                  </select></label
                >
              </div>
<div id="open-bin-handles" class="ctrl-row box-style-controls" hidden>
  <div class="switch-row">
    <span class="ctrl-label" data-i18n="handles">Alças de mão</span
    ><label class="toggle-switch"
      ><input id="handles_enabled" type="checkbox" /><span
        class="toggle-track"
      ></span
    ></label>
  </div>
  <label class="ctrl-row"
    ><span class="ctrl-label" data-i18n="handleFaces">Par de faces</span
    ><select id="handle_faces" class="vp-select box-select">
      <option value="left_right" data-i18n="leftRight">
        Esquerda / direita
      </option>
      <option value="front_back" data-i18n="frontBack">Frente / trás</option>
    </select></label
  >
  <div data-slider="handle_width" class="ctrl-row">
    <label class="ctrl-top"
      ><span
        class="ctrl-label"
        data-pt="Largura útil da alça"
        data-en="Grip clear width"
        >Largura útil da alça</span
      ><span class="ctrl-val-wrap"
        ><input
          class="ctrl-num"
          data-p="handle_width"
          type="number"
          min="12"
          max="160"
          step="1"
        /><span class="ctrl-unit">mm</span></span
      ></label
    ><input
      class="orca-slider"
      data-param-range="handle_width"
      type="range"
      min="12"
      max="160"
      step="1"
    />
  </div>
  <div data-slider="handle_height" class="ctrl-row">
    <label class="ctrl-top"
      ><span
        class="ctrl-label"
        data-pt="Altura útil da alça"
        data-en="Grip clear height"
        >Altura útil da alça</span
      ><span class="ctrl-val-wrap"
        ><input
          class="ctrl-num"
          data-p="handle_height"
          type="number"
          min="6"
          max="40"
          step="1"
        /><span class="ctrl-unit">mm</span></span
      ></label
    ><input
      class="orca-slider"
      data-param-range="handle_height"
      type="range"
      min="6"
      max="40"
      step="1"
    />
  </div>
  <div data-slider="handle_top_margin" class="ctrl-row">
    <label class="ctrl-top"
      ><span
        class="ctrl-label"
        data-pt="Distância ao topo"
        data-en="Distance from top"
        >Distância ao topo</span
      ><span class="ctrl-val-wrap"
        ><input
          class="ctrl-num"
          data-p="handle_top_margin"
          type="number"
          min="3"
          max="40"
          step="1"
        /><span class="ctrl-unit">mm</span></span
      ></label
    ><input
      class="orca-slider"
      data-param-range="handle_top_margin"
      type="range"
      min="3"
      max="40"
      step="1"
    />
  </div>
</div>
<div id="snap-latch-options" class="ctrl-row box-style-controls" hidden>
  <div data-slider="lid_wall_height" class="ctrl-row">
    <label class="ctrl-top"
      ><span
        class="ctrl-label"
        data-pt="Profundidade de encaixe da tampa"
        data-en="Lid skirt depth"
        >Profundidade de encaixe da tampa</span
      ><span class="ctrl-val-wrap"
        ><input
          class="ctrl-num"
          data-p="lid_wall_height"
          type="number"
          min="3"
          max="25"
          step="1"
        /><span class="ctrl-unit">mm</span></span
      ></label
    ><input
      class="orca-slider"
      data-param-range="lid_wall_height"
      type="range"
      min="3"
      max="25"
      step="1"
    />
  </div>
  <div data-slider="latch_width" class="ctrl-row">
    <label class="ctrl-top"
      ><span class="ctrl-label" data-pt="Largura da trava" data-en="Latch width"
        >Largura da trava</span
      ><span class="ctrl-val-wrap"
        ><input
          class="ctrl-num"
          data-p="latch_width"
          type="number"
          min="8"
          max="30"
          step="1"
        /><span class="ctrl-unit">mm</span></span
      ></label
    ><input
      class="orca-slider"
      data-param-range="latch_width"
      type="range"
      min="8"
      max="30"
      step="1"
    />
  </div>
  <div data-slider="latch_thickness" class="ctrl-row">
    <label class="ctrl-top"
      ><span
        class="ctrl-label"
        data-pt="Espessura do fecho"
        data-en="Latch body thickness"
        >Espessura do fecho</span
      ><span class="ctrl-val-wrap"
        ><input
          class="ctrl-num"
          data-p="latch_thickness"
          type="number"
          min="1.2"
          max="4"
          step="0.1"
        /><span class="ctrl-unit">mm</span></span
      ></label
    ><input
      class="orca-slider"
      data-param-range="latch_thickness"
      type="range"
      min="1.2"
      max="4"
      step="0.1"
    />
  </div>
  <div data-slider="latch_retention" class="ctrl-row">
    <label class="ctrl-top"
      ><span
        class="ctrl-label"
        data-pt="Engate do gancho"
        data-en="Hook engagement"
        >Engate do gancho</span
      ><span class="ctrl-val-wrap"
        ><input
          class="ctrl-num"
          data-p="latch_retention"
          type="number"
          min="0.2"
          max="1.2"
          step="0.05"
        /><span class="ctrl-unit">mm</span></span
      ></label
    ><input
      class="orca-slider"
      data-param-range="latch_retention"
      type="range"
      min="0.2"
      max="1.2"
      step="0.05"
    />
  </div>
  <div data-slider="latch_pivot_diameter" class="ctrl-row">
    <label class="ctrl-top"
      ><span
        class="ctrl-label"
        data-pt="Diâmetro do pivô do fecho"
        data-en="Latch pivot diameter"
        >Diâmetro do pivô do fecho</span
      ><span class="ctrl-val-wrap"
        ><input
          class="ctrl-num"
          data-p="latch_pivot_diameter"
          type="number"
          min="2.4"
          max="4"
          step="0.1"
        /><span class="ctrl-unit">mm</span></span
      ></label
    ><input
      class="orca-slider"
      data-param-range="latch_pivot_diameter"
      type="range"
      min="2.4"
      max="4"
      step="0.1"
    />
  </div>
  <p class="helper-note" data-i18n="twoLatches">
    Duas travas articuladas na base, com pega e gancho. Solte as travas antes de
    retirar a tampa.
  </p>
  <p id="latch-motion-phase" class="helper-note" aria-live="polite" hidden></p>
</div>
<div data-slider="snap_retention" class="ctrl-row">
  <label class="ctrl-top"
    ><span
      class="ctrl-label"
      data-pt="Retenção do encaixe"
      data-en="Snap interference"
      >Retenção do encaixe</span
    ><span class="ctrl-val-wrap"
      ><input
        class="ctrl-num"
        data-p="snap_retention"
        type="number"
        min="0.03"
        max="0.30"
        step="0.01"
      /><span class="ctrl-unit">mm</span></span
    ></label
  ><input
    class="orca-slider"
    data-param-range="snap_retention"
    type="range"
    min="0.03"
    max="0.30"
    step="0.01"
  />
</div>
<div id="stackable-bin-options" class="ctrl-row box-style-controls" hidden>
  <div data-slider="front_access_width" class="ctrl-row">
    <label class="ctrl-top"
      ><span
        class="ctrl-label"
        data-pt="Largura da abertura frontal"
        data-en="Front access width"
        >Largura da abertura frontal</span
      ><span class="ctrl-val-wrap"
        ><input
          class="ctrl-num"
          data-p="front_access_width"
          type="number"
          min="12"
          max="300"
          step="1"
        /><span class="ctrl-unit">mm</span></span
      ></label
    ><input
      class="orca-slider"
      data-param-range="front_access_width"
      type="range"
      min="12"
      max="300"
      step="1"
    />
  </div>
  <div data-slider="front_access_drop" class="ctrl-row">
    <label class="ctrl-top"
      ><span
        class="ctrl-label"
        data-pt="Rebaixo frontal a partir do topo"
        data-en="Front opening drop from top"
        >Rebaixo frontal a partir do topo</span
      ><span class="ctrl-val-wrap"
        ><input
          class="ctrl-num"
          data-p="front_access_drop"
          type="number"
          min="4"
          max="150"
          step="1"
        /><span class="ctrl-unit">mm</span></span
      ></label
    ><input
      class="orca-slider"
      data-param-range="front_access_drop"
      type="range"
      min="4"
      max="150"
      step="1"
    />
  </div>
  <div data-slider="stack_foot_height" class="ctrl-row">
    <label class="ctrl-top"
      ><span
        class="ctrl-label"
        data-pt="Altura do pé de empilhamento"
        data-en="Stacking foot height"
        >Altura do pé de empilhamento</span
      ><span class="ctrl-val-wrap"
        ><input
          class="ctrl-num"
          data-p="stack_foot_height"
          type="number"
          min="1"
          max="5"
          step="0.1"
        /><span class="ctrl-unit">mm</span></span
      ></label
    ><input
      class="orca-slider"
      data-param-range="stack_foot_height"
      type="range"
      min="1"
      max="5"
      step="0.1"
    />
  </div>
  <div data-slider="stack_clearance" class="ctrl-row">
    <label class="ctrl-top"
      ><span
        class="ctrl-label"
        data-pt="Folga por lado para empilhar"
        data-en="Stacking clearance per side"
        >Folga por lado para empilhar</span
      ><span class="ctrl-val-wrap"
        ><input
          class="ctrl-num"
          data-p="stack_clearance"
          type="number"
          min="0.1"
          max="0.8"
          step="0.05"
        /><span class="ctrl-unit">mm</span></span
      ></label
    ><input
      class="orca-slider"
      data-param-range="stack_clearance"
      type="range"
      min="0.1"
      max="0.8"
      step="0.05"
    />
  </div>
  <p class="helper-note" data-i18n="stackingFamily">
    A altura total inclui o pé. Para empilhar alturas diferentes, mantenha as
    dimensões X/Y, cantos, paredes e encaixes iguais.
  </p>
</div>
<div id="clamshell-pip-options" class="ctrl-row box-style-controls" hidden>
  <div data-slider="pip_clearance" class="ctrl-row">
    <label class="ctrl-top"
      ><span
        class="ctrl-label"
        data-pt="Folga da dobradiça PIP"
        data-en="PIP hinge clearance"
        >Folga da dobradiça PIP</span
      ><span class="ctrl-val-wrap"
        ><input
          class="ctrl-num"
          data-p="pip_clearance"
          type="number"
          min="0.2"
          max="0.6"
          step="0.05"
        /><span class="ctrl-unit">mm</span></span
      ></label
    ><input
      class="orca-slider"
      data-param-range="pip_clearance"
      type="range"
      min="0.2"
      max="0.6"
      step="0.05"
    />
  </div>
  <div data-slider="hinge_separation" class="ctrl-row">
    <label class="ctrl-top"
      ><span
        class="ctrl-label"
        data-pt="Afastamento da articulação"
        data-en="Hinge separation"
        >Afastamento da articulação</span
      ><span class="ctrl-val-wrap"
        ><input
          class="ctrl-num"
          data-p="hinge_separation"
          type="number"
          min="4"
          max="12"
          step="0.5"
        /><span class="ctrl-unit">mm</span></span
      ></label
    ><input
      class="orca-slider"
      data-param-range="hinge_separation"
      type="range"
      min="4"
      max="12"
      step="0.5"
    />
  </div>
  <p id="clamshell-closed-height" class="helper-note"></p>
  <p
    id="clamshell-feature-warning"
    class="helper-note warn"
    data-i18n="clamshellFeatures"
    hidden
  >
    Remova acessórios incompatíveis.
  </p>
</div>
<p id="pipNote" class="helper-note warn"></p>
            </div>
            <div id="card-gardening" class="studio-card">
              <div class="card-head">
                <span class="card-title" data-i18n="manufacture"
                  >manufacture</span
                >
              </div>
              <div class="switch-row">
                <span class="ctrl-label" data-i18n="enableGasket"
                  >enableGasket</span
                ><label class="toggle-switch"
                  ><input id="gasket_enabled" type="checkbox" /><span
                    class="toggle-track"
                  ></span
                ></label>
              </div>
              <div data-slider="gasket_width" class="ctrl-row">
                <label class="ctrl-top"
                  ><span
                    class="ctrl-label"
                    data-pt="Largura do canal TPU"
                    data-en="TPU channel width"
                    >Largura do canal TPU</span
                  ><span class="ctrl-val-wrap"
                    ><input
                      class="ctrl-num"
                      data-p="gasket_width"
                      type="number"
                      min="0.6"
                      max="2"
                      step="0.1"
                    /><span class="ctrl-unit">mm</span></span
                  ></label
                ><input
                  class="orca-slider"
                  data-param-range="gasket_width"
                  type="range"
                  min="0.6"
                  max="2"
                  step="0.1"
                />
              </div>
              <div data-slider="gasket_depth" class="ctrl-row">
                <label class="ctrl-top"
                  ><span
                    class="ctrl-label"
                    data-pt="Profundidade do canal"
                    data-en="Channel depth"
                    >Profundidade do canal</span
                  ><span class="ctrl-val-wrap"
                    ><input
                      class="ctrl-num"
                      data-p="gasket_depth"
                      type="number"
                      min="0.5"
                      max="2"
                      step="0.1"
                    /><span class="ctrl-unit">mm</span></span
                  ></label
                ><input
                  class="orca-slider"
                  data-param-range="gasket_depth"
                  type="range"
                  min="0.5"
                  max="2"
                  step="0.1"
                />
              </div>
              <div class="switch-row">
                <span class="ctrl-label" data-i18n="auto">auto</span
                ><label class="toggle-switch"
                  ><input id="auto_configure_slicer" type="checkbox" /><span
                    class="toggle-track"
                  ></span
                ></label>
              </div>
              <label class="ctrl-row"
                ><span class="ctrl-label" data-i18n="manufacture"
                  >manufacture</span
                ><select id="target" class="vp-select box-select">
                  <option value="base_and_lid">base_and_lid</option>
                  <option value="base_only">base_only</option>
                  <option value="lid_only">lid_only</option>
                  <option value="gasket">gasket</option>
                  <option value="fit_test_kit">fit_test_kit</option>
                  <option value="full_suite">full_suite</option>
                </select></label
              >
              <p class="helper-note" data-i18n="printHelp"></p>
            </div>
          </div>
          <!-- Wide Mode Sticky Action Footer -->
          <footer class="action-footer">
            <button class="btn-hero" id="send" data-action="send_to_plater">
              <span>🚀</span>
              <span data-i18n="btn_send_plater"
                >Enviar para a Mesa do OrcaSlicer</span
              >
            </button>
            <div class="export-btn-row">
              <button class="btn" id="mf" data-action="export_3mf">
                💾 <span data-i18n="btn_exp_3mf">Exportar .3MF</span>
              </button>
              <button class="btn" id="stl" data-action="export_stl">
                📐 <span data-i18n="btn_exp_stl">Exportar .STL</span>
              </button>
              <button
                class="btn btn-icon"
                id="folder"
                data-action="open_folder"
                title="Open Exports Folder"
              >
                📂
              </button>
            </div>
          </footer>
        </section>
      </main>
      <!-- Compact Dock Mode Sticky Footer -->
      <footer class="action-footer dock-global-footer">
        <button
          class="btn-hero job"
          data-action="send_to_plater"
          style="padding: 8px 10px; font-size: 12px"
        >
          <span>🚀</span>
          <span data-i18n="btn_send_plater"
            >Enviar para a Mesa do OrcaSlicer</span
          >
        </button>
        <div class="export-btn-row">
          <button class="btn job" data-action="export_3mf">💾 .3MF</button>
          <button class="btn job" data-action="export_stl">📐 .STL</button>
          <button
            class="btn btn-icon"
            data-action="open_folder"
            title="Open Exports Folder"
          >
            📂
          </button>
        </div>
      </footer>
    </div>
    <div
      id="toast-banner"
      class="toast-banner"
      role="status"
      aria-live="polite"
    ></div>
    <script>
const INITIAL = __BOX_CONTEXT__;
(() => {
  "use strict";
  const $ = (id) =>
      document.getElementById(
        {
          gl: "gl-canvas",
          presets: "presets-grid",
          printer: "printer-pill-name",
          plan: "curve-canvas",
        }[id] || id,
      ),
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
    localDirty = false,
    meshParams = clone(INITIAL.params),
    meshRevisionKey = null,
    openingStyle = null,
    lastInterfaceError = null,
    statusTranslationKey = null,
    timer = null,
    playing = false,
    angle = 25,
    drag = null;
  let userOverrodeTheme = false;
  let hostThemeExplicit =
    INITIAL.theme_explicit ?? INITIAL.host?.theme_explicit ?? true;
  function detectInjectedOrcaTheme() {
    if (
      typeof window === "undefined" ||
      typeof window.getComputedStyle !== "function"
    )
      return null;
    if (typeof document === "undefined" || !document.documentElement)
      return null;
    try {
      const style = window.getComputedStyle(document.documentElement);
      if (!style || typeof style.getPropertyValue !== "function") return null;
      const raw = String(style.getPropertyValue("--orca-bg") || "").trim();
      if (!raw) return null;
      let r = NaN,
        g = NaN,
        b = NaN;
      if (raw[0] === "#") {
        const hex = raw.slice(1).trim();
        if (hex.length === 3) {
          r = parseInt(hex[0] + hex[0], 16);
          g = parseInt(hex[1] + hex[1], 16);
          b = parseInt(hex[2] + hex[2], 16);
        } else if (hex.length >= 6) {
          r = parseInt(hex.slice(0, 2), 16);
          g = parseInt(hex.slice(2, 4), 16);
          b = parseInt(hex.slice(4, 6), 16);
        }
      } else {
        const m = raw.match(
          /rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)/i,
        );
        if (m) {
          r = parseFloat(m[1]);
          g = parseFloat(m[2]);
          b = parseFloat(m[3]);
        }
      }
      if (!Number.isFinite(r) || !Number.isFinite(g) || !Number.isFinite(b))
        return null;
      const lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0;
      return lum > 0.52 ? "light" : "dark";
    } catch (_) {
      return null;
    }
  }

  function resolveHostTheme(message = {}) {
    if (typeof message.theme_explicit === "boolean")
      hostThemeExplicit = message.theme_explicit;
    else if (typeof message.host?.theme_explicit === "boolean")
      hostThemeExplicit = message.host.theme_explicit;
    if (userOverrodeTheme) return;
    const injected =
      hostThemeExplicit === false ? detectInjectedOrcaTheme() : null;
    const resolved = injected || message.theme || message.host?.theme;
    if ((resolved === "light" || resolved === "dark") && resolved !== theme) {
      theme = resolved;
      translate();
    }
  }
  function watchHostTheme() {
    if (typeof MutationObserver !== "function") return;
    const apply = () => resolveHostTheme();
    const rootObserver = new MutationObserver(apply);
    rootObserver.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-orca-theme"],
    });
    if (document.head) {
      const styleObserver = new MutationObserver(apply);
      styleObserver.observe(document.head, {
        childList: true,
        subtree: true,
        characterData: true,
      });
    }
  }

  const texts = {
    pt: {
      shape: "Caixa",
      features: "Acessórios",
      presets: "Presets",
      construction: "Construção",
      style: "Estilo de caixa",
      openBin: "Caixa aberta",
      snapLatch: "Tampa com travas",
      stackableBin: "Caixa empilhável",
      clamshellPip: "Estojo articulado PIP",
      hingedAssembly: "Conjunto articulado",
      equalHalfNote:
        "Metades iguais · altura fechada: {height} mm. O conjunto é impresso aberto a 180°.",
      clamshellPrintBounds: "Na mesa, aberto: {size} mm.",
      clamshellFeatures:
        "Remova torres, recortes, divisórias e TPU existentes para usar este estilo.",
      stackingFamily:
        "A altura total inclui o pé. Para empilhar alturas diferentes, mantenha as dimensões X/Y, cantos, paredes e encaixes iguais.",
      connections: "Encaixes & alças",
      handles: "Alças de mão",
      handleFaces: "Par de faces",
      leftRight: "Esquerda / direita",
      frontBack: "Frente / trás",
      twoLatches:
        "Duas travas articuladas na base, com pega e gancho. Solte as travas antes de retirar a tampa.",
      releaseAndOpen: "Soltar fechos e abrir",
      releaseClipsAndOpen: "Retirar presilhas e abrir",
      ruggedClosed: "Presilhas instaladas · tampa fechada",
      ruggedReleasing: "Retirando presilhas · tampa parada",
      ruggedOpening: "Presilhas retiradas · abrindo a tampa",
      ruggedOpen: "Presilhas retiradas · tampa aberta",
      latchesEngaged: "Fechos presos · tampa fechada",
      releasingLatches: "Soltando os fechos · tampa parada",
      liftingLid: "Fechos abertos · afastando a tampa",
      lidRemoved: "Fechos abertos · tampa afastada",
      latchMotionUnavailable:
        "Movimento dos fechos indisponível. Gere a prévia novamente.",
      width: "Largura X",
      depth: "Profundidade Y",
      height: "Altura da base Z",
      radius: "Raio de canto",
      wall: "Parede",
      floor: "Fundo",
      lid: "Espessura tampa",
      clearance: "Folga por lado",
      hingeClearance: "Folga da dobradiça",
      lip: "Profundidade de encaixe",
      hinge: "Dobradiça",
      pin: "Diâmetro do pino",
      screw: "Parafuso de canto",
      quality: "Resolução da superfície",
      qualityStandard: "Padrão",
      qualityFine: "Fina",
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
        "Base com fundo na mesa; preserve a orientação exportada das peças. Imprima o kit de encaixe antes da peça final. Tempo depende da impressora e do perfil.",
      printHelpClamshell:
        "Base e tampa com a mesma altura. Exporte o conjunto articulado aberto a 180°, com as duas faces externas apoiadas na mesa. Preserve essa posição no fatiador e teste a articulação impressa.",
      printHelpOpen:
        "Base com fundo na mesa e abertura para cima. Confira as paredes e as pontes das alças, quando ativadas, na prévia do fatiador.",
      printHelpStack:
        "Imprima com o pé apoiado na mesa e a frente aberta. A altura total inclui o pé. Teste o encaixe entre peças da mesma família antes de empilhar.",
      printHelpLatch:
        "Conjunto: base, tampa e duas travas. Imprima base e tampa pelas faces externas, e as travas em pé. Monte as travas nos pivôs da base; solte os ganchos antes de retirar a tampa. Teste o encaixe das peças impressas.",
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
      openBin: "Open bin",
      snapLatch: "Latch lid",
      stackableBin: "Stackable bin",
      clamshellPip: "PIP clamshell",
      hingedAssembly: "Hinged assembly",
      equalHalfNote:
        "Equal halves · closed height: {height} mm. The assembly prints open at 180°.",
      clamshellPrintBounds: "Open footprint on the bed: {size} mm.",
      clamshellFeatures:
        "Remove existing standoffs, cutouts, dividers and TPU features to use this style.",
      stackingFamily:
        "Total height includes the foot. To stack different heights, keep X/Y dimensions, corners, walls and mating features identical.",
      connections: "Connections & grips",
      handles: "Hand grips",
      handleFaces: "Pair of faces",
      leftRight: "Left / right",
      frontBack: "Front / back",
      twoLatches:
        "Two latches pivot on the base, each with a grip and hook. Release them before lifting off the lid.",
      releaseAndOpen: "Release latches & open",
      releaseClipsAndOpen: "Remove clips & open",
      ruggedClosed: "Clips installed · lid closed",
      ruggedReleasing: "Removing clips · lid stationary",
      ruggedOpening: "Clips removed · opening the lid",
      ruggedOpen: "Clips removed · lid open",
      latchesEngaged: "Latches engaged · lid closed",
      releasingLatches: "Releasing latches · lid stationary",
      liftingLid: "Latches open · lifting the lid",
      lidRemoved: "Latches open · lid removed",
      latchMotionUnavailable:
        "Latch motion unavailable. Regenerate the preview.",
      width: "Width X",
      depth: "Depth Y",
      height: "Base height Z",
      radius: "Corner radius",
      wall: "Wall",
      floor: "Floor",
      lid: "Lid thickness",
      clearance: "Clearance per side",
      hingeClearance: "Hinge clearance",
      lip: "Locating skirt depth",
      hinge: "Hinge",
      pin: "Pin diameter",
      screw: "Corner screw",
      quality: "Surface resolution",
      qualityStandard: "Standard",
      qualityFine: "Fine",
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
        "Base on its floor; preserve the exported orientation of each part. Print the fit kit first. Print time depends on printer and profile.",
      printHelpClamshell:
        "Base and lid have equal height. Export the hinged assembly open at 180°, both outer faces on the bed. Keep that pose in the slicer and check the printed hinge.",
      printHelpOpen:
        "Base floor down, opening upwards. Check the walls and the bridges above hand grips, when enabled, in the slicer preview.",
      printHelpStack:
        "Print with the foot on the bed and the front open. Total height includes the foot. Test the fit between bins of the same family before stacking.",
      printHelpLatch:
        "Set: base, lid and two latches. Print the shells on their outer faces and the latches upright. Fit the latches onto the base pivots; release the hooks before lifting the lid. Check the fit of the printed parts.",
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
  function status(s, error = false, translationKey = null) {
    statusTranslationKey = translationKey;
    $("status").textContent = s;
    $("status").classList.toggle("warn", error);
    const banner = $("toast-banner");
    banner.textContent = s;
    banner.classList.add("visible");
    banner.classList.toggle("error", error);
    clearTimeout(status.timer);
    status.timer = setTimeout(
      () => banner.classList.remove("visible"),
      error ? 6000 : 2500,
    );
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
  function updatePrintHelp() {
    const key =
      {
        open_bin: "printHelpOpen",
        stackable_bin: "printHelpStack",
        snap_latch: "printHelpLatch",
        clamshell_pip: "printHelpClamshell",
      }[p.style] || "printHelp";
    document.querySelector('[data-i18n="printHelp"]').textContent = tr(key);
  }
  function updateClamshellNote() {
    let note = tr("equalHalfNote").replace(
      "{height}",
      (2 * Number(p.height_z) + Number(p.fit_clearance)).toFixed(2),
    );
    if (
      !localDirty &&
      meshParams.style === "clamshell_pip" &&
      INITIAL.print_bounds?.size
    ) {
      note +=
        " " +
        tr("clamshellPrintBounds").replace(
          "{size}",
          INITIAL.print_bounds.size
            .map((value) => Number(value).toFixed(1))
            .join("×"),
        );
    }
    $("clamshell-closed-height").textContent = note;
  }
  function updateClearanceLabels() {
    const clamshell = p.style === "clamshell_pip";
    const label = document.querySelector(
      '[data-slider="fit_clearance"] .ctrl-label',
    );
    label.dataset.pt = clamshell ? "Folga entre metades Z" : "Folga por lado";
    label.dataset.en = clamshell
      ? "Gap between halves Z"
      : "Clearance per side";
    label.textContent = label.dataset[lang];
    document.querySelector('[data-i18n="hud_mouth_hole"]').textContent = tr(
      clamshell ? "hingeClearance" : "clearance",
    );
    $("hud-clearance").textContent =
      Number(clamshell ? p.pip_clearance : p.fit_clearance).toFixed(2) + " mm";
  }
  function updateOpeningCaption() {
    document.querySelector('[data-i18n="open"]').textContent = tr(
      p.style === "snap_latch" ? "releaseAndOpen" : p.style === "rugged_box" ? "releaseClipsAndOpen" : "open",
    );
  }
  function updatePreviewText() {
    if (Number.isFinite(lastInterfaceError)) {
      $("surface").textContent =
        (lang === "pt" ? "Alvo de erro nas interfaces curvas ≤ " : "Curved interface chord-error target ≤ ") +
        lastInterfaceError.toFixed(3) + " mm";
    }
    if (statusTranslationKey === "ready") {
      $("status").textContent = tr("ready");
      $("toast-banner").textContent = tr("ready");
    }
  }
  function translate() {
    p.theme = theme;
    p.lang = lang;
    document.documentElement.lang = lang;
    document.documentElement.dataset.theme = theme;
    $("lang").textContent = lang.toUpperCase();
    $("theme").textContent = theme === "dark" ? "☾" : "☀";
    document
      .querySelectorAll("[data-i18n]")
      .forEach((e) => (e.textContent = tr(e.dataset.i18n)));
    document
      .querySelectorAll("[data-pt]")
      .forEach((e) => (e.textContent = e.dataset[lang]));
    updatePreviewText();
    updateClearanceLabels();
    updateOpeningCaption();
    updatePrintHelp();
    updateClamshellNote();
    if (p.style === "rugged_box") updateRuggedMotionStatus();
    const names = {
      base_and_lid: tr("both"),
      base_only: tr("baseOnly"),
      lid_only: tr("lidOnly"),
      gasket: tr("gasketOnly"),
      fit_test_kit: tr("kit"),
      full_suite: tr("full"),
    };
    for (const option of $("target").options)
      option.textContent = names[option.value] || option.value;
    presets();
    syncPresetSelection();
    features();
    drawPlan();
    render();
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
    updateClearanceLabels();
    updateOpeningCaption();
    updatePrintHelp();
    const openBin = p.style === "open_bin";
    const lidless = openBin || p.style === "stackable_bin";
    const heightLabel = document.querySelector(
      '[data-slider="height_z"] .ctrl-label',
    );
    heightLabel.dataset.pt =
      p.style === "clamshell_pip"
        ? "Altura de cada metade Z"
        : p.style === "stackable_bin"
          ? "Altura total Z"
          : "Altura Z";
    heightLabel.dataset.en =
      p.style === "clamshell_pip"
        ? "Height of each half Z"
        : p.style === "stackable_bin"
          ? "Total height Z"
          : "Height Z";
    heightLabel.textContent = heightLabel.dataset[lang];
    document.querySelector('[data-slider="snap_retention"]').style.display =
      p.style === "lip_snap" ? "grid" : "none";
    $("open-bin-handles").hidden = !openBin;
    $("snap-latch-options").hidden = p.style !== "snap_latch";
    $("stackable-bin-options").hidden = p.style !== "stackable_bin";
    const clamshell = p.style === "clamshell_pip";
    $("clamshell-pip-options").hidden = !clamshell;
    updateClamshellNote();
    $("clamshell-feature-warning").hidden =
      !clamshell ||
      !(
        ["standoffs", "cutouts", "dividers_x", "dividers_y"].some(
          (key) => p[key]?.length,
        ) || p.gasket_enabled
      );
    $("addPost").disabled = clamshell;
    $("addPort").disabled = clamshell;
    const diameterRow = document.querySelector(
      '[data-slider="hinge_pin_diameter"]',
    );
    diameterRow.style.display = ["rugged_box", "clamshell_pip"].includes(
      p.style,
    )
      ? "grid"
      : "none";
    const diameterLabel = diameterRow.querySelector(".ctrl-label");
    diameterLabel.dataset.pt = clamshell
      ? "Diâmetro do eixo integral"
      : "Diâmetro do pino";
    diameterLabel.dataset.en = clamshell
      ? "Integral axle diameter"
      : "Pin diameter";
    diameterLabel.textContent = diameterLabel.dataset[lang];
    $("open").disabled = lidless || INITIAL.preview_mode === "calibration";
    $("play").disabled = lidless || INITIAL.preview_mode === "calibration";
    for (const key of ["lid_height", "lip_depth", "fit_clearance"]) {
      const row = document.querySelector('[data-slider="' + key + '"]');
      row.style.display =
        lidless ||
        (p.style === "sliding_lid" && key !== "fit_clearance") ||
        (p.style === "snap_latch" && key === "lip_depth") ||
        (p.style === "clamshell_pip" && key !== "fit_clearance")
          ? "none"
          : "grid";
    }
    $("gasket_enabled").closest(".switch-row").style.display =
      (lidless || clamshell || p.style === "sliding_lid") && !p.gasket_enabled ? "none" : "flex";
    for (const key of ["gasket_width", "gasket_depth"])
      document.querySelector('[data-slider="' + key + '"]').style.display =
        lidless || ["clamshell_pip", "sliding_lid"].includes(p.style) ? "none" : "grid";
    for (const option of $("target").options) {
      option.disabled =
        (lidless &&
          ["lid_only", "gasket", "fit_test_kit"].includes(option.value)) ||
        (p.style === "snap_latch" && option.value === "fit_test_kit") ||
        (p.style === "clamshell_pip" &&
          !["base_and_lid", "full_suite"].includes(option.value)) ||
        (p.style === "rugged_box" && p.hinge_mode === "print_in_place" &&
          ["base_only", "lid_only"].includes(option.value)) ||
        (option.value === "gasket" && (!p.gasket_enabled || p.style === "sliding_lid"));
      if (option.value === "base_and_lid")
        option.textContent =
          p.style === "clamshell_pip"
            ? tr("hingedAssembly")
            : lidless
              ? tr("baseOnly")
              : tr("both");
    }
    if ([...$("target").options].some(option => option.value === p.export_target && option.disabled))
      p.export_target = "base_and_lid";
    $("name").value = p.name;
    document
      .querySelectorAll("[data-p]")
      .forEach((e) => (e.value = p[e.dataset.p]));
    for (const key of [
      "style",
      "hinge_mode",
      "screw_size",
      "quality",
      "handle_faces",
    ])
      $(key).value = p[key];
    for (const key of [
      "gasket_enabled",
      "auto_configure_slicer",
      "handles_enabled",
    ])
      $(key).checked = p[key];
    $("dividers_x").value = p.dividers_x.join(", ");
    $("dividers_y").value = p.dividers_y.join(", ");
    $("target").value = p.export_target;
    document
      .querySelectorAll(".rugged")
      .forEach(
        (e) => (e.style.display = p.style === "rugged_box" ? "grid" : "none"),
      );
    document
      .querySelectorAll(".screw")
      .forEach(
        (e) => (e.style.display = p.style === "screw_corner" ? "grid" : "none"),
      );
    $("pipNote").textContent =
      p.style === "rugged_box" && p.hinge_mode === "print_in_place"
        ? tr("pip")
        : "";
    document
      .querySelectorAll("[data-param-range]")
      .forEach((e) => (e.value = p[e.dataset.paramRange]));
    syncPresetSelection();
    features();
    drawPlan();
    buttons();
    render();
  }
  function requestPreview(commit = true) {
    clearTimeout(timer);
    localDirty = true;
    const request_id = ++serial;
    latest = request_id;
    if (!commit) return;
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
    if (
      key === "style" &&
      ((["open_bin", "stackable_bin"].includes(value) &&
        ["lid_only", "gasket", "fit_test_kit"].includes(p.export_target)) ||
        (value === "snap_latch" && p.export_target === "fit_test_kit") ||
        (value === "clamshell_pip" &&
          !["base_and_lid", "full_suite"].includes(p.export_target)))
    )
      p.export_target = "base_and_lid";
    sync();
    requestPreview();
  }
  document
    .querySelectorAll("[data-p]")
    .forEach((e) =>
      e.addEventListener("change", () => change(e.dataset.p, Number(e.value))),
    );
  document
    .querySelectorAll("[data-p],#name,#dividers_x,#dividers_y")
    .forEach((element) =>
      element.addEventListener("input", () => requestPreview(false)),
    );
  for (const key of [
    "style",
    "hinge_mode",
    "screw_size",
    "quality",
    "handle_faces",
  ])
    $(key).onchange = () => change(key, $(key).value);
  for (const key of [
    "gasket_enabled",
    "auto_configure_slicer",
    "handles_enabled",
  ])
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
    userOverrodeTheme = true;
    theme = theme === "dark" ? "light" : "dark";
    translate();
  };
  $("sync").onclick = () => send({ type: "sync_printer" });
  $("folder").onclick = () => send({ type: "open_exports_folder" });
  document.addEventListener("keydown", (e) => {
    const tag =
      e.target && e.target.tagName
        ? String(e.target.tagName).toUpperCase()
        : "";
    if (tag === "INPUT" || tag === "TEXTAREA" || e.target?.isContentEditable)
      return;
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
      e.preventDefault();
      (e.shiftKey ? $("redo") : $("undo")).click();
    } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "y") {
      e.preventDefault();
      $("redo").click();
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
            x.classList.toggle("section-hidden", x.dataset.section !== tab),
          );
        drawPlan();
      }),
  );
  $("savePreset").onclick = () =>
    send({ type: "save_preset", params: p, name: p.name });
  function fieldInput(label, value, onchange, step = ".1") {
    const lab = document.createElement("label");
    lab.className = "ctrl-row";
    const span = document.createElement("span");
    span.textContent = label;
    const inp = document.createElement("input");
    inp.className = "ctrl-num";
    span.className = "ctrl-label";
    inp.type = "number";
    inp.step = step;
    inp.value = value;
    inp.onchange = () => onchange(Number(inp.value));
    lab.append(span, inp);
    return lab;
  }
  function selectInput(label, value, values, onchange) {
    const lab = document.createElement("label");
    lab.className = "ctrl-row";
    const span = document.createElement("span");
    span.textContent = label;
    const sel = document.createElement("select");
    sel.className = "vp-select box-select";
    span.className = "ctrl-label";
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
      card.className = "box-feature";
      const head = document.createElement("div");
      head.className = "box-feature-title";
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
        row.className = "box-pair";
        row.append(
          fieldInput(a, s[ka], (v) => featureChange("standoffs", i, ka, v)),
          fieldInput(b, s[kb], (v) => featureChange("standoffs", i, kb, v)),
        );
        card.append(row);
      });
      const row = document.createElement("div");
      row.className = "box-pair";
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
      card.className = "box-feature";
      const head = document.createElement("div");
      head.className = "box-feature-title";
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
      row.className = "box-pair";
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
        r.className = "box-pair";
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
    const rounded = (x, y, width, height, radius) => {
      c.beginPath();
      if (typeof c.roundRect === "function")
        c.roundRect(x, y, width, height, radius);
      else c.rect(x, y, width, height);
    };
    rounded(
      cx - (p.width_x * s) / 2,
      cy - (p.depth_y * s) / 2,
      p.width_x * s,
      p.depth_y * s,
      p.corner_radius * s,
    );
    c.fillStyle =
      theme === "dark" ? "rgba(0,168,150,.18)" : "rgba(0,137,123,.12)";
    c.fill();
    c.strokeStyle = theme === "dark" ? "#00bfa5" : "#00897b";
    c.lineWidth = 2;
    c.stroke();
    rounded(
      cx - (p.width_x / 2 - p.wall_thickness) * s,
      cy - (p.depth_y / 2 - p.wall_thickness) * s,
      (p.width_x - 2 * p.wall_thickness) * s,
      (p.depth_y - 2 * p.wall_thickness) * s,
      Math.max(0, p.corner_radius - p.wall_thickness) * s,
    );
    c.fillStyle = theme === "dark" ? "#17191e" : "#ffffff";
    c.fill();
    c.lineWidth = 1;
    c.stroke();
    c.strokeStyle = theme === "dark" ? "#36444f" : "#cad5dc";
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
    requestPreview(false);
    const r = $("plan").getBoundingClientRect(),
      s = Math.min(455 / p.width_x, 285 / p.depth_y);
    p.standoffs[drag].x =
      Math.round(((((e.clientX - r.left) * 500) / r.width - 250) / s) * 10) /
      10;
    p.standoffs[drag].y =
      Math.round(((165 - ((e.clientY - r.top) * 330) / r.height) / s) * 10) /
      10;
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
    document.querySelectorAll("[data-action]").forEach((b) => {
      if (b.dataset.action !== "open_folder") b.disabled = on;
    });
  }
  function manufacture(type, format) {
    p.export_target = $("target").value;
    p.lang = lang;
    busy(true);
    status(tr("generating"));
    if (!send({ type, format, params: p, export_target: p.export_target })) {
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
    if (m.type === "randomize_result") {
      if (m.ok) setDesign(m.params);
      else status(m.message, true);
      return;
    }
    if (m.type === "design_changed") {
      if (localDirty) return;
      p = clone(m.params);
      sync();
      requestPreview();
      return;
    }
    if (m.type === "init_state") {
      if (m.host) {
        INITIAL.host = m.host;
        updatePrinter();
      }
      resolveHostTheme(m);
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
      if (
        m.params?.style === "snap_latch" &&
        (!m.latch_motion?.clip_left || !m.latch_motion?.clip_right)
      ) {
        status(tr("latchMotionUnavailable"), true);
        return;
      }
      if (m.params?.style === "snap_latch") {
        try {
          for (const part of ["clip_left", "clip_right", "lid"])
            snapLatchTransform(part, 0, m.latch_motion);
        } catch (_) {
          status(tr("latchMotionUnavailable"), true);
          return;
        }
      }
      localDirty = false;
      p = clone(m.params);
      p.lang = lang;
      p.theme = theme;
      meshParams = clone(m.params);
      INITIAL.hinge = m.hinge;
      INITIAL.print_bounds = m.print_bounds || null;
      INITIAL.latch_motion = m.latch_motion || null;
      INITIAL.preview_mode = m.preview_mode || "assembly";
      if (!m.geometry_key || m.geometry_key !== meshRevisionKey) {
        loadMeshes(m.meshes);
        meshRevisionKey = m.geometry_key || null;
      }
      $("volume").textContent = m.volume_cm3.toFixed(1);
      $("triangles").textContent =
        (m.meshes.reduce((s, x) => s + x.triangle_count, 0) / 1000).toFixed(0) +
        "k";
      lastInterfaceError = Math.max(...m.meshes.map((x) => x.interface_error_mm));
      updatePreviewText();
      status(tr("ready"), false, "ready");
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
  // Canonical material, three-light shader, bed grid and CAD annotation styling
  // adapted from the MIT Orca Studio reference. Geometry always comes from Python.
  let gl = $("gl").getContext("webgl2", {
      antialias: true,
      alpha: false,
      depth: true,
    }),
    program = null,
    lineProg = null,
    bedBuffer = null,
    bedVertCount = 0,
    yaw = -0.75,
    pitch = 0.68,
    zoom = 1,
    orbit = null,
    material = "emerald_silk",
    wire = false,
    calipers = false,
    spin = false,
    cutAxis = "y",
    lastFrame = null;
  const TWO_PI = Math.PI * 2;
  const MATERIAL_PRESETS = {
    emerald_silk: {
      base: [0.02, 0.72, 0.63],
      saucer: [0.14, 0.24, 0.25],
      rough: 0.22,
      metal: 0.3,
    },
    terracotta: {
      base: [0.79, 0.4, 0.28],
      saucer: [0.68, 0.34, 0.24],
      rough: 0.78,
      metal: 0.02,
    },
    matte_ceramic: {
      base: [0.91, 0.9, 0.87],
      saucer: [0.8, 0.78, 0.74],
      rough: 0.66,
      metal: 0.02,
    },
    copper_bronze: {
      base: [0.76, 0.48, 0.31],
      saucer: [0.36, 0.25, 0.2],
      rough: 0.26,
      metal: 0.72,
    },
    xray: {
      base: [0.04, 0.8, 0.72],
      saucer: [0.16, 0.48, 0.52],
      rough: 0.18,
      metal: 0.15,
    },
    heatmap: {
      base: [0.05, 0.76, 0.45],
      saucer: [0.05, 0.76, 0.45],
      rough: 0.55,
      metal: 0.05,
    },
  };
  function shader(type, source) {
    const s = gl.createShader(type);
    gl.shaderSource(s, source);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS))
      throw Error(gl.getShaderInfoLog(s));
    return s;
  }
  function compileProgram(vs, fs) {
    const p = gl.createProgram();
    gl.attachShader(p, shader(gl.VERTEX_SHADER, vs));
    gl.attachShader(p, shader(gl.FRAGMENT_SHADER, fs));
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS))
      throw Error(gl.getProgramInfoLog(p));
    return p;
  }
  function initializeGL() {
    if (!gl) {
      status("WebGL2 indisponível / unavailable", true);
      return;
    }
    program = compileProgram(
      `#version 300 es
 precision highp float;layout(location=0)in vec3 a_pos;layout(location=1)in vec3 a_nrm;layout(location=2)in float a_role;
 uniform mat4 u_mvp;uniform mat4 u_model;out vec3 v_pos;out vec3 v_localPos;out vec3 v_nrm;out float v_ovh;out float v_part;out float v_surfaceRole;
 void main(){vec4 w=u_model*vec4(a_pos,1.0);v_pos=w.xyz;v_localPos=a_pos;v_nrm=mat3(u_model)*a_nrm;v_ovh=degrees(asin(clamp(-normalize(v_nrm).z,0.0,1.0)));v_part=0.0;v_surfaceRole=a_role;gl_Position=u_mvp*w;}`,
      `#version 300 es
      precision highp float;
      in vec3 v_pos;
      in vec3 v_localPos;
      in vec3 v_nrm;
      in float v_ovh;
      in float v_part;
      in float v_surfaceRole;
      uniform vec3 u_eye;
      uniform mat4 u_model;
      uniform vec3 u_baseColor;
      uniform vec3 u_saucerColor;
      uniform float u_roughness;
      uniform float u_metallic;
      uniform float u_heatmap;
      uniform float u_xrayMode;
      uniform float u_clipMode;
      uniform float u_clipVal;
      uniform float u_passMode;
      uniform float u_lightTheme;
      out vec4 outColor;

      vec3 heatmapColor(float deg) {
        vec3 safeA = vec3(0.02, 0.76, 0.45);
        vec3 safeB = vec3(0.18, 0.85, 0.42);
        vec3 warn  = vec3(1.00, 0.68, 0.02);
        vec3 crit  = vec3(0.98, 0.20, 0.16);
        if (deg <= 42.0) return mix(safeA, safeB, clamp(deg / 42.0, 0.0, 1.0));
        if (deg <= 46.0) return mix(safeB, warn, (deg - 42.0) / 4.0);
        if (deg <= 55.0) return mix(warn, crit, (deg - 46.0) / 9.0);
        return crit;
      }

      void main() {
        // Derivatives precede clipping/discard so every fragment quad is defined.
        vec3 faceCross = cross(dFdx(v_localPos), dFdy(v_localPos));
        vec3 localFace = faceCross / max(length(faceCross), 1e-12);
        float clipRim = 0.0;
        if (u_clipMode > 0.5 && u_passMode < 0.5) {
          float dist = (u_clipMode < 1.5) ? (v_pos.y - u_clipVal) : (u_clipVal - v_pos.z);
          if (dist < 0.0) {
            discard;
          }
          if (dist < 1.45) {
            clipRim = 1.0 - (dist / 1.45);
          }
        } else if (u_clipMode > 0.5 && u_clipMode < 1.5 && u_passMode > 1.5) {
          if (v_pos.y < u_clipVal) discard;
        }

        // Special Pass 1: Solid Horizontal Z-Slice CAD Cross-Section Cap
        if (u_passMode > 0.5 && u_passMode < 1.5) {
          float hatch = sin((v_pos.x + v_pos.y) * 2.35);
          vec3 capA = vec3(1.00, 0.76, 0.20);
          vec3 capB = vec3(0.08, 0.92, 0.80);
          vec3 cCol = mix(capA, capB, hatch > 0.25 ? 0.65 : 0.12);
          outColor = vec4(cCol, u_xrayMode > 0.5 ? 0.90 : 1.0);
          return;
        }

        // Special Pass 2: Holographic Spiral Mode Top-Cap Indicator Disk
        if (u_passMode > 1.5) {
          float r = length(v_pos.xy);
          float rings = 0.5 + 0.5 * sin(r * 1.45);
          float diag = step(0.35, fract((v_pos.x - v_pos.y) * 0.14));
          vec3 holoCol = mix(vec3(1.00, 0.68, 0.18), vec3(0.10, 0.92, 0.82), rings * 0.65);
          float alpha = 0.18 + 0.20 * diag * rings;
          outColor = vec4(holoCol, alpha);
          return;
        }

        vec3 N = normalize(v_nrm);
        // Large analytic wall/floor triangles must retain their planar normal.
        // Test in the canonical part frame so a rotating lid keeps its creases.
        // Curved triangles retain the interpolated studio normal; no mesh copies.
        float axial = max(max(abs(localFace.x), abs(localFace.y)), abs(localFace.z));
        if (axial > 0.99995) {
          vec3 faceNormal = normalize(mat3(u_model) * localFace);
          if (dot(faceNormal, N) < 0.0) faceNormal = -faceNormal;
          N = faceNormal;
        }
        bool backFace = !gl_FrontFacing;
        if (backFace) N = -N;

        vec3 V = normalize(u_eye - v_pos);
        vec3 L1 = normalize(vec3(-0.52, -0.64, 0.56));
        vec3 L2 = normalize(vec3(0.68, -0.25, 0.42));
        vec3 L3 = normalize(vec3(0.05, 0.82, 0.35));
        float diff1 = max(dot(N, L1), 0.0);
        float diff2 = max(dot(N, L2), 0.0);
        float diff3 = max(dot(N, L3), 0.0);

        // Two-Pass Translucent X-Ray / Wall Caliper Shader
        if (u_xrayMode > 0.5) {
          float ndv = abs(dot(N, V));
          float fresnel = pow(1.0 - clamp(ndv, 0.0, 1.0), 2.15);
          vec3 Hx = normalize(L1 + V);
          float specX = pow(max(dot(N, Hx), 0.0), 54.0) * 0.45;

          vec3 xCol;
          float xAlpha;
          if (v_surfaceRole > 0.5 && v_surfaceRole < 1.5) {
            // Inner cavity wall, inner floor, and drainage holes -> warm glowing amber/coral!
            bool isFloorPlane = abs(N.z) > 0.68;
            vec3 innerBase = isFloorPlane ? vec3(1.00, 0.43, 0.18) : vec3(1.00, 0.58, 0.22);
            if (u_lightTheme > 0.5) innerBase *= 0.88;
            xCol = innerBase * (0.48 + 0.55 * diff1 + 0.25 * diff2)
                 + vec3(1.00, 0.84, 0.46) * (fresnel * 0.65 + specX * 0.5);
            xAlpha = isFloorPlane ? (0.52 + 0.28 * fresnel) : (0.35 + 0.42 * fresnel);
          } else if (v_surfaceRole >= 1.5) {
            // Top mouth lip / rim -> crisp luminous cyan-gold ring
            xCol = vec3(0.28, 0.96, 0.86) * (0.58 + 0.42 * diff1) + vec3(0.85) * specX;
            xAlpha = 0.62 + 0.28 * fresnel;
          } else {
            // Outer wall -> smoky emerald/cyan glass with Fresnel rim glow
            vec3 glassBase = (u_lightTheme > 0.5) ? vec3(0.00, 0.56, 0.52) : vec3(0.05, 0.82, 0.74);
            if (v_part > 0.5) glassBase = (u_lightTheme > 0.5) ? vec3(0.22, 0.42, 0.46) : vec3(0.18, 0.55, 0.58);
            xCol = glassBase * (0.40 + 0.52 * diff1 + 0.22 * diff2)
                 + vec3(0.46, 0.98, 0.92) * (fresnel * 0.78)
                 + vec3(1.0) * specX;
            xAlpha = 0.15 + 0.48 * fresnel + specX * 0.28;
          }

          if (backFace) xAlpha *= 0.76;
          if (clipRim > 0.01) {
            xCol = mix(xCol, vec3(1.00, 0.82, 0.24), clipRim * 0.88);
            xAlpha = max(xAlpha, 0.94 * clipRim);
          }
          outColor = vec4(clamp(xCol, 0.0, 1.0), clamp(xAlpha, 0.08, 0.95));
          return;
        }

        // Standard Opaque PBR-Lite Studio Shading
        vec3 albedo = v_part > 0.5 ? u_saucerColor : u_baseColor;
        if (u_heatmap > 0.5) {
          albedo = heatmapColor(v_ovh);
        } else if (u_clipMode > 0.5 && v_surfaceRole > 0.5 && v_surfaceRole < 1.5) {
          albedo = mix(albedo, vec3(0.98, 0.58, 0.24), 0.42);
        } else if (backFace && u_clipMode > 0.5) {
          albedo = mix(albedo, vec3(1.0, 0.72, 0.28), 0.45);
        }

        float layerWave = 0.985 + 0.015 * sin(v_pos.z * 31.4159);
        albedo *= layerWave;

        vec3 H1 = normalize(L1 + V);
        float shininess = mix(96.0, 14.0, u_roughness);
        float spec1 = pow(max(dot(N, H1), 0.0), shininess) * mix(0.28, 0.85, 1.0 - u_roughness);

        float hemi = 0.5 + 0.5 * N.z;
        vec3 ambient = mix(vec3(0.14, 0.16, 0.20), vec3(0.34, 0.37, 0.42), hemi);
        float rim = pow(1.0 - max(dot(N, V), 0.0), 3.2) * 0.22;

        vec3 specTint = mix(vec3(1.0), albedo, u_metallic);
        vec3 color = albedo * (ambient + 0.78 * diff1 + 0.32 * diff2 + 0.22 * diff3)
                   + specTint * spec1
                   + vec3(0.55, 0.85, 0.80) * rim;

        if (clipRim > 0.01) {
          color = mix(color, vec3(1.00, 0.80, 0.22), clipRim * 0.85);
        }

        color = pow(clamp(color, 0.0, 1.0), vec3(0.92));
        outColor = vec4(color, 1.0);
      }
    `,
    );
    lineProg = compileProgram(
      `#version 300 es
 precision highp float;layout(location=0)in vec3 a_pos;uniform mat4 u_mvp;void main(){gl_Position=u_mvp*vec4(a_pos,1.0);}`,
      `#version 300 es
 precision highp float;uniform vec4 u_color;out vec4 outColor;void main(){outColor=u_color;}`,
    );
    bedBuffer = gl.createBuffer();
    rebuildBedGeometry();
    gl.enable(gl.DEPTH_TEST);
  }
  function currentPrinter() {
    return (
      INITIAL.host || {
        bed_x: 220,
        bed_y: 220,
        max_z: 250,
        nozzle_mm: 0.4,
        line_width_mm: 0.42,
      }
    );
  }
  function rebuildBedGeometry() {
    if (!gl || !bedBuffer) return;
    const bx = Math.max(80, Number(currentPrinter().bed_x) || 220);
    const by = Math.max(80, Number(currentPrinter().bed_y) || 220);
    const hx = 0.5 * bx;
    const hy = 0.5 * by;
    const isCircular =
      String(currentPrinter().bed_shape || "").toLowerCase() === "circular";
    const verts = [];

    const step = bx > 320 || by > 320 ? 30 : 20;
    if (isCircular) {
      const rBed = Math.min(hx, hy);
      const rSq = rBed * rBed;
      for (
        let x = -Math.floor(rBed / step) * step;
        x <= rBed + 0.01;
        x += step
      ) {
        const spanY = Math.sqrt(Math.max(0.0, rSq - x * x));
        if (spanY > 1.0) verts.push(x, -spanY, -0.08, x, spanY, -0.08);
      }
      for (
        let y = -Math.floor(rBed / step) * step;
        y <= rBed + 0.01;
        y += step
      ) {
        const spanX = Math.sqrt(Math.max(0.0, rSq - y * y));
        if (spanX > 1.0) verts.push(-spanX, y, -0.08, spanX, y, -0.08);
      }
      const ringSegs = 72;
      for (let s = 0; s < ringSegs; s++) {
        const a0 = (TWO_PI * s) / ringSegs;
        const a1 = (TWO_PI * (s + 1)) / ringSegs;
        verts.push(
          rBed * Math.cos(a0),
          rBed * Math.sin(a0),
          0.02,
          rBed * Math.cos(a1),
          rBed * Math.sin(a1),
          0.02,
        );
      }
      verts.push(-16, -rBed - 4, 0.02, 16, -rBed - 4, 0.02);
    } else {
      for (let x = -Math.floor(hx / step) * step; x <= hx + 0.01; x += step) {
        verts.push(x, -hy, -0.08, x, hy, -0.08);
      }
      for (let y = -Math.floor(hy / step) * step; y <= hy + 0.01; y += step) {
        verts.push(-hx, y, -0.08, hx, y, -0.08);
      }
      verts.push(
        -hx,
        -hy,
        0.02,
        hx,
        -hy,
        0.02,
        hx,
        -hy,
        0.02,
        hx,
        hy,
        0.02,
        hx,
        hy,
        0.02,
        -hx,
        hy,
        0.02,
        -hx,
        hy,
        0.02,
        -hx,
        -hy,
        0.02,
      );
      verts.push(-18, -hy - 4, 0.02, 18, -hy - 4, 0.02);
    }

    const arr = new Float32Array(verts);
    bedVertCount = arr.length / 3;
    gl.bindBuffer(gl.ARRAY_BUFFER, bedBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, arr, gl.STATIC_DRAW);
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
  function openingFraction(value = Number($("open").value)) {
    const shape = typeof meshParams === "undefined" ? p : meshParams;
    return value / (shape.style === "clamshell_pip" ? 180 : 100);
  }
  function openingLabel() {
    const suffix = meshParams.style === "clamshell_pip" ? "°" : "%";
    $("openValue").textContent = Math.round(Number($("open").value)) + suffix;
    if (meshParams.style === "snap_latch") updateLatchMotionStatus();
    if (meshParams.style === "rugged_box") updateRuggedMotionStatus();
  }
  function configureOpening() {
    const nextStyle = meshParams.style;
    const isClamshell = nextStyle === "clamshell_pip";
    $("open").max = isClamshell ? "180" : "100";
    if (isClamshell && openingStyle !== nextStyle) $("open").value = "180";
    else if (["snap_latch", "rugged_box"].includes(nextStyle) && openingStyle !== nextStyle)
      $("open").value = "0";
    else if (
      !isClamshell &&
      !["snap_latch", "rugged_box"].includes(nextStyle) &&
      ["clamshell_pip", "snap_latch", "rugged_box"].includes(openingStyle)
    )
      $("open").value = "25";
    openingStyle = nextStyle;
    openingLabel();
  }
  function snapLatchTransform(part, opening, motion) {
    if (part !== "lid" && !part.startsWith("clip")) return I();
    const left = motion?.clip_left;
    const right = motion?.clip_right;
    if (!left || !right) throw Error("Missing latch motion metadata");
    for (const info of [left, right]) {
      if (!info.pivot || ![info.pivot.x, info.pivot.y, info.pivot.z, info.release_fraction, info.release_angle, info.lid_lift_mm].every(Number.isFinite) || info.release_fraction <= 0 || info.release_fraction >= 1 || info.release_angle <= 0 || info.lid_lift_mm <= 0)
        throw Error("Invalid latch motion metadata");
    }
    const phase = Math.max(0, Math.min(1, opening));
    const releaseFraction = Math.max(
      left.release_fraction,
      right.release_fraction,
    );
    if (part === "lid") {
      const liftPhase = Math.max(
        0,
        Math.min(1, (phase - releaseFraction) / (1 - releaseFraction)),
      );
      return translateM(0, 0, liftPhase * left.lid_lift_mm);
    }
    const info = motion[part];
    if (!info) throw Error("Unknown latch part: " + part);
    const angle =
      (Math.min(1, phase / info.release_fraction) *
        info.release_angle *
        Math.PI) /
      180;
    const pivot = info.pivot;
    return mult(
      translateM(pivot.x, pivot.y, pivot.z),
      mult(rotateX(angle), translateM(-pivot.x, -pivot.y, -pivot.z)),
    );
  }
  function updateLatchMotionStatus() {
    const label = $("latch-motion-phase");
    const info = INITIAL.latch_motion?.clip_left;
    label.hidden = !info;
    if (!info) return;
    const phase = openingFraction();
    const key =
      phase <= 0
        ? "latchesEngaged"
        : phase < info.release_fraction
          ? "releasingLatches"
          : phase < 1
            ? "liftingLid"
            : "lidRemoved";
    const message = tr(key);
    if (label.textContent !== message) label.textContent = message;
  }
  function updateRuggedMotionStatus() {
    const label = $("rugged-motion-phase");
    if (!label) return;
    const shape = typeof meshParams === "undefined" ? p : meshParams;
    label.hidden = shape.style !== "rugged_box" || INITIAL.preview_mode === "calibration";
    if (label.hidden) return;
    const phase = openingFraction();
    const message = tr(phase <= 0 ? "ruggedClosed" : phase < 0.25 ? "ruggedReleasing" : phase < 1 ? "ruggedOpening" : "ruggedOpen");
    if (label.textContent !== message) label.textContent = message;
  }
  function partTransform(part, opening = openingFraction(), offset = null) {
    const shape = typeof meshParams === "undefined" ? p : meshParams;
    const frame = translateM(...(offset || [0, 0, 0]));
    if (INITIAL.preview_mode === "calibration") return frame;
    if (shape.style === "snap_latch")
      return mult(
        frame,
        snapLatchTransform(part, opening, INITIAL.latch_motion),
      );
    let model = I();
    if (shape.style === "rugged_box") {
      // Remove the spring clips completely before the hinged lid rotates.
      const phase = Math.max(0, Math.min(1, opening));
      const releaseFraction = 0.25;
      if (part.startsWith("clip"))
        model = translateM(0, -15 * Math.min(1, phase / releaseFraction), 0);
      else if (part === "lid") {
        const h = INITIAL.hinge || {y: shape.depth_y / 2 + 5, z: shape.height_z - 4};
        const angle = -Math.PI * Math.max(0, (phase - releaseFraction) / (1 - releaseFraction));
        model = mult(translateM(0, h.y, h.z), mult(rotateX(angle), translateM(0, -h.y, -h.z)));
      }
      return mult(frame, model);
    }
    if (part === "lid") {
      if (shape.style === "clamshell_pip") {
        const h = INITIAL.hinge || {
          y: shape.depth_y / 2 + 5,
          z: shape.height_z - 4,
        };
        model = mult(
          translateM(0, h.y, h.z),
          mult(rotateX(-opening * Math.PI), translateM(0, -h.y, -h.z)),
        );
      } else if (shape.style === "sliding_lid")
        model = translateM(0, -opening * (shape.depth_y + 10), 0);
      else model = translateM(0, 0, opening * 50);
    }
    return mult(frame, model);
  }
  function transformPoint(m, x, y, z) {
    return [
      m[0] * x + m[4] * y + m[8] * z + m[12],
      m[1] * x + m[5] * y + m[9] * z + m[13],
      m[2] * x + m[6] * y + m[10] * z + m[14],
    ];
  }
  function sceneBounds(opening = openingFraction()) {
    if (!meshes.length) return null;
    const lo = [Infinity, Infinity, Infinity],
      hi = [-Infinity, -Infinity, -Infinity];
    for (const mesh of meshes) {
      const m = partTransform(mesh.part, opening, mesh.preview_offset),
        b = mesh.bounds;
      for (const x of [b.min[0], b.max[0]])
        for (const y of [b.min[1], b.max[1]])
          for (const z of [b.min[2], b.max[2]]) {
            const q = transformPoint(m, x, y, z);
            for (let a = 0; a < 3; a++) {
              lo[a] = Math.min(lo[a], q[a]);
              hi[a] = Math.max(hi[a], q[a]);
            }
          }
    }
    return {
      min: lo,
      max: hi,
      size: hi.map((x, i) => x - lo[i]),
      center: hi.map((x, i) => (x + lo[i]) / 2),
    };
  }
  function camera(aspect) {
    const b = sceneBounds() || {
        min: [-0.5, -0.5, -0.5],
        max: [0.5, 0.5, 0.5],
        center: [0, 0, 0],
        size: [1, 1, 1],
      },
      target = b.center;
    const radius = Math.max(0.1, Math.hypot(...b.size) / 2),
      fov = (38 * Math.PI) / 180,
      fitAngle = Math.min(fov, 2 * Math.atan(Math.tan(fov / 2) * aspect)),
      distance = ((radius / Math.sin(fitAngle / 2)) * 1.12) / zoom;
    const eye = [
        target[0] + distance * Math.cos(yaw) * Math.cos(pitch),
        target[1] + distance * Math.sin(yaw) * Math.cos(pitch),
        target[2] + distance * Math.sin(pitch),
      ],
      z = normalize(eye.map((x, i) => x - target[i])),
      x = normalize(cross([0, 0, 1], z)),
      y = cross(z, x),
      view = new Float32Array([
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
      near = Math.max(0.01, distance - radius * 1.7),
      far = Math.max(100, distance + radius * 3),
      f = 1 / Math.tan(fov / 2),
      projection = new Float32Array([
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
    return {
      mvp: mult(projection, view),
      eye,
      bounds: b,
      distance,
      target,
    };
  }
  function decode(s, ctor) {
    const b = atob(s),
      a = new Uint8Array(b.length);
    for (let i = 0; i < b.length; i++) a[i] = b.charCodeAt(i);
    return new ctor(a.buffer);
  }
  function loadMeshes(items) {
    configureOpening();
    const calibration = INITIAL.preview_mode === "calibration";
    $("open").disabled =
      calibration || ["open_bin", "stackable_bin"].includes(meshParams.style);
    $("play").disabled =
      calibration || ["open_bin", "stackable_bin"].includes(meshParams.style);
    if (
      calibration ||
      ["open_bin", "stackable_bin"].includes(meshParams.style)
    ) {
      playing = false;
      $("play").textContent = "▶";
    }
    if (!gl) return;
    for (const m of meshes) {
      for (const b of [m.pb, m.nb, m.rb, m.ib, m.wireBuffer])
        if (b) gl.deleteBuffer(b);
      gl.deleteVertexArray(m.vao);
    }
    meshes = items.map((item) => {
      const pos = decode(item.vertices, Float32Array),
        tri = decode(item.triangles, Uint32Array),
        norm = new Float32Array(pos.length),
        roles = new Float32Array(pos.length / 3);
      const lo = [Infinity, Infinity, Infinity],
        hi = [-Infinity, -Infinity, -Infinity];
      let maxOverhang = 0;
      for (let i = 0; i < pos.length; i += 3)
        for (let a = 0; a < 3; a++) {
          lo[a] = Math.min(lo[a], pos[i + a]);
          hi[a] = Math.max(hi[a], pos[i + a]);
        }
      for (let i = 0; i < tri.length; i += 3) {
        const a = tri[i] * 3,
          b = tri[i + 1] * 3,
          c = tri[i + 2] * 3,
          ux = pos[b] - pos[a],
          uy = pos[b + 1] - pos[a + 1],
          uz = pos[b + 2] - pos[a + 2],
          vx = pos[c] - pos[a],
          vy = pos[c + 1] - pos[a + 1],
          vz = pos[c + 2] - pos[a + 2],
          nx = uy * vz - uz * vy,
          ny = uz * vx - ux * vz,
          nz = ux * vy - uy * vx,
          l = Math.hypot(nx, ny, nz) || 1;
        if (Math.max(pos[a + 2], pos[b + 2], pos[c + 2]) > lo[2] + 0.02)
          maxOverhang = Math.max(
            maxOverhang,
            (Math.asin(Math.max(0, Math.min(1, -nz / l))) * 180) / Math.PI,
          );
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
        const inner = norm[i] * pos[i] + norm[i + 1] * pos[i + 1] < 0,
          innerFloor =
            norm[i + 2] > 0.7 &&
            Math.abs(pos[i + 2] - meshParams.floor_thickness) < 0.03;
        roles[i / 3] =
          inner || innerFloor
            ? 1
            : pos[i + 2] > meshParams.height_z - 0.03 && norm[i + 2] > 0.6
              ? 2
              : 0;
      }
      const vao = gl.createVertexArray();
      gl.bindVertexArray(vao);
      const upload = (loc, data, size) => {
        const b = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, b);
        gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);
        gl.enableVertexAttribArray(loc);
        gl.vertexAttribPointer(loc, size, gl.FLOAT, false, 0, 0);
        return b;
      };
      const pb = upload(0, pos, 3),
        nb = upload(1, norm, 3),
        rb = upload(2, roles, 1),
        ib = gl.createBuffer();
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ib);
      gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, tri, gl.STATIC_DRAW);
      return {
        ...item,
        bounds: { min: lo, max: hi, size: hi.map((x, i) => x - lo[i]) },
        vao,
        pb,
        nb,
        rb,
        ib,
        count: tri.length,
        indices: tri,
        maxOverhang,
        positions: pos,
      };
    });
    zoom = 1;
    render();
  }
  function drawLines(buffer, count, mvp, color) {
    gl.useProgram(lineProg);
    gl.uniformMatrix4fv(gl.getUniformLocation(lineProg, "u_mvp"), false, mvp);
    gl.uniform4fv(gl.getUniformLocation(lineProg, "u_color"), color);
    gl.bindVertexArray(null);
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 0, 0);
    gl.drawArrays(gl.LINES, 0, count);
  }
  function updateHud(b) {
    if (!b) return;
    if (meshParams.style === "snap_latch") updateLatchMotionStatus();
    const h = currentPrinter(),
      printSize =
        meshParams.style === "clamshell_pip" && INITIAL.print_bounds?.size
          ? INITIAL.print_bounds.size
          : b.size,
      fits =
        printSize[0] <= h.bed_x &&
        printSize[1] <= h.bed_y &&
        printSize[2] <= h.max_z;
    $("hud-dims").textContent = b.size.map((x) => x.toFixed(1)).join("×");
    $("hud-wall-floor").textContent =
      `${p.wall_thickness.toFixed(1)} / ${p.floor_thickness.toFixed(1)} mm`;
    $("hud-clearance").textContent =
      Number(
        p.style === "clamshell_pip" ? p.pip_clearance : p.fit_clearance,
      ).toFixed(2) + " mm";
    $("hud-overhang").textContent =
      Math.max(0, ...meshes.map((m) => m.maxOverhang)).toFixed(1) + "°";
    $("hud-status-pill").textContent = fits ? "OK" : "⚠";
    $("hud-status-pill").className =
      "hud-status-pill " + (fits ? "ok" : "warn");
    $("bed-alert-banner").classList.toggle("visible", !fits);
    $("wall-perim-hint").textContent =
      `≈ ${Math.ceil(p.wall_thickness / (h.line_width_mm || 0.42))} ${lang === "pt" ? "perímetros de" : "walls of"} ${(h.line_width_mm || 0.42).toFixed(2)} mm`;
  }
  function render() {
    if (!gl || !program) return;
    const cv = $("gl"),
      r = cv.getBoundingClientRect(),
      dpr = Math.min(devicePixelRatio || 1, 2),
      w = Math.max(1, Math.floor(r.width * dpr)),
      h = Math.max(1, Math.floor(r.height * dpr));
    if (cv.width !== w || cv.height !== h) {
      cv.width = w;
      cv.height = h;
    }
    gl.viewport(0, 0, w, h);
    gl.depthMask(true);
    gl.enable(gl.DEPTH_TEST);
    gl.disable(gl.CULL_FACE);
    gl.disable(gl.BLEND);
    if (theme === "light") gl.clearColor(0.84, 0.88, 0.92, 1);
    else gl.clearColor(0.095, 0.11, 0.138, 1);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    const cam = camera(w / h);
    lastFrame = { ...cam, cssW: r.width, cssH: r.height };
    drawLines(
      bedBuffer,
      bedVertCount,
      cam.mvp,
      theme === "light" ? [0.35, 0.45, 0.52, 0.45] : [0, 0.72, 0.62, 0.34],
    );
    const value = Number($("cut").value),
      b = cam.bounds,
      clipMode = value === 0 ? 0 : cutAxis === "y" ? 1 : 2,
      clipValue =
        cutAxis === "y"
          ? b.min[1] + b.size[1] * (1 - value / 100)
          : b.min[2] + b.size[2] * (1 - value / 100);
    const mat =
      MATERIAL_PRESETS[$("xray").checked ? "xray" : material] ||
      MATERIAL_PRESETS.emerald_silk;
    for (const m of meshes) {
      const model = partTransform(m.part, openingFraction(), m.preview_offset);
      gl.useProgram(program);
      gl.uniformMatrix4fv(
        gl.getUniformLocation(program, "u_mvp"),
        false,
        cam.mvp,
      );
      gl.uniformMatrix4fv(
        gl.getUniformLocation(program, "u_model"),
        false,
        model,
      );
      gl.uniform3fv(gl.getUniformLocation(program, "u_eye"), cam.eye);
      gl.uniform3fv(
        gl.getUniformLocation(program, "u_baseColor"),
        m.part === "lid" ? mat.saucer : mat.base,
      );
      gl.uniform3fv(
        gl.getUniformLocation(program, "u_saucerColor"),
        mat.saucer,
      );
      for (const [key, v] of Object.entries({
        u_roughness: mat.rough,
        u_metallic: mat.metal,
        u_heatmap: material === "heatmap" && !$("xray").checked ? 1 : 0,
        u_xrayMode: $("xray").checked ? 1 : 0,
        u_clipMode: clipMode,
        u_clipVal: clipValue,
        u_passMode: 0,
        u_lightTheme: theme === "light" ? 1 : 0,
      }))
        gl.uniform1f(gl.getUniformLocation(program, key), v);
      gl.bindVertexArray(m.vao);
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, m.ib);
      if ($("xray").checked) {
        gl.enable(gl.BLEND);
        gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
        gl.depthMask(false);
        gl.enable(gl.CULL_FACE);
        gl.cullFace(gl.FRONT);
        gl.drawElements(gl.TRIANGLES, m.count, gl.UNSIGNED_INT, 0);
        gl.cullFace(gl.BACK);
        gl.drawElements(gl.TRIANGLES, m.count, gl.UNSIGNED_INT, 0);
        gl.disable(gl.CULL_FACE);
        gl.depthMask(true);
        gl.disable(gl.BLEND);
      } else gl.drawElements(gl.TRIANGLES, m.count, gl.UNSIGNED_INT, 0);
      if (wire && clipMode === 0) {
        if (!m.wireBuffer) {
          const edges = new Uint32Array(m.indices.length * 2);
          for (let i = 0, k = 0; i < m.indices.length; i += 3) {
            const a = m.indices[i],
              b = m.indices[i + 1],
              c = m.indices[i + 2];
            for (const e of [a, b, b, c, c, a]) edges[k++] = e;
          }
          m.wireBuffer = gl.createBuffer();
          gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, m.wireBuffer);
          gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, edges, gl.STATIC_DRAW);
          m.wireCount = edges.length;
        }
        gl.useProgram(lineProg);
        gl.uniformMatrix4fv(
          gl.getUniformLocation(lineProg, "u_mvp"),
          false,
          mult(cam.mvp, model),
        );
        gl.uniform4fv(
          gl.getUniformLocation(lineProg, "u_color"),
          [0, 0, 0, 0.32],
        );
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, m.wireBuffer);
        gl.enable(gl.BLEND);
        gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
        gl.drawElements(gl.LINES, m.wireCount, gl.UNSIGNED_INT, 0);
        gl.disable(gl.BLEND);
      }
    }
    updateHud(sceneBounds());
    renderCalipers();
  }
  function projectWorldToScreen(wx, wy, wz, mvp, cssW, cssH) {
    const cx = mvp[0] * wx + mvp[4] * wy + mvp[8] * wz + mvp[12];
    const cy = mvp[1] * wx + mvp[5] * wy + mvp[9] * wz + mvp[13];
    const cz = mvp[2] * wx + mvp[6] * wy + mvp[10] * wz + mvp[14];
    const cw = mvp[3] * wx + mvp[7] * wy + mvp[11] * wz + mvp[15];
    if (cw <= 0.1) return null;
    const ndcX = cx / cw;
    const ndcY = cy / cw;
    return {
      x: (ndcX * 0.5 + 0.5) * cssW,
      y: (0.5 - ndcY * 0.5) * cssH,
      ndcZ: cz / cw,
    };
  }

  function drawCadArrowHead(ctx, tipX, tipY, dirX, dirY, len) {
    const nx = -dirY;
    const ny = dirX;
    const w = len * 0.44;
    ctx.beginPath();
    ctx.moveTo(tipX, tipY);
    ctx.lineTo(tipX - dirX * len + nx * w, tipY - dirY * len + ny * w);
    ctx.lineTo(tipX - dirX * len - nx * w, tipY - dirY * len - ny * w);
    ctx.closePath();
    ctx.fill();
  }

  function drawCadDoubleArrow(ctx, x1, y1, x2, y2, color, dashed) {
    const dx = x2 - x1;
    const dy = y2 - y1;
    const dist = Math.hypot(dx, dy);
    if (dist < 4.0) return;
    const ux = dx / dist;
    const uy = dy / dist;
    const arrowLen = Math.min(7.5, dist * 0.28);

    ctx.save();
    ctx.strokeStyle = color;
    ctx.fillStyle = color;
    ctx.lineWidth = 1.65;
    if (dashed) ctx.setLineDash([4, 3]);
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineTo(x2, y2);
    ctx.stroke();
    ctx.setLineDash([]);
    drawCadArrowHead(ctx, x1, y1, -ux, -uy, arrowLen);
    drawCadArrowHead(ctx, x2, y2, ux, uy, arrowLen);
    ctx.restore();
  }

  function drawCadPill(
    ctx,
    cx,
    cy,
    text,
    borderColor,
    cssW,
    cssH,
    placedBoxes,
  ) {
    ctx.save();
    ctx.font = "700 10.8px 'Cascadia Code', Consolas, 'Segoe UI', monospace";
    const padX = 7;
    const boxH = 20;
    const tw = ctx.measureText(text).width;
    const boxW = tw + padX * 2;

    let x = Math.max(10, Math.min(cssW - boxW - 10, cx - boxW * 0.5));
    let y = Math.max(44, Math.min(cssH - boxH - 46, cy - boxH * 0.5));

    // Gentle vertical collision avoidance so pills never overlap each other
    if (Array.isArray(placedBoxes)) {
      for (let pass = 0; pass < 4; pass++) {
        let hit = false;
        for (let k = 0; k < placedBoxes.length; k++) {
          const b = placedBoxes[k];
          const overlapX = x < b.x + b.w + 4 && x + boxW + 4 > b.x;
          const overlapY = y < b.y + b.h + 3 && y + boxH + 3 > b.y;
          if (overlapX && overlapY) {
            y =
              y >= b.y
                ? Math.min(cssH - boxH - 46, b.y + b.h + 4)
                : Math.max(44, b.y - boxH - 4);
            hit = true;
          }
        }
        if (!hit) break;
      }
      placedBoxes.push({ x: x, y: y, w: boxW, h: boxH });
    }

    const r = 5;
    ctx.beginPath();
    if (typeof ctx.roundRect === "function") {
      ctx.roundRect(x, y, boxW, boxH, r);
    } else {
      ctx.rect(x, y, boxW, boxH);
    }
    ctx.fillStyle =
      theme === "light"
        ? "rgba(250, 252, 255, 0.94)"
        : "rgba(15, 18, 24, 0.90)";
    ctx.fill();
    ctx.lineWidth = 1.4;
    ctx.strokeStyle = borderColor;
    ctx.stroke();

    ctx.fillStyle = theme === "light" ? "#141a22" : "#f3f7fb";
    ctx.textBaseline = "middle";
    ctx.fillText(text, x + padX, y + boxH * 0.5 + 0.5);
    ctx.restore();
    return { cx: x + boxW * 0.5, cy: y + boxH * 0.5 };
  }

  function renderCalipers() {
    const cv = $("vp-caliper-canvas"),
      ctx = cv.getContext("2d"),
      r = cv.getBoundingClientRect(),
      dpr = Math.min(devicePixelRatio || 1, 2);
    cv.width = Math.max(1, r.width * dpr);
    cv.height = Math.max(1, r.height * dpr);
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, r.width, r.height);
    if (!calipers || !lastFrame || !meshes.length) return;
    const b = sceneBounds(),
      lo = b.min,
      hi = b.max,
      placed = [],
      color = theme === "light" ? "#007f74" : "#6cffe8";
    for (const [a, bpoint, text] of [
      [
        [lo[0], lo[1], lo[2]],
        [hi[0], lo[1], lo[2]],
        b.size[0].toFixed(2) + " mm",
      ],
      [
        [hi[0], lo[1], lo[2]],
        [hi[0], hi[1], lo[2]],
        b.size[1].toFixed(2) + " mm",
      ],
      [
        [lo[0], lo[1], lo[2]],
        [lo[0], lo[1], hi[2]],
        b.size[2].toFixed(2) + " mm",
      ],
    ]) {
      const aa = projectWorldToScreen(...a, lastFrame.mvp, r.width, r.height),
        bb = projectWorldToScreen(...bpoint, lastFrame.mvp, r.width, r.height);
      if (aa && bb) {
        drawCadDoubleArrow(ctx, aa.x, aa.y, bb.x, bb.y, color, false);
        drawCadPill(
          ctx,
          (aa.x + bb.x) / 2,
          (aa.y + bb.y) / 2,
          text,
          color,
          r.width,
          r.height,
          placed,
        );
      }
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
    zoom = Math.max(0.35, Math.min(4, zoom * Math.exp(-e.deltaY * 0.001)));
    render();
  };
  $("home").onclick = () => {
    zoom = 1;
    yaw = -0.75;
    pitch = 0.68;
    render();
  };
  $("open").oninput = () => {
    openingLabel();
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
    const extent = Number($("open").max) || 100;
    $("open").value = extent / 2 - (extent / 2) * Math.cos(t * 0.0007);
    openingLabel();
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
  Object.assign(texts.pt, {
    sec_presets: "Galeria de Modelos",
    btn_save_preset: "+ Salvar",
    cat_all: "Todos",
    cat_user: "Meus",
    shape: "Forma",
    features: "Recursos",
    manufacture: "Impressão",
    hud_title: "Inspeção da malha",
    hud_wall_floor: "Parede / Fundo",
    hud_mouth_hole: "Folga por lado",
    hud_dims: "Cena atual (mm)",
    hud_overhang: "Overhang da malha",
    hud_weight: "Volume sólido (cm³)",
    hud_Tris: "Triângulos",
    mat_emerald: "Seda Esmeralda Orca",
    mat_terracotta: "Cerâmica Terracota",
    mat_white: "Porcelana Branca Mate",
    mat_copper: "Bronze Cobre Escovado",
    mat_xray: "🔬 Raio-X / Parede (Translúcido)",
    mat_heatmap: "Mapa de Overhang (°)",
    vp_xray: "🔬 Raio-X / Parede",
    vp_calipers: "📏 Cotas mm",
    vp_heatmap: "🔥 Overhang",
    vp_wire: "⌗ Malha",
    cam_front: "Frente",
    cam_top: "Topo",
    cam_bottom: "Base",
    cam_fit: "Enquadrar",
    vp_cut_y: "✂ Corte Vertical (Perfil Y)",
    vp_cut_z: "💿 Fatia Horizontal Z",
    leg_outer: "Externa",
    leg_inner: "Cavidade & Fundo",
    btn_send_plater: "Enviar para a Mesa do OrcaSlicer",
    btn_exp_3mf: "Exportar .3MF",
    btn_exp_stl: "Exportar .STL",
    btn_surprise: "Surpreenda-me",
  });
  Object.assign(texts.en, {
    sec_presets: "Model Gallery",
    btn_save_preset: "+ Save",
    cat_all: "All",
    cat_user: "Mine",
    shape: "Shape",
    features: "Features",
    manufacture: "Print",
    hud_title: "Mesh inspection",
    hud_wall_floor: "Wall / Floor",
    hud_mouth_hole: "Clearance per side",
    hud_dims: "Current scene (mm)",
    hud_overhang: "Mesh overhang",
    hud_weight: "Solid volume (cm³)",
    hud_Tris: "Triangles",
    mat_emerald: "Orca Emerald Silk",
    mat_terracotta: "Terracotta Ceramic",
    mat_white: "Matte White Porcelain",
    mat_copper: "Brushed Copper Bronze",
    mat_xray: "🔬 X-Ray / Wall (Translucent)",
    mat_heatmap: "Overhang Map (°)",
    vp_xray: "🔬 X-Ray / Wall",
    vp_calipers: "📏 Calipers mm",
    vp_heatmap: "🔥 Overhang",
    vp_wire: "⌗ Mesh",
    cam_front: "Front",
    cam_top: "Top",
    cam_bottom: "Bottom",
    cam_fit: "Fit",
    vp_cut_y: "✂ Vertical Cut Y",
    vp_cut_z: "💿 Horizontal Slice Z",
    leg_outer: "Outer",
    leg_inner: "Cavity & Floor",
    btn_send_plater: "Send to OrcaSlicer Plater",
    btn_exp_3mf: "Export .3MF",
    btn_exp_stl: "Export .STL",
    btn_surprise: "Surprise me",
  });
  let presetFilter = "all",
    activePreset = null;
  function presetSignature(params) {
    const ignored = new Set([
      "name",
      "lang",
      "theme",
      "export_target",
      "auto_configure_slicer",
    ]);
    return JSON.stringify(
      Object.fromEntries(
        Object.keys(params)
          .filter((k) => !ignored.has(k))
          .sort()
          .map((k) => [k, params[k]]),
      ),
    );
  }
  function syncPresetSelection() {
    const all = [...(INITIAL.user_presets || []), ...(INITIAL.presets || [])];
    const selected = all.find((item) => item.id === activePreset);
    const signature = presetSignature(p);
    if (!selected || presetSignature(selected.params) !== signature)
      activePreset =
        all.find((item) => presetSignature(item.params) === signature)?.id ||
        null;
    presets();
  }
  function presetThumb(params) {
    if (params.style === "clamshell_pip") {
      const shell = (x, y) =>
        `<path d="M${x} ${y}l16 -8h44l-16 8Z" fill="#00a896" fill-opacity=".55" stroke="#80ffea"/><path d="M${x} ${y}v14h44v-14M${x + 44} ${y}l16 -8v14l-16 8" fill="#00796b" fill-opacity=".45" stroke="#55cfbb"/>`;
      return `<svg viewBox="0 0 124 92" fill="none" aria-hidden="true">${shell(43, 24)}<path d="M37 44l17 -8M65 44l17 -8" stroke="#ffcf77" stroke-width="3"/>${shell(12, 51)}</svg>`;
    }

    const w = params.width_x || 90,
      d = params.depth_y || 65,
      h = params.height_z || 35,
      sx = Math.min(52 / w, 34 / d, 38 / h),
      ww = w * sx,
      dd = d * sx * 0.48,
      hh = h * sx,
      ox = 62 - ww / 2,
      oy = 70 - hh;
    const lid = ["open_bin", "stackable_bin"].includes(params.style)
      ? ""
      : `<path d="M${ox} ${oy - 8}l${dd} ${-dd * 0.5} ${ww} 0 ${-dd} ${dd * 0.5}Z" fill="#26363e" stroke="#ffcf77"/>`;
    const accessWidth = Math.min(
      ww * 0.85,
      (params.front_access_width || w * 0.6) * sx,
    );
    const accessDrop = Math.min(
      hh * 0.8,
      (params.front_access_drop || h * 0.35) * sx,
    );
    const details =
      params.style === "stackable_bin"
        ? `<path d="M${ox + (ww - accessWidth) / 2} ${oy - 1}v${accessDrop}h${accessWidth}v${-accessDrop}Z" fill="#172126" stroke="#80ffea"/><path d="M${ox + 2} ${oy + hh - 2}h${ww - 4}" stroke="#80ffea"/>`
        : params.style === "open_bin" && params.handles_enabled
          ? params.handle_faces === "front_back"
            ? `<rect x="${ox + ww * 0.28}" y="${oy + hh * 0.3}" width="${ww * 0.44}" height="5" rx="2.5" fill="#172126" stroke="#80ffea"/>`
            : `<path d="M${ox + ww + dd * 0.2} ${oy + hh * 0.25 - dd * 0.1}l${dd * 0.6} ${-dd * 0.3}v5l${-dd * 0.6} ${dd * 0.3}Z" fill="#172126" stroke="#80ffea"/>`
          : params.style === "snap_latch"
            ? [0.2, 0.7]
                .map(
                  (x) =>
                    `<rect x="${ox + ww * x}" y="${oy - 5}" width="${ww * 0.1}" height="12" rx="1" fill="#ffb74d" stroke="#ffe0a3"/>`,
                )
                .join("")
            : "";
    return `<svg viewBox="0 0 124 92" fill="none" aria-hidden="true"><path d="M${ox} ${oy}l${dd} ${-dd * 0.5} ${ww} 0 ${-dd} ${dd * 0.5}Z" fill="#00a896" fill-opacity=".6" stroke="#80ffea"/><path d="M${ox} ${oy}v${hh}h${ww}v${-hh}M${ox + ww} ${oy}l${dd} ${-dd * 0.5}v${hh}l${-dd} ${dd * 0.5}" fill="#00796b" fill-opacity=".4" stroke="#55cfbb"/>${lid}${details}</svg>`;
  }
  function presets() {
    const grid = $("presets");
    grid.replaceChildren();
    const combined = [
      ...(INITIAL.user_presets || []).map((x) => ({ ...x, user: true })),
      ...(INITIAL.presets || []),
    ];
    for (const item of combined) {
      if (presetFilter === "user" && !item.user) continue;
      if (
        !["all", "user"].includes(presetFilter) &&
        item.params.style !== presetFilter
      )
        continue;
      const card = document.createElement("div");
      card.className =
        "preset-card" + (activePreset === item.id ? " active" : "");
      card.dataset.presetId = item.id;
      card.tabIndex = 0;
      card.setAttribute("role", "button");
      card.innerHTML =
        '<div class="preset-thumb">' +
        presetThumb(item.params) +
        '</div><div class="preset-meta"><div class="preset-name"></div><div class="preset-sub"></div></div>';
      card.querySelector(".preset-name").textContent = item.user
        ? item.name
        : lang === "pt"
          ? item.name_pt
          : item.name_en;
      card.querySelector(".preset-sub").textContent =
        `${item.params.width_x}×${item.params.depth_y}×${item.params.height_z} mm`;
      const apply = () => {
        activePreset = item.id;
        setDesign(item.params);
        presets();
      };
      card.onclick = apply;
      card.onkeydown = (e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          apply();
        }
      };
      if (item.user) {
        const del = document.createElement("button");
        del.className = "preset-del-btn";
        del.textContent = "×";
        del.title = tr("delete");
        del.onclick = (e) => {
          e.stopPropagation();
          send({ type: "delete_preset", preset_id: item.id });
        };
        card.append(del);
      }
      grid.append(card);
    }
  }
  function updatePrinter() {
    const h = currentPrinter();
    $("printer").textContent = h.printer_name || "OrcaSlicer";
    $("printer-pill-specs").textContent =
      `· ${h.bed_x}×${h.bed_y}×${h.max_z} mm · ${h.nozzle_mm}mm`;
    $("sync").classList.remove("syncing");
    if (gl && program) rebuildBedGeometry();
    render();
  }
  document.querySelectorAll("[data-cat]").forEach(
    (button) =>
      (button.onclick = () => {
        presetFilter = button.dataset.cat;
        document
          .querySelectorAll("[data-cat]")
          .forEach((x) => x.classList.toggle("active", x === button));
        presets();
      }),
  );
  $("btn-toggle-save-preset").onclick = () =>
    $("save-preset-bar").classList.toggle("open");
  $("savePreset").onclick = () =>
    send({
      type: "save_preset",
      params: p,
      name: $("inp-save-preset-name").value.trim() || p.name,
    });
  $("btn-randomize").onclick = () => {
    const bytes = new Uint32Array(1);
    if (window.crypto?.getRandomValues) window.crypto.getRandomValues(bytes);
    else bytes[0] = Date.now() >>> 0;
    status(tr("generating"));
    if (!send({ type: "randomize", seed: bytes[0], params: clone(p) }))
      status(tr("noHost"));
  };
  $("sync").onclick = () => {
    $("sync").classList.add("syncing");
    send({ type: "sync_printer" });
    setTimeout(() => $("sync").classList.remove("syncing"), 1200);
  };
  document.querySelectorAll("[data-tab]").forEach(
    (button) =>
      (button.onclick = () => {
        document.body.dataset.dockTab = button.dataset.tab;
        document
          .querySelectorAll("[data-tab]")
          .forEach((x) => x.classList.toggle("active", x === button));
        drawPlan();
        render();
      }),
  );
  document.querySelectorAll("[data-param-range]").forEach((range) => {
    let gesture = false;
    range.onpointerdown = () => {
      snapshot();
      gesture = true;
    };
    range.oninput = () => {
      requestPreview(false);
      if (!gesture) {
        snapshot();
        gesture = true;
      }
      p[range.dataset.paramRange] = Number(range.value);
      document.querySelector(
        '[data-p="' + range.dataset.paramRange + '"]',
      ).value = range.value;
      drawPlan();
    };
    range.onchange = () => {
      if (!gesture) snapshot();
      gesture = false;
      sync();
      requestPreview();
    };
  });
  document
    .querySelectorAll("[data-wall-preset]")
    .forEach(
      (button) =>
        (button.onclick = () =>
          change("wall_thickness", Number(button.dataset.wallPreset))),
    );
  document.querySelectorAll("[data-action]").forEach(
    (button) =>
      (button.onclick = () => {
        const a = button.dataset.action;
        if (a === "open_folder") send({ type: "open_exports_folder" });
        else
          manufacture(
            a === "send_to_plater" ? a : "export_file",
            a === "export_stl" ? "stl" : "3mf",
          );
      }),
  );
  function viewButtons() {
    for (const [id, on] of [
      ["xray", $("xray").checked],
      ["btn-vp-calipers", calipers],
      ["btn-vp-wire", wire],
      ["btn-vp-spin", spin],
      ["btn-vp-heatmap", material === "heatmap"],
    ])
      $(id).classList.toggle("active", !!on);
    $("xray-legend").classList.toggle("visible", !!$("xray").checked);
    $("heatmap-legend").classList.toggle(
      "visible",
      material === "heatmap" && !$("xray").checked,
    );
  }
  $("xray").onclick = () => {
    $("xray").checked = !$("xray").checked;
    viewButtons();
    render();
  };
  $("btn-vp-calipers").onclick = () => {
    calipers = !calipers;
    viewButtons();
    render();
  };
  $("btn-vp-wire").onclick = () => {
    wire = !wire;
    viewButtons();
    render();
  };
  $("sel-material").onchange = () => {
    const choice = $("sel-material").value;
    $("xray").checked = choice === "xray";
    if (choice !== "xray") material = choice;
    viewButtons();
    render();
  };
  $("btn-vp-heatmap").onclick = () => {
    material = material === "heatmap" ? "emerald_silk" : "heatmap";
    $("xray").checked = false;
    $("sel-material").value = material;
    viewButtons();
    render();
  };
  document.querySelectorAll("[data-cam]").forEach(
    (button) =>
      (button.onclick = () => {
        zoom = 1;
        switch (button.dataset.cam) {
          case "front":
            yaw = -Math.PI / 2;
            pitch = 0.02;
            break;
          case "top":
            yaw = -Math.PI / 2;
            pitch = Math.PI / 2 - 0.0001;
            break;
          case "bottom":
            yaw = -Math.PI / 2;
            pitch = -Math.PI / 2 + 0.0001;
            break;
          case "iso":
            yaw = -0.75;
            pitch = 0.68;
            break;
        }
        render();
      }),
  );
  $("btn-cut-mode-y").onclick = () => {
    cutAxis = "y";
    $("btn-cut-mode-y").classList.add("active");
    $("btn-cut-mode-z").classList.remove("active");
    render();
  };
  $("btn-cut-mode-z").onclick = () => {
    cutAxis = "z";
    $("btn-cut-mode-z").classList.add("active");
    $("btn-cut-mode-y").classList.remove("active");
    render();
  };
  $("cut").oninput = () => {
    $("lbl-cross-cut").textContent =
      $("cut").value === "0" ? "Off" : $("cut").value + "%";
    render();
  };
  $("btn-cut-half").onclick = () => {
    $("cut").value = 50;
    $("cut").oninput();
  };
  $("btn-cut-off").onclick = () => {
    $("cut").value = 0;
    $("cut").oninput();
  };
  let scheduledAnimation = 0,
    lastAnimationTime = 0;
  function animate(t) {
    scheduledAnimation = 0;
    if (document.hidden) {
      playing = false;
      spin = false;
      return;
    }
    const dt = lastAnimationTime ? Math.min(t - lastAnimationTime, 50) : 16;
    lastAnimationTime = t;
    if (playing) {
      const extent = Number($("open").max) || 100;
      $("open").value = extent / 2 - (extent / 2) * Math.cos(t * 0.0007);
      openingLabel();
    }
    if (spin) yaw += dt * 0.00025;
    render();
    if (playing || spin) scheduledAnimation = requestAnimationFrame(animate);
  }
  function scheduleAnimation() {
    if (!scheduledAnimation)
      scheduledAnimation = requestAnimationFrame(animate);
  }
  $("play").onclick = () => {
    playing = !playing;
    $("play").textContent = playing ? "Ⅱ" : "▶";
    scheduleAnimation();
  };
  $("btn-vp-spin").onclick = () => {
    spin = !spin;
    viewButtons();
    scheduleAnimation();
  };
  window.OrcaBoxStudio = {
    handleHostMessage: receive,
    getState: () => clone(p),
    getSceneBounds: sceneBounds,
    fitCamera: () => {
      zoom = 1;
      render();
      return lastFrame
        ? {
            distance: lastFrame.distance,
            target: lastFrame.target,
            bounds: lastFrame.bounds,
          }
        : null;
    },
  };
  updatePrinter();
  viewButtons();

  if (INITIAL.mode === "dock") {
    document.body.dataset.mode = "dock";
    document.body.dataset.dockTab = "shape";
  }
  if (hostThemeExplicit === false) {
    const injectedTheme = detectInjectedOrcaTheme();
    if (injectedTheme) theme = injectedTheme;
  }
  configureOpening();
  try {
    initializeGL();
  } catch (e) {
    status(String(e), true);
  }
  translate();
  sync();
  if (INITIAL.host) updatePrinter();
  if (INITIAL.meshes) loadMeshes(INITIAL.meshes);
  else requestPreview();
  watchHostTheme();
})();
</script>
  </body>
</html>
"""


def get_studio_html(
    mode: str = "page", initial_context: dict[str, Any] | None = None
) -> str:
    ctx = copy.deepcopy(initial_context) if isinstance(initial_context, dict) else {}
    ctx["params"] = normalize_params(ctx.get("params"))
    ctx.setdefault("presets", BUILTIN_PRESETS)
    ctx["mode"] = "dock" if str(mode).strip().lower() == "dock" else "page"
    lang = (
        "en"
        if str(ctx.get("lang") or ctx["params"].get("lang", "pt"))
        .lower()
        .startswith("en")
        else "pt"
    )
    theme = (
        "light"
        if str(ctx.get("theme") or ctx["params"].get("theme", "dark")).lower()
        == "light"
        else "dark"
    )
    ctx.update(lang=lang, theme=theme)
    payload = (
        json.dumps(ctx, ensure_ascii=False, separators=(",", ":"))
        .replace("</", "<\\/")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
    return (
        _BOX_HTML.replace("__INITIAL_LANG__", lang)
        .replace("__INITIAL_THEME__", theme)
        .replace("__INITIAL_MODE__", ctx["mode"])
        .replace("__BOX_CONTEXT__", payload)
    )
