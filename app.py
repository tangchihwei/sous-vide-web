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

def message_gen(target, timestamp, event, payload):
    message = {
        "target" : target,
        "timestamp" : timestamp,
        "event" : event,
        "payload" : payload
    }
    return message
def preheat_est(temp):
    return ANOVA_PRE_HEAT_TIME

def update_time(target_time, duration):
    if target_time[4] - duration:
        return  strptime(str(target_time[3])+":"+str(target_time[4]-duration),"%H:%M")
    elif 
        time_hr = target_time[3] - duration/60
        time_min = target_time[4] - duration%60
        if time_min < 0:
            time_hr -= 1
            time_min = 60 + time_min
        return striptime(str(timehr) + ":" + str(time_min), "%H:%M")

        
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

@app.route('/control', methods=['POST'])
def control():
    cook_temp = float(request.form['target_temp'])
    cook_time = int(request.form['set_time_hr']) * 60 + int(request.form['set_time_min'])
    ready_time = request.form['ready_time']

    message = message_gen(
        "TASK_ANOVA", str(get_time()), "ANOVA_ORDER", {
            "cook_temp" : cook_temp,
            "cook_time" : cook_time,
            "ready_time" : ready_time
        })

    app.messages.append(message)
    message["target"] = "TASK_SCHEDULER"
    # message["event"] = "SCHEDULER_READY_TIME"
    app.messages.append(message)

    # app.anova.set_temp(cook_temp)
    # app.anova.set_timer(int(cook_time))
    # print str(get_time()) + " -- Order Received: Cooking Temperature = " + str(cook_temp) + "C, Cooking Time = " + str(cook_time) + " min, Ready Time = " + str(ready_time) 
    # time_to_preheat = get_time_diff(get_time(), ready_time) - cook_time - ANOVA_PRE_HEAT_TIME
    # if time_to_preheat < 0:
    # 	time_to_preheat = 0
    #     print str(get_time()) + " -- start anova now!!!"
    # 	app.anova.start_anova()
    # 	# update ready time
    # else:
    # 	delay_min(time_to_preheat)
    # 	app.anova.start_anova()

    # while not float_compare(float(app.anova.read_temp()), cook_temp):
    #     print str(get_time()) + " --  target_temp: "+ str(cook_temp) + "C | " + "current temp: "+ str(app.anova.read_temp()) + "C"
    #     time.sleep(5)

    # print str(get_time()) + " -- start the timer now, start cooking"
    # app.anova.start_timer()
    # # print "read timer: " + str(app.anova.read_timer())
    # while (app.anova.read_timer().split()[1]) == "running":
    #     print str(get_time()) + " -- Almost done.." + str(app.anova.read_timer().split()[0]) + " minutes to go"
    #     time.sleep(60)
    # app.anova.stop_timer()
    # app.anova.stop_anova()
    # print str(get_time()) + " -- Food is Ready!, Original Ready Time = " + str(ready_time)
    return render_template('form.html')
def task_timer(messages, timer_name, min):
    timer_time = min
    while min > 0:
        print str(get_time()) + " -- waiting ..." + str(min) + " min"
        time.sleep(60)
        min -=1  

    message = message_gen(
        "TASK_SCHEDULER", "str(get_time()), "SCHEDULER_TIME_UP", {
                "timer_time" : timer_time,
                "timer_name" : timer_name
            }
        )
    messages.append(message)

#this task 
def task_scheduler(messages):
    #ready_time
    #send out 

    preheat_start_time = time.strptime("0:0","%H:%M")
    # start_cook_time = time.strptime("0:0", "%H:%M")
    ready_time = time.strptime("0:0","%H:%M")
    while True:
        if get_time_diff(get_time(), ) 
        for i, message in enumerate(messages):
            if message["target"] = "TASK_SCHEDULER":
                if message["event"] == "ANOVA_ORDER": #new order received
                    cook_time = message["payload"]["cook_time"]
                    cook_temp = message["payload"]["cook_temp"]
                    ready_time = time.strptime((message["payload"]["ready_time"]),"%H:%M") #parse ready time in 24hr
                    time_to_preheat = get_time_diff(get_time(), ready_time) - preheat_est(cook_temp) - cook_time
                    if time_to_preheat <= 0:
                        print "start anova now"
                        packet = message_gen(
                            "TASK_ANOVA", str(get_time()), "ANOVA_PREHEAT",
                            {
                                "cook_temp" : cook_temp,
                                "cook_time" : cook_time
                            })
                        messages.append(packet)
                    else:
                        process_timer = multiprocessing.Process(
                            target = task_timer,
                            args = ("TIMER_TO_PREHEAT", time_to_preheat ,)
                        process_timer.start()

                elif message["event"] == "SCHEDULER_TIME_UP":
                    if message["payload"]["timer_name"] == "TIMER_TO_PREHEAT":
                        packet = message_gen(
                            "TASK_ANOVA", str(get_time()), "ANOVA_PREHEAT",
                            {
                                "cook_temp" : cook_temp,
                                "cook_time" : cook_time
                            })
                        messages.append(packet)

                elif message["event"] == "SCHEDULER_PREHEAT_DONE":
                    #TODO:update final ready time
                    #start 
                    print "preheat done"        
                    packet = message_gen{
                        "TASK_ANOVA", str(get_time()), "ANOVA_COOK", {}
                    }           
                    messages.append(packet)

                messages.pop(i)

                

        time.sleep(0.2) #5 Hz



def task_flask(messages):
    app.messages = messages
    app.run(host = '0.0.0.0', port = 5000, use_reloader = False)
    # while True:
    #     for i, message in enumerate(app.messages):

    #     time.sleep(2) #0.5 Hz

def task_anova(messages):
    anova = AnovaController(ANOVA_MAC_ADDRESS)
    device_status = anova.anova_status() #'running', 'stopped', 'low water', 'heater error'
    
    #check connection, check system status
    while True:
        if not anova.is_connected :
            anova.connect()
        else:
            if not device_status == anova.anova_status():
                print anova.anova_status() #status change, something wrong?
            else: 
                if device_status == "preheating"
                message_gen("TASK_SCHEDULER", )
                #parse message
                for i, message in enumerate(messages):
                    if message["target"] == "TASK_ANOVA":
                        # if message["event"] == "ANOVA_ORDER":
                        #     preheat_time = ANOVA_PRE_HEAT_TIME #TODO: check temp diff for estimate
                        #     messages.append(message_gen("TASK_SCHEDULER", str(get_time()), "SCHEDULER_PREHEAT_EST", preheat_time))
                        if message["event"] == "ANOVA_PREHEAT":
                            anova.set_temp(message["payload"]["cook_temp"])
                            anova.set_timer(message["payload"]["cook_time"])
                            anova.start_anova()
                            device_status = "running" #need to validate
                        elif message["event"] == "ANOVA_COOK":
                            anova.start_timer()
                        else :
                            print "other event: " + message["event"]
                        messages.pop(i)
        time.sleep(0.5) #2 Hz message queue

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
