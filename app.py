from flask import Flask, request, render_template
from pycirculate.anova import AnovaController
import time
import os
import logging, sys, datetime

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
		# TODO: check to see whether ready time is for next day

def float_compare(a, b):
        threshold = 0.05
        return abs(a-b) < threshold

def delay_min(min):
	while min > 0:
		print "waiting to start in ..." + str(min)
		time.sleep(60)
		min -=1 

@app.route('/')
def index():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    return 'You entered: {}'.format(request.form)

@app.route('/test')
def test():
    print "in test"
    print "temp in test: "+ str(app.anova.read_temp())
    app.anova.set_temp(65)
    app.anova.set_timer(60)
#    app.anova.start_anova()

@app.route('/control', methods=['POST'])
def control():
    #TODO: all the settings
    print "in control"
    cook_temp = request.form['target_temp']
    print "set time hr(min): " + str(int(request.form['set_time_hr'])*60)
    print "set time min: " + request.form['set_time_min']
    cook_time = int(request.form['set_time_hr']) * 60 + int(request.form['set_time_min'])
    print "cook time: "+str(cook_time)
    app.anova.set_temp(cook_temp)
    print "after set temp"
    app.anova.set_timer(int(cook_time))
    print "after set timer"
    ready_time = request.form['ready_time']
    print "cal time_to_preheat"
    time_to_preheat = get_time_diff(get_time(), ready_time) - cook_time - ANOVA_PRE_HEAT_TIME
    print "time to preheat: " + str(time_to_preheat)
    if time_to_preheat < 0:
    	time_to_preheat = 0
    	app.anova.start_anova()
    	# update ready time
    else:
    	delay_min(time_to_preheat)
    	# anova.start_anova()

    while not float_compare(float(anova.read_temp()), cook_temp):
        print "target_temp: "+ str(target_temp)
        print "current temp: "+ anova.read_temp()
        time.sleep(1)

    print "start the timer now, start cooking"
    anova.start_timer()
    return render_template('form.html')

def main():
    app.anova = AnovaController(ANOVA_MAC_ADDRESS)
    print "temp: " + str(app.anova.read_temp())
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()

