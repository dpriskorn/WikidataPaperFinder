import logging

from flask import Flask, render_template, request

import config
from wpf import WPF

logging.basicConfig(level=config.loglevel)


app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        reference_text = request.form.get('reference_text').strip()
        if reference_text:
            wpf = WPF(reference_text=reference_text)  # Create an instance of WPF
            result = wpf.ask_ai()
    return render_template('index.html', result=result)


if __name__ == '__main__':
    app.run(debug=True)
