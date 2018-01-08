from flask import Flask, request, render_template
from pycirculate.anova import AnovaController
import time
import os

app = Flask(__name__)

with open("keys.txt") as f:
    keys = f.read().splitlines()

ANOVA_MAC_ADDRESS = keys[0]
ANOVA_PRE_HEAT_TIME = 25
#25 min assume from 23C to 60C with 2 gallon water (http://www.amazingfoodmadeeasy.com/info/modernist-cooking-blog/more/how-long-does-it-take-a-sous-vide-machine-to-heat-up)

os.environ["TZ"] = "US/Pacific"

def get_time():
    t=time.time()
    time.tzset()
    return (time.strftime("%I:%M %p", time.localtime(t)))

def get_time_diff(now, ready_time):
	current_time=time.strptime(now,"%I:%M %p")
	dinner_time = time.strptime(ready_time,"%H:%M")
	print "current time: " + str(current_time[3]) + " : " + str(current_time[4])
	print "ready time parsed: " + str(dinner_time[3]) + " : " + str(dinner_time[4])
	if int(dinner_time[3])-int(current_time[3]) > 0:
		return 60*(int(dinner_time[3]) - int(current_time[3])) + (int(dinner_time[4])-int(current_time[4]))
	else:
		return -1

def float_compare(a, b):
        threshold = 0.05
        return abs(a-b) < threshold

def delay_min(min):
	while min > 0:
		print "waiting to start in ..." + str(min)
		time.sleep(60)
		min -=1 

# anova = AnovaController(ANOVA_MAC_ADDRESS)

def set_sous_vide(target_temp, cook_timer):
    print "set target temp"
    print "cook time"

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
    print "ready time incoming: " + request.form['ready_time']
    print "mins to start: " + str(get_time_diff(get_time(), request.form['ready_time']) - ANOVA_PRE_HEAT_TIME)
    delay_min(2)
    print "after 2 min"
    return render_template('form.html')

if __name__== '__main__':
    app.run(host='0.0.0.0', use_reloader=True, debug = True)


