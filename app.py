from flask import Flask, request, render_template
from pycirculate.anova import AnovaController
import time
import os

app = Flask(__name__)

with open("keys.txt") as f:
    keys = f.read().splitlines()

ANOVA_MAC_ADDRESS = keys[0]

os.environ["TZ"] = "US/Pacific"

def get_time():
    t=time.time()
    time.tzset()
    return (time.strftime("%I:%M %p", time.localtime(t)))

def get_time_diff(now, ready_time):
	current_time=time.strptime(now,"%I:%M %p")
	dinner_time = time.strptime(ready_time,"%I:%M %p")
	print "current time: " + current_time
	print "ready time2: " + dinner_time

# a = time.strptime(get_time(),"%I:%M %p")

def float_compare(a, b):
        threshold = 0.05
        return abs(a-b) < threshold

# anova = AnovaController(ANOVA_MAC_ADDRESS)

@app.route('/')
def index():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    return 'You entered: {}'.format(request.form)

@app.route('/control', methods=['POST'])
def control():
    print "Cooking Temperature: "+ request.form['target_temp']
    print "Cooking Time: "+ request.form['set_time_hr'] + " : " + request.form['set_time_min']
    print "ready time1" + request.form['ready_time']
    get_time_diff(get_time, request.form['ready_time'])

    return render_template('form.html')

if __name__== '__main__':
    app.run(host='0.0.0.0', use_reloader=True, debug = True)


