from flask import Flask, request, jsonify, render_template_string
import os
import requests

app = Flask(__name__)

# Your Groq API key — set as environment variable for safety
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise Exception("Set the GROQ_API_KEY environment variable")

MODEL = "llama3-8b-8192"  # Groq free model, adjust if needed

INDEX_HTML = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta charset="utf-8">
<title>Mini AI Chat (Groq API)</title>
<style>
  html,body{height:100%; margin:0; font-family:system-ui,Arial; background:#fff; color:#000}
  .wrap{max-width:320px; margin:0 auto; padding:6px; box-sizing:border-box}
  header{font-weight:700; font-size:16px; padding:6px 0}
  #log{height:58vh; overflow:auto; border:1px solid #ccc; padding:6px; white-space:pre-wrap; font-size:14px}
  .you{color:#003366; margin-bottom:4px}
  .bot{color:#006600; margin-bottom:6px}
  #compose {
    display: flex;
    gap: 4px;           /* smaller gap for tighter layout */
    margin-top: 6px;
  }
  #msg {
    flex: 1 1 auto;     /* take as much width as possible */
    padding: 8px 12px;  /* comfortable padding */
    font-size: 16px;    /* bigger font */
    min-width: 0;       /* fix shrinking issue */
    outline-color: #888;
    border: 1px solid #ccc;
    border-radius: 4px;
  }
  button {
    padding: 8px 12px;
    font-size: 16px;
    flex-shrink: 0;
    cursor: pointer;
    border: 1px solid #006600;
    background: #008000;
    color: white;
    border-radius: 4px;
    transition: background-color 0.2s ease;
  }
  button:hover {
    background-color: #005500;
  }
  small{color:#666}
</style>
</head>
<body>
<div class="wrap">
  <header>Mini AI Chat (Groq API)</header>
  <div id="log" tabindex="0" aria-live="polite"></div>
  <div id="compose">
    <input id="msg" autocomplete="off" placeholder="Type message..." spellcheck="false" />
    <button id="send" aria-label="Send message">Send</button>
  </div>
  <div style="margin-top:6px"><small>Press Enter to send</small></div>
</div>

<script>
const log = document.getElementById('log');
const msg = document.getElementById('msg');
const sendBtn = document.getElementById('send');

function append(kind, text) {
  const el = document.createElement('div');
  el.className = kind;
  el.textContent = (kind === 'you' ? 'You: ' : 'Bot: ') + text;
  log.appendChild(el);
  log.scrollTop = log.scrollHeight;
}

msg.addEventListener('keydown', function(e){
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    send();
  }
});

sendBtn.addEventListener('click', send);

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
      if(last) last.textContent = 'Bot: [Error] ' + err;
      return;
    }
    const data = await r.json();
    const last = log.lastChild;
    if(last) last.textContent = 'Bot: ' + (data.reply || '[no reply]');
    log.scrollTop = log.scrollHeight;
  } catch(e) {
    const last = log.lastChild;
    if(last) last.textContent = 'Bot: [Network error]';
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

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_text}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        result = response.json()
        answer = result["choices"][0]["message"]["content"].strip()
        return jsonify({"reply": answer})
    except Exception as e:
        return f"API error: {e}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))