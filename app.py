#!/usr/bin/env python3
"""
Subtitle Translator - 字幕翻译器
Standalone desktop app for translating subtitle files.
Supports SRT, VTT, ASS formats with multiple translation APIs.
"""

__author__ = "Ming"
__email__ = "l.umen@qq.com"
__url__ = "https://github.com/lumenming/SubtitleTranslator"
__version__ = "1.0.0"
__license__ = "MIT"

import json
import os
import re
import sys
import threading
from pathlib import Path

import webview
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)

CONFIG_FILE = Path.home() / ".subtitle-translator-config.json"

HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>字幕翻译器 - Subtitle Translator</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f0f2f5;color:#333;min-height:100vh}
.header{background:#fff;border-bottom:1px solid #e8e8e8;padding:14px 24px;display:flex;justify-content:space-between;align-items:center}
.header h1{font-size:18px;font-weight:600;color:#1a1a1a}
.btn-settings{background:none;border:1px solid #d0d0d0;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:13px;color:#666}
.btn-settings:hover{background:#f5f5f5}
.container{max-width:960px;margin:0 auto;padding:20px}

/* Upload */
.upload-zone{border:2px dashed #d0d0d0;border-radius:10px;padding:40px 20px;text-align:center;background:#fff;cursor:pointer;transition:all .2s}
.upload-zone:hover,.upload-zone.drag-over{border-color:#4f46e5;background:#f8f7ff}
.upload-zone .icon{font-size:40px;margin-bottom:8px}
.upload-zone h3{font-size:15px;margin-bottom:6px;color:#555;font-weight:500}
.upload-zone p{font-size:12px;color:#999}
.file-card{display:none;margin-top:12px;padding:12px 16px;background:#fff;border-radius:8px;border:1px solid #e8e8e8;align-items:center;gap:12px}
.file-card.active{display:flex}
.file-card .fname{font-weight:500;font-size:13px;flex:1}
.file-card .fstat{font-size:12px;color:#999}
.file-card .fremove{background:none;border:none;color:#999;cursor:pointer;font-size:16px;padding:4px}

/* Panels */
.panel{background:#fff;border-radius:10px;border:1px solid #e8e8e8;margin-top:16px;overflow:hidden}
.panel-header{padding:12px 16px;border-bottom:1px solid #f0f0f0;font-weight:600;font-size:13px;display:flex;justify-content:space-between;align-items:center}
.panel-body{padding:16px}

/* Controls */
.controls{display:flex;gap:12px;flex-wrap:wrap;align-items:end}
.field{display:flex;flex-direction:column;gap:5px}
.field label{font-size:12px;font-weight:500;color:#888}
.field select,.field input{padding:7px 10px;border:1px solid #ddd;border-radius:6px;font-size:13px;background:#fff;outline:none;min-width:160px}
.field select:focus,.field input:focus{border-color:#4f46e5}
.btn{padding:8px 18px;border:none;border-radius:6px;font-size:13px;font-weight:500;cursor:pointer;transition:all .15s;white-space:nowrap}
.btn-go{background:#4f46e5;color:#fff}
.btn-go:hover{background:#4338ca}
.btn-go:disabled{background:#c7c7c7;cursor:not-allowed}
.btn-dl{background:#fff;color:#4f46e5;border:1px solid #4f46e5}
.btn-dl:hover{background:#f8f7ff}
.btn-dl:disabled{border-color:#ddd;color:#999;cursor:not-allowed}

/* Status */
.status{display:none;margin-top:12px;padding:10px 14px;border-radius:6px;font-size:12px}
.status.show{display:block}
.status.info{background:#eff6ff;color:#2563eb;border:1px solid #bfdbfe}
.status.ok{background:#f0fdf4;color:#16a34a;border:1px solid #bbf7d0}
.status.err{background:#fef2f2;color:#dc2626;border:1px solid #fecaca}

/* Progress */
.progress-wrap{display:none;margin-top:12px}
.progress-wrap.active{display:block}
.progress-bar{height:5px;background:#e8e8e8;border-radius:3px;overflow:hidden}
.progress-fill{height:100%;background:#4f46e5;border-radius:3px;transition:width .3s;width:0}
.progress-text{font-size:11px;color:#999;margin-top:4px;text-align:center}

/* Preview table */
.preview-wrap{display:none;margin-top:16px}
.preview-wrap.active{display:block}
.subtitle-table{width:100%;border-collapse:collapse;font-size:12px}
.subtitle-table th{text-align:left;padding:8px 12px;background:#fafafa;border-bottom:1px solid #e8e8e8;font-weight:500;color:#888;font-size:11px}
.subtitle-table td{padding:8px 12px;border-bottom:1px solid #f0f0f0;vertical-align:top;line-height:1.5}
.subtitle-table tr:nth-child(even) td{background:#fafafa}
.col-idx{width:50px;color:#aaa}
.col-orig{width:45%}
.col-trans{width:45%;color:#4f46e5}
.preview-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.preview-header span{font-size:12px;color:#888}

/* Modal */
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:100;justify-content:center;align-items:center}
.modal-overlay.active{display:flex}
.modal{background:#fff;border-radius:12px;width:520px;max-height:80vh;overflow-y:auto;box-shadow:0 8px 30px rgba(0,0,0,.15)}
.modal-header{padding:14px 18px;border-bottom:1px solid #eee;display:flex;justify-content:space-between;align-items:center}
.modal-header h3{font-size:15px;font-weight:600}
.modal-close{background:none;border:none;font-size:18px;cursor:pointer;color:#999}
.modal-body{padding:18px}
.modal-body label{display:block;font-size:12px;font-weight:500;color:#666;margin-bottom:4px;margin-top:14px}
.modal-body label:first-child{margin-top:0}
.modal-body input,.modal-body select,.modal-body textarea{width:100%;padding:8px 10px;border:1px solid #ddd;border-radius:6px;font-size:13px;outline:none;font-family:inherit}
.modal-body input:focus,.modal-body select:focus,.modal-body textarea:focus{border-color:#4f46e5}
.modal-body textarea{resize:vertical;min-height:60px;font-family:monospace}
.modal-body .hint{font-size:11px;color:#999;margin-top:3px}
.modal-footer{padding:14px 18px;border-top:1px solid #eee;display:flex;justify-content:flex-end;gap:8px}

@media(max-width:640px){
.container{padding:10px}
.controls{flex-direction:column}
.field select,.field input{min-width:100%}
.subtitle-table{font-size:11px}
.subtitle-table td,.subtitle-table th{padding:6px 8px}
.col-orig,.col-trans{width:auto}
}
.footer{text-align:center;padding:14px 20px;font-size:12px;color:#aaa;border-top:1px solid #eee;margin-top:20px;background:#fafafa}
.footer span{color:#666;font-weight:500}

/* Dark mode */
body.dark{background:#1e1e2e;color:#cdd6f4}
body.dark .header{background:#181825;border-color:#313244}
body.dark .header h1{color:#cdd6f4}
body.dark .btn-settings{color:#a6adc8;border-color:#45475a;background:transparent}
body.dark .btn-settings:hover{background:#313244}
body.dark .upload-zone{background:#181825;border-color:#45475a}
body.dark .upload-zone h3{color:#a6adc8}
body.dark .upload-zone p{color:#6c7086}
body.dark .upload-zone:hover,.dark .upload-zone.drag-over{border-color:#89b4fa;background:#1e1e2e}
body.dark .file-card{background:#181825;border-color:#313244}
body.dark .file-card .fstat{color:#6c7086}
body.dark .file-card .fremove{color:#6c7086}
body.dark .panel{background:#181825;border-color:#313244}
body.dark .panel-header{border-color:#313244}
body.dark .field label{color:#a6adc8}
body.dark .field select,body.dark .field input{background:#1e1e2e;border-color:#45475a;color:#cdd6f4}
body.dark .field select:focus,body.dark .field input:focus{border-color:#89b4fa}
body.dark .btn-dl{background:transparent;color:#89b4fa;border-color:#89b4fa}
body.dark .btn-dl:hover{background:#1e1e2e}
body.dark .btn-dl:disabled{border-color:#45475a;color:#6c7086}
body.dark .btn-go:disabled{background:#45475a}
body.dark .subtitle-table th{background:#1e1e2e;border-color:#313244;color:#6c7086}
body.dark .subtitle-table td{border-color:#313244}
body.dark .subtitle-table tr:nth-child(even) td{background:#1e1e2e}
body.dark .col-trans{color:#a6e3a1}
body.dark .modal{background:#1e1e2e;box-shadow:0 8px 30px rgba(0,0,0,.5)}
body.dark .modal-header{border-color:#313244}
body.dark .modal-body label{color:#a6adc8}
body.dark .modal-body input,.dark .modal-body select,.dark .modal-body textarea{background:#181825;border-color:#45475a;color:#cdd6f4}
body.dark .modal-body input:focus,.dark .modal-body select:focus,.dark .modal-body textarea:focus{border-color:#89b4fa}
body.dark .modal-footer{border-color:#313244}
body.dark .modal-close{color:#6c7086}
body.dark .progress-bar{background:#313244}
body.dark .progress-text{color:#6c7086}
body.dark .footer{background:#181825;border-color:#313244;color:#6c7086}
body.dark .footer span{color:#a6adc8}
body.dark .btn-go{background:#89b4fa;color:#1e1e2e}
body.dark .btn-go:hover{background:#b4d0fb}
body.dark .status.info{background:#1e1e2e;color:#89b4fa;border-color:#45475a}
body.dark .status.ok{background:#1e1e2e;color:#a6e3a1;border-color:#45475a}
body.dark .status.err{background:#1e1e2e;color:#f38ba8;border-color:#45475a}
body.dark .preview-header span{color:#6c7086}
body.dark ::-webkit-scrollbar{width:8px}
body.dark ::-webkit-scrollbar-track{background:#1e1e2e}
body.dark ::-webkit-scrollbar-thumb{background:#45475a;border-radius:4px}
body.dark .modal-body{color:#cdd6f4}
body.dark .modal-body [style*="color:#888"]{color:#a6adc8!important}
body.dark .modal-body [style*="color:#999"]{color:#6c7086!important}
body.dark .modal-body [style*="color:#555"]{color:#cdd6f4!important}
body.dark .modal-body [style*="border-top:1px solid #eee"]{border-color:#313244!important}
</style>
</head>
<body>

<div class="header">
  <h1>字幕翻译器</h1>
  <div style="display:flex;gap:8px">
    <button class="btn-settings" id="darkToggle" onclick="toggleDark()">🌙</button>
    <button class="btn-settings" onclick="openAbout()">ℹ 关于</button>
    <button class="btn-settings" onclick="openSettings()">⚙ API 设置</button>
  </div>
</div>

<div class="container">

  <!-- Upload -->
  <div class="upload-zone" id="uploadZone">
    <div class="icon">📁</div>
    <h3>拖放字幕文件到此处，或点击选择</h3>
    <p>支持 SRT · VTT · ASS 格式</p>
    <input type="file" id="fileInput" hidden accept=".srt,.vtt,.ass">
  </div>

  <div class="file-card" id="fileCard">
    <span class="fname" id="fname"></span>
    <span class="fstat" id="fstat"></span>
    <button class="fremove" onclick="clearFile()" title="移除">×</button>
  </div>

  <!-- Settings -->
  <div class="panel">
    <div class="panel-header">翻译选项</div>
    <div class="panel-body">
      <div class="controls">
        <div class="field">
          <label>源语言</label>
          <select id="srcLang">
            <option value="auto">自动检测</option>
            <option value="en">英语 English</option>
            <option value="zh-CN">中文 (简体)</option>
            <option value="zh-TW">中文 (繁体)</option>
            <option value="ja">日语 日本語</option>
            <option value="ko">韩语 한국어</option>
            <option value="fr">法语 Français</option>
            <option value="de">德语 Deutsch</option>
            <option value="es">西班牙语 Español</option>
            <option value="pt">葡萄牙语 Português</option>
            <option value="id">印尼语 Bahasa Indonesia</option>
            <option value="ru">俄语 Русский</option>
            <option value="ar">阿拉伯语 العربية</option>
            <option value="th">泰语 ไทย</option>
            <option value="vi">越南语 Tiếng Việt</option>
            <option value="it">意大利语 Italiano</option>
            <option value="nl">荷兰语 Nederlands</option>
            <option value="pl">波兰语 Polski</option>
            <option value="tr">土耳其语 Türkçe</option>
            <option value="hi">印地语 हिन्दी</option>
          </select>
        </div>
        <div class="field">
          <label>目标语言</label>
          <select id="tgtLang">
            <option value="zh-CN">中文 (简体)</option>
            <option value="zh-TW">中文 (繁体)</option>
            <option value="en">英语 English</option>
            <option value="ja">日语 日本語</option>
            <option value="ko">韩语 한국어</option>
            <option value="fr">法语 Français</option>
            <option value="de">德语 Deutsch</option>
            <option value="es">西班牙语 Español</option>
            <option value="pt">葡萄牙语 Português</option>
            <option value="id">印尼语 Bahasa Indonesia</option>
            <option value="ru">俄语 Русский</option>
            <option value="ar">阿拉伯语 العربية</option>
            <option value="th">泰语 ไทย</option>
            <option value="vi">越南语 Tiếng Việt</option>
            <option value="it">意大利语 Italiano</option>
            <option value="nl">荷兰语 Nederlands</option>
            <option value="pl">波兰语 Polski</option>
            <option value="tr">土耳其语 Türkçe</option>
            <option value="hi">印地语 हिन्दी</option>
          </select>
        </div>
        <button class="btn btn-go" id="goBtn" disabled onclick="startTranslate()">开始翻译</button>
        <button class="btn btn-dl" id="dlBtn" disabled onclick="downloadResult()">下载译文</button>
      </div>
    </div>
  </div>

  <!-- Status & Progress -->
  <div class="status" id="status"></div>
  <div class="progress-wrap" id="progressWrap">
    <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
    <div class="progress-text" id="progressText"></div>
  </div>

  <!-- Preview -->
  <div class="preview-wrap" id="previewWrap">
    <div class="preview-header">
      <span id="previewLabel">翻译结果</span>
    </div>
    <div style="max-height:500px;overflow-y:auto;border:1px solid #e8e8e8;border-radius:8px">
      <table class="subtitle-table">
        <thead><tr><th class="col-idx">#</th><th class="col-orig">原文</th><th class="col-trans">译文</th></tr></thead>
        <tbody id="previewBody"></tbody>
      </table>
    </div>
  </div>

</div>

<div class="footer">
  <span>字幕翻译器</span> v<span id="footerVersion">---</span> &nbsp;|&nbsp;
  作者: <span id="footerAuthor">---</span> &nbsp;|&nbsp;
  <span id="footerEmail">---</span>
</div>

<!-- Settings Modal -->
<div class="modal-overlay" id="settingsModal">
  <div class="modal">
    <div class="modal-header">
      <h3>API 设置</h3>
      <button class="modal-close" onclick="closeSettings()">×</button>
    </div>
    <div class="modal-body">
      <label>翻译服务</label>
      <select id="apiService" onchange="onServiceChange()">
        <option value="mymemory">MyMemory (免费，无需 Key)</option>
        <option value="google">Google Cloud Translation API</option>
        <option value="deepl">DeepL API</option>
        <option value="openai">OpenAI 兼容接口</option>
      </select>

      <div id="apiKeyGroup">
        <label>API Key</label>
        <input type="password" id="apiKey" placeholder="输入你的 API Key">
      </div>

      <div id="apiUrlGroup" style="display:none">
        <label>API 端点 URL</label>
        <input type="text" id="apiUrl" placeholder="https://api.openai.com/v1/chat/completions">
        <div class="hint">OpenAI 兼容接口的完整地址</div>
      </div>

      <div id="apiModelGroup" style="display:none">
        <label>模型名称</label>
        <input type="text" id="apiModel" placeholder="gpt-4o-mini">
      </div>

      <div id="apiPromptGroup" style="display:none">
        <label>翻译提示词</label>
        <textarea id="apiPrompt" placeholder="将以下文本翻译成目标语言，只返回译文，不要解释。"></textarea>
        <div class="hint">{"{{text}}"} 会被替换为原文</div>
      </div>

      <label style="margin-top:16px">请求间隔 (毫秒)</label>
      <input type="number" id="apiDelay" value="200" min="0" max="5000">
      <div class="hint">每条字幕之间的延迟，避免触发 API 速率限制</div>
    </div>
    <div class="modal-footer">
      <button class="btn btn-dl" onclick="testApi()">测试连接</button>
      <button class="btn btn-go" onclick="saveSettings()">保存设置</button>
    </div>
  </div>
</div>

<!-- About Modal -->
<div class="modal-overlay" id="aboutModal">
  <div class="modal">
    <div class="modal-header">
      <h3>关于</h3>
      <button class="modal-close" onclick="closeAbout()">×</button>
    </div>
    <div class="modal-body" style="text-align:center;line-height:1.8">
      <div style="font-size:40px;margin-bottom:8px">📝</div>
      <div style="font-size:20px;font-weight:600">字幕翻译器</div>
      <div style="font-size:13px;color:#888">Subtitle Translator</div>
      <div style="margin-top:8px;font-size:12px;color:#999">版本 <span id="aboutVersion">---</span></div>
      <hr style="border:none;border-top:1px solid #eee;margin:14px 0">
      <div style="font-size:13px;color:#555">
        <div>作者: <span id="aboutAuthor">---</span></div>
        <div>邮箱: <span id="aboutEmail">---</span></div>
        <div>网址: <span id="aboutUrl">---</span></div>
        <div>许可证: <span id="aboutLicense">---</span></div>
      </div>
      <hr style="border:none;border-top:1px solid #eee;margin:14px 0">
      <div style="font-size:12px;color:#999">
        <p>支持 SRT / VTT / ASS 格式的字幕翻译桌面工具。</p>
        <p>支持 MyMemory、Google、DeepL、OpenAI 等多种翻译服务。</p>
      </div>
    </div>
  </div>
</div>

<script>
// --- State ---
let subtitles = [];
let translated = [];
let originalExt = 'srt';

// --- Upload ---
const uz = document.getElementById('uploadZone');
const fi = document.getElementById('fileInput');
uz.addEventListener('click', () => fi.click());
fi.addEventListener('change', e => loadFile(e.target.files[0]));

uz.addEventListener('dragover', e => { e.preventDefault(); uz.classList.add('drag-over'); });
uz.addEventListener('dragleave', () => uz.classList.remove('drag-over'));
uz.addEventListener('drop', e => {
  e.preventDefault();
  uz.classList.remove('drag-over');
  if (e.dataTransfer.files[0]) loadFile(e.dataTransfer.files[0]);
});

function loadFile(file) {
  if (!file) return;
  originalExt = file.name.split('.').pop().toLowerCase();
  if (!['srt','vtt','ass'].includes(originalExt)) {
    showStatus('不支持的格式，请上传 SRT、VTT 或 ASS 文件', 'err');
    return;
  }
  const r = new FileReader();
  r.onload = e => {
    subtitles = parseSubtitles(e.target.result, originalExt);
    translated = [];
    document.getElementById('fname').textContent = file.name;
    document.getElementById('fstat').textContent = subtitles.length + ' 条字幕';
    document.getElementById('fileCard').classList.add('active');
    document.getElementById('goBtn').disabled = subtitles.length === 0;
    document.getElementById('dlBtn').disabled = true;
    document.getElementById('previewWrap').classList.remove('active');
    hideStatus();
    if (subtitles.length === 0) showStatus('未能解析到字幕内容', 'err');
  };
  r.readAsText(file);
}

function clearFile() {
  subtitles = [];
  translated = [];
  fi.value = '';
  document.getElementById('fileCard').classList.remove('active');
  document.getElementById('goBtn').disabled = true;
  document.getElementById('dlBtn').disabled = true;
  document.getElementById('previewWrap').classList.remove('active');
  hideStatus();
}

function parseSubtitles(text, fmt) {
  const entries = [];
  if (fmt === 'srt') {
    const blocks = text.trim().split(/\n\s*\n/);
    for (const b of blocks) {
      const lines = b.trim().split('\n');
      if (lines.length < 3) continue;
      const idx = parseInt(lines[0]);
      if (isNaN(idx)) continue;
      const m = lines[1].match(/([\d:,]+)\s*-->\s*([\d:,]+)/);
      if (!m) continue;
      entries.push({index:idx, start:m[1].trim(), end:m[2].trim(), text:lines.slice(2).join('\n').trim()});
    }
  } else if (fmt === 'vtt') {
    const blocks = text.replace(/^WEBVTT.*\n/, '').trim().split(/\n\s*\n/);
    let idx = 0;
    for (const b of blocks) {
      const lines = b.trim().split('\n');
      const m = lines[0].match(/([\d:.]+)\s*-->\s*([\d:.]+)/);
      if (!m) continue;
      idx++;
      entries.push({index:idx, start:m[1].trim(), end:m[2].trim(), text:lines.slice(1).join('\n').trim()});
    }
  } else if (fmt === 'ass') {
    const lines = text.split('\n');
    let inEv = false, idx = 0;
    for (const l of lines) {
      if (l.startsWith('[Events]')) { inEv = true; continue; }
      if (l.startsWith('[') && inEv) break;
      if (!inEv || !l.startsWith('Dialogue:')) continue;
      const parts = l.substring(9).split(',');
      if (parts.length < 9) continue;
      idx++;
      entries.push({index:idx, start:(parts[1]||'').trim(), end:(parts[2]||'').trim(),
        text: parts.slice(9).join(',').replace(/\\N/g,'\n').replace(/\{[^}]*\}/g,'').trim()});
    }
  }
  return entries;
}

// --- Translation ---
async function startTranslate() {
  if (!subtitles.length) return;
  const btn = document.getElementById('goBtn');
  btn.disabled = true;
  document.getElementById('dlBtn').disabled = true;
  document.getElementById('progressWrap').classList.add('active');
  document.getElementById('progressFill').style.width = '0';
  showStatus('正在翻译...', 'info');

  translated = [];
  const src = document.getElementById('srcLang').value;
  const tgt = document.getElementById('tgtLang').value;
  const total = subtitles.length;

  for (let i = 0; i < total; i++) {
    const text = subtitles[i].text;
    if (!text.trim()) {
      translated.push({...subtitles[i], text:''});
      continue;
    }
    try {
      const res = await fetch('/api/translate', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({text, from: src, to: tgt})
      });
      const data = await res.json();
      translated.push({...subtitles[i], text: data.translated || text});
    } catch(e) {
      translated.push({...subtitles[i], text});
    }
    const pct = Math.round((i+1)/total*100);
    document.getElementById('progressFill').style.width = pct+'%';
    document.getElementById('progressText').textContent = `${i+1} / ${total}`;
  }

  document.getElementById('progressWrap').classList.remove('active');
  showStatus(`翻译完成！${translated.length} 条字幕`, 'ok');
  document.getElementById('dlBtn').disabled = false;
  btn.disabled = false;
  renderPreview();
}

function renderPreview() {
  const display = translated.slice(0, 60);
  const tbody = document.getElementById('previewBody');
  tbody.innerHTML = display.map((s,i) =>
    `<tr><td class="col-idx">${s.index}</td><td class="col-orig">${esc(subtitles[i]?.text||'')}</td><td class="col-trans">${esc(s.text)}</td></tr>`
  ).join('');
  document.getElementById('previewLabel').textContent =
    `翻译结果 (${display.length}${translated.length > 60 ? ' / 共'+translated.length : ''} 条)`;
  document.getElementById('previewWrap').classList.add('active');
}

function esc(s) { const d=document.createElement('div'); d.textContent=s; return d.innerHTML; }

// --- Download ---
function downloadResult() {
  if (!translated.length) return;
  let content;
  const ext = originalExt;
  if (ext === 'srt') {
    content = translated.map((s,i) => `${i+1}\n${s.start} --> ${s.end}\n${s.text}\n`).join('\n');
  } else if (ext === 'vtt') {
    content = 'WEBVTT\n\n' + translated.map(s => `${s.start} --> ${s.end}\n${s.text}\n`).join('\n');
  } else if (ext === 'ass') {
    content = '[Script Info]\nTitle: Translated\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n';
    for (const s of translated) {
      content += `Dialogue: 0,${s.start},${s.end},Default,,0,0,0,,${s.text.replace(/\n/g,'\\N')}\n`;
    }
  }
  const blob = new Blob([content], {type:'text/plain;charset=utf-8'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  const base = document.getElementById('fname').textContent.replace(/\.[^.]+$/,'');
  const tgt = document.getElementById('tgtLang').value;
  a.download = `${base}.${tgt}.${ext}`;
  a.href = url; a.click();
  URL.revokeObjectURL(url);
}

// --- Settings ---
async function loadConfig() {
  try { const r = await fetch('/api/config'); const c = await r.json();
    document.getElementById('apiService').value = c.service || 'mymemory';
    document.getElementById('apiKey').value = c.api_key || '';
    document.getElementById('apiUrl').value = c.api_url || 'https://api.openai.com/v1/chat/completions';
    document.getElementById('apiModel').value = c.api_model || 'gpt-4o-mini';
    document.getElementById('apiPrompt').value = c.api_prompt || '将以下文本翻译成目标语言，只返回译文，不要解释。';
    document.getElementById('apiDelay').value = c.delay || 200;
    onServiceChange();
  } catch(e) {}
}
loadConfig();

function onServiceChange() {
  const s = document.getElementById('apiService').value;
  document.getElementById('apiKeyGroup').style.display = s === 'mymemory' ? 'none' : '';
  document.getElementById('apiUrlGroup').style.display = s === 'openai' ? '' : 'none';
  document.getElementById('apiModelGroup').style.display = s === 'openai' ? '' : 'none';
  document.getElementById('apiPromptGroup').style.display = s === 'openai' ? '' : 'none';
}

function openSettings() { document.getElementById('settingsModal').classList.add('active'); }
function closeSettings() { document.getElementById('settingsModal').classList.remove('active'); }

function openAbout() { document.getElementById('aboutModal').classList.add('active'); }
function closeAbout() { document.getElementById('aboutModal').classList.remove('active'); }

async function loadAbout() {
  try {
    const r = await fetch('/api/about');
    const d = await r.json();
    document.getElementById('aboutVersion').textContent = d.version;
    document.getElementById('aboutAuthor').textContent = d.author;
    document.getElementById('aboutEmail').textContent = d.email;
    document.getElementById('aboutUrl').textContent = d.url;
    document.getElementById('aboutLicense').textContent = d.license;
    document.getElementById('footerVersion').textContent = d.version;
    document.getElementById('footerAuthor').textContent = d.author;
    document.getElementById('footerEmail').textContent = d.email;
  } catch(e) {}
}
loadAbout();

// --- Dark mode ---
function setDark(on) {
  if (on) {
    document.body.classList.add('dark');
    document.getElementById('darkToggle').textContent = '☀️';
  } else {
    document.body.classList.remove('dark');
    document.getElementById('darkToggle').textContent = '🌙';
  }
  try { localStorage.setItem('darkMode', on ? '1' : '0'); } catch(e) {}
}
function toggleDark() { setDark(!document.body.classList.contains('dark')); }
(function(){
  const saved = (function(){ try { return localStorage.getItem('darkMode'); } catch(e) { return null; } })();
  setDark(saved === '1');
})();

async function saveSettings() {
  const cfg = {
    service: document.getElementById('apiService').value,
    api_key: document.getElementById('apiKey').value,
    api_url: document.getElementById('apiUrl').value,
    api_model: document.getElementById('apiModel').value,
    api_prompt: document.getElementById('apiPrompt').value,
    delay: parseInt(document.getElementById('apiDelay').value) || 200
  };
  await fetch('/api/config', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(cfg)});
  closeSettings();
  showStatus('设置已保存', 'ok');
}

async function testApi() {
  showStatus('正在测试 API 连接...', 'info');
  try {
    const r = await fetch('/api/test', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        service: document.getElementById('apiService').value,
        api_key: document.getElementById('apiKey').value,
        api_url: document.getElementById('apiUrl').value,
        api_model: document.getElementById('apiModel').value,
        api_prompt: document.getElementById('apiPrompt').value
      })
    });
    const d = await r.json();
    if (d.ok) showStatus('连接成功！测试翻译: ' + d.result, 'ok');
    else showStatus('连接失败: ' + d.error, 'err');
  } catch(e) {
    showStatus('连接失败: ' + e.message, 'err');
  }
}

// --- Helpers ---
function showStatus(msg, cls) {
  const el = document.getElementById('status');
  el.textContent = msg;
  el.className = 'status show ' + cls;
}
function hideStatus() {
  const el = document.getElementById('status');
  el.className = 'status';
}
</script>
</body>
</html>'''

# --- Translation API handlers ---

def translate_mymemory(text, from_lang, to_lang, config):
    import urllib.request
    import urllib.parse
    url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair={from_lang}|{to_lang}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
        if data.get('responseStatus') == 200:
            return data['responseData']['translatedText']
        raise Exception(data.get('responseDetails', 'Translation failed'))

def translate_google(text, from_lang, to_lang, config):
    import urllib.request
    api_key = config.get('api_key', '')
    if not api_key:
        raise Exception('请先设置 Google API Key')
    url = f"https://translation.googleapis.com/language/translate/v2"
    body = json.dumps({'q': text, 'source': from_lang, 'target': to_lang, 'format': 'text'}).encode()
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
    req.add_header('Authorization', f'Bearer {api_key}')
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
        return data['data']['translations'][0]['translatedText']

def translate_deepl(text, from_lang, to_lang, config):
    import urllib.request
    api_key = config.get('api_key', '')
    if not api_key:
        raise Exception('请先设置 DeepL API Key')
    # DeepL uses different language codes
    dl_map = {'zh-CN': 'ZH', 'zh-TW': 'ZH', 'en': 'EN', 'ja': 'JA', 'ko': 'KO',
              'fr': 'FR', 'de': 'DE', 'es': 'ES', 'pt': 'PT', 'id': 'ID',
              'ru': 'RU', 'ar': 'AR', 'it': 'IT', 'nl': 'NL', 'pl': 'PL', 'tr': 'TR'}
    dl_from = dl_map.get(from_lang, from_lang.upper())
    dl_to = dl_map.get(to_lang, to_lang.upper())
    url = "https://api-free.deepl.com/v2/translate" if ':fx' not in api_key else "https://api.deepl.com/v2/translate"
    body = urllib.parse.urlencode({'text': text, 'source_lang': dl_from, 'target_lang': dl_to}).encode()
    req = urllib.request.Request(url, data=body)
    req.add_header('Authorization', f'DeepL-Auth-Key {api_key}')
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
        return data['translations'][0]['text']

def translate_openai(text, from_lang, to_lang, config):
    import urllib.request
    api_key = config.get('api_key', '')
    api_url = config.get('api_url', 'https://api.openai.com/v1/chat/completions')
    api_model = config.get('api_model', 'gpt-4o-mini')
    api_prompt = config.get('api_prompt', '将以下文本翻译成目标语言，只返回译文，不要解释。')
    if not api_key:
        raise Exception('请先设置 API Key')

    lang_map = {'zh-CN': '简体中文', 'zh-TW': '繁体中文', 'en': '英语', 'ja': '日语', 'ko': '韩语',
                'fr': '法语', 'de': '德语', 'es': '西班牙语', 'pt': '葡萄牙语', 'id': '印尼语',
                'ru': '俄语', 'ar': '阿拉伯语', 'th': '泰语', 'vi': '越南语', 'it': '意大利语',
                'nl': '荷兰语', 'pl': '波兰语', 'tr': '土耳其语', 'hi': '印地语'}
    target_name = lang_map.get(to_lang, to_lang)
    prompt = api_prompt.replace('{{text}}', text).replace('{text}', text)
    system_msg = f'你是一个专业的翻译助手。请将用户输入的文本翻译成{target_name}。只返回翻译结果，不要添加任何解释、备注或标点符号以外的内容。'
    body = json.dumps({
        'model': api_model,
        'messages': [
            {'role': 'system', 'content': system_msg},
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0.3
    }).encode()
    req = urllib.request.Request(api_url, data=body, headers={'Content-Type': 'application/json'})
    req.add_header('Authorization', f'Bearer {api_key}')
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
        return data['choices'][0]['message']['content'].strip()

# --- Routes ---

def _load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def _save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/about')
def handle_about():
    return jsonify({
        'author': __author__,
        'email': __email__,
        'url': __url__,
        'version': __version__,
        'license': __license__,
    })

@app.route('/api/config', methods=['GET', 'POST'])
def handle_config():
    if request.method == 'GET':
        return jsonify(_load_config())
    cfg = request.get_json()
    _save_config(cfg)
    return jsonify({'ok': True})

@app.route('/api/translate', methods=['POST'])
def handle_translate():
    data = request.get_json()
    text = data.get('text', '')
    from_lang = data.get('from', 'auto')
    to_lang = data.get('to', 'zh-CN')
    config = _load_config()
    service = config.get('service', 'mymemory')

    translators = {
        'mymemory': translate_mymemory,
        'google': translate_google,
        'deepl': translate_deepl,
        'openai': translate_openai,
    }

    try:
        translator = translators.get(service, translate_mymemory)
        result = translator(text, from_lang, to_lang, config)
        return jsonify({'translated': result})
    except Exception as e:
        return jsonify({'translated': text, 'error': str(e)})

@app.route('/api/test', methods=['POST'])
def handle_test():
    data = request.get_json()
    service = data.get('service', 'mymemory')
    config = {
        'api_key': data.get('api_key', ''),
        'api_url': data.get('api_url', ''),
        'api_model': data.get('api_model', 'gpt-4o-mini'),
        'api_prompt': data.get('api_prompt', ''),
    }
    translators = {
        'mymemory': translate_mymemory,
        'google': translate_google,
        'deepl': translate_deepl,
        'openai': translate_openai,
    }
    try:
        translator = translators.get(service, translate_mymemory)
        result = translator('Hello, how are you?', 'en', 'zh-CN', config)
        return jsonify({'ok': True, 'result': result})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)})


def run_flask():
    app.run(host='127.0.0.1', port=5118, debug=False)

if __name__ == '__main__':
    print('字幕翻译器启动中...')
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
    webview.create_window('字幕翻译器 - Subtitle Translator', 'http://127.0.0.1:5118',
                          width=1000, height=720, resizable=True, min_size=(720, 500))
    webview.start()
    os._exit(0)
