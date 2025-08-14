from flask import Flask, request, jsonify, render_template_string, session
import os
import requests

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "changeme")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise Exception("Set the GROQ_API_KEY environment variable")

MODEL = "llama3-8b-8192"
MAX_HISTORY = 12  # system + last 6 exchanges

INDEX_HTML = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta charset="utf-8">
<title>Grok Mini</title>
<style>
  html,body {margin:0;font-family:sans-serif;background:#fff;color:#000;}
  .wrap {max-width:320px;margin:0 auto;padding:6px;}
  header {font-weight:700;font-size:16px;padding:6px 0;}
  #log {height:58vh;overflow:auto;border:1px solid #ccc;padding:6px;white-space:pre-wrap;font-size:14px;}
  .you {color:#003366;}
  .bot {color:#006600;}
  #compose {display:flex;flex-direction:column;gap:6px;margin-top:6px;}
  #msg {padding:6px;font-size:14px;}
  button {padding:8px;font-size:14px;background:#007bff;color:#fff;border:none;}
  button:active {background:#0056b3;}
  #clear {background:#dc3545;}
  small {color:#666;}
</style>
</head>
<body>
<div class="wrap">
  <header>🤖 Grok Mini</header>
  <div id="log"></div>
  <div id="compose">
    <input id="msg" autocomplete="off" placeholder="Type message..." />
    <button id="send">Send</button>
    <button id="clear">Clear Chat</button>
  </div>
  <div style="margin-top:6px"><small>Enter = send | 5 = focus</small></div>
</div>

<script>
const log = document.getElementById('log');
const msg = document.getElementById('msg');

function append(kind, text) {
  const el = document.createElement('div');
  el.className = kind;
  el.textContent = (kind === 'you' ? 'You: ' : 'Bot: ') + text;
  log.appendChild(el);

  // Trim old lines
  while (log.children.length > 20) {
    log.removeChild(log.firstChild);
  }
  // Always scroll to new element's top
  el.scrollIntoView({behavior: 'smooth', block: 'start'});
}

document.getElementById('send').onclick = send;
document.getElementById('clear').onclick = async () => {
  await fetch('/api/clear', {method:'POST'});
  log.innerHTML = '';
};

msg.onkeydown = e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    send();
  }
};

async function send(){
  const text = msg.value.trim();
  if (!text) return;
  append('you', text);
  msg.value = '';

  const botEl = document.createElement('div');
  botEl.className = 'bot';
  botEl.textContent = 'Bot: ...';
  log.appendChild(botEl);
  botEl.scrollIntoView({behavior: 'smooth', block: 'start'}); // Focus bot start

  try {
    const r = await fetch('/api/chat', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({text})
    });
    if (!r.ok) {
      botEl.textContent = 'Bot: [Error]';
    } else {
      const data = await r.json();
      botEl.textContent = 'Bot: ' + (data.reply || '[no reply]');
    }
  } catch {
    botEl.textContent = 'Bot: [Network error]';
  }
  botEl.scrollIntoView({behavior: 'smooth', block: 'start'}); // Keep showing start
}

// Focus box with key 5
document.addEventListener('keydown', e => {
  if (e.key === '5') {
    e.preventDefault();
    msg.focus();
  }
});
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
        session["history"] = [{"role": "system", "content": "You are a helpful assistant."}]

    session["history"].append({"role": "user", "content": user_text})

    # Limit history size
    if len(session["history"]) > MAX_HISTORY:
        session["history"] = [session["history"][0]] + session["history"][-(MAX_HISTORY-1):]

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"model": MODEL, "messages": session["history"]}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        result = response.json()
        answer = result["choices"][0]["message"]["content"].strip()

        session["history"].append({"role": "assistant", "content": answer})
        session.modified = True

        # Limit again after adding bot
        if len(session["history"]) > MAX_HISTORY:
            session["history"] = [session["history"][0]] + session["history"][-(MAX_HISTORY-1):]

        return jsonify({"reply": answer})
    except Exception as e:
        return f"API error: {e}", 500

@app.route("/api/clear", methods=["POST"])
def clear_history():
    session.pop("history", None)
    return "cleared"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))