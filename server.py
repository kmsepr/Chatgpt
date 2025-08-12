from flask import Flask, request, jsonify, render_template_string, session
import os
import requests

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super-secret-key")  # Change in production!

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise Exception("Set the GROQ_API_KEY environment variable")

MODEL = "llama3-8b-8192"  # Adjust if needed

INDEX_HTML = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta charset="utf-8">
<title>Mini AI Chat (Groq API)</title>
<style>
  html, body {
    height: 100%; margin: 0; font-family: system-ui, Arial; background: #fff; color: #000;
  }
  .wrap {
    max-width: 600px; margin: 0 auto; padding: 12px; box-sizing: border-box;
    height: 100vh; display: flex; flex-direction: column;
  }
  header {
    font-weight: 700; font-size: 20px; padding: 12px 0;
  }
  #log {
    flex: 1 1 auto;
    overflow-y: auto;
    border: 1px solid #ccc;
    padding: 12px;
    white-space: pre-wrap;
    font-size: 16px;
    line-height: 1.4;
  }
  .you { color: #003366; margin-bottom: 8px; }
  .bot { color: #006600; margin-bottom: 12px; }
  a {
    color: #008000; text-decoration: underline;
  }
  #compose {
    margin-top: 6px;
    gap: 4px;
    display: none; /* hidden by default */
    flex-wrap: nowrap;
    align-items: center;
  }
  #msg {
    flex: 1 1 auto;
    padding: 8px 12px;
    font-size: 16px;
    min-width: 0;
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
    transition: background-color 0.2s ease;
  }
  #send:hover {
    background-color: #005500;
  }
  small {
    color: #666;
    margin-top: 6px;
  }
</style>
</head>
<body>
<div class="wrap">
  <header>Mini AI Chat (Groq API)</header>
  <div id="log" aria-live="polite" tabindex="0"></div>
  <div id="compose">
    <input id="msg" autocomplete="off" placeholder="Type message..." spellcheck="false" />
    <button id="send" aria-label="Send message">Send</button>
  </div>
  <div><small>Press 5 to edit, 0 to send, Enter to send</small></div>
</div>

<script>
const log = document.getElementById('log');
const compose = document.getElementById('compose');
const msg = document.getElementById('msg');
const sendBtn = document.getElementById('send');

function linkify(text) {
  const urlRegex = /(\bhttps?:\/\/[^\s<>"]+|\bwww\.[^\s<>"]+)/gi;
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

function showCompose(show) {
  compose.style.display = show ? 'flex' : 'none';
  if (show) {
    msg.focus();
  }
}

msg.addEventListener('keydown', function(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    send();
  }
});

sendBtn.addEventListener('click', send);

document.addEventListener('keydown', function(e) {
  // If focus is on input or textarea, allow '0' to send
  if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
    if (e.key === '0') {
      e.preventDefault();
      send();
    }
    return;
  }
  if (e.key === '5') {
    e.preventDefault();
    showCompose(true);
  } else if (e.key === '0') {
    e.preventDefault();
    send();
  }
});

async function send(){
  const text = msg.value.trim();
  if (!text) return;
  append('you', text);
  msg.value = '';
  showCompose(false);
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
    if(last) last.innerHTML = 'Bot: ' + linkify(data.reply || '[no reply]');
    log.scrollTop = log.scrollHeight;
  } catch(e) {
    const last = log.lastChild;
    if(last) last.innerHTML = 'Bot: [Network error]';
  }
}
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(INDEX_HTML)

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True) or {}
    user_text = data.get("text", "").strip()
    if not user_text:
        return "Empty message", 400

    if "history" not in session:
        session["history"] = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]

    session["history"].append({"role": "user", "content": user_text})

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": session["history"]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        result = response.json()
        answer = result["choices"][0]["message"]["content"].strip()

        session["history"].append({"role": "assistant", "content": answer})

        return jsonify({"reply": answer})
    except Exception as e:
        return f"API error: {e}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))