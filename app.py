from flask import Flask, request, render_template
from pycirculate.anova import AnovaController
import time
import os
import logging, sys, datetime
import multiprocessing

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
	if int(dinner_time[3])-int(current_time[3]) > 0:
            val = 60*(int(dinner_time[3]) - int(current_time[3])) + (int(dinner_time[4])-int(current_time[4]))
            return val
	else:
		return -1
		# TODO: check to see whether ready time is for next day

def float_compare(a, b):
        threshold = 0.05
        return abs(a-b) < threshold

def delay_min(min):
	while min > 0:
		print str(get_time()) + " -- waiting to start in ..." + str(min) + " min"
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
    cook_temp = float(request.form['target_temp'])
    cook_time = int(request.form['set_time_hr']) * 60 + int(request.form['set_time_min'])
    app.anova.set_temp(cook_temp)
    app.anova.set_timer(int(cook_time))
    ready_time = request.form['ready_time']
    print str(get_time()) + " -- Order Received: Cooking Temperature = " + str(cook_temp) + "C, Cooking Time = " + str(cook_time) + " min, Ready Time = " + str(ready_time) 
    time_to_preheat = get_time_diff(get_time(), ready_time) - cook_time - ANOVA_PRE_HEAT_TIME
    if time_to_preheat < 0:
    	time_to_preheat = 0
        print str(get_time()) + " -- start anova now!!!"
    	app.anova.start_anova()
    	# update ready time
    else:
    	delay_min(time_to_preheat)
    	app.anova.start_anova()

    while not float_compare(float(app.anova.read_temp()), cook_temp):
        print str(get_time()) + " --  target_temp: "+ str(cook_temp) + "C | " + "current temp: "+ str(app.anova.read_temp()) + "C"
        time.sleep(5)

    print str(get_time()) + " -- start the timer now, start cooking"
    app.anova.start_timer()
    # print "read timer: " + str(app.anova.read_timer())
    while (app.anova.read_timer().split()[1]) == "running":
        print str(get_time()) + " -- Almost done.." + str(app.anova.read_timer().split()[0]) + " minutes to go"
        time.sleep(60)
    app.anova.stop_timer()
    app.anova.stop_anova()
    print str(get_time()) + " -- Food is Ready!, Original Ready Time = " + str(ready_time)
    return render_template('form.html')

def task_flask(messages):
    app.messages = messages
    app.run(host = '0.0.0.0', port = 5000, use_reloader = False)

def task_anova(messages):
    anova = AnovaController(ANOVA_MAC_ADDRESS)

    while True:
        for message in messages:
            if message["key"] == "TASK_ANOVA":
                if message["event"] == "COOK_ORDER":
                    anova.set_timer(message["payload"]["set_time"])
                    anova.set_temp(message["payload"]["target_temp"])
        time.sleep(0.5) #2Hz message queue

def main():

    manager = multiprocessing.Manager()
    messages = manager.list()
    process_flask = multiprocessing.Process(
        target = task_flask,
        args = (messages,))
    process_anova = multiprocessing.Process(
        target = task_anova,
        args = (messages,))
    process_flask.start()
    process_anova.start()
    process_flask.join()
    process_anova.join()


if __name__ == '__main__':
    main()

