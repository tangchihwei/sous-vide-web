from flask import Flask, request, render_template
from pycirculate.anova import AnovaController
import time
import os
import logging, sys, datetime
import multiprocessing
from bluepy import btle


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
        print str(current_time[3]) + " : " + str(current_time[4])
	dinner_time = time.strptime(ready_time,"%H:%M")
        print str(dinner_time[3]) + " : " + str(dinner_time[4])

	if int(dinner_time[3])-int(current_time[3]) >= 0:
            val_hr = int(dinner_time[3]) - int(current_time[3])
            val_min = int(dinner_time[4])-int(current_time[4])
	else: #next day
            val_hr = int(dinner_time[3]) + 24 - int(current_time[3])
            val_min = int(dinner_time[4]) - int(current_time[4])
	return 60 * val_hr + val_min

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
    print "new message: " + str(message)
    return message
def preheat_est(temp):
    # TODO estimate preheat time
    return ANOVA_PRE_HEAT_TIME

def update_time(target_time, duration):
    if target_time[4] - duration:
        return  strptime(str(target_time[3])+":"+str(target_time[4]-duration),"%H:%M")
    else:
        time_hr = target_time[3] - duration/60
        time_min = target_time[4] - duration%60
        if time_min < 0:
            time_hr -= 1
            time_min = 60 + time_min
        return striptime(str(timehr) + ":" + str(time_min), "%H:%M")
def ble_connection(anova):
    try: 
        unit = anova.read_unit()
        val = True
        # print "connection good!"
    except (TypeError, btle.BTLEException) as e:
        print str(e) + " connection error"
        val = False
    return val 

def anova_start_preheat(messages, cook_temp, cook_time):
    print "start anova now"
    packet = message_gen(
        "TASK_ANOVA", str(get_time()), "ANOVA_PREHEAT",
        {
            "cook_temp" : cook_temp,
            "cook_time" : cook_time
        })
    messages.append(packet)
        
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
    cook_time = int(request.form['set_time_hr']) * 60 + int(request.form['set_time_min']) #in mins
    ready_time = request.form['ready_time']

    message = message_gen(
        "TASK_SCHEDULER", str(get_time()), "ANOVA_ORDER", {
            "cook_temp" : cook_temp,
            "cook_time" : cook_time,
            "ready_time" : ready_time
        })
    app.messages.append(message)
    return render_template('form.html')
def task_timer(messages, timer_name, min):
    timer_time = min
    while min > 0:
        print str(get_time()) + " -- waiting ..." + str(min) + " min"
        time.sleep(60)
        min -=1  

    message = message_gen(
        "TASK_SCHEDULER", str(get_time()), "SCHEDULER_TIME_UP", {
                "timer_time" : timer_time,
                "timer_name" : timer_name
            }
        )
    messages.append(message)

#this task 
def task_scheduler(messages):
    print "in task scheduler"
    while True:
        for i, message in enumerate(messages):
            if message["target"] == "TASK_SCHEDULER":
                print "event for scheduler: " + str(message)
                if message["event"] == "ANOVA_ORDER": #new order received
                    cook_time = message["payload"]["cook_time"]
                    cook_temp = message["payload"]["cook_temp"]
                    ready_time = message["payload"]["ready_time"]

                    temp_time = get_time_diff(get_time(), ready_time)
                    print "temp get time diff: " + str(temp_time)
                    time_to_preheat = temp_time - preheat_est(cook_temp) - cook_time
                    print "time to preheat: " + str(time_to_preheat)
                    if time_to_preheat <= 0:
                        anova_start_preheat(messages, cook_temp, cook_time)
                    else:
                        process_timer = multiprocessing.Process(
                            target = task_timer,
                            args = (messages, "TIMER_TO_PREHEAT", time_to_preheat,))
                        process_timer.start()

                elif message["event"] == "SCHEDULER_TIME_UP":
                    if message["payload"]["timer_name"] == "TIMER_TO_PREHEAT":
                        anova_start_preheat(messages, cook_temp, cook_time)

                elif message["event"] == "SCHEDULER_PREHEAT_DONE":
                    #TODO:update final ready time
                    print "preheat done"        
                    packet = message_gen(
                        "TASK_ANOVA", str(get_time()), "ANOVA_COOK", {}
                    )
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
    device_status = "before start"
    anova = AnovaController.__new__(AnovaController)
    while True:
        try:
            anova = AnovaController(ANOVA_MAC_ADDRESS)
            print "anova connected"
            break
        except (TypeError, btle.BTLEException) as e:
            print str(e) + " not able to connect"
        print "wait 3 seconds, and try again"
        time.sleep(3)

    try: 
        device_status = anova.anova_status() #'running', 'stopped', 'low water', 'heater error' + "preheating" (custom)
        print "read successful"
    except (TypeError, btle.BTLEException) as e:
        print str(e) + " unable to read anova, weird. may need to reconnect "
    cook_temp = float(0)
    cook_time = int(0)
    #check connection, check system status
    while True:
        if not ble_connection(anova) :
            print "reconnecting"
            try: 
                anova = AnovaController(ANOVA_MAC_ADDRESS)
            except (TypeError, btle.BTLEException) as e:
                print str(e) + "...still not able to connect"
        else:
            try: 
                low_water = False
                if anova.anova_status()  == "low water":
                    print "low water!" #status change, something wrong?
                    low_water = True
            except (TypeError, btle.BTLEException) as e:
                print str(e)
            if not low_water:
                if device_status == "preheating":
                    print "preheating"
                    try: 
                        anova_temp = anova.read_temp()
                    except (TypeError, btle.BTLEException) as e:
                        print str(e) + " unable to read anova temp"
                        anova_temp = 0
                    if float_compare(float(anova_temp) ,cook_temp):
                        print "preheating completed"
                        packet = message_gen("TASK_SCHEDULER", str(get_time()), "SCHEDULER_PREHEAT_DONE", {})
                        messages.append(packet)
                        device_status = "post preheat"
                    else:
                        print str(get_time()) + " -- preheating, current temp: " + str(anova_temp) + " - target temp: " + str(cook_temp)
                elif device_status == "cooking":
                    try:
                        anova_timer = anova.read_timer()
                    except (TypeError, btle.BTLEException) as e:
                        print str(e) + "unable to read anova timer"

                    else:
                        if anova_timer.split()[1] == "running":
                            print "Food still cooking.." + str(anova_timer).split()[0] + "more minutes to go"
                        else:
                            print "Food is ready" 
                            # anova.send_command_async("stop time") #stop anova timer, TODO: need to test further to stop the beeping after done.
                            try:
                                anova.stop_anova() #anova keeps beeping afterwards
                                device_status = "stopped"
                            except (TypeError, btle.BTLEException) as e:
                                print str(e) + " unable to stop anova device"
                            else:
                                print "anova device was stopped."

                for i, message in enumerate(messages):
                    if message["target"] == "TASK_ANOVA":
                        message_processed = False
                        print "event for anova: " + str(message)
                        if message["event"] == "ANOVA_PREHEAT":
                            cook_temp = message["payload"]["cook_temp"]
                            cook_time = message["payload"]["cook_time"]
                            try:
                                anova.set_temp(cook_temp)
                                anova.set_timer(cook_time)
                                anova.start_anova()
                            except (TypeError, btle.BTLEException) as e:
                                print str(e) + " unable to set temperature and start preheating, connection may have failed"
                            else:
                                device_status = "preheating" #need to validate
                                message_processed = True
                        elif message["event"] == "ANOVA_COOK":
                            print "start timer"
                            try:
                                anova.start_timer()
                            except (TypeEerror, btle.BTLEException) as e:
                                print str(e) + " unable to start timer"
                            else:
                                device_status = "cooking"
                                message_processed = True
                        if message_processed:
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
    process_scheduler = multiprocessing.Process(
        target = task_scheduler,
        args = (messages,))
    process_flask.start()
    process_anova.start()
    process_scheduler.start()
    process_flask.join()
    process_scheduler.join()
    process_anova.join()

if __name__ == '__main__':
    main()
