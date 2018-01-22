# Anova sous-vide machine with scheduler 

This is a project to provide scheduler functionality for Anova machine.

It allows users to pre-set the time when the food should be ready. The scheduler function as to estimate the preheat time, and automatically start the anova machine to start cooking at the right time. 

This project utilize the Anova wrapper library by pyCirculate. See below for link.

## Getting Started

Be sure to checkout the basic requirements for PyCirculate library and Flask

### Usage

Simply fill in the time for the food to be ready, and the desired cooking temperature and time.

![web](https://raw.githubusercontent.com/tangchihwei/sous-vide-web/assets/assets/web.png)

## System Diagram
![multiprocess](https://raw.githubusercontent.com/tangchihwei/sous-vide-web/assets/assets/multiprocess.png)

## TODO
1. Better UI for the web, with dynamic updates of the latest cooking status.
2. Allow users to copy recipe link and automatically parse the cook time and temperature
3. Debug "TypeError" after the cook is completed and machine stops.
4. Update preheat estimate with autocalibration.


## Built With

* [PyCirculate](https://github.com/erikcw/pycirculate) - Python wrapper library for Anova 2 Bluetooth LE


