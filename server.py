from flask import Flask, request, jsonify, render_template_string, session
import os
import requests

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super-secret-key")  # Change in production!

# --- Setup API key ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise Exception("Set the GROQ_API_KEY environment variable first.")

MODEL = "llama3-8b-8192"  # Change if needed

# --- Minimal UI HTML ---
INDEX_HTML = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta charset="utf-8">
<title></title>
<style>
  html, body {
    height: 100%;
    margin: 0;
    font-family: system-ui, Arial;
    background: #fff;
    color: #000;
    display: flex;
    flex-direction: column;
  }
  #log {
    flex: 1 1 auto;
    overflow-y: auto;
    padding: 12px;
    box-sizing: border-box;
    white-space: pre-wrap;
    font-size: 16px;
    line-height: 1.4;
    border: none;
  }
  .you { color: #003366; margin-bottom: 8px; }
  .bot { color: #006600; margin-bottom: 12px; }
  a {
    color: #008000;
    text-decoration: underline;
  }
  #compose {
    display: flex;
    gap: 4px;
    padding: 8px;
    border-top: 1px solid #ccc;
    background: #fff;
  }
  #msg {
    flex: 1 1 auto;
    padding: 8px 12px;
    font-size: 16px;
    outline-color: #888;
    border: 1px solid #ccc;
    border-radius: 4px;
  }
  #send {
    padding: 8px 12px;
    font-size: 16px;
    cursor: pointer;
    border: 1px solid #006600;
    background: #008000;
    color: white;
    border-radius: 4px;
  }
  #send:hover {
    background: #005500;
  }
</style>
</head>
<body>
  <div id="log" aria-live="polite" tabindex="0"></div>
  <div id="compose">
    <input id="msg" autocomplete="off" placeholder="Type message..." spellcheck="false" />
    <button id="send" aria-label="Send message">Send</button>
  </div>

<script>
const log = document.getElementById('log');
const msg = document.getElementById('msg');
const sendBtn = document.getElementById('send');

function linkify(text) {
  const urlRegex = /(\\bhttps?:\\/\\/[^\\s<>"]+|\\bwww\\.[^\\s<>"]+)/gi;
  return text.replace(urlRegex, url => {
    let href = url;
    if (!href.startsWith('http')) href = 'http://' + href;
    return `<a href="${href}" target="_blank" rel="noopener noreferrer">${url}</a>`;
  });
}

function append(kind, text) {
  const el = document.createElement('div');
  el.className = kind;
  el.innerHTML = (kind === 'you' ? 'You: ' : 'Bot: ') + linkify(text);
  log.appendChild(el);
  log.scrollTop = log.scrollHeight;
}

async function send(){
  const text = msg.value.trim();
  if (!text) return;
  append('you', text);
  msg.value = '';
  append('bot', '...');
  try {
    const r = await fetch('/api/chat', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({text})
    });
    if (!r.ok) {
      const err = await r.text();
      const last = log.lastChild;
      if(last) last.innerHTML = 'Bot: [Error] ' + err;
      return;
    }
    const data = await r.json();
    const last = log.lastChild;
    if(last) last.innerHTML = '
