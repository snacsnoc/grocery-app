# error_handlers.py
from flask import render_template, redirect, url_for
from werkzeug.exceptions import HTTPException


def configure_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(error):
        return redirect(url_for("index"))

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return redirect(url_for("index"))

    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            return e
        app.logger.exception(e)
        return render_template("error.html"), 500
