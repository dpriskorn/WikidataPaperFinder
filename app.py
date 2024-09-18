import logging
from flask import Flask, render_template, request, redirect, url_for, abort
import config
from wpf import WPF

logging.basicConfig(level=config.loglevel)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.errorhandler(500)
def internal_error(error):
    # Render the custom 500 error page
    return render_template('500.html'), 500

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/search", methods=["GET", "POST"])
def search():
    reference_text = (
        request.form.get("reference_text")
        if request.method == "POST"
        else request.args.get("reference_text")
    )
    if reference_text:
        reference_text = reference_text.strip()
        wpf = WPF(reference_text=reference_text)  # Create an instance of WPF
        wpf.run()
        if not wpf.status:
            abort(500)
        logger.info(wpf.status)
        # print(wpf.query_result)
        # We pass the whole object here to make life easier
        return render_template("results.html", wpf=wpf)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
