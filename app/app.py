from flask import Flask
import socket
import os

app = Flask(__name__)

@app.route('/')
def hello():
    hostname = socket.gethostname()
    version = os.getenv('APP_VERSION', 'v1.0')
    
    return f"""
    <html>
        <head><title>Hello from Kubernetes</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>Hello from Kubernetes!</h1>
            <p><strong>Pod hostname:</strong> {hostname}</p>
            <p><strong>Version:</strong> {version}</p>
            <p>Refresh the page to see load balancing in action!</p>
        </body>
    </html>
    """

@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)