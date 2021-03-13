# rpi-adafruit-tasker

Basic app runner for Adafruit Mini PiTFT. Specifically [this one](https://www.adafruit.com/product/4484) (1.3" 240x240). Some modifications would be needed to support other displays. Using the python interfacing option as described [here](https://learn.adafruit.com/adafruit-mini-pitft-135x240-color-tft-add-on-for-raspberry-pi/python-setup).

![screenshot](screenshot.png)

# Dev Instructions

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt.freeze
python main.py example-task-config.json
```
