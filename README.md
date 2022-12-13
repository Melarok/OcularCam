# OcularCam
This is a small utility to record time-series images from a webcam-like camera on Linux. It's intended for use with a USB microscope ocular camera.

## Features:
- Live preview of the camera feed during the experiment.
- Setting up the experiment by specifying the number of captures to be made and the interval between them.
- Insertion of a scale bar into any corner of the image. It's also possible to choose between a black and a white scale bar.
- Supports multiple magnifications.

## Limitations:
### Many things are currently hard-coded, so if you want to adapt it to your setup you'll have to change some values in the code.
- Scale bar calibration is hard-coded: I'm planing to extend it, so one can supply their own calibration file for the scale bar.
- Automatic camera selection is hard-coded, so you'll need to alter that part of the code or the software will default to `/dev/video0`.

## Dependencies:
- pyqt5
- python-mpv
- Pillow

## Usage:
- `git clone` this repo and `cd` into it
- Run the code with `python OcularCam.py`
- Alternatively, create a .desktop file for ease of use
