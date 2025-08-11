from flask import Flask, request, Response
import os
import openai

openai.api_key = os.environ.get("OPENAI_API_KEY")

app = Flask(__name__)

HISTORY = {}
MODEL = "gpt-4o-mini"

HTML_PAGE = """
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ChatGPT Clone</title>
<style>
  body{font-family:system-ui,Arial; padding:8px; font-size:16px; background:#f8f8f8}
  #chat{height:65vh; overflow:auto; border:1px solid #ccc; padding:6px; background:#fff}
  .msg{margin:6px 0}
  .user{font-weight:600; color:#333}
  .bot{white-space:pre-wrap; color:#000}
  #input{width:100%; box-sizing:border-box; padding:8px}
</style>
</head>
<body>
<h2>💬 ChatGPT Clone</h2>
<div id="chat"></div>
<textarea id="input" rows="2" placeholder="Type and press Enter"></textarea>
<script>
const chatEl = document.getElementById('chat');
const input = document.getElementById('input');

function append(cls, text){
  const d=document.createElement('div');
  d.className='msg '+cls;
  d.textContent=text;
  chatEl.appendChild(d);
  chatEl.scrollTop=chatEl.scrollHeight;
}

input.addEventListener('keydown', async (e) => {
  if(e.key === 'Enter' && !e.shiftKey){
    e.preventDefault();
    const text = input.value.trim();
    if(!text) return;
    append('user', 'You: '+text);
    input.value='';
    const botLine=document.createElement('div');
    botLine.className='msg bot';
    botLine.textContent='...';
    chatEl.appendChild(botLine);
    try {
      const res = await fetch('/api/chat', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({session_id: 'mobile', text})
      });
      botLine.textContent='';
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      while(true){
        const {done,value} = await reader.read();
        if(done) break;
        botLine.textContent += decoder.decode(value, {stream:true});
        chatEl.scrollTop=chatEl.scrollHeight;
      }
    } catch(err){
      botLine.textContent='[Network Error]';
    }
  }
});
</script>
</body>
</html>
"""

def build_messages(session_id, user_text):
    hist = HISTORY.get(session_id, [])
    hist = hist[-6:]
    hist.append({"role": "user", "content": user_text})
    HISTORY[session_id] = hist
    return [{"role": "system", "content": "You are a helpful assistant."}] + hist

@app.route("/")
def index():
    return HTML_PAGE

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json or {}
    session_id = data.get("session_id", "anon")
    user_text = data.get("text", "").strip()

    if not user_text:
        return Response("Error: Empty message", status=400)

    messages = build_messages(session_id, user_text)

    def stream():
        response = openai.ChatCompletion.create(
            model=MODEL,
            messages=messages,
            stream=True
        )
        collected = []
        for chunk in response:
            delta = chunk["choices"][0]["delta"].get("content", "")
            if delta:
                collected.append(delta)
                yield delta
        HISTORY[session_id].append({"role": "assistant", "content": "".join(collected)})

    return Response(stream(), mimetype="text/plain; charset=utf-8")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
