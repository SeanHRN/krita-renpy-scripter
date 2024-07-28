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
    QMessageBox,
    QSlider,
    QCheckBox,
    QTextEdit,
    QApplication,

)

from PyQt5.QtGui import *

from PyQt5.QtCore import Qt, QEvent


import os
import sys
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
app_notifier = KI.notifier()
app_notifier.setActive(True)


# Load configs from JSON file
z = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "configs.json"))
c = json.load(z)
config_data = c["configs"][0]
default_configs_dict = {
    "string_xposypos" : "{four_space_indent}show {image}:\n{eight_space_indent}pos ({xcoord}, {ycoord})\n",
    "string_atsetposxy": "{four_space_indent}show {image}:\n{eight_space_indent}at setPos({xcoord}, {ycoord})\n",
    "string_alignxy"  : "{four_space_indent}show {image}:\n{eight_space_indent}align ({xcoord}, {ycoord})\n",
    "string_xalignyalign" : "{four_space_indent}show {image}:\n{eight_space_indent}xalign {xcoord} yalign {ycoord}\n",
    "string_layeredimagedefstart" : "layeredimage {overall_image}:\n"
}
pos_button_text = "pos (x, y)"

# For parameterizing the menu text to allow customization
replacer_dict = {
    "{xcoord}" : "x",
    "{ycoord}" : "y"
}

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

def parseLayers(layer, layer_list, coordinates_list, centers_list):
    """
    parseLayers() gets the data from the layers.
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
                centers_list.append([center_point.x(), center_point.y()])
            else:
                currentDoc = KI.activeDocument()
                width = currentDoc.width()
                height = currentDoc.height()
                centers_list.append([round(width/2), round(height/2)])
            layer_list.append(layer)
            coordinates_list.append([coord_x, coord_y])
        elif layer.type() == "grouplayer":
            for child in layer.childNodes():
                parseLayers(child, layer_sublist, coordinates_sublist, \
centers_sublist)
            layer_list.extend(layer_sublist) # TODO: Experiment: putting these indented into the elif instead of by the elif
            coordinates_list.extend(coordinates_sublist)
            centers_list.extend(centers_sublist)


def calculateAlign(data_list, centers_list, spacing_num):
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
        
    spacing_list = generateSpaces(spacing_num)
    new_data_list = []
    for d, c in zip(data_list, centers_list):
        xalign = closestNum(spacing_list, (c[0] / width))
        yalign = closestNum(spacing_list, (c[1] / height))
        new_data_list.append(tuple((d[0],xalign,yalign,d[3],d[4])))
    return new_data_list

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


class TextOutput(QWidget):
    """
    Text window to open up with the Ren'Py Script output
    Button options:
        Copy:  Copies the output text onto the system clipboard.
        Close: Closes both TextOutput and FormatMenu.
        Back:  Closes only TextOutput (this window),
               so that the user can choose a different format.
    """
    def __init__(self, script, prevWindow):
        super().__init__()

        self.setWindowTitle("Ren'Py Script Output")
        self.resize(500,500)

        self.textEdit = QTextEdit()
        self.textEdit.setPlainText(script)
        self.copyButton = QPushButton("Copy To Clipboard")
        self.copyButton.clicked.connect(self.copyText)
        self.closeButton = QPushButton("Close")
        self.closeButton.clicked.connect(self.close)
        self.closeButton.clicked.connect(prevWindow.close)
        self.backButton = QPushButton("Back To Format Selection")
        self.backButton.clicked.connect(self.close)

        textOutputLayout = QVBoxLayout()
        textOutputLayout.addWidget(self.textEdit)
        textOutputLayout.addWidget(self.copyButton)
        textOutputLayout.addWidget(self.closeButton)
        textOutputLayout.addWidget(self.backButton)
        self.setLayout(textOutputLayout)


    def copyText(self):
        clipboard = QApplication.clipboard()
        clipboard.clear(mode=clipboard.Clipboard)
        clipboard.setText(self.textEdit.toPlainText(), mode=clipboard.Clipboard)

class FormatMenu(QWidget):
    """
    Window that should open when called from the docker.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Choose Your Format")
        self.createFormatMenuInterface()
        self.DEBUG_MESSAGE = ""


    def createFormatMenuInterface(self):
        main_layout = QVBoxLayout()
        pos_layout = QHBoxLayout()
        align_layout = QHBoxLayout()
        spacing_layout = QHBoxLayout()
        image_definition_layout = QHBoxLayout()
        settings_layout = QHBoxLayout()

        format_label = QLabel("Output Format")
        pos_label = QLabel("pos")
        #pos_button = QPushButton("pos (x, y)")
        self.pos_button_text = pos_button_text
        self.pos_button = QPushButton(self.pos_button_text, self)
        self.pos_button.clicked.connect(lambda: self.process(1))
        atSetPos_button = QPushButton("at setPos(x, y)")
        atSetPos_button.clicked.connect(lambda: self.process(2))
        align_label = QLabel("align")
        self.spacing_slider = QSlider(Qt.Horizontal, self)
        self.spacing_slider.setGeometry(30, 40, 200, 30)
        self.spacing_slider.setRange(1, 9)
        self.spacing_slider.setValue(9)
        self.spacing_slider.setFocusPolicy(Qt.NoFocus)
        self.spacing_slider.setPageStep(1)
        self.spacing_slider.setTickInterval(1)
        self.spacing_slider.setTickPosition(QSlider.TicksBelow)
        self.spacing_slider.valueChanged[int].connect(self.updateSpacingValue)
        spacing_label = QLabel("Spacing Count: ")
        spacing_label.setToolTip("Choose number of evenly-distributed \
spaces to use for align(x, y).")
        self.spacing_number_label = QLabel(f"{self.spacing_slider.value()}")
        self.spacing_number_label.setAlignment(Qt.AlignVCenter)
        self.rule_of_thirds_check = QCheckBox("Rule of Thirds")
        self.rule_of_thirds_check.setToolTip("Set align(x, y) \
statements to Rule of Thirds intersections. This is equivalent to using 4 spaces.")
        self.rule_of_thirds_check.setChecked(False)
        self.rule_of_thirds_check.toggled.connect(lambda:self.ruleOfThirdsFlag(self.rule_of_thirds_check))
        align_button = QPushButton("align (x, y)")
        align_button.clicked.connect(lambda: self.process(3))
        xalignyalign_button = QPushButton("xalign x yalign y")
        xalignyalign_button.clicked.connect(lambda: self.process(4))
        image_definition_label = QLabel("Image Definition")
        normal_image_def_button = QPushButton("Normal Images")
        normal_image_def_button.setToolTip("Generate the definitions of individual images in Ren'Py using \
the Krita layer structure for the directory.")
        normal_image_def_button.clicked.connect(lambda: self.process(5))
        layered_image_def_button = QPushButton("Layered Image")
        layered_image_def_button.setToolTip("Generate the definition of a Ren'Py layeredimage using \
the Krita layer structure for the directory.")
        layered_image_def_button.clicked.connect(lambda: self.process(6))
        settings_label = QLabel("Output Settings")
        default_button = QPushButton("Default")
        default_button.setToolTip("Revert output text format to the default configurations.")
        self.customize_button = QPushButton("Customize", self)
        self.customize_button.setToolTip("Open configs.json in your default text editor to make changes to the output formats.")
        self.customize_button.clicked.connect(lambda: self.settingCustomize)
        main_layout.addWidget(format_label)
        main_layout.addWidget(pos_label)
        pos_layout.addWidget(self.pos_button)
        pos_layout.addWidget(atSetPos_button)
        main_layout.addLayout(pos_layout)
        main_layout.addWidget(align_label)
        spacing_layout.setContentsMargins(0,0,0,0)
        spacing_layout.addWidget(spacing_label)
        spacing_layout.addWidget(self.spacing_number_label)
        spacing_layout.addWidget(self.spacing_slider)
        spacing_layout.addWidget(self.rule_of_thirds_check)
        main_layout.addLayout(spacing_layout)
        align_layout.addWidget(align_button)
        align_layout.addWidget(xalignyalign_button)
        main_layout.addLayout(align_layout)
        main_layout.addWidget(image_definition_label)
        image_definition_layout.addWidget(normal_image_def_button)
        image_definition_layout.addWidget(layered_image_def_button)
        main_layout.addLayout(image_definition_layout)
        main_layout.addWidget(settings_label)
        settings_layout.addWidget(self.customize_button)
        settings_layout.addWidget(default_button)
        main_layout.addLayout(settings_layout)
        self.setLayout(main_layout)
        self.mainWindow = None

    def process(self, button_num):
        """
        Gets the script and then directs it to the TextOutput window.
        A reference to the FormatMenu (the self) is passed
        so that the first window can be closed from TextOutput.
        """
        outScript = self.writeScript(button_num, self.spacing_slider.value())
        self.outputWindow = TextOutput(outScript, self)
        self.outputWindow.show()
    
    def writeScript(self, button_num, spacing_num):
        """
        Do nothing if the data_list isn't populated.

        Image Definition:
            Button 5: Normal
                - Currently outputs both png and jpg lines if requested,
                  though that would be a double definition, and I don't
                  think anyone would request both png and jpg and not
                  just use the png in a Ren'Py project.
            Button 6: Layered Image (The Ren'Py Feature)
        """
        script = ""
        data_list = self.getData(button_num, spacing_num)
        if len(data_list) == 0:
            return script
        ATL_dict = {}
        currentDoc = KI.activeDocument()
        if currentDoc != None:
            ATL_dict, invalid_dict = self.getATL(currentDoc.rootNode())

        # For image definition scripting
        #
        # d[1] is the xcoord
        # d[2] is the ycoord
        # d[3] is a list
        # d[3][0] is the scale (in this test), so it can't be printed without casting to str.
        # d[4][0] is the file format
        # d[4][1] is out of range on this test
        # d[5] is the list of paths
        #
        if button_num == 5 or button_num == 6:

            #script += self.DEBUG_MESSAGE
            if button_num == 5: # Normal Images
                for index, d in enumerate(data_list):
                    for format in d[4]:
                        script += "image " + d[0] + " = " + "\"" + d[5][index] + "." + format + "\"" + "\n"
                #        script += "BISON: " + s + "\n"
            else: # Layered Image
                overall_image_name = ""
                script += config_data["string_layeredimagedefstart"].format(overall_image=overall_image_name)
                for d in data_list:
                    script += (' '*indent)
                    script += "attribute " + d[0] + ":\n"

        # For image position scripting
        else:
            for d in data_list:
                at_statement = ""
                ATL = ""
                property_dict = {}
                for t in transform_properties:
                    property_dict[t] = None
                no_property_block = True
                if d[0] in ATL_dict:
                    for key in property_dict:
                        if key in ATL_dict[d[0]]:
                            no_property_block = False
                            property_dict[key] = ATL_dict[d[0]][key]
                    for f in ["f", "func", "function"]:
                        if f in ATL_dict[d[0]]:
                            ATL = self.getATLFunction(ATL_dict[d[0]][f], d, data_list)
                            break
                if button_num == 1:
                    script += config_data["string_xposypos"].format\
(four_space_indent=(' '*indent),image=d[0],eight_space_indent=' '*(indent*2),\
xcoord=str(d[1]),ycoord=str(d[2]))
                elif button_num == 2:
                    if no_property_block:
                        optional_colon = ""
                    script += config_data["string_atsetposxy"].format\
(four_space_indent=(' '*indent),image=d[0],eight_space_indent=' '*(indent*2),\
xcoord=str(d[1]),ycoord=str(d[2]))
                elif button_num == 3:
                    script += config_data["string_alignxy"].format\
(four_space_indent=(' '*indent),image=d[0],eight_space_indent=' '*(indent*2),\
xcoord=str(d[1]),ycoord=str(d[2]))
                elif button_num == 4:
                    script += config_data["string_xalignyalign"].format\
(four_space_indent=(' '*indent),image=d[0],eight_space_indent=' '*(indent*2),\
xcoord=str(d[1]),ycoord=str(d[2]))
                for key in property_dict:
                    if property_dict[key] is not None:
                        script += f"{' ' * (indent * 2)}{key} {property_dict[key]}\n"
                if ATL and button_num == 4:
                    script += f"{' ' * (indent * 2)}{ATL}\n"
        return script

    def storeArray(self, dir, tag_dict, path_list, pathLen):
        """
        Concept: Store each max-length path into the final path_list with the
        image file name for each layer.

        Template: "images/your-directory/your-image-name.file-format"

        The Batch Exporter supports png and jpg format, so path_list would get
        a path for each individual format request.
        Layers with no file format tag would be simply skipped over in case
        the user has files in the Krita document that aren't meant to get scripting.

        Why dir[1 : pathLen-1]:
            At this stage, the path (or dir in this function) consists of the directory,
            ending with the layer name as it appears in Krita, with the batch exporter tags.
            The directory strings must be modified to use the corresponding names
            instead of the layer names.
            It starts at 1 instead of 0 because 0 is just the root node in Krita.

        The image formats aren't added to the string here. Instead, the formats are added by writeScript().   
        """
        toInsert = "images/"
        imageFileName = dir[pathLen-1].split(' ')[0]
        for i in dir[1 : pathLen-1]:
            toInsert = toInsert + (i + "/")
        if "e=" in ''.join(dir).lower():
            path_list.append(toInsert + imageFileName)


    # TODO: Get the meta tag inheritance system working.
    def pathRec(self, node, path, tag_dict, path_list, pathLen):
        """
        Searches for all the node to leaf paths and stores them in path_list.
        Currently, layers that aren't batch exporter formated are still sent to storeArray(),
        but they would be ignored. tag_dict isn't used for anything yet because it's not working.
        Reference: GeeksforGeeks solution to finding paths in a binary search tree
        """
        layerData = node.name().split(' ')
        layerName = layerData[0] # parse out actual layer name from metadata
        #for tag in layerData[1:]:
        #    tagPieces = tag.split('=')
        #    tag_dict[tagPieces[0].lower()] = tagPieces[1].lower()
        if (len(path) > pathLen):
            path[pathLen] = node.name()
        else:
            path.append(node.name())
        pathLen = pathLen + 1
        if len(node.childNodes()) == 0:
            self.storeArray(path, tag_dict, path_list, pathLen)
        else:
            for i in node.childNodes():
                # EXPERIMENTAL: Looks silly and work-aroundy but seems to work.
                # The pathbuilding gets messed up without this subtraction on path.
                removeAmount = len(path) - pathLen
                path = path[: len(path) - removeAmount]
                self.pathRec(i, path, tag_dict, path_list, pathLen)


    #TODO: Eventually, this should be used to get the tags for the non-image def scripting as well.
    def recordLayerStructure(self, node, path_list):
        path = []
        tag_dict = defaultdict(str)
        self.pathRec(node, path, tag_dict, path_list, 0)
        return path_list

    def getData(self, button_num, spacing_num):
        """
        Uses a dictionary system to parse the
        layer data and apply changes to coordinates.

        """
        outScript = ""
        data_list =  []
        layer_list = []
        contents = []
        all_coords = []
        all_centers = []
        layer_dict = defaultdict(dict)
        test_list = []
        path_list = []
        currentDoc = KI.activeDocument()
        if currentDoc != None:
            root_node = currentDoc.rootNode()
            path_list = self.recordLayerStructure(root_node, path_list)
            for i in root_node.childNodes():
                parseLayers(i, layer_list, all_coords, all_centers)
            for l in layer_list:
                contents = l.name().split(" ")
                layer_dict[l.name()]["actual name"] = contents[0]
                for c in contents[1:]:
                    if "=" in c:
                        category_data = c.split("=") # 0: Category String, 1: Data String
                        category_data_list = category_data[1].split(",")
                        layer_dict[l.name()][category_data[0]] = category_data_list
            for layer, coord_indv in zip(layer_list, all_coords):
                x = 0
                y = 0
                size_list = []
                image_format_list = []
                if "e" in layer_dict[layer.name()]:
                    image_format_list = [str(j) for j in layer_dict[layer.name()]["e"]]
                if "m" in layer_dict[layer.name()]:
                    for i in layer_dict[layer.name()]["m"]:
                        margin_list = [int(i) for i in layer_dict[layer.name()]["m"]]
                        coord_indv[0] -= max(margin_list)
                        coord_indv[1] -= max(margin_list)
                if "s" in layer_dict[layer.name()]:
                    size_list = [float(i) for i in layer_dict[layer.name()]["s"]]
                    x = round(coord_indv[0] * (min(size_list)/100))
                    y = round(coord_indv[1] * (min(size_list)/100))
                data_list.append(tuple((layer_dict[layer.name()]["actual name"], x, y, size_list, image_format_list, path_list)))
                if button_num == 3 or button_num == 4:
                    data_list = calculateAlign(data_list, all_centers, spacing_num)
        return data_list

    def getATL(self, curr_node):
        """
        getATL() checks for ATL information in invisible layers.
        Since spaces are used to split the contents, I don't think
        the function statement could allow any spaces.

        Tags that are not recognized from the list transform_properties
        are recorded and put in the dictionary invalid_dict.
        """
        ATL_dict = defaultdict(dict)
        invalid_dict = defaultdict(dict)
        for i in curr_node.childNodes():
            if i.visible() == False and i.name().upper().startswith("ATL"):
                if i.type() == "grouplayer":
                    ATL_dict.update(self.getATL(i))
                elif i.type() == "paintlayer":
                    contents = i.name().split(" ")
                    invalid_list = []
                    for c in contents[2:]:
                        if "=" in c:
                            ATL_data = c.split("=") #0: Tag string, 1: Data String
                            ATL_data_list = ATL_data[1]
                            ATL_dict[contents[1]][ATL_data[0]] = ATL_data_list
                            if ATL_data[0] not in transform_properties:
                                invalid_list.append(ATL_data[0])
                    if len(invalid_list) != 0:
                        invalid_dict[contents[1]] = invalid_list

        return ATL_dict, invalid_dict

    def getATLFunction(input_string, input_layer_tuple, input_data):
        """
        The regex is a thing from stack overflow to find
        'comma that is followed by a char that is not a space'.
        """
        modified_string = input_string
        modified_string = re.sub('(,(?=\S)|:)', ", ", modified_string)
        for i in input_data:
            if i[0] == input_layer_tuple[0]:
                if "currX" in modified_string:
                    modified_string = modified_string.replace("currX", str(input_layer_tuple[1]))
                if "currY" in modified_string:
                    modified_string = modified_string.replace("currY", str(input_layer_tuple[2]))
        return modified_string

    def ruleOfThirdsFlag(self, c):
        if c.isChecked() == True:
            self.spacing_slider.setSliderPosition(4)

    def updateSpacingValue(self):
        self.spacing_number_label.setText(str(self.spacing_slider.value()))
        if self.spacing_slider.value() == 4:
            self.rule_of_thirds_check.setChecked(True)
        else:
            self.rule_of_thirds_check.setChecked(False)

    def settingCustomize(self):
        self.pos_button_text = "Senku"
        self.customize_button.setText("CHECK") #TEST PROBLEM: text isn't updating

class GenerateRenpyScripting(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generate Ren'Py Scripting V2 WIP")
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
        generate_button = QPushButton("Generate")
        generate_button.clicked.connect(self.decideStep)

        main_layout = QVBoxLayout()
        main_layout.addWidget(generate_button)

        mainWidget = QWidget(self)
        mainWidget.setLayout(main_layout)
        self.setWidget(mainWidget)

    def decideStep(self):
        #Consideration: Add a system to check if there are solid color layers and/or scrolling.
        #The program should proceed to the generate menu afterwards.
        #For now, it will go straight to the generate menu.
        self.show_format_menu()

    def show_format_menu(self):
        self.f = FormatMenu()
        self.f.show()

    # notifies when views are added or removed
    # 'pass' means do not do anything
    def canvasChanged(self, canvas):
        pass

def kritaClosingEvent():
        clipboard = QApplication.clipboard()
        clipboard.clear(mode=clipboard.Clipboard)
        clipboard.setText("application closed!!!", mode=clipboard.Clipboard)
    #QApplication.closeAllWindows() # not successful yet

def registerDocker():
    Krita.instance().addDockWidgetFactory(DockWidgetFactory\
("generateRenpyScripting", DockWidgetFactoryBase.DockRight\
 , GenerateRenpyScripting))

app_notifier.applicationClosing.connect(kritaClosingEvent) #EXPERIMENTAL
