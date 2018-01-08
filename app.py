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

class RESTAnovaController(AnovaController):
    """
    This version of the Anova Controller will keep a connection open over bluetooth
    until the timeout has been reach.
    NOTE: Only a single BlueTooth connection can be open to the Anova at a time.
    """

    TIMEOUT = 5 * 60 # Keep the connection open for this many seconds.
    TIMEOUT_HEARTBEAT = 20

    def __init__(self, mac_address, connect=True, logger=None):
        self.last_command_at = datetime.datetime.now()
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger()
        super(RESTAnovaController, self).__init__(mac_address)

    def set_timeout(self, timeout):
        """
        Adjust the timeout period (in seconds).
        """
        self.TIMEOUT = timeout

    def timeout(self, seconds=None):
        """
        Determines whether the Bluetooth connection should be timed out
        based on the timestamp of the last exectuted command.
        """
        if not seconds:
            seconds = self.TIMEOUT
        timeout_at = self.last_command_at + datetime.timedelta(seconds=seconds)
        if datetime.datetime.now() > timeout_at:
            self.close()
            self.logger.info('Timeout bluetooth connection. Last command ran at {0}'.format(self.last_command_at))
        else:
            self._timeout_timer = Timer(self.TIMEOUT_HEARTBEAT, lambda: self.timeout())
            self._timeout_timer.setDaemon(True)
            self._timeout_timer.start()
            self.logger.debug('Start connection timeout monitor. Will idle timeout in {0} seconds.'.format(
                (timeout_at - datetime.datetime.now()).total_seconds())) 

    def connect(self):
        super(RESTAnovaController, self).connect()
        self.last_command_at = datetime.datetime.now()
        self.timeout()

    def close(self):
        super(RESTAnovaController, self).close()
        try:
            self._timeout_timer.cancel()
        except AttributeError:
            pass

    def _send_command(self, command):
        if not self.is_connected:
            self.connect()
        self.last_command_at = datetime.datetime.now()
        return super(RESTAnovaController, self)._send_command(command)

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

anova = AnovaController(ANOVA_MAC_ADDRESS)

# def set_sous_vide(target_temp, cook_timer):
#     print "set target temp"
#     print "cook time"

@app.route('/')
def index():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    return 'You entered: {}'.format(request.form)

@app.route('/control', methods=['POST'])
def control():
    #TODO: all the settings
    cook_temp = request.form['target_temp']
    cook_time = request.form['set_time_hr'] * 60 + request.form['set_time_min']
    anova.set_temp(cook_temp)
    anova.set_timer(cook_time)
    ready_time = request.form['ready_time']
    time_to_preheat = get_time_diff(get_time(), ready_time) - cook_time - ANOVA_PRE_HEAT_TIME
    if time_to_preheat < 0:
    	time_to_preheat = 0
    	anova.start_anova()
    	# update ready time
    else:
    	delay_min(time_to_preheat)
    	anova.start_anova()

    while not float_compare(float(anova.read_temp()), cook_temp):
        print "target_temp: "+ str(target_temp)
        print "current temp: "+ anova.read_temp()
        time.sleep(1)

    print "start the timer now"
    anova.start_timer()
    # print "mins to start: " + str(get_time_diff(get_time(), request.form['ready_time']) - ANOVA_PRE_HEAT_TIME)
    return render_template('form.html')
    

# if __name__== '__main__':
#     app.run(host='0.0.0.0', use_reloader=True, debug = True)


def main():
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)

    app.anova_controller = RESTAnovaController(ANOVA_MAC_ADDRESS, logger=app.logger)
    print "temp: " + str(app.anova_controller.read_temp())

    # try:
    #     username = os.environ["PYCIRCULATE_USERNAME"]
    #     password = os.environ["PYCIRCULATE_PASSWORD"]
    #     app.wsgi_app = AuthMiddleware(app.wsgi_app, username, password)
    # except KeyError:
    #     warnings.warn("Enable HTTP Basic Authentication by setting the 'PYCIRCULATE_USERNAME' and 'PYCIRCULATE_PASSWORD' environment variables.")

    app.run(host='0.0.0.0', port=5000, use_reloader=True, debug = True)

if __name__ == '__main__':
    main()

