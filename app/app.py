from flask import Flask
import socket, os

app = Flask(__name__)

@app.route('/')
def hello():
    return f"""
    <h1>My Name is Reddy</h1>
    <p>Pod: {socket.gethostname()}</p>
    <p>Version: {os.getenv('APP_VERSION','v1')}</p>
    """

@app.route('/health')
def health():
    return {"status": "ok"}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
