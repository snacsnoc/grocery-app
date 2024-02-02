from flask import Flask, render_template, request, redirect, abort, url_for
import os

from config import Config
from routes import configure_routes
from error_handlers import configure_error_handlers

app = Flask(__name__)
app.config.from_object(Config)
configure_routes(app)
configure_error_handlers(app)

if not os.path.exists(app.config["CACHE_DIR"]):
    os.makedirs(app.config["CACHE_DIR"])

# Run the app
if __name__ == "__main__":
    app.run()
