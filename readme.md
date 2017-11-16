This lets you use a webcam to scan QR codes, and POSTs the scanned ids to the library server.


## Installation

```
sudo apt install libzbar0 libjpeg8-dev
pip install -r requirements.txt
```

## Usage

```
python main.py <LIBRARY HOST>
```

## Note on autofocus

We're using C920 webcams which have a very sensitive autofocus.

I recommend [disabling autofocus](https://stackoverflow.com/a/16658508/1097920):

    v4l2-ctl -c focus_auto=0

Then manually setting the focus:

    v4l2-ctl -c focus_absolute=20

For reference: `v4l2-ctl -l`

If your video device is one other than `/dev/video0`, use the `-d` flag to specify it.

## Running remotely

We're running this off of Raspberry Pis.

When SSH'd into the Pi, to launch properly:

    export DISPLAY=:0
    python3 main.py

If you need to wake the Pi's screen:

    export DISPLAY=:0
    xset s reset
