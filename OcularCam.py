#
# package manager dependency: PyQt5 --> Arch: pyqt5; openSUSE: python-qt5
# pip dependencies: python-mpv Pillow
#

import mpv, time, sys, os, locale, subprocess
from PIL import Image, ImageDraw, ImageFont
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.uic import loadUi
from datetime import datetime


class MainWindow(QDialog):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        loadUi("GUI.ui",self)

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
        self.start.clicked.connect(self.prepare)
        self.quit.clicked.connect(self.exit)
        self.mag.addItems(["-","4x","10x","40x"])
        self.mag.setCurrentIndex(0)
        self.posi.addItems(["TL","TR","BL","BR"])
        self.posi.setCurrentIndex(2)
        time.sleep(1.5)
        self.activateWindow()
        self.show()


    def scalebarChanged(self):
        global makeScale
        if self.scalebar.isChecked():
            self.col_label.setEnabled(True)
            self.col_black.setEnabled(True)
            self.col_white.setEnabled(True)
            self.posi_label.setEnabled(True)
            self.posi.setEnabled(True)
            makeScale = self.mag.currentIndex()
        else:
            self.col_label.setEnabled(False)
            self.col_black.setEnabled(False)
            self.col_white.setEnabled(False)
            self.posi_label.setEnabled(False)
            self.posi.setEnabled(False)
            makeScale = 0


    def browseFolders(self):
        fname=QFileDialog.getExistingDirectory(self, "Select folder", os.environ['HOME']+"/Desktop/OcularCam-Captures")
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


    def prepare(self):
        abort = self.checkAbort()
        if abort == 1:
            self.textOut.append("Not starting experiment, since one or more parameters are missing!")
        else:
            self.prepareScalebar()
            self.startExperiment()

        
    def checkAbort(self):
        self.start.setEnabled(False)
        self.repeats_label.setEnabled(False)
        self.repeats.setEnabled(False)
        self.interval_label.setEnabled(False)
        self.interval.setEnabled(False)
        self.path_label.setEnabled(False)            
        self.browse.setEnabled(False)
        self.mag_label.setEnabled(False)
        self.mag.setEnabled(False)
        self.scalebar.setEnabled(False)
        self.col_label.setEnabled(False)
        self.col_black.setEnabled(False)
        self.col_white.setEnabled(False)
        self.posi_label.setEnabled(False)
        self.posi.setEnabled(False)

        abort = 0
        try:
            global repeats
            repeats = int(self.repeats.text())
        except:
            self.textOut.append("Error: Number of captures not provided!")
            abort = 1
        try:
            global interval
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
            global path
            path = self.path.text()
        #if self.scalebar.isChecked() & interval == 1:
        #    self.textOut.append("Error: Inserting the scalebar requires the interval to be >= 2 s")
        #    abort = 1

        if abort == 1:
            self.start.setEnabled(True)
            self.repeats_label.setEnabled(True)
            self.repeats.setEnabled(True)
            self.interval_label.setEnabled(True)
            self.interval.setEnabled(True)
            self.path_label.setEnabled(True)
            self.browse.setEnabled(True)
            self.mag_label.setEnabled(True)
            self.mag.setEnabled(True)
            self.scalebar.setEnabled(True)
            if self.scalebar.isChecked():
                self.col_label.setEnabled(True)
                self.col_black.setEnabled(True)
                self.col_white.setEnabled(True)
                self.posi_label.setEnabled(True)
                self.posi.setEnabled(True)
        return abort


    def prepareScalebar(self):
        self.textOut.append("Preparing scale bar ...")
        # set calibration and corresponding text
        global calibration, cal_text, color, position
        if self.mag.currentIndex() == 1:
            calibration = 195
            cal_text = "150 µm"
        elif self.mag.currentIndex() == 2:
            calibration = 262
            cal_text = "40 µm"
        elif self.mag.currentIndex() == 3:
            calibration = 198
            cal_text = "20 µm"
        # set scale bar color
        if self.col_black.isChecked() == True:
            color = (0, 0, 0, 255)
        else:
            color = (255, 255, 255, 255)
        # set position
        position = self.posi.currentIndex()


    def startExperiment(self):  
        self.textOut.append("Starting experiment")
        counter = int(0)

        def handler():
            nonlocal counter
            counter += 1
            self.saveImage(counter)
            if counter >= repeats:
                timer.stop()
                timer.deleteLater()
        timer = QTimer()
        timer.timeout.connect(handler)
        timer.start(interval)


    def saveImage(self, counter):
        self.textOut.append("Saving capture: "+str(counter)+" at time: "+str(datetime.now()))
        capture = self.player.screenshot_raw()
        capture.save(f"{path}/Capture-{datetime.now()}.png", compress_level=1)
        if makeScale != 0:
            self.insertScalebar(capture)

        self.textOut.append("Capture "+str(counter)+" complete!")
        if counter >= repeats:
            self.textOut.append("Experiment complete!")
            self.start.setEnabled(True)
            self.repeats_label.setEnabled(True)
            self.repeats.setEnabled(True)
            self.interval_label.setEnabled(True)
            self.interval.setEnabled(True)
            self.path_label.setEnabled(True)
            self.browse.setEnabled(True)
            self.mag_label.setEnabled(True)
            self.mag.setEnabled(True)
            self.scalebar.setEnabled(True)
            if self.scalebar.isChecked():
                self.col_label.setEnabled(True)
                self.col_black.setEnabled(True)
                self.col_white.setEnabled(True)
                self.posi_label.setEnabled(True)
                self.posi.setEnabled(True)


    def insertScalebar(self, capture):
        img_w, img_h = capture.size
        font = ImageFont.truetype('/usr/share/fonts/noto/NotoSans-Regular.ttf', 20)
        text_l, text_t, text_w, text_h = font.getbbox(cal_text, anchor="lt")
        margin = 20
        line_w = 2
        side_length = 20
        # position scale bar in desired corner
        if position == 0:
            offsetX = 0
            offsetY = 0
        elif position == 1:
            offsetX = img_w - margin*2 - calibration
            offsetY = 0
        elif position == 2:
            offsetX = 0
            offsetY = img_h - margin*2 - text_h - 5
        elif position == 3:
            offsetX = img_w - margin*2 - calibration
            offsetY = img_h - margin*2 - text_h - 5
        # calculate the x,y coordinates of the bars and text
        side1_xy1 = ((offsetX + margin),(offsetY + margin))
        side1_xy2 = ((offsetX + margin),(offsetY + margin + side_length))
        side2_xy1 = ((offsetX + margin + calibration),(offsetY + margin))
        side2_xy2 = ((offsetX + margin + calibration),(offsetY + margin + side_length))
        bar_xy1 = ((offsetX + margin),(offsetY + margin + (side_length/2)))
        bar_xy2 = ((offsetX + margin + calibration),(offsetY + margin + (side_length/2)))
        txt_xy = ((offsetX + margin + (calibration/2)),(offsetY + margin + side_length))
        # draw the scalebar
        draw = ImageDraw.Draw(capture)
        draw.line([side1_xy1,side1_xy2], width=line_w, fill=color)
        draw.line([side2_xy1,side2_xy2], width=line_w, fill=color)
        draw.line([bar_xy1,bar_xy2], width=line_w, fill=color)
        draw.text((txt_xy), cal_text, font=font, align="center", anchor="mt", fill=color)
        # save the image
        self.textOut.append("Saving with scale bar")
        capture.save(f"{path}/Capture-withScale-{datetime.now()}.png", compress_level=1)


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
