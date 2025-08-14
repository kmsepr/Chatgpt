🤖 Grok Mini — Flask Chat App

A lightweight chat web app for Groq API (LLaMA-3) with conversation history stored in Flask sessions.
Mobile-friendly interface, works even on low-resolution devices.


---

📂 Project Structure

grok-mini/
├── server.py         # Main Flask app
├── requirements.txt  # Python dependencies
├── .env.example      # Example environment file
└── README.md         # This file


---

🚀 Features

Chat with Groq's LLaMA-3 model (llama3-8b-8192)

Minimal HTML/CSS frontend

Works well on small screens

Key 5 to focus input box

Short conversation memory (last 6 exchanges)

"Clear Chat" button to reset conversation



---

🔧 Installation

1️⃣ Clone the repository

git clone https://github.com/your-username/grok-mini.git
cd grok-mini

2️⃣ Create and activate virtual environment

python3 -m venv venv
source venv/bin/activate   # On Linux/Mac
venv\Scripts\activate      # On Windows

3️⃣ Install dependencies

pip install -r requirements.txt


---

🔑 Environment Variables

The app needs two environment variables:

SECRET_KEY — used by Flask to sign session cookies

GROQ_API_KEY — your Groq API key from console.groq.com


You can copy .env.example to .env and fill in your values:

cp .env.example .env

Example .env:

SECRET_KEY=f3b9a64f32b44c96ab85ec10a7b85c3a
GROQ_API_KEY=your_groq_api_key
PORT=8080


---

🛠 Generating a secure SECRET_KEY

Run this in your terminal:

python -c "import secrets; print(secrets.token_hex(32))"

Copy the result into your .env file.


---

▶️ Run locally

python server.py

Then open:

http://127.0.0.1:8080


---

🌐 Deploy to Koyeb / Railway / Render

Koyeb Example

1. Push your repo to GitHub


2. On Koyeb, create a new service from your repo


3. Build command:

pip install -r requirements.txt


4. Run command:

python server.py


5. Add environment variables:

SECRET_KEY

GROQ_API_KEY



6. Deploy




---

📜 License

MIT — free to use and modify.
