from flask import Flask, render_template, request

from wpf import WPF

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    if request.method == 'POST':
        reference_text = request.form.get('reference_text')
        if reference_text:
            wpf = WPF()  # Create an instance of WPF
            result = wpf.ask_ai(reference_text)  # Call the method with the input reference text
    return render_template('index.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)
