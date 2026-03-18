import React, { startTransition, useDeferredValue, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { FiDownloadCloud, FiLayers, FiZap } from "react-icons/fi";

import InputForm from "./components/InputForm";
import SettingsPanel from "./components/SettingsPanel";
import SlidePreview from "./components/SlidePreview";
import Slideshow from "./components/Slideshow";


const API_BASE = process.env.REACT_APP_API_BASE || "http://127.0.0.1:5000";

const appStyles = `
  :root {
    --bg: #f5f7ff;
    --panel: rgba(255, 255, 255, 0.82);
    --panel-solid: #ffffff;
    --stroke: rgba(148, 163, 184, 0.2);
    --stroke-strong: rgba(99, 102, 241, 0.24);
    --text: #0f172a;
    --muted: #52607a;
    --brand-start: #2563eb;
    --brand-end: #7c3aed;
    --brand-soft: rgba(59, 130, 246, 0.1);
    --emerald-soft: rgba(16, 185, 129, 0.1);
    --danger-soft: rgba(244, 63, 94, 0.14);
    --shadow-lg: 0 32px 80px rgba(15, 23, 42, 0.12);
    --shadow-md: 0 18px 45px rgba(15, 23, 42, 0.08);
    --radius-xl: 28px;
    --radius-lg: 22px;
    --radius-md: 16px;
  }

  * {
    box-sizing: border-box;
  }

  body {
    margin: 0;
    font-family: "Inter", "Segoe UI", sans-serif;
    color: var(--text);
    background:
      radial-gradient(circle at 10% 0%, rgba(96, 165, 250, 0.2), transparent 34%),
      radial-gradient(circle at 100% 0%, rgba(168, 85, 247, 0.18), transparent 24%),
      linear-gradient(180deg, #fbfcff 0%, var(--bg) 100%);
  }

  button,
  input,
  select,
  textarea {
    font: inherit;
  }

  button {
    cursor: pointer;
  }

  .app-shell {
    min-height: 100vh;
    padding: 40px 20px 72px;
  }

  .app-frame {
    width: min(100%, 1180px);
    margin: 0 auto;
  }

  .hero {
    display: grid;
    gap: 20px;
    margin-bottom: 28px;
  }

  .hero-top {
    display: grid;
    grid-template-columns: minmax(0, 1.35fr) minmax(280px, 360px);
    gap: 24px;
    align-items: stretch;
  }

  .hero-card,
  .panel {
    position: relative;
    overflow: hidden;
    background: var(--panel);
    backdrop-filter: blur(18px);
    border: 1px solid var(--stroke);
    border-radius: var(--radius-xl);
    box-shadow: var(--shadow-lg);
  }

  .hero-card {
    padding: 30px;
  }

  .hero-card::before,
  .panel::before {
    content: "";
    position: absolute;
    inset: 0 auto auto 0;
    width: 100%;
    height: 1px;
    background: linear-gradient(90deg, rgba(255, 255, 255, 0.9), rgba(255, 255, 255, 0));
    pointer-events: none;
  }

  .hero-badge,
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    border-radius: 999px;
    padding: 9px 14px;
    background: rgba(255, 255, 255, 0.76);
    border: 1px solid rgba(148, 163, 184, 0.18);
    color: #334155;
    font-size: 0.84rem;
    font-weight: 700;
  }

  .hero-badge {
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.12), rgba(124, 58, 237, 0.14));
    color: #1e3a8a;
  }

  .badge.subtle {
    background: rgba(248, 250, 252, 0.82);
    color: var(--muted);
  }

  .hero-title {
    margin: 18px 0 12px;
    font-size: clamp(2.5rem, 5vw, 4.6rem);
    line-height: 0.94;
    letter-spacing: -0.055em;
    max-width: 11ch;
  }

  .hero-copy {
    margin: 0;
    max-width: 62ch;
    color: var(--muted);
    font-size: 1.02rem;
    line-height: 1.75;
  }

  .hero-subcopy {
    margin: 18px 0 0;
    color: #334155;
    font-size: 0.95rem;
    font-weight: 600;
  }

  .metric-stack {
    display: grid;
    gap: 14px;
  }

  .metric-card {
    padding: 20px;
    border-radius: var(--radius-lg);
    border: 1px solid rgba(148, 163, 184, 0.16);
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.94)),
      linear-gradient(135deg, rgba(37, 99, 235, 0.1), rgba(124, 58, 237, 0.1));
    box-shadow: var(--shadow-md);
  }

  .metric-label {
    display: flex;
    align-items: center;
    gap: 10px;
    color: var(--muted);
    font-size: 0.9rem;
    font-weight: 700;
    margin-bottom: 10px;
  }

  .metric-value {
    margin: 0;
    font-size: 1.5rem;
    letter-spacing: -0.04em;
  }

  .metric-note {
    margin: 6px 0 0;
    color: var(--muted);
    font-size: 0.92rem;
  }

  .status-row {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }

  .status-pill,
  .file-pill,
  .slide-counter,
  .quiz-index,
  .setting-value,
  .slide-tab-index,
  .grid-slide-counter,
  .slideshow-counter {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 999px;
    padding: 8px 12px;
    background: rgba(255, 255, 255, 0.88);
    border: 1px solid rgba(148, 163, 184, 0.18);
    color: #334155;
    font-size: 0.84rem;
    font-weight: 700;
  }

  .status-pill.ready {
    background: rgba(16, 185, 129, 0.12);
    color: #047857;
  }

  .status-pill.error {
    background: rgba(244, 63, 94, 0.14);
    color: #be123c;
  }

  .panel {
    padding: 24px;
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    gap: 18px;
    align-items: flex-start;
    margin-bottom: 20px;
  }

  .panel-header.compact {
    margin-bottom: 14px;
  }

  .panel-header h2,
  .panel-header h3,
  .panel-header h4 {
    margin: 0;
    letter-spacing: -0.04em;
  }

  .panel-copy,
  .muted-copy {
    margin: 8px 0 0;
    color: var(--muted);
    line-height: 1.7;
  }

  .eyebrow {
    margin: 0 0 8px;
    color: #4f46e5;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    font-size: 0.72rem;
    font-weight: 800;
  }

  .controls-grid {
    display: grid;
    grid-template-columns: minmax(0, 1.35fr) minmax(300px, 0.9fr);
    gap: 24px;
    margin-bottom: 24px;
    align-items: start;
  }

  .control-stack {
    display: grid;
    gap: 24px;
  }

  .input-form,
  .settings-grid {
    display: grid;
    gap: 20px;
  }

  .hero-chip-group,
  .slide-meta-stack,
  .slide-toolbar,
  .workspace-actions,
  .utility-list,
  .preview-inline-actions,
  .slide-stage-actions,
  .slideshow-toolbar {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: center;
  }

  .input-form label,
  .setting-label {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    color: var(--text);
    font-size: 0.92rem;
    font-weight: 700;
  }

  .notes-textarea,
  .slide-title-input,
  .point-input,
  .difficulty-select {
    width: 100%;
    border-radius: 20px;
    border: 1px solid rgba(148, 163, 184, 0.25);
    background: rgba(255, 255, 255, 0.92);
    color: var(--text);
    transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
  }

  .notes-textarea,
  .point-input,
  .difficulty-select {
    padding: 16px 18px;
  }

  .notes-textarea {
    min-height: 220px;
    resize: vertical;
    line-height: 1.7;
  }

  .difficulty-select {
    appearance: none;
  }

  .slide-title-input {
    padding: 0;
    border: none;
    background: transparent;
    font-size: clamp(1.85rem, 3vw, 2.7rem);
    line-height: 1.02;
    font-weight: 800;
    letter-spacing: -0.05em;
  }

  .point-input {
    min-height: 86px;
    resize: vertical;
    line-height: 1.65;
  }

  .notes-textarea:focus,
  .slide-title-input:focus,
  .point-input:focus,
  .difficulty-select:focus,
  .range-slider:focus {
    outline: none;
    border-color: rgba(79, 70, 229, 0.32);
    box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.14);
  }

  .input-footer {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 220px;
    gap: 18px;
    align-items: stretch;
  }

  .submit-stack {
    display: grid;
    gap: 14px;
    align-content: space-between;
  }

  .upload-zone {
    position: relative;
    overflow: hidden;
    display: grid;
    gap: 12px;
    align-content: start;
    padding: 22px;
    min-height: 150px;
    border-radius: 22px;
    border: 1px dashed rgba(99, 102, 241, 0.3);
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(238, 242, 255, 0.9)),
      linear-gradient(135deg, rgba(37, 99, 235, 0.08), rgba(124, 58, 237, 0.1));
    transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
  }

  .upload-zone.dragging {
    transform: translateY(-2px);
    border-color: rgba(79, 70, 229, 0.54);
    box-shadow: 0 18px 35px rgba(79, 70, 229, 0.12);
  }

  .upload-zone input[type="file"] {
    position: absolute;
    inset: 0;
    opacity: 0;
    cursor: pointer;
  }

  .upload-icon {
    width: 44px;
    height: 44px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 16px;
    background: rgba(99, 102, 241, 0.12);
    color: #4338ca;
    font-size: 1.3rem;
  }

  .upload-zone strong {
    font-size: 1rem;
  }

  .upload-zone p {
    margin: 0;
    color: var(--muted);
    line-height: 1.6;
  }

  .primary-button,
  .secondary-button,
  .icon-button,
  .download-button,
  .density-button,
  .view-toggle-button,
  .grid-slide-card,
  .slide-tab {
    border: none;
    transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease, opacity 0.18s ease;
  }

  .primary-button,
  .download-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    padding: 14px 18px;
    border-radius: 18px;
    color: #ffffff;
    font-weight: 800;
    background: linear-gradient(135deg, var(--brand-start), var(--brand-end));
    box-shadow: 0 18px 34px rgba(79, 70, 229, 0.22);
  }

  .secondary-button,
  .icon-button,
  .view-toggle-button,
  .density-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 12px 16px;
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(148, 163, 184, 0.18);
    color: var(--text);
    font-weight: 700;
  }

  .icon-button {
    min-width: 46px;
    padding: 12px;
  }

  .icon-button.ghost {
    background: rgba(248, 250, 252, 0.9);
  }

  .primary-button:hover,
  .secondary-button:hover,
  .icon-button:hover,
  .download-button:hover,
  .density-button:hover,
  .view-toggle-button:hover,
  .grid-slide-card:hover,
  .slide-tab:hover {
    transform: translateY(-1px);
  }

  .primary-button:disabled,
  .secondary-button:disabled,
  .icon-button:disabled,
  .download-button:disabled {
    opacity: 0.56;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }

  .spinner,
  .spinner-inline {
    display: inline-flex;
    width: 16px;
    height: 16px;
    border-radius: 999px;
    border: 2px solid rgba(255, 255, 255, 0.34);
    border-top-color: rgba(255, 255, 255, 0.95);
    animation: spin 0.9s linear infinite;
  }

  .spinner-inline {
    width: 18px;
    height: 18px;
    border-color: rgba(99, 102, 241, 0.18);
    border-top-color: rgba(79, 70, 229, 0.95);
  }

  .settings-grid {
    gap: 22px;
  }

  .setting-group {
    display: grid;
    gap: 12px;
  }

  .setting-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .density-toggle {
    display: grid;
    gap: 10px;
  }

  .density-button {
    justify-content: space-between;
    text-align: left;
  }

  .density-button.active,
  .view-toggle-button.active {
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.14), rgba(124, 58, 237, 0.14));
    border-color: rgba(99, 102, 241, 0.24);
    color: #312e81;
  }

  .density-copy {
    color: var(--muted);
    font-size: 0.82rem;
    font-weight: 600;
  }

  .range-slider {
    width: 100%;
    accent-color: #4f46e5;
  }

  .range-labels {
    display: flex;
    justify-content: space-between;
    color: var(--muted);
    font-size: 0.82rem;
    font-weight: 600;
  }

  .utility-panel .utility-list {
    display: grid;
    gap: 12px;
    margin-bottom: 18px;
  }

  .utility-item {
    display: flex;
    justify-content: space-between;
    gap: 14px;
    padding: 14px 16px;
    border-radius: 18px;
    background: rgba(248, 250, 252, 0.92);
    border: 1px solid rgba(148, 163, 184, 0.14);
  }

  .utility-item span {
    color: var(--muted);
    font-weight: 600;
  }

  .utility-item strong {
    text-align: right;
    max-width: 16ch;
    font-size: 0.95rem;
  }

  .workspace-panel {
    padding: 26px;
  }

  .workspace-header {
    display: flex;
    justify-content: space-between;
    gap: 18px;
    align-items: flex-start;
    margin-bottom: 20px;
  }

  .view-toggle {
    display: inline-flex;
    gap: 10px;
    padding: 6px;
    border-radius: 18px;
    background: rgba(248, 250, 252, 0.9);
    border: 1px solid rgba(148, 163, 184, 0.16);
  }

  .tab-rail {
    display: flex;
    gap: 12px;
    overflow-x: auto;
    padding-bottom: 8px;
    margin-bottom: 22px;
    scrollbar-width: thin;
  }

  .slide-tab {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    flex: 0 0 auto;
    max-width: 220px;
    padding: 10px 12px 10px 10px;
    border-radius: 999px;
    background: rgba(248, 250, 252, 0.96);
    border: 1px solid rgba(148, 163, 184, 0.16);
    color: var(--muted);
  }

  .slide-tab.active {
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.12), rgba(124, 58, 237, 0.14));
    border-color: rgba(99, 102, 241, 0.2);
    color: #1e1b4b;
    box-shadow: 0 16px 28px rgba(79, 70, 229, 0.12);
  }

  .slide-tab-label {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-size: 0.92rem;
    font-weight: 700;
  }

  .focus-stage {
    display: grid;
    gap: 18px;
  }

  .preview-inline-actions {
    justify-content: space-between;
  }

  .slide-toolbar {
    justify-content: space-between;
  }

  .muted-inline {
    color: var(--muted);
    font-size: 0.9rem;
    font-weight: 600;
  }

  .slide-type-badge.normal {
    background: rgba(37, 99, 235, 0.12);
    color: #1d4ed8;
  }

  .slide-type-badge.explanation {
    background: rgba(245, 158, 11, 0.16);
    color: #b45309;
  }

  .slide-type-badge.data {
    background: rgba(16, 185, 129, 0.14);
    color: #047857;
  }

  .slide-canvas,
  .slideshow-stage {
    position: relative;
    overflow: hidden;
    border-radius: 30px;
    background:
      radial-gradient(circle at top right, rgba(191, 219, 254, 0.34), transparent 34%),
      linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.96));
    border: 1px solid rgba(226, 232, 240, 0.9);
    box-shadow: var(--shadow-md);
  }

  .slide-canvas {
    display: grid;
    gap: 22px;
    min-height: 540px;
    padding: 34px;
  }

  .slide-canvas::before,
  .slideshow-stage::before {
    content: "";
    position: absolute;
    inset: 0 0 auto 0;
    height: 8px;
    background: linear-gradient(90deg, var(--brand-start), var(--brand-end));
  }

  .slide-card-kicker {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 0.78rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #4338ca;
    font-weight: 800;
  }

  .points-editor {
    display: grid;
    gap: 14px;
  }

  .point-row {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr) auto;
    gap: 14px;
    align-items: start;
  }

  .bullet-marker {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 38px;
    height: 38px;
    margin-top: 14px;
    border-radius: 14px;
    background: rgba(37, 99, 235, 0.1);
    color: #1d4ed8;
    font-size: 0.82rem;
    font-weight: 800;
  }

  .slide-footer-actions {
    display: flex;
    justify-content: flex-start;
  }

  .slide-nav-footer {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    align-items: center;
  }

  .nav-button {
    min-width: 132px;
  }

  .slide-counter-card {
    display: grid;
    justify-items: center;
    gap: 4px;
    padding: 14px 18px;
    min-width: 180px;
    border-radius: 20px;
    background: rgba(248, 250, 252, 0.9);
    border: 1px solid rgba(148, 163, 184, 0.14);
    text-align: center;
  }

  .slide-counter-label {
    color: var(--muted);
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 700;
  }

  .slide-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
  }

  .grid-slide-card {
    display: grid;
    gap: 14px;
    padding: 18px;
    border-radius: 22px;
    text-align: left;
    background: rgba(255, 255, 255, 0.94);
    border: 1px solid rgba(148, 163, 184, 0.16);
    box-shadow: var(--shadow-md);
  }

  .grid-slide-card.active {
    background: linear-gradient(180deg, rgba(238, 242, 255, 0.96), rgba(255, 255, 255, 0.96));
    border-color: rgba(99, 102, 241, 0.22);
  }

  .grid-slide-top {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    align-items: center;
  }

  .grid-slide-card h3 {
    margin: 0;
    font-size: 1.12rem;
    line-height: 1.3;
    letter-spacing: -0.03em;
  }

  .grid-slide-points {
    margin: 0;
    padding-left: 18px;
    color: var(--muted);
    line-height: 1.6;
  }

  .grid-slide-link {
    color: #4338ca;
    font-weight: 700;
  }

  .preview-empty {
    min-height: 340px;
    display: grid;
    place-items: center;
    text-align: center;
  }

  .loading-state {
    display: grid;
    gap: 14px;
    justify-items: center;
  }

  .quiz-block {
    margin-top: 28px;
    display: grid;
    gap: 16px;
  }

  .quiz-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 16px;
  }

  .quiz-card {
    display: grid;
    gap: 12px;
    align-content: start;
    padding: 20px;
    border-radius: 22px;
    background: rgba(255, 255, 255, 0.94);
    border: 1px solid rgba(148, 163, 184, 0.14);
    box-shadow: var(--shadow-md);
  }

  .quiz-card h4 {
    margin: 0;
    line-height: 1.55;
    font-size: 1rem;
  }

  .quiz-options {
    display: grid;
    gap: 10px;
  }

  .quiz-option-button {
    display: inline-flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 11px 12px;
    border-radius: 14px;
    border: 1px solid rgba(148, 163, 184, 0.18);
    background: rgba(248, 250, 252, 0.94);
    text-align: left;
    color: var(--text);
    transition: transform 0.18s ease, border-color 0.18s ease, background 0.18s ease;
  }

  .quiz-option-button:hover {
    transform: translateY(-1px);
    border-color: rgba(99, 102, 241, 0.2);
  }

  .quiz-option-button:disabled {
    opacity: 1;
  }

  .quiz-option-button.correct {
    background: rgba(16, 185, 129, 0.14);
    color: #047857;
    border-color: rgba(16, 185, 129, 0.2);
    font-weight: 700;
  }

  .quiz-option-button.incorrect {
    background: rgba(244, 63, 94, 0.12);
    color: #be123c;
    border-color: rgba(244, 63, 94, 0.18);
    font-weight: 700;
  }

  .quiz-option-button.revealed {
    opacity: 0.8;
    color: var(--muted);
  }

  .quiz-feedback,
  .quiz-prompt {
    margin: 0;
    font-size: 0.92rem;
  }

  .quiz-feedback.correct {
    color: #047857;
    font-weight: 800;
  }

  .quiz-feedback.incorrect {
    color: #be123c;
    font-weight: 800;
  }

  .quiz-prompt {
    color: var(--muted);
  }

  .chart-wrapper {
    padding: 18px;
    border-radius: 22px;
    background: rgba(248, 250, 252, 0.9);
    border: 1px solid rgba(148, 163, 184, 0.14);
  }

  .chart-header {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    align-items: center;
    margin-bottom: 14px;
  }

  .chart-surface {
    height: 260px;
  }

  .error-banner {
    margin-bottom: 18px;
    padding: 14px 16px;
    border-radius: 18px;
    background: rgba(255, 241, 242, 0.94);
    border: 1px solid rgba(251, 113, 133, 0.28);
    color: #be123c;
    font-weight: 700;
  }

  .slideshow-overlay {
    position: fixed;
    inset: 0;
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 22px;
    background:
      radial-gradient(circle at top left, rgba(59, 130, 246, 0.24), transparent 24%),
      radial-gradient(circle at top right, rgba(124, 58, 237, 0.2), transparent 24%),
      rgba(2, 6, 23, 0.96);
  }

  .slideshow-shell {
    width: min(100%, 1240px);
    display: grid;
    gap: 18px;
  }

  .slideshow-topbar {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    align-items: center;
    flex-wrap: wrap;
  }

  .slideshow-counter {
    background: rgba(255, 255, 255, 0.12);
    border-color: rgba(255, 255, 255, 0.12);
    color: #e2e8f0;
  }

  .slideshow-toolbar .secondary-button {
    background: rgba(255, 255, 255, 0.1);
    color: #e2e8f0;
    border-color: rgba(255, 255, 255, 0.14);
  }

  .slideshow-progress {
    height: 8px;
    border-radius: 999px;
    overflow: hidden;
    background: rgba(255, 255, 255, 0.08);
  }

  .slideshow-progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #60a5fa, #a855f7);
    transition: width 0.25s ease;
  }

  .slideshow-stage {
    min-height: calc(100vh - 210px);
    padding: clamp(26px, 4vw, 54px);
    box-shadow: 0 36px 110px rgba(0, 0, 0, 0.34);
  }

  .slideshow-stage-header {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    align-items: center;
    flex-wrap: wrap;
    margin-bottom: 20px;
  }

  .slideshow-title {
    margin: 0;
    font-size: clamp(2.3rem, 4vw, 4.2rem);
    line-height: 0.95;
    letter-spacing: -0.055em;
    max-width: 13ch;
  }

  .slideshow-divider {
    width: 92px;
    height: 5px;
    border-radius: 999px;
    margin: 22px 0 28px;
    background: linear-gradient(90deg, var(--brand-start), var(--brand-end));
  }

  .slideshow-points {
    margin: 0;
    padding: 0;
    list-style: none;
    display: grid;
    gap: 18px;
  }

  .slideshow-point {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr);
    gap: 16px;
    align-items: start;
    color: #1e293b;
    font-size: clamp(1rem, 2vw, 1.42rem);
    line-height: 1.6;
  }

  .slideshow-point-marker {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 2.25rem;
    height: 2.25rem;
    border-radius: 999px;
    background: rgba(37, 99, 235, 0.1);
    color: #1d4ed8;
    font-weight: 800;
  }

  .slideshow-hint {
    margin: 0;
    text-align: center;
    color: rgba(226, 232, 240, 0.8);
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }

    to {
      transform: rotate(360deg);
    }
  }

  @media (max-width: 1040px) {
    .hero-top,
    .controls-grid {
      grid-template-columns: 1fr;
    }
  }

  @media (max-width: 720px) {
    .app-shell {
      padding: 22px 14px 54px;
    }

    .hero-card,
    .panel {
      padding: 20px;
      border-radius: 24px;
    }

    .hero-title {
      max-width: none;
    }

    .workspace-header,
    .panel-header,
    .slide-toolbar,
    .slide-nav-footer,
    .slideshow-topbar {
      flex-direction: column;
      align-items: stretch;
    }

    .input-footer,
    .point-row {
      grid-template-columns: 1fr;
    }

    .bullet-marker {
      margin-top: 0;
    }

    .slide-canvas {
      min-height: auto;
      padding: 24px 20px;
    }

    .slide-counter-card,
    .nav-button,
    .primary-button,
    .secondary-button,
    .download-button {
      width: 100%;
    }

    .view-toggle,
    .workspace-actions,
    .preview-inline-actions,
    .slideshow-toolbar {
      width: 100%;
    }

    .view-toggle-button,
    .slideshow-toolbar .secondary-button,
    .slideshow-toolbar .primary-button {
      flex: 1 1 0;
      justify-content: center;
    }

    .slideshow-overlay {
      padding: 12px;
    }

    .slideshow-stage {
      min-height: calc(100vh - 190px);
      padding: 22px 18px;
    }

    .slideshow-point {
      grid-template-columns: 1fr;
    }
  }
`;

async function readJsonResponse(response, label) {
  console.log(`${label} status:`, response.status, "url:", response.url);
  const rawText = await response.text();
  console.log(`${label} raw response:`, rawText);

  if (!rawText) {
    throw new Error(
      `Empty response from server (${response.status}). Verify Flask is running and reachable at ${API_BASE}.`
    );
  }

  let data;
  try {
    data = JSON.parse(rawText);
  } catch (parseError) {
    console.error(`${label} JSON parse error:`, parseError);
    throw new Error("Invalid JSON response from server");
  }

  if (!response.ok) {
    throw new Error(data.error || `Server error (${response.status})`);
  }

  return data;
}

function App() {
  const [settings, setSettings] = useState({
    density: "concise",
    difficulty: "Beginner",
    slideCount: 8,
  });
  const [slides, setSlides] = useState([]);
  const [quiz, setQuiz] = useState([]);
  const [sessionId, setSessionId] = useState("");
  const [metadata, setMetadata] = useState(null);
  const [currentSlide, setCurrentSlide] = useState(0);
  const [viewMode, setViewMode] = useState("single");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [syncStatus, setSyncStatus] = useState("idle");
  const [isSlideshowOpen, setIsSlideshowOpen] = useState(false);
  const [regeneratingSlideIndex, setRegeneratingSlideIndex] = useState(null);
  const skipSyncRef = useRef(false);
  const deferredSlides = useDeferredValue(slides);
  const deferredQuiz = useDeferredValue(quiz);
  const requestedSlideCount = Math.max(5, Math.min(15, Number(settings.slideCount) || 8));

  useEffect(() => {
    if (!slides.length) {
      setCurrentSlide(0);
      return;
    }

    if (currentSlide >= slides.length) {
      setCurrentSlide(slides.length - 1);
    }
  }, [slides, currentSlide]);

  useEffect(() => {
    if (!sessionId || !slides.length) {
      return undefined;
    }

    if (skipSyncRef.current) {
      skipSyncRef.current = false;
      return undefined;
    }

    const timer = window.setTimeout(() => {
      syncSession();
    }, 600);

    return () => window.clearTimeout(timer);
  }, [sessionId, slides, quiz]);

  const syncSession = async () => {
    if (!sessionId) {
      return false;
    }

    try {
      setSyncStatus("saving");
      const response = await fetch(`${API_BASE}/sync-session/${sessionId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ slides, quiz }),
      });

      const data = await readJsonResponse(response, "Sync session");
      console.log("Sync session parsed response:", data);

      setError("");
      setSyncStatus("saved");
      return true;
    } catch (syncError) {
      setSyncStatus("error");
      setError(syncError.message || "Unable to sync slide edits.");
      return false;
    }
  };

  const handleSubmit = async ({ notes, file }) => {
    setLoading(true);
    setError("");
    setSyncStatus("idle");

    try {
      const formData = new FormData();
      formData.append("text", notes);
      if (file) {
        formData.append("file", file);
      }
      formData.append("density", settings.density);
      formData.append("difficulty", settings.difficulty);
      formData.append("slide_count", String(requestedSlideCount));

      const response = await fetch(`${API_BASE}/generate-slides`, {
        method: "POST",
        body: formData,
      });

      const data = await readJsonResponse(response, "Generate slides");
      console.log("Generate slides parsed response:", data);

      const nextSlides = (data.slides || []).slice(0, requestedSlideCount);
      const nextMetadata = {
        ...(data.metadata || {}),
        requested_slide_count: requestedSlideCount,
        displayed_slide_count: nextSlides.length,
      };

      skipSyncRef.current = true;
      startTransition(() => {
        setSlides(nextSlides);
        setQuiz(data.quiz || []);
        setSessionId(data.session_id || "");
        setMetadata(nextMetadata);
        setCurrentSlide(0);
        setViewMode("single");
        setSyncStatus("saved");
      });
    } catch (submissionError) {
      setError(submissionError.message || "Slide generation failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleSlideChange = (slideIndex, updatedSlide) => {
    startTransition(() => {
      setSlides((currentSlides) =>
        currentSlides.map((slide, index) => (index === slideIndex ? updatedSlide : slide))
      );
    });
  };

  const handleDownload = async () => {
    if (!sessionId) {
      return;
    }

    setError("");
    const saved = await syncSession();
    if (!saved) {
      return;
    }

    window.open(`${API_BASE}/download-ppt?session_id=${encodeURIComponent(sessionId)}`, "_blank");
  };

  const handleRegenerateSlide = async (slideIndex) => {
    if (!sessionId || slideIndex < 0 || slideIndex >= slides.length) {
      return;
    }

    setError("");
    setRegeneratingSlideIndex(slideIndex);

    try {
      const synced = await syncSession();
      if (!synced) {
        return;
      }

      const response = await fetch(`${API_BASE}/regenerate-slide`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          slide_index: slideIndex,
        }),
      });

      const data = await readJsonResponse(response, "Regenerate slide");
      console.log("Regenerate slide parsed response:", data);

      const deckLimit = metadata?.requested_slide_count || slides.length || requestedSlideCount;

      skipSyncRef.current = true;
      startTransition(() => {
        setSlides((data.slides || slides).slice(0, deckLimit));
        if (data.metadata) {
          setMetadata((currentMetadata) => ({ ...(currentMetadata || {}), ...data.metadata }));
        }
        if (data.slide_index !== undefined) {
          setCurrentSlide(data.slide_index);
        }
      });
    } catch (regenerationError) {
      setError(regenerationError.message || "Unable to regenerate the slide.");
    } finally {
      setRegeneratingSlideIndex(null);
    }
  };

  const handleStartSlideshow = (startIndex) => {
    const maxIndex = slides.length - 1;
    const safeIndex = Math.min(Math.max(startIndex, 0), Math.max(maxIndex, 0));
    setCurrentSlide(safeIndex);
    setIsSlideshowOpen(true);
  };

  const handleCloseSlideshow = (lastIndex) => {
    const maxIndex = slides.length - 1;
    const safeIndex = Math.min(Math.max(lastIndex, 0), Math.max(maxIndex, 0));
    setCurrentSlide(safeIndex);
    setIsSlideshowOpen(false);
  };

  return (
    <>
      <style>{appStyles}</style>
      {isSlideshowOpen ? (
        <Slideshow
          slides={slides}
          initialIndex={currentSlide}
          onClose={handleCloseSlideshow}
          quizCount={quiz.length}
        />
      ) : null}

      <main className="app-shell">
        <div className="app-frame">
          <motion.header
            className="hero"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, ease: "easeOut" }}
          >
            <div className="hero-top">
              <div className="hero-card">
                <span className="hero-badge">
                  <FiZap />
                  AI Class Slides Generator
                </span>
                <h1 className="hero-title">Build polished class decks from raw notes.</h1>
                <p className="hero-copy">
                  Paste notes or upload a PDF/TXT file, set the teaching depth, choose exactly how many
                  slides you want, and review a clean editable deck before exporting a PPT.
                </p>
                <p className="hero-subcopy">
                  Designed for quick lesson prep, one focused slide at a time.
                </p>
              </div>

              <div className="metric-stack">
                <div className="metric-card">
                  <div className="metric-label">
                    <FiLayers />
                    Target deck size
                  </div>
                  <h3 className="metric-value">{requestedSlideCount} slides</h3>
                  <p className="metric-note">Generated decks are trimmed to your selected slide count.</p>
                </div>

                <div className="metric-card">
                  <div className="metric-label">
                    <FiZap />
                    Active teaching mode
                  </div>
                  <h3 className="metric-value">
                    {settings.difficulty} · {settings.density === "concise" ? "Concise" : "Detailed"}
                  </h3>
                  <p className="metric-note">Slides stay aligned with your explanation level and density.</p>
                </div>
              </div>
            </div>

            <div className="status-row">
              <span className={`status-pill ${slides.length ? "ready" : ""}`}>
                {slides.length ? `${slides.length} slides ready` : "Awaiting notes"}
              </span>
              <span className={`status-pill ${syncStatus === "error" ? "error" : syncStatus === "saved" ? "ready" : ""}`}>
                {loading
                  ? "Generating..."
                  : syncStatus === "saving"
                    ? "Saving edits..."
                    : syncStatus === "saved"
                      ? "Edits synced"
                      : "Autosave idle"}
              </span>
              {metadata?.provider ? (
                <span className="status-pill">
                  Provider:{" "}
                  {metadata.provider === "fallback"
                    ? "heuristic fallback"
                    : metadata.used_llm
                      ? metadata.provider
                      : `${metadata.provider} fallback`}
                </span>
              ) : null}
            </div>
          </motion.header>

          <AnimatePresence>
            {error ? (
              <motion.div
                className="error-banner"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                {error}
              </motion.div>
            ) : null}
          </AnimatePresence>

          <section className="controls-grid">
            <InputForm loading={loading} onSubmit={handleSubmit} />

            <div className="control-stack">
              <SettingsPanel settings={settings} onChange={setSettings} />

              <motion.section
                className="panel utility-panel"
                initial={{ opacity: 0, y: 18 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1, duration: 0.3 }}
              >
                <div className="panel-header compact">
                  <div>
                    <p className="eyebrow">Export & Status</p>
                    <h2>Ready for presentation</h2>
                  </div>
                  <span className="badge subtle">
                    <FiDownloadCloud />
                    .pptx
                  </span>
                </div>

                <div className="utility-list">
                  <div className="utility-item">
                    <span>Slide preview mode</span>
                    <strong>{viewMode === "grid" ? "Grid overview" : "Single slide focus"}</strong>
                  </div>
                  <div className="utility-item">
                    <span>Quiz questions</span>
                    <strong>{quiz.length ? `${quiz.length} ready` : "Generated after deck build"}</strong>
                  </div>
                  <div className="utility-item">
                    <span>Presentation provider</span>
                    <strong>{metadata?.provider || "Will appear after generation"}</strong>
                  </div>
                </div>

                <button
                  type="button"
                  className="download-button"
                  onClick={handleDownload}
                  disabled={!sessionId || !slides.length}
                >
                  <FiDownloadCloud />
                  Download PPT
                </button>
              </motion.section>
            </div>
          </section>

          <SlidePreview
            slides={deferredSlides}
            currentSlide={currentSlide}
            onNavigate={(index) => {
              const maxIndex = deferredSlides.length - 1;
              const safeIndex = Math.min(Math.max(index, 0), Math.max(maxIndex, 0));
              setCurrentSlide(safeIndex);
            }}
            onSlideChange={handleSlideChange}
            quiz={deferredQuiz}
            onStartSlideshow={handleStartSlideshow}
            onRegenerateSlide={handleRegenerateSlide}
            regeneratingSlideIndex={regeneratingSlideIndex}
            loading={loading}
            viewMode={viewMode}
            onViewModeChange={setViewMode}
          />
        </div>
      </main>
    </>
  );
}

export default App;
