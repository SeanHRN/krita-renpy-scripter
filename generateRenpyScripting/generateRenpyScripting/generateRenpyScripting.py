from krita import DockWidget, DockWidgetFactory, DockWidgetFactoryBase, Krita

from PyQt5.QtWidgets import (
    QPushButton,
    QLabel,
    QLineEdit,
    QHBoxLayout,
    QVBoxLayout,
    QGroupBox,
    QWidget,
    QDoubleSpinBox,
    QApplication,
    QMessageBox
)

#from PyQt5 import QtCore

import os
from os.path import join, exists, dirname
import math
from pathlib import Path
import webbrowser
from sys import platform
import subprocess
import shutil
import re
import json
from collections import defaultdict

KI = Krita.instance()
open_notifier = KI.notifier()
open_notifier.setActive(True)
close_notifier = KI.notifier()
close_notifier.setActive(True)

default_outfile_name = "renpyblock.txt"
indent = 4
decimal_place_count = 3
transform_properties = {
                        "rotate", "rotate_pad", "transform_anchor",
                        "zoom", "xzoom", "yzoom", "nearest", "alpha",
                        "additive", "around", "alignaround", "crop",
                        "subpixel", "delay", "events", "xpan", "ypan",
                        "xtile", "ytile", "matrixcolor", "blur"
                        }
def closestNum(num_list, value):
    return num_list[min(range(len(num_list)), key = lambda i: abs(num_list[i]-value))]

def truncate(number, digit_count):
    step = 10.0 ** digit_count
    return math.trunc(step * number) / step

def generateSpaces(spacing_count):
    step = 1.0 / (spacing_count - 1)
    spacing_list = []
    for i in range(spacing_count):
        spacing_list.append(truncate(i*step, decimal_place_count))
    return spacing_list

def convertKeyValue(input_dict_value):
    """
    convertKeyValue removes characters from a dictionary string that
    should not be printed. The input is a key, and the output is a string.
    """
    output = str(input_dict_value)
    return output.translate(str.maketrans('','','[]\''))

class CustomDoubleSpinBox(QDoubleSpinBox):
    """
    Customized double spin box with these modifier increments for arrow click:
    Alt: 0.01
    Shift: 0.1
    No Modifier: 1
    Ctrl: 10 (It appears to be default in Qt.)
    """
    def __init__(self, parent=None):
        super(CustomDoubleSpinBox, self).__init__(parent)

    def stepBy(self, steps):
        modifiers = QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.AltModifier:
            QDoubleSpinBox.setSingleStep(self, 0.01)
        elif modifiers == QtCore.Qt.ShiftModifier:
            QDoubleSpinBox.setSingleStep(self, 0.1)
        else:
            QDoubleSpinBox.setSingleStep(self, 1.0)
        QDoubleSpinBox.stepBy(self, steps)

class FormatMenu(QWidget):
    """
    Window that should open when called from the docker.
    """
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout()
        pos_layout = QHBoxLayout()
        align_layout = QHBoxLayout()

        format_label = QLabel("Export Format")
        pos_label = QLabel("pos")
        pos_button = QPushButton("pos (x, y)")
        #pos_button.clicked.connect(lambda: TOFILLIN)
        atSetPos_button = QPushButton("at setPos(x, y)")
        #atSetPos_button.clicked.connect(lambda: TOFILLIN)
        align_label = QLabel("align")
        align_button = QPushButton("align (x, y)")
        #align_button.clicked.connect(lambda: self.process(2))

        xalignyalign_button = QPushButton("xalign x yalign y")
        #xalignyalign_button.clicked.connect(lambda: self.process(3))
        
        main_layout.addWidget(format_label)
        main_layout.addWidget(pos_label)
        pos_layout.addWidget(pos_button)
        pos_layout.addWidget(atSetPos_button)
        main_layout.addLayout(pos_layout)
        main_layout.addWidget(align_label)
        align_layout.addWidget(align_button)
        align_layout.addWidget(xalignyalign_button)
        main_layout.addLayout(align_layout)
        self.setLayout(main_layout)
        self.mainWindow = None


class GenerateRenpyScripting(DockWidget):
    title = "Generate Ren'Py Scripting V2"

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.title)
        self.createInterface()
        self.mainWindow = None
        #open_notifier.imageCreated.connect(self.updateScaleCalculation)
        #open_notifier.imageCreated.connect(self.initiateScaleCalculation)
        #close_notifier.viewClosed.connect(self.wasLast)

    def wasLast(self):
        """
        At the moment a view is closed, the view is still part of the window's
        view count, so when the final view is closed, Window.views() is 1.
        Set the dimensions back to 0x0.
        """
        if len(KI.activeWindow().views()) == 1:
            self.wipeScaleCalculation()

    def showErrorMessage(self, toPrint):
        msg = QMessageBox()
        msg.setText(toPrint)
        msg.exec_()

    def createInterface(self):
        export_button = QPushButton("Export Ren'Py Scripting")
        export_button.clicked.connect(self.decideStep)

        main_layout = QVBoxLayout()
        main_layout.addWidget(export_button)

        mainWidget = QWidget(self)
        mainWidget.setLayout(main_layout)
        self.setWidget(mainWidget)

    def decideStep(self):
        #TODO: Add a system to check if there are solid color layers and/or scrolling.
        #The program should proceed to the export menu afterwards.
        #For now, it will go straight to the export menu.
        self.show_format_menu()

    def show_format_menu(self):
        self.f = FormatMenu()
        self.f.show()

    # notifies when views are added or removed
    # 'pass' means do not do anything
    def canvasChanged(self, canvas):
        pass

def registerDocker():
    Krita.instance().addDockWidgetFactory(DockWidgetFactory\
("generateRenpyScripting", DockWidgetFactoryBase.DockRight\
 , GenerateRenpyScripting))
