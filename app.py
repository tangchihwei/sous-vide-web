from flask import Flask, request, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    return 'You entered: {}'.format(request.form)

@app.route('/control', methods=['POST'])
def control():
    print request.form['say']
    return "hello"

if __name__== '__main__':
    app.run(host='0.0.0.0', use_reloader=True, debug = True)


