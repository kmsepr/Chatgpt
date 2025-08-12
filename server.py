from flask import Flask, request, jsonify, render_template_string, session
import os
import requests

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super-secret-key")  # Change for production

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise Exception("Set the GROQ_API_KEY environment variable first.")

MODEL = "llama3-8b-8192"  # You may change to your preferred model

INDEX_HTML = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta charset="utf-8">
<title>Chat - HMD110 Keypad Friendly</title>
<style>
  html, body {
    height: 100%;
    margin: 0;
    font-family: system-ui, Arial, sans-serif;
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
    font-size: 18px;
    line-height: 1.5;
    border: none;
    outline: none;
  }
  .you { color: #003366; margin-bottom: 8px; }
  .bot { color: #006600; margin-bottom: 12px; }
  a {
    color: #008000;
    text-decoration: underline;
  }

  #instructions {
    font-size: 14px;
    background: #eee;
    padding: 6px 10px;
    border-top: 1px solid #ccc;
    user-select: none;
  }

  #inputOverlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.7);
    display: none;  /* Hidden initially */
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }
  #inputBox {
    background: white;
    padding: 12px;
    border-radius: 6px;
    width: 90%;
    max-width: 400px;
    box-sizing: border-box;
    display: flex;
    gap: 8px;
  }
  #msg {
    flex: 1 1 auto;
    font-size: 18px;
    padding: 8px 12px;
    border: 1px solid #ccc;
    border-radius: 4px;
    outline-color: #008000;
  }
  #sendBtn, #cancelBtn {
    font-size: 18px;
    padding: 8px 14px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    user-select: none;
  }
  #sendBtn {
    background: #008000;
    color: white;
  }
  #sendBtn:disabled {
    background: #ccc;
    cursor: not-allowed;
  }
  #cancelBtn {
    background: #cc0000;
    color: white;
  }
</style>
</head>
<body>
  <div id="log" aria-live="polite" tabindex="0"></div>
  <div id="instructions">
    Use keypad:<br>
    [5] Toggle message input &nbsp;&nbsp; [0] Send &nbsp;&nbsp; [9] Cancel input <br>
    [2]/[8] Scroll Up/Down
  </div>

  <div id="inputOverlay" role="dialog" aria-modal="true" aria-label="Message input">
    <div id="inputBox">
      <input id="msg" type="text" autocomplete="off" spellcheck="false" maxlength="200" aria-label="Message input" />
      <button id="sendBtn" disabled>Send (0)</button>
      <button id="cancelBtn">Cancel (9)</button>
    </div>
  </div>

<script>
const log = document.getElementById('log');
const inputOverlay = document.getElementById('inputOverlay');
const msgInput = document.getElementById('msg');
const sendBtn = document.getElementById('sendBtn');
const cancelBtn = document.getElementById('cancelBtn');

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

function openInput() {
  inputOverlay.style.display = 'flex';
  msgInput.value = '';
  sendBtn.disabled = true;
  msgInput.focus();
}

function closeInput() {
  inputOverlay.style.display = 'none';
  msgInput.value = '';
  sendBtn.disabled = true;
  log.focus();
}

sendBtn.addEventListener('click', () => {
  sendMessage();
});
cancelBtn.addEventListener('click', () => {
  closeInput();
});

msgInput.addEventListener('input', () => {
  sendBtn.disabled = msgInput.value.trim() === '';
});

async function sendMessage() {
  const text = msgInput.value.trim();
  if (!text) return;
  append('you', text);
  closeInput();
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

document.body.addEventListener('keydown', (e) => {
  // console.log(e.key);
  if (inputOverlay.style.display === 'flex') {
    // Input overlay open
    if (e.key === '0') {  // Send
      e.preventDefault();
      if (!sendBtn.disabled) sendMessage();
    } else if (e.key === '9' || e.key === '5') { // Cancel or toggle input box
      e.preventDefault();
      closeInput();
    }
  } else {
    // Input overlay closed
    if (e.key === '5') {
      e.preventDefault();
      openInput();
    } else if (e.key === '2') {
      e.preventDefault();
      log.scrollBy(0, -40);
    } else if (e.key === '8') {
      e.preventDefault();
      log.scrollBy(0, 40);
    }
  }
});

window.onload = () => {
  log.focus();
};
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