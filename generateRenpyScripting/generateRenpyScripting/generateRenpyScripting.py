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
                - If both png and jpg are requested for a single image,
                  the jpg line will be written but commented out.
            Button 6: Layered Image (The Ren'Py Feature)
        """
        script = ""

        data_list = self.getData(button_num, spacing_num)
        script += self.DEBUG_MESSAGE
        if len(data_list) == 0:
            script += "Error: data_list not populated.\n"
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
            script += "Printing data from button 5:"
            for line in data_list:
                #for datum in line:
                script += line[0] + "\n"
                script += line[1] + "\n"
                script += str(line[3]) + "\n"
                script += "<<<<<<<<<<<<<\n"
            #bison
            pass #temp
            ##if button_num == 5: # Normal Images
            ##    for index, d in enumerate(data_list):
            ##        for format in d[4]:
            ##            if len(d[4])>1 and format == "jpg":
            ##                script += '#'
            ##            script += "image " + d[0] + " = " + "\"" + d[5][index] + "." + format + "\"" + "\n"
            ##else: # Layered Image
            ##    overall_image_name = ""
            ##    script += config_data["string_layeredimagedefstart"].format(overall_image=overall_image_name)
            ##    for d in data_list:
            ##        script += (' '*indent)
            ##        script += "attribute " + d[0] + ":\n"

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

    def storeArray(self, dir, path_list, pathLen):
        """
        Concept: Store each max-length path into the final path_list (starting with images instead of root).
        """
        toInsert = "images/"
        for i in dir[1 : pathLen-1]:
            toInsert = toInsert + (i + "/")
        imageFileName = dir[pathLen-1]
        self.DEBUG_MESSAGE += "appending to path_list: " + toInsert + imageFileName + "\n"
        path_list.append(toInsert + imageFileName)

    def getTags(self, path_list):
        """
        Function to take in the list of complete layer paths (from within data_list)
        and populate a list of dictionaries of tags for each path.
        It works this way because the Batch Exporter offers meta tag inheritance.
        If [i=false] or [i=no] is found, inheritance is disabled for that layer,
        so the dictionary for that path would be cleared before adding anything.

        problem: d[5] doesn't have the tag data!
        """
        tag_dict_list = []
        for path in path_list:
            tag_dict = {}
            path_pieces = path.split('/')
            for layer in path_pieces:
                layer = layer.lower()
                tag_data = layer.split(' ')[1:]

                # First pass: See if 'i=false' or 'i=no' is present.
                # If so, clear the dictionary before adding any tags.
                for tag in tag_data:
                    letter, value = tag.split('=', 1)
                    if letter == "i":
                        if value == "false" or value == "no":
                            tag_dict.clear()

                # Second pass: Add the tags.
                for tag in tag_data:
                    letter, value = tag.split('=', 1)
                    tag_dict[letter] = value
                    #self.DEBUG_MESSAGE += "letter found: " + letter + "\n"
                    #self.DEBUG_MESSAGE += "value found: " + str(value) + "\n"
            tag_dict_list.append(tag_dict)
            #self.DEBUG_MESSAGE += "Printing out tag_dict_list:\n"
            #for index, d in enumerate(tag_dict_list):
                #self.DEBUG_MESSAGE += "Path: " + path_list[index] + "\n"
                #self.DEBUG_MESSAGE += ("index:" , str(index) + "\n")
                #for key, value in d.items():
                #    self.DEBUG_MESSAGE += key + " : " + value + "\n"
                #self.DEBUG_MESSAGE += "<><><><><>\n"
            #self.DEBUG_MESSAGE += "DICT DONE\n"
        #tag_dict_list.reverse() # EXPERIMENTAL: Get the list in the expected order.
        return tag_dict_list


    def pathRec(self, node, path, path_list, pathLen, coords_list):
        """
        Searches for all the node to leaf paths and stores them in path_list.
        Currently, layers that aren't batch exporter formated are still sent to storeArray(),
        but they would be ignored. tag_dict isn't used for anything yet because it's not working.
        Reference: GeeksforGeeks solution to finding paths in a binary search tree

        New version: Takes out all tag data because it'll be handled elsewhere for the inheritance system.

        Current concept: give storeArray() the entire paths (including all the tags)
        and correct the path data later (while picking up the tags with inheritance)

        New concept: Pick up the coordinates during the process.
        """
        layer_data = node.name().split(' ')
        if (len(path) > pathLen):
            path[pathLen] = node.name()
        else:
            path.append(node.name())
        pathLen = pathLen + 1
        if len(node.childNodes()) == 0:
            self.storeArray(path, path_list, pathLen)
            coord_x = node.bounds().topLeft().x()
            coord_y = node.bounds().topLeft().y()
            coord_center = node.bounds().center()
            coords_list.append([coord_x, coord_y, coord_center])
        else:
            for i in node.childNodes():
                # Looks silly and work-aroundy but seems to work.
                # The pathbuilding gets messed up without this subtraction on path.
                removeAmount = len(path) - pathLen
                path = path[: len(path) - removeAmount]
                self.pathRec(i, path, path_list, pathLen, coords_list)

    def removeUnusedPaths(self, path_list, tag_dict_list, coords_list):
        """
        Copy over usable paths to different lists, which are returned.
        """
        smaller_path_list = []
        smaller_coords_list = []
        for index, path in enumerate(path_list):
            if "e" in tag_dict_list[index]:
                smaller_path_list.append(path_list[index])
                smaller_coords_list.append(coords_list[index])
        return smaller_path_list, smaller_coords_list

    def removeTagsFromPaths(self, path_list):
        """
        Remove the meta tags from the paths.
        The cleaned path gets the last slash cut off because that would
        be between the file name and the extension (which is attached during the print step).
        """
        cleaned_path_list = []
        for path in path_list:
            layers = path.split('/')
            cleaned_path = ""
            for layer in layers:
                #self.DEBUG_MESSAGE += "layer: " + layer + "\n"
                cleaned_path = cleaned_path + layer.split(' ')[0] + "/"
            cleaned_path = cleaned_path[:-1]
            cleaned_path_list.append(cleaned_path)
        return cleaned_path_list

    def getExportLayerList(self, path_list):
        """
        Pre-requisite: removeTagsFromPaths() should have been called to clean path_list.
        Makes a list of the names of the image files (without the extensions) by pulling
        them from the paths.
        """
        export_layer_list = []
        for path in path_list:
            layer_data = path.split('/')
            layer_name_to_export = layer_data[-1]
            export_layer_list.append(layer_name_to_export)
        return export_layer_list

    #TODO: Eventually, this should be used to get the tags for the non-image def scripting as well.
    def recordLayerStructure(self, node, path_list):
        """
        Exports:
            path_list            (Unused paths and tags are filtered out.)
            path_list_with_tags  (Unused paths are filtered out,
                                  but tags (at the layers they are declared) are not.)
            tag_dict_list        (List where each index corresponds to the index of its path,
                                  and the content is a dictionary with the tags applicable to
                                  the final layer of that path, adjusted for Batch Exporter
                                  inheritance.)
            export_layer_list    (List of the names of the layers to be exported; no tags.)

            coords_list          (For each layer: x position, y position, and center point)
        """
        path = []
        path_list_with_tags = []
        tag_dict_list = []
        export_layer_list = []
        coords_list = []
        self.pathRec(node, path, path_list, 0, coords_list)
        tag_dict_list = self.getTags(path_list)

        self.DEBUG_MESSAGE += "Checking coords_list BEFORE pruning: \n"
        for index, c_tuple in enumerate(coords_list):
            self.DEBUG_MESSAGE += "List #" + str(index) + ": " + str(c_tuple)+ "\n"
        path_list, coords_list = self.removeUnusedPaths(path_list, tag_dict_list, coords_list)
        path_list_with_tags = path_list
        path_list = self.removeTagsFromPaths(path_list)
        tag_dict_list = list(filter(None, tag_dict_list))

        export_layer_list = self.getExportLayerList(path_list)
        return path_list, path_list_with_tags, tag_dict_list, export_layer_list, coords_list


    def getData(self, button_num, spacing_num):
        """
        New version of getData() that fully utilizes the dictionary system so that it works with inheritance.
        """
        outScript = ""
        data_list =  []
        export_layer_list = []
        contents = []
        #all_coords = []
        coords_list = []
        all_centers = []
        layer_dict = defaultdict(dict)
        test_list = []
        path_list = []
        tag_dict_list = []
        coords_list = []
        currentDoc = KI.activeDocument()
        if currentDoc != None:
            root_node = currentDoc.rootNode()
            """
            Concept: 1) Get all the paths.
                     2) Get all the tags (with inheritance).
                     3) Filter the paths by checking them with tags.
                     4) Get the names of the layers.
            """
            path_list, path_list_with_tags, tag_dict_list, export_layer_list, coords_list = self.recordLayerStructure(root_node, path_list)

            self.DEBUG_MESSAGE += "Checking path_list_with_tags: \n"
            for p in path_list_with_tags:
                self.DEBUG_MESSAGE += p + "\n"
            self.DEBUG_MESSAGE += "\n"
            self.DEBUG_MESSAGE += "checking path_list: \n"
            for p in path_list:
                self.DEBUG_MESSAGE += p + "\n"
            self.DEBUG_MESSAGE += "checking export_layer_list: \n"
            for e in export_layer_list:
                self.DEBUG_MESSAGE += e + "\n"
            self.DEBUG_MESSAGE += "\n"
            self.DEBUG_MESSAGE += "Checking tag_dict_list: \n"
            for index,td in enumerate(tag_dict_list):
                self.DEBUG_MESSAGE += "Dict " + str(index) + "\n"
                for key,value in td.items():
                    self.DEBUG_MESSAGE += key + " : " + value  + "\n"

            #coords_list = self.getCoordinates(root_node, path_list_with_tags)
            self.DEBUG_MESSAGE += "Checking coords_list: \n"
            for index, c_tuple in enumerate(coords_list):
                self.DEBUG_MESSAGE += "List #" + str(index) + ": " + str(c_tuple)+ "\n"

            for i,layer in enumerate(export_layer_list):
                data_list.append(tuple([layer, path_list[i], tag_dict_list[i], coords_list[i]]))
            #data_list.append(tuple((layer_dict[layer.name()]["actual name"], x, y, size_list, image_format_list, path_list)))


            #for path in path_list:
            #for i in root_node.childNodes():
            #    parseLayers(i, layer_list, all_coords, all_centers)
            #for l in layer_list:
            #    contents = l.name().split(" ")
            #    layer_dict[l.name()]["actual name"] = contents[0]
            #    for c in contents[1:]:
            #        if "=" in c:
            #            category_data = c.split("=") # 0: Category String, 1: Data String
            #            category_data_list = category_data[1].split(",")
            #            layer_dict[l.name()][category_data[0]] = category_data_list
            #for layer, coord_indv in zip(layer_list, all_coords):
            #    x = 0
            #    y = 0
            #    size_list = []
            #    image_format_list = []
            #    if "e" in layer_dict[layer.name()]:
            #        image_format_list = [str(j) for j in layer_dict[layer.name()]["e"]]
            #    if "m" in layer_dict[layer.name()]:
            #        for i in layer_dict[layer.name()]["m"]:
            #            margin_list = [int(i) for i in layer_dict[layer.name()]["m"]]
            #            coord_indv[0] -= max(margin_list)
            #            coord_indv[1] -= max(margin_list)
            #    if "s" in layer_dict[layer.name()]:
            #        size_list = [float(i) for i in layer_dict[layer.name()]["s"]]
            #        x = round(coord_indv[0] * (min(size_list)/100))
            #        y = round(coord_indv[1] * (min(size_list)/100))
            #    data_list.append(tuple((layer_dict[layer.name()]["actual name"], x, y, size_list, image_format_list, path_list)))
            #    if button_num == 3 or button_num == 4:
            #        data_list = calculateAlign(data_list, all_centers, spacing_num)


        #self.DEBUG_MESSAGE += "getData() sending data_list of len: " + str(len(data_list)) + "\n"
        return data_list
        


    def getDataOLD(self, button_num, spacing_num):
        """
        Uses a dictionary system to parse the
        layer data and apply changes to coordinates.

        TODO: Have the dictionaries from tag_dict_list handle the data_list population instead
        so that tag inheritance would work.

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
        tag_dict_list = []
        currentDoc = KI.activeDocument()
        if currentDoc != None:
            root_node = currentDoc.rootNode()
            """
            Concept: 1) Get all the paths.
                     2) Get all the tags (with inheritance).
                     3) Filter the paths by checking them with tags.
            """
            #path_list,tag_dict_list = self.recordLayerStructure(root_node, path_list)
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

        return data_list, tag_dict_list

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
