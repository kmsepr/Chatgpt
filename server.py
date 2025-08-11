# server.py
from flask import Flask, request, Response, render_template_string, jsonify
import os
import openai
import time

# Load API key from environment
openai.api_key = os.getenv("OPENAI_API_KEY")

# Config
MODEL = "gpt-4o-mini"        # mini model as requested
HISTORY_LIMIT = 6           # keep last N messages per session
PORT = int(os.getenv("PORT", 8080))

app = Flask(__name__)

# In-memory simple session history (for demo). For production use persistent store.
SESSIONS = {}

# Super minimal keypad-friendly HTML (fits ~240-320px width)
INDEX_HTML = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta charset="utf-8">
<title>Mini AI Chat</title>
<style>
  html,body{height:100%; margin:0; font-family:system-ui,Arial; background:#fff; color:#000}
  .wrap{max-width:320px; margin:0 auto; padding:6px; box-sizing:border-box}
  header{font-weight:700; font-size:16px; padding:6px 0}
  #log{height:58vh; overflow:auto; border:1px solid #ccc; padding:6px; white-space:pre-wrap; font-size:14px}
  .you{color:#003366; margin-bottom:4px}
  .bot{color:#006600; margin-bottom:6px}
  #compose{display:flex; gap:6px; margin-top:6px}
  #msg{flex:1; padding:6px; font-size:14px}
  button{padding:6px 8px; font-size:14px}
  /* Make buttons and inputs easy to focus using keypad */
  input, button, textarea { outline-color:#888; }
  small{color:#666}
</style>
</head>
<body>
<div class="wrap">
  <header>Mini AI Chat</header>
  <div id="log" tabindex="0" aria-live="polite"></div>
  <div id="compose">
    <input id="msg" autocomplete="off" placeholder="Type message..." />
    <button id="send">Send</button>
  </div>
  <div style="margin-top:6px"><small>Press Enter to send — keeps last {{history_limit}} messages</small></div>
</div>

<script>
const log = document.getElementById('log');
const msg = document.getElementById('msg');
const sendBtn = document.getElementById('send');
const sessionId = 'mobile'; // single session for demo

function append(kind, text) {
  const el = document.createElement('div');
  el.className = kind;
  el.textContent = (kind === 'you' ? 'You: ' : 'Bot: ') + text;
  log.appendChild(el);
  log.scrollTop = log.scrollHeight;
  // small delay so screen readers / keypad feel natural
}

// send when pressing Enter (works with keypad Enter)
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
  append('bot', '...'); // placeholder
  // POST to server
  try {
    const r = await fetch('/api/chat', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({session_id: sessionId, text})
    });
    if (!r.ok) {
      const err = await r.text();
      // replace last placeholder with error
      const last = log.lastChild;
      if (last) last.textContent = 'Bot: [Error] ' + err;
      return;
    }
    const data = await r.json();
    // replace placeholder with real reply
    const last = log.lastChild;
    if (last) last.textContent = 'Bot: ' + (data.reply || '[no reply]');
    log.scrollTop = log.scrollHeight;
  } catch (e) {
    const last = log.lastChild;
    if (last) last.textContent = 'Bot: [Network error]';
  }
}
</script>
</body>
</html>
"""

def trim_history(session_id):
    hist = SESSIONS.get(session_id, [])
    if len(hist) > HISTORY_LIMIT:
        SESSIONS[session_id] = hist[-HISTORY_LIMIT:]

def build_messages(session_id, user_text):
    hist = SESSIONS.get(session_id, [])
    # hist is list of dicts: {"role": "user"/"assistant", "content": "..."}
    hist.append({"role": "user", "content": user_text})
    SESSIONS[session_id] = hist
    trim_history(session_id)
    # system prompt kept minimal to reduce token use
    system = {"role": "system", "content": "You are a concise, helpful assistant. Keep answers short."}
    return [system] + SESSIONS[session_id]

@app.route("/", methods=["GET"])
def index():
    return render_template_string(INDEX_HTML, history_limit=HISTORY_LIMIT)

@app.route("/api/chat", methods=["POST"])
def chat():
    if openai.api_key is None:
        return Response("OpenAI API key not configured on server", status=500)

    data = request.get_json(force=True, silent=True) or {}
    session_id = data.get("session_id", "anon")
    user_text = (data.get("text") or "").strip()
    if not user_text:
        return Response("Empty message", status=400)

    # Build messages and call OpenAI (simple non-streaming call for reliability on low-end devices)
    messages = build_messages(session_id, user_text)

    try:
        # Use ChatCompletion (older SDK) or adapt if your openai python SDK differs.
        resp = openai.ChatCompletion.create(
            model=MODEL,
            messages=messages,
            max_tokens=200,
            temperature=0.6
        )
        # Extract assistant text
        choice = resp.choices[0]
        assistant_text = ""
        # Different SDKs return either 'message' or 'text' in different places
        if hasattr(choice, "message"):
            assistant_text = choice.message.get("content", "")
        else:
            assistant_text = choice.get("text", "") or choice.get("message", {}).get("content","")
        assistant_text = (assistant_text or "").strip()
        # store assistant reply to session history
        SESSIONS[session_id].append({"role":"assistant", "content": assistant_text})
        trim_history(session_id)

        return jsonify({"reply": assistant_text})
    except Exception as e:
        # Log minimal info to help debug (avoid leaking tokens)
        err_msg = str(e)
        return Response(err_msg, status=500)

if __name__ == "__main__":
    # safety: wait a second when launching so logs are readable on some hosts
    time.sleep(1)
    app.run(host="0.0.0.0", port=PORT)