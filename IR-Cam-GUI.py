#
# package manager dependency: PyQt5 --> Arch: pyqt5 libvips; openSUSE: python-qt5 ?libvips?
# pip dependencies: python-mpv Pillow pyvips
#

import mpv, time, sys, os, locale, subprocess, pyvips, PIL
from PIL import Image
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.uic import loadUi
from datetime import datetime


class MainWindow(QDialog):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        loadUi("./Assets/IR-Cam-GUI.ui",self)

        global dev
        dev = subprocess.getoutput("v4l2-ctl --list-devices | grep -A 2 'MikrOkularFullHD' | grep -m 1 /dev/video | sed -e 's/^\s*//'")

        if dev == "":
            self.textOut.append("Couldn't find ocular camera, using webcam instead")
            dev = "/dev/video0"
        else:
            self.textOut.append("Found ocular camera!")

        self.textOut.append("Using video input "+ dev)

        self.startPreview()
        self.onlyInt = QIntValidator()
        self.interval.setValidator(self.onlyInt)
        self.repeats.setValidator(self.onlyInt)
        self.scalebar.stateChanged.connect(self.scalebarChanged)
        self.browse.clicked.connect(self.browseFolders)
        self.start.clicked.connect(self.startCapture)
        self.quit.clicked.connect(self.exit)

        self.mag.addItems(["-","4x","10x","100x"])
        self.mag.setCurrentIndex(0)

        time.sleep(1.5)
        self.activateWindow()
        self.show()

    def scalebarChanged(self):
        if self.scalebar.isChecked():
            self.col_label.setEnabled(True)
            self.col_black.setEnabled(True)
            self.col_white.setEnabled(True)
        else:
            self.col_label.setEnabled(False)
            self.col_black.setEnabled(False)
            self.col_white.setEnabled(False)

    def browseFolders(self):
        fname=QFileDialog.getExistingDirectory(self, "Select folder", os.environ['HOME']+"/Desktop/IR-Cam-Captures")
        self.path.setText(fname)

    def startPreview(self):
        locale.setlocale(locale.LC_NUMERIC, "C")
        self.player = mpv.MPV(input_default_bindings=True, input_vo_keyboard=True)
        self.player["vo"] = "gpu"
        #self.player["gpu-context"] = "drm"
        self.player["demuxer-lavf-format"] = "video4linux2"
        self.player["demuxer-lavf-o"] = "video_size=1920x1080,input_format=mjpeg"
        self.player.profile = "low-latency"
        self.player.untimed = True
        self.player.play(dev)
        self.start.setEnabled(True)

    def startCapture(self, counter):
        self.start.setEnabled(False)
        self.repeats.setEnabled(False)
        self.interval.setEnabled(False)
        self.browse.setEnabled(False)
        self.mag_label.setEnabled(False)
        self.mag.setEnabled(False)

        if self.scalebar.isChecked():
            makeScale = self.mag.currentIndex()
        else:
            makeScale = 0

        abort = 0

        try:
            repeats = int(self.repeats.text())
        except:
            self.textOut.append("Error: Number of captures not provided!")
            abort = 1

        try:
            interval = int(self.interval.text()) * 1000
        except:
            self.textOut.append("Error: Interval not provided!")
            abort = 1

        if self.mag.currentIndex() == 0:
            self.textOut.append("Error: Magnification not provided!")
            abort = 1

        if os.path.exists(self.path.text()) != True:
            self.textOut.append("Error: Output path not provided!")
            abort = 1
        else:
            path = self.path.text()
        
        if abort == 1:
            self.textOut.append("Not starting experiment, since one or more parameters are missing!")
            self.repeats.setEnabled(True)
            self.interval.setEnabled(True)
            self.browse.setEnabled(True)
            self.start.setEnabled(True)
            self.mag_label.setEnabled(True)
            self.mag.setEnabled(True)
        else:
            if makeScale != 0:
                # set scalebar color and load it
                pngPath = self.setScalebarColor(makeScale)
                scalePng = Image.open(pngPath)

            self.textOut.append("Starting experiment")
            counter = int(0)
        
            def handler():
                nonlocal counter
                counter += 1
                self.saveImage(counter, repeats, path, makeScale, scalePng)
                if counter >= repeats:
                    timer.stop()
                    timer.deleteLater()
            timer = QTimer()
            timer.timeout.connect(handler)
            timer.start(interval)

    def setScalebarColor(self, makeScale):
        self.textOut.append("Generating scale bars ...")
        
        # strings to replace
        blackBar = []
        blackBar.append("style=\"font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;font-size:20px;font-family:sans-serif;-inkscape-font-specification:'sans-serif, Normal';font-variant-ligatures:normal;font-variant-caps:normal;font-variant-numeric:normal;font-variant-east-asian:normal;fill:#000000;stroke-width:1.66669\"")
        blackBar.append("<path style=\"fill:#000000;stroke:#000000;stroke-width:2;stroke-dasharray:none;stroke-opacity:1\" d=\"M 22,1032.4772 H 218\" id=\"path1227\"/>")
        blackBar.append("<path style=\"fill:#000000;stroke:#000000;stroke-width:2;stroke-dasharray:none;stroke-opacity:1\" d=\"m 21,1022.5 v 20\" id=\"path1227-9\"/>")
        blackBar.append("<path style=\"fill:#000000;stroke:#000000;stroke-width:2;stroke-dasharray:none;stroke-opacity:1\" d=\"m 219,1022.5 v 20\" id=\"path1227-9-2\"/>")
        whiteBar = []
        whiteBar.append("style=\"font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;font-size:20px;font-family:sans-serif;-inkscape-font-specification:'sans-serif, Normal';font-variant-ligatures:normal;font-variant-caps:normal;font-variant-numeric:normal;font-variant-east-asian:normal;fill:#FFFFFF;stroke-width:1.66669\"")
        whiteBar.append("<path style=\"fill:#FFFFFF;stroke:#FFFFFF;stroke-width:2;stroke-dasharray:none;stroke-opacity:1\" d=\"M 22,1032.4772 H 218\" id=\"path1227\"/>")
        whiteBar.append("<path style=\"fill:#FFFFFF;stroke:#FFFFFF;stroke-width:2;stroke-dasharray:none;stroke-opacity:1\" d=\"m 21,1022.5 v 20\" id=\"path1227-9\"/>")
        whiteBar.append("<path style=\"fill:#FFFFFF;stroke:#FFFFFF;stroke-width:2;stroke-dasharray:none;stroke-opacity:1\" d=\"m 219,1022.5 v 20\" id=\"path1227-9-2\"/>")
        
        # get svg path
        if makeScale == 1:
            svgPath = "./Assets/ScaleBar4x.svg"
        if makeScale == 2:
            svgPath = "./Assets/ScaleBar10x.svg"
        if makeScale == 3:
            svgPath = "./Assets/ScaleBar100x.svg"
        
        # open the svg file as text
        f = open(svgPath, "rt")
        data = f.read()
        # close the svg file
        f.close()

        # replace the strings
        if self.col_black.isChecked() == True:
            for n in range(0, len(blackBar)):
                data = data.replace(whiteBar[n], blackBar[n])   # replace all occurrences of the required string

        if self.col_white.isChecked() == True:
            for n in range(0, len(whiteBar)):
                data = data.replace(blackBar[n], whiteBar[n])   # replace all occurrences of the required string
        
        # open the svg file in write mode
        f = open(svgPath, "wt")
        # overwrite the svg file with the resulting data
        f.write(data)
        # close the svg file
        f.close()
        
        # get PNG path
        self.textOut.append("Loading scale bars ...")
        if makeScale == 1:
            pngPath = "./Assets/ScaleBar4x.png"
        if makeScale == 2:
            pngPath = "./Assets/ScaleBar10x.png"
        if makeScale == 3:
            pngPath = "./Assets/ScaleBar100x.png"

        # convert the svg to png
        img = pyvips.Image.new_from_file(svgPath,dpi=72,scale=1)
        img.write_to_file(pngPath)

        return pngPath

    def saveImage(self, counter, repeats, path, makeScale, scalePng):
        self.textOut.append("Saving capture: "+str(counter)+" at time: "+str(datetime.now()))
        capture = self.player.screenshot_raw()
        capture.save(f"{path}/Capture-{datetime.now()}.png", compress_level=0)
        if makeScale != 0:
            capture.paste(scalePng, (0,0), scalePng)
            capture.save(f"{path}/Capture-withScale-{datetime.now()}.png", compress_level=0)

        self.textOut.append("Capture "+str(counter)+" complete!")
        if counter >= repeats:
            self.textOut.append("Experiment complete!")
            self.repeats.setEnabled(True)
            self.interval.setEnabled(True)
            self.browse.setEnabled(True)
            self.start.setEnabled(True)
            self.mag_label.setEnabled(True)
            self.mag.setEnabled(True)
            
    def exit(self):
        sys.exit()


app = QApplication([])
window = MainWindow()
widget=QStackedWidget()
widget.addWidget(window)
widget.setFixedWidth(400)
widget.setFixedHeight(500)
widget.show()
app.exec_()
