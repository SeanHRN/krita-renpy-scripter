from krita import *
import sys
import math
from pathlib import Path
import os
from os.path import join, exists, dirname
import webbrowser
from PyQt5.QtWidgets import *
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

default_outfile_name = "rpblock.txt"
indent = 4
decimal_place_count = 3

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

def parseLayers(layer, layer_list, coordinates_list, centers_list):
    """
    almost the same; just makes a list of layers instead of a list of layer names
    """
    if layer.visible() == True:
        layer_sublist = []
        coordinates_sublist = []
        centers_sublist = []
        lower_n = layer.name().lower()
        if lower_n.find(" e=") != -1:
            coord_x, coord_y, center_point = 0, 0, [0,0]
            if lower_n.find(" t=false") == -1 and lower_n.find(" t=no") == -1:
                coord_x = layer.bounds().topLeft().x()
                coord_y = layer.bounds().topLeft().y()
                center_point = layer.bounds().center()
                layer_list.append(layer)
            coordinates_list.append([coord_x, coord_y])
            centers_list.append([center_point.x(), center_point.y()])
        elif layer.type() == "grouplayer":
                for child in layer.childNodes():
                    parseLayers(child, layer_sublist, coordinates_sublist, \
centers_sublist)
        layer_list.extend(layer_sublist)
        coordinates_list.extend(coordinates_sublist)
        centers_list.extend(centers_sublist)

def calculateAlign(data_list, centers_list, spacing_count):
    """
    calculateAlign converts the pos(x,y) coordinates
    in the data list into align(x,y) coordinates
    by comparing the center point of each image
    to a finite set of values from 0.0 to 1.0.
    """
    width, height = 1, 1
    currentDoc = KI.activeDocument()
    if currentDoc != None:
        width = currentDoc.width()
        height = currentDoc.height()

    spacing_list = generateSpaces(spacing_count)
    new_data_list = []
    for d, c in zip(data_list, centers_list):
        xalign = closestNum(spacing_list, (c[0] / width))
        yalign = closestNum(spacing_list, (c[1] / height))
        new_data_list.append(tuple((d[0],xalign,yalign,d[3])))
    return new_data_list

def getData(button_num, spacing_count):
    """
    Uses a dictionary system to parse the layer data
    and apply changes to coordinates.
    """
    file_open = False
    data_list = []
    layer_list = []
    contents = []
    all_coords = []
    all_centers = []
    layer_dict = defaultdict(dict)
    test_list = []
    currentDoc = KI.activeDocument()
    if currentDoc != None:
        file_open = True
        root_node = currentDoc.rootNode()
        for i in root_node.childNodes():
            parseLayers(i, layer_list, all_coords, all_centers)
    for l in layer_list:
        contents = l.name().split(" ")
        layer_dict[l.name()]["actual name"] = contents[0]
        for c in contents[1:]:
            if "=" in c:
                category_data = c.split("=") # 0: Category string, 1: Data string
                category_data_list = category_data[1].split(",")
                layer_dict[l.name()][category_data[0]] = category_data_list
    for layer, coord_indv in zip(layer_list, all_coords):
        if "m" in layer_dict[layer.name()]:
            for i in layer_dict[layer.name()]["m"]:
                margin_list = [int(i) for i in layer_dict[layer.name()]["m"]]
                coord_indv[0] -= max(margin_list)
                coord_indv[1] -= max(margin_list)
        if "s" in layer_dict[layer.name()]:
            size_list = [float(i) for i in layer_dict[layer.name()]["s"]]
            x = round(coord_indv[0] * (min(size_list)/100))
            y = round(coord_indv[1] * (min(size_list)/100))
            data_list.append(tuple((layer_dict[layer.name()]["actual name"], \
x, y, size_list)))
    if button_num == 2 or button_num == 3:
        data_list = calculateAlign(data_list, all_centers, spacing_count)
    return file_open, data_list

def writeData(input_data, path, format_num):
    outfile = open(path, "w")
    outfile.write("\n")
    prefix = "pos"
    if format_num == 2:
        prefix = "align"
    for d in input_data:
        outfile.write(f"{' ' * indent}show {d[0]}:\n")
        if format_num != 3: # Modes 1 and 2
            outfile.write(f"{' ' * (indent * 2)}{prefix} ({str(d[1])}, {str(d[2])})\n")
        else:               # Mode 3
            outfile.write(f"{' ' * (indent * 2)}xalign {str(d[1])} yalign {str(d[2])}\n")
    outfile.write("\n")
    outfile.write(f"{' ' * indent}pause")
    outfile.close()

def renameRecursion(dir_name, export_dir_name, suffix, folder_name):
    """
    Helper function for recursiveRenameStart()
    dir_name:        the directory to be copied.
    export_dir_name: the directory into which the files are copied.
    suffix:          the part of the file name string that is to be removed.
    folder_name:     name of the top folder of the copy directory;
                     it's needed to prevent infinite looping.
    """
    for filename in os.listdir(dir_name):
        f = os.path.join(dir_name, filename)
        if filename == folder_name:
            continue
        elif filename.find(suffix) != -1 and os.path.isfile(f):
            exp_fname, exp_ext = os.path.splitext(filename)
            exp_fname = exp_fname[:exp_fname.find(suffix)]
            exp_fname += exp_ext
            dst = os.path.join(export_dir_name, exp_fname)
            shutil.copy(f, dst)
        elif os.path.isdir(f):
            sub_export_dir_name = os.path.join(export_dir_name, filename)
            Path(sub_export_dir_name).mkdir(parents=True, exist_ok=False)
            renameRecursion(f, sub_export_dir_name, suffix, folder_name)

def recursiveRenameStart(data_list):
    """
    Uses data_list to get the layer names and the scales.
    A folder named after the smallest scale is created.
    The images of that scale are copied over with the scale tag removed from
    their names.
    The data_list gives the scale list in numbers out of 100, so this function
    divides those numbers by 100 to get the multiplier for the folder name.
    """
    if KI.activeDocument() != None:
        dir_name = os.path.dirname(KI.activeDocument().fileName())
        dir_name = os.path.join(dir_name, "export")
        smallest_scale = 200.0
        for d in data_list:
            if min(d[3]) < smallest_scale:
                smallest_scale = min(d[3])
        suffix = "_@" + str(smallest_scale/100) + "x"
        new_folder_name = "x" + str(smallest_scale/100.0)
        export_dir_name = dir_name + os.sep + new_folder_name
        Path(export_dir_name).mkdir(parents=True, exist_ok=True)
        #    of = open(os.path.join(export_dir_name, "diagnostic.txt"), "w")
        #    of.write(dir_name + "\n" + export_dir_name + "\n" + suffix + "\n")
        #    of.close()
        renameRecursion(dir_name, export_dir_name, suffix, new_folder_name)

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

class GenerateRenpyScripting(DockWidget):
    title = "Generate Ren'Py Scripting"

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.title)
        self.createInterface()
        self.mainWindow = None
        open_notifier.imageCreated.connect(self.updateScaleCalculation)
        open_notifier.imageCreated.connect(self.initiateScaleCalculation)
        close_notifier.viewClosed.connect(self.wasLast)

    def initiateScaleCalculation(self):
        self.mainWindow = KI.activeWindow()
        self.mainWindow.activeViewChanged.connect(self.updateScaleCalculation)

    def wasLast(self):
        """
        At the moment a view is closed, the view is still part of the window's
        view count, so when the final view is closed, Window.views() is 1.
        Set the dimensions back to 0x0.
        """
        if len(KI.activeWindow().views()) == 1:
            self.wipeScaleCalculation()

    def bang(self, toPrint):
        """
        For debugging.
        """
        msg = QMessageBox()
        msg.setGeometry(100, 200, 100, 100)
        msg.setText(toPrint)
        msg.exec_()

    def createInterface(self):
        export_label = QLabel("Export")
        export_label.setToolTip("Export a file with a block of Ren'Py scripting\
for a quick copy and paste.")

        pos_button = QPushButton("pos (x, y)")
        pos_button.clicked.connect(lambda: self.process(1))

        align_button = QPushButton("align (x, y)")
        align_button.clicked.connect(lambda: self.process(2))

        xalignyalign_button = QPushButton("xalign x yalign y")
        xalignyalign_button.clicked.connect(lambda: self.process(3))

        self.spacing_slider = QSlider(Qt.Horizontal, self)
        self.spacing_slider.setGeometry(30, 40, 200, 30)
        self.spacing_slider.setRange(2, 9)
        self.spacing_slider.setValue(9)
        self.spacing_slider.setFocusPolicy(Qt.NoFocus)
        self.spacing_slider.setPageStep(1)
        self.spacing_slider.setTickInterval(1)
        self.spacing_slider.setTickPosition(QSlider.TicksBelow)
        self.spacing_slider.valueChanged[int].connect(self.updateSpacingValue)
        self.spacing_label = QLabel("align (x, y) Spacing Count: ")
        self.spacing_label.setToolTip("Choose number of evenly-distributed \
spaces to use for align(x, y).")
        self.spacing_number_label = QLabel(f"{self.spacing_slider.value()}")
        self.spacing_number_label.setAlignment(Qt.AlignVCenter)
        self.rule_of_thirds_check = QCheckBox("Rule of Thirds")
        self.rule_of_thirds_check.setToolTip("Set align(x, y) \
statements to Rule of Thirds intersections. This is equivalent to using 4 spaces.")
        self.rule_of_thirds_check.setChecked(False)

        scale_label = QLabel("Scale Percentage Size Calculator")
        scale_label.setToolTip("Check the image's dimensions \
at the given scale.\nHold Alt to increment by 0.01%.\nHold Shift to increment \
by 0.1%.\nHold Ctrl to edit by 10%.")
        self.scale_box_percent = CustomDoubleSpinBox(self)
        self.scale_box_percent.setRange(0.0, 200.0)
        self.scale_box_percent.setValue(100.0)
        self.scale_box_percent.valueChanged[float].connect(self.calculatorScaleChanged)
        scale_text = QLabel("% Scale Dimensions:")
        self.onlyDouble = QDoubleValidator()
        width_label = QLabel("Width:")
        self.calculator_width = QLineEdit(self)
        self.calculator_width.setValidator(self.onlyDouble)
        self.calculator_width.setText("0.0")
        self.calculator_width.textEdited[str].connect(self.calculatorWidthEdited)
        height_label = QLabel("Height:")
        self.calculator_height = QLineEdit(self)
        self.calculator_height.setValidator(self.onlyDouble)
        self.calculator_height.setText("0.0")
        self.calculator_height.textEdited[str].connect(self.calculatorHeightEdited)

        rename_button = QPushButton("Rename Batch-Exported Files")
        rename_button.clicked.connect(lambda: self.renameClicked())
        rename_button.setToolTip("Option to save copies of the Batch-Exported \
files of the smallest scale without the size suffix, placed in a folder.")

        filename_label = QLabel("Output File")
        self.filename_line = QLineEdit()
        self.filename_line.setToolTip("Output file name with .[extension]")
        self.filename_line.setText(default_outfile_name)

        main_layout = QVBoxLayout()
        export_layout = QHBoxLayout()
        spacing_layout = QHBoxLayout()
        scale_layout = QHBoxLayout()

        main_layout.addWidget(export_label)
        export_layout.addWidget(pos_button)
        export_layout.addWidget(align_button)
        export_layout.addWidget(xalignyalign_button)
        export_layout.setContentsMargins(0, 4, 0, 2) #left top right bottom
        main_layout.addLayout(export_layout)

        main_layout.addWidget(self.spacing_label)
        spacing_layout.setContentsMargins(0,0,0,0)
        spacing_layout.addWidget(self.spacing_number_label)
        spacing_layout.addWidget(self.spacing_slider)
        spacing_layout.addWidget(self.rule_of_thirds_check)
        main_layout.addLayout(spacing_layout)

        main_layout.addWidget(scale_label)
        self.scale_box_percent.setGeometry(0, 0, 10, 10)
        scale_layout.addWidget(self.scale_box_percent)
        scale_layout.addWidget(scale_text)
        scale_layout.addWidget(width_label)
        scale_layout.addWidget(self.calculator_width)
        scale_layout.addWidget(height_label)
        scale_layout.addWidget(self.calculator_height)
        main_layout.addLayout(scale_layout)

        main_layout.addWidget(rename_button)
        main_layout.addWidget(filename_label)
        main_layout.addWidget(self.filename_line)
        main_layout.addStretch()

        mainWidget = QWidget(self)
        mainWidget.setLayout(main_layout)
        self.setWidget(mainWidget)

    def updateScaleCalculation(self):
        multiplier = float(self.scale_box_percent.value() / 100.0)
        currentDoc = KI.activeDocument()
        width, height = 0.0, 0.0
        if currentDoc != None:
            width = round((currentDoc.width() * multiplier), decimal_place_count)
            height = round((currentDoc.height() * multiplier), decimal_place_count)
        self.calculator_width.setText(f"{width}")
        self.calculator_height.setText(f"{height}")

    def wipeScaleCalculation(self):
        self.calculator_width.setText("0")
        self.calculator_height.setText("0")

    def calculatorScaleChanged(self):
        currentDoc = KI.activeDocument()
        multiplier = float(self.scale_box_percent.value() / 100.0)
        if currentDoc != None:
            width = round((float(currentDoc.width()) * multiplier), decimal_place_count)
            height = round((float(currentDoc.height()) * multiplier), decimal_place_count)
            if self.calculator_width.hasFocus() == False:
                self.calculator_width.setText(str(width))
            if self.calculator_height.hasFocus() == False:
                self.calculator_height.setText(str(height))

    def calculatorWidthEdited(self):
        """
        Difference between QLineEdit::textChanged() and QLineEdit::textEdited:
        textEdited() is emitted whenever the text is directly edited.
        textChanged() is emitted whenever the text is edited by any means.
        Use textEdited() to not have calculation loops.
        """
        currentDoc = KI.activeDocument()
        multiplier = 1.0
        if currentDoc != None:
            try:
                multiplier = float(self.calculator_width.text()) / currentDoc.width()
            except:
                multiplier = 1.0
            if self.scale_box_percent.hasFocus() == False:
                self.scale_box_percent.setValue(100 * multiplier)
            self.calculator_height.setText(f"{round(float(currentDoc.height() * multiplier), 2)}")

    def calculatorHeightEdited(self):
        """
        Difference between QLineEdit::textChanged() and QLineEdit::textEdited:
        textEdited() is emitted whenever the text is directly edited.
        textChanged() is emitted whenever the text is edited by any means.
        Use textEdited() to not have calculation loops.
        """
        currentDoc = KI.activeDocument()
        multiplier = 1.0
        if currentDoc != None:
            try:
                multiplier = float(self.calculator_height.text()) / currentDoc.height()
            except:
                multiplier = 1.0
            if self.scale_box_percent.hasFocus() == False:
                self.scale_box_percent.setValue(100 * multiplier)
            self.calculator_width.setText(f"{round(float(currentDoc.width() * multiplier), 2)}")

    def updateSpacingValue(self):
        self.spacing_number_label.setText(str(self.spacing_slider.value()))

    def process(self, button_num):
        spacing_count = 9 # Just a placeholder value that works.
        if self.rule_of_thirds_check.isChecked():
            spacing_count = 4
        else:
            spacing_count = self.spacing_slider.value()
        file_open_test_result, data = getData(button_num, spacing_count)
        if file_open_test_result == True:
            path = str(QFileDialog.getExistingDirectory(None, "Select a save location."))
            outfile_name = default_outfile_name
            if self.filename_line.text() != "":
                outfile_name = self.filename_line.text()
            path += os.sep + outfile_name
            writeData(data, path, button_num)
            outfile_exists = exists(path)
            if outfile_exists:
                webbrowser.open(path)
            else:
                push_message = "Failure: Open a Krita document."
                QMessageBox.information(QWidget(), "Generate Ren'Py Scripting", push_message)

    def renameClicked(self):
        """
        The getData() call here ignores the first value
        and gets the second value. The inputs [1, 9] don't really matter here.
        """
        data = getData(1, 9)[1]
        recursiveRenameStart(data)

    def canvasChanged(self, canvas):
        pass

def registerDocker():
    Krita.instance().addDockWidgetFactory(DockWidgetFactory\
("generateRenpyScripting", DockWidgetFactoryBase.DockRight\
 , GenerateRenpyScripting))
