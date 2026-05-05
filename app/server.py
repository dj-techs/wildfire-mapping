"""Flask + Dash entry point.

Flask owns the WSGI app (so we can mount auth routes alongside Dash). Dash
mounts at the root; auth pages live at /login and /logout.

Local dev:  python -m app.server          (runs Flask dev server on :8050)
Production: gunicorn 'app.server:server'  (Flask app object exported as `server`)
"""
from __future__ import annotations

import dash
import dash_bootstrap_components as dbc
from flask import Flask, redirect, render_template_string, request, url_for
from flask_login import current_user, login_required

from app.auth import attempt_login, do_logout, init_auth
from app.callbacks.map_callbacks import register_callbacks
from app.components.layout import build_layout
from app.config import Config

# ---- Flask shell ----------------------------------------------------------
server = Flask(__name__)
server.config.from_object(Config)
init_auth(server)


_LOGIN_PAGE = """
<!doctype html><meta charset=utf-8><title>Sign in</title>
<style>
  body{font-family:system-ui;background:#0f172a;color:#e5e7eb;display:flex;
       align-items:center;justify-content:center;height:100vh;margin:0}
  form{background:#1f2937;padding:32px;border-radius:8px;min-width:320px;
       box-shadow:0 10px 40px rgba(0,0,0,.5)}
  h1{margin:0 0 16px;font-size:20px}
  input{width:100%;padding:8px;margin:6px 0 14px;border:1px solid #374151;
        background:#0f172a;color:#e5e7eb;border-radius:4px;box-sizing:border-box}
  button{width:100%;padding:10px;background:#f59e0b;border:0;border-radius:4px;
         color:#1f2937;font-weight:600;cursor:pointer}
  .err{color:#f87171;font-size:13px;margin-bottom:8px}
  .hint{color:#9ca3af;font-size:12px;margin-top:14px;text-align:center}
</style>
<form method=post>
  <h1>Wildfire Mapping Platform</h1>
  {% if error %}<div class=err>{{ error }}</div>{% endif %}
  <label>Email</label><input name=email value="demo@example.com">
  <label>Password</label><input name=password type=password value="demo">
  <button>Sign in</button>
  <div class=hint>Demo: demo@example.com / demo</div>
</form>
"""


@server.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        ok = attempt_login(request.form["email"], request.form["password"])
        if ok:
            return redirect("/")
        return render_template_string(_LOGIN_PAGE, error="Invalid credentials")
    return render_template_string(_LOGIN_PAGE, error=None)


@server.route("/logout")
def logout():
    do_logout()
    return redirect("/login")


@server.route("/health")
def health():
    return {"status": "ok"}


# ---- Dash app -------------------------------------------------------------
app = dash.Dash(
    __name__,
    server=server,
    external_stylesheets=[dbc.themes.DARKLY],
    title="Wildfire Mapping Platform",
    suppress_callback_exceptions=True,
    update_title=None,
)
app.layout = build_layout
register_callbacks(app)


# Gate Dash behind auth unless AUTH_DISABLED.
if not Config.AUTH_DISABLED:
    for view_func in list(server.view_functions):
        if view_func.startswith("/_dash") or view_func == "/":
            server.view_functions[view_func] = login_required(server.view_functions[view_func])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=Config.DEBUG)
