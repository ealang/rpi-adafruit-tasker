# rpi-adafruit-tasker

Basic app runner for Adafruit Mini PiTFT. Specifically [this one](https://www.adafruit.com/product/4484) (1.3" 240x240). Some modifications would be needed to support other displays. Using the python interfacing option as described [here](https://learn.adafruit.com/adafruit-mini-pitft-135x240-color-tft-add-on-for-raspberry-pi/python-setup).

Use buttons to switch apps. Text color indicates the status of the selected app. Exception colors: red for failed, grey for exited without error.

![screenshot](screenshot.png)

# Dev Instructions

Can run on real hardware, or with matplotlib as the display/input driver.

Create a virtual environment and install dependencies:
```
python3 -m venv venv
source venv/bin/activate

# option 1: install dependencies for real hardware
pip install -r requirements.txt.freeze
# option 2: install dependencies for matplotlib virtual mode
pip install -r requirements-matplotlib.txt
```

Run (remove `--virtual` to run on real hardware):
```
python -m tasker.main example-task-config.json --virtual
```

# Launch on Startup

Example of how to run at startup using [Supervisor](http://supervisord.org/index.html).

1. Install app into a virtual environment
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt.freeze
python setup.py install
```

2. Install Supervisor
```
apt install supervisor
```

3. Add a config file

`/etc/supervisor/conf.d/rpi_adafruit_tasker.conf`:
```
[program:rpi_adafruit_tasker]
command=/home/pi/git/rpi-adafruit-tasker/venv/bin/tasker /home/pi/git/rpi-adafruit-tasker/example-task-config.json
stderr_logfile=/var/log/rpi_adafruit_tasker.err.log
autostart=true
```

4. Reload supervisor

```
sudo supervisorctl reread
sudo supervisorctl update
```

You can now check the status with `sudo supervisorctl status` and start/stop/restart by e.g. `sudo supervisorctl restart rpi_adafruit_tasker`.
