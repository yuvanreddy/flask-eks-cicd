from flask import Flask, render_template, request, redirect, url_for, session
import socket, os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "secret123")

# Dummy users (you can later connect DB)
USERS = {
    "admin": "admin123",
    "yuvan": "yuvan123"
}

@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username in USERS and USERS[username] == password:
            session["user"] = username
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="Invalid Username/Password")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        user=session["user"],
        pod=socket.gethostname(),
        version=os.getenv("APP_VERSION", "v1")
    )

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/health")
def health():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
