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

from PyQt5.QtCore import Qt, QEvent, QPoint

import xml.etree.ElementTree as ET

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
from typing import Iterable, List, TypeVar
T = TypeVar("T")

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
    "string_layeredimagedefstart" : "layeredimage {overall_image}:\n",
    "atl_zoom_decimal_places" : "3",
    "atl_rotate_decimal_places" : "3"
}
default_button_text_dict = {
    "pos_button_text": "pos (x, y)"
}
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

"""
Function from Delena Malan to sort a list with a sublist given priority.
sortListByPriority(values: <list to sort>, priority: <sublist>)
"""
def sortListByPriority(values: Iterable[T], priority: List[T]) -> List[T]:
    priority_dict = {k: i for i, k in enumerate(priority)}
    def priority_getter(value):
        return priority_dict.get(value, len(values))
    return sorted(values, key=priority_getter)

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

def calculateAlign(data_list, spacing_num):
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
    align_modified_data_list = []
    for line in data_list:
        center = line[3][2]
        xalign = closestNum(spacing_list, (line[3][2].x() / width))
        yalign = closestNum(spacing_list, (line[3][2].y() / height))
        modified_coords = [xalign, yalign, center]
        align_modified_data_list.append(tuple((line[0],line[1],line[2],modified_coords)))
    return align_modified_data_list


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
        self.pos_button_text = default_button_text_dict["pos_button_text"]
        self.pos_button = QPushButton(self.pos_button_text, self)
        self.pos_button.clicked.connect(lambda: self.process(1))
        atSetPos_button = QPushButton("at setPos(x, y)")
        atSetPos_button.clicked.connect(lambda: self.process(2))
        align_label = QLabel("align")
        self.spacing_slider = QSlider(Qt.Horizontal, self)
        self.spacing_slider.setGeometry(30, 40, 200, 30)
        self.spacing_slider.setRange(2, 9)
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

        Each line in data_list:
            line[0] - Name of the layer with no meta tags
            line[1] - Directory from /images/ to /layername/, with no file extension.
            line[2] - Dictionary of meta tags applicable to the layer.
            line[3] - Tuple containing xcoord, ycoord, and center point (as a QPoint)

        Image Definition:
            Button 5: Normal
                - Format Priority:
                      - If both png and jpg are requested for a single image,
                        the jpg line will be written but commented out.
                      - If webp is requested, it takes priority over png,
                        though webp isn't actually supported by the Batch Exporter plugin;
                        it's just preferred for Ren'Py.
                      - Any unrecognized format get a commented out line.
            Button 6: Layered Image (The Ren'Py Feature)
        """
        script = ""

        data_list = self.getDataList(button_num, spacing_num)
        script += self.DEBUG_MESSAGE
        if len(data_list) == 0:
            script += "Cannot find layers to script. Check whether your target layers have Batch Exporter format.\n"
            return script

        ATL_dict = {}
        currentDoc = KI.activeDocument()
        if currentDoc != None:
            ATL_dict, invalid_dict = self.getATL(currentDoc.rootNode())
        #BISON
        if button_num == 5 or button_num == 6:
            if button_num == 5: # Normal Images
                for line in data_list:
                    line[2]["e"] = sortListByPriority(values=line[2]["e"], priority=["webp","png","jpg","jpeg"])
                    if "e" in line[2]:
                        format_set = set(line[2]["e"])
                        chosen_format = ""
                        if "webp" in format_set:
                            chosen_format = "webp"
                        elif "png" in format_set:
                            chosen_format = "png"
                        elif "jpg" in format_set or "jpeg" in format_set:
                            chosen_format = "jpg"
                        for f in line[2]["e"]:
                            if f != chosen_format:
                                script += '#'
                            script += config_data["string_normalimagedef"].format\
(image=line[0],path_to_image=line[1],file_extension=f)
                    else:
                        script += "### Error: File format not defined for layer " + line[0] + "\n"
                    if "scaleX" in line[2]:
                        script += str(line[2]["scaleX"])+"\n"
                    if "scaleY" in line[2]:
                        script += str(line[2]["scaleY"])+"\n"
            ##else: # Layered Image
            ##    overall_image_name = ""
            ##    script += config_data["string_layeredimagedefstart"].format(overall_image=overall_image_name)
            ##    for d in data_list:
            ##        script += (' '*indent)
            ##        script += "attribute " + d[0] + ":\n"

        # For image position scripting
        else:
            for line in data_list:
                modifier_block = self.getModifierBlock(line)
                if button_num == 1:
                    script += config_data["string_xposypos"].format\
(four_space_indent=(' '*indent),image=line[0],eight_space_indent=' '*(indent*2),\
xcoord=str(line[3][0]),ycoord=str(line[3][1]))
                    script += modifier_block
                elif button_num == 2:
                    #if no_property_block:
                    #    optional_colon = ""
                    script += config_data["string_atsetposxy"].format\
(four_space_indent=(' '*indent),image=line[0],eight_space_indent=' '*(indent*2),\
xcoord=str(line[3][0]),ycoord=str(line[3][1]))
                    script += modifier_block
                elif button_num == 3:
                    script += config_data["string_alignxy"].format\
(four_space_indent=(' '*indent),image=line[0],eight_space_indent=' '*(indent*2),\
xcoord=str(line[3][0]),ycoord=str(line[3][1]))
                elif button_num == 4:
                    script += config_data["string_xalignyalign"].format\
(four_space_indent=(' '*indent),image=line[0],eight_space_indent=' '*(indent*2),\
xcoord=str(line[3][0]),ycoord=str(line[3][1]))

        return script


    def storePath(self, dir, path_list, pathLen):
        """
        Concept: Store each max-length path into the final path_list (starting with images instead of root).
        """
        toInsert = "images/"
        for i in dir[1 : pathLen-1]:
            toInsert = toInsert + (i + "/")
        imageFileName = dir[pathLen-1]
        path_list.append(toInsert + imageFileName)


    def updateMaskPropertiesDict(self, tag_dict, tm_node):
        """
        Helper function to make sure the transform properties update correctly
        in a given dictionary.

        The node passed in must be a transform mask.

        Property                                : Data Type (Not in the original XML string, but instead how it's stored)
        scaleX and scaleY (xzoom and yzoom)     : floats

        transformedCenter (xoffset and yoffset) : int array of [x, y]
            [Must]
        
        #basic:
        #tag_dict[p.tag] = p.attrib
        """
        xml_root = ET.fromstring(tm_node.toXML())
        for ft in xml_root.iter("free_transform"):
            for p in ft:
                #self.DEBUG_MESSAGE += p.tag + "   :  " + str(p.attrib) + "\n" # Keep this for checking the data.
                # scaleX and scaleY: Multiply the new scale by the existing scale.
                if p.tag == "scaleX":
                    if "scaleX" in tag_dict.keys():
                        tag_dict["scaleX"] = float(tag_dict["scaleX"]) * float(p.attrib["value"])
                    else:
                        tag_dict["scaleX"] = p.attrib["value"]
                elif p.tag == "scaleY":
                    if "scaleY" in tag_dict.keys():
                        tag_dict["scaleY"] = float(tag_dict["scaleY"]) * float(p.attrib["value"])
                    else:
                        tag_dict["scaleY"] = p.attrib["value"]

                # rotation: Add to existing value. Convert from radians to degrees.
                if p.tag == "aZ":
                    new_rot_degrees = float(p.attrib["value"]) * (180 / math.pi)
                    if "aZ" in tag_dict.keys():
                        updated_rot_degrees = float(tag_dict["aZ"]) + new_rot_degrees
                        tag_dict["aZ"] = float(updated_rot_degrees % 360)
                    else:
                        tag_dict["aZ"] = float(new_rot_degrees % 360)

                # transformedCenter: Add to existing value.
                """
                Issue: This probably isn't an accurate use of offset.
                if p.tag == "transformedCenter":
                    if "transformedCenter" in tag_dict.keys():
                        new_x = tag_dict["transformedCenter"][0] + int(float(p.attrib["x"]))
                        new_y = tag_dict["transformedCenter"][0] + int(float(p.attrib["y"]))
                        #self.DEBUG_MESSAGE += "new offset: " + str(p.attrib["x"]) + ", " + str(p.attrib["y"]) + "\n"
                        tag_dict["transformedCenter"] = [new_x, new_y]
                    else:
                        #self.DEBUG_MESSAGE += "entering offset initially: " + str(p.attrib["x"]) + ", " + str(p.attrib["y"]) + "\n"
                        tag_dict["transformedCenter"] = [int(float(p.attrib["x"])), int(float(p.attrib["y"]))]
                """

        return tag_dict


    def getMaskPropertiesRecursion(self, search_path_pieces, tag_dict, curr_node):
        """
        Check through a path and pick up the transform mask properties for that path's tag_dict.
        Case 1: The mask is a sibling layer, so it applies to all its siblings.
        Case 2: The mask is a child layer, so it applies only to its parent.

        Check for case 1 before descending. At the end of the path, case 2 will be seen if it's there.
        
        For now, all the XML info under "free_transform" is added to the dictionary.

        The recursion halts because the list of layers in the path to explore decreases with each call.
        """
        # path is empty, so the leaf is reached, so check for child transform layers
        if not search_path_pieces:
            for leaf_child in curr_node.childNodes():
                if leaf_child.type() == "transformmask" and leaf_child.visible():
                    tag_dict = self.updateMaskPropertiesDict(tag_dict, leaf_child)
        else:
            for check_layer in curr_node.childNodes():
                if check_layer.type() == "transformmask" and check_layer.visible():
                    tag_dict = self.updateMaskPropertiesDict(tag_dict, check_layer)
            for check_layer in curr_node.childNodes():
                if search_path_pieces:
                    if check_layer.name() == search_path_pieces[0]: # Implicitly, this should only ever be a group or a paint layer.
        #            #if check_layer.type() == "grouplayer" or check_layer.type() == "paintlayer":
                        curr_node = check_layer
                        self.getMaskPropertiesRecursion(search_path_pieces[1:], tag_dict, curr_node)


    def getMaskPropertiesStart(self, path_pieces, tag_dict):
        """
        TODO: Function to check a path for transform masks and add their properties to the dictionary.
        """
        currentDoc = KI.activeDocument()
        if currentDoc != None:
            curr_node = currentDoc.rootNode()
        #search_path = path_pieces.split("/",1)

        #search_path_pieces = search_path.split('/')
        self.getMaskPropertiesRecursion(path_pieces[1:], tag_dict, curr_node)

        return tag_dict


    def getTags(self, path_list):
        """
        Function to take in the list of complete layer paths (from within data_list)
        and populate a list of dictionaries of tags for each path.
        It works this way because the Batch Exporter offers meta tag inheritance.
        If [i=false] or [i=no] is found, inheritance is disabled for that layer,
        so the dictionary for that path would be cleared before adding anything.

        By default, the scale of each layer is understood to be 100.0%.

        For incomplete tags [tag=<no value>]:
        i= : Nothing happens.
        e= : png is used.
        s= : The list always has at least 100.0 for 100% scale.
        m= : Margin of 0 is inserted, so nothing changes, but only if the
             value is empty since the smallest margin in a list is used by default.
        
        TODO: Additionally, Add opacity/alpha (with inheritance) to the dictionaries.
        TODO: Additionally, call the function to add properties from transform masks to the dictionaries.

        """
        tag_dict_list = []
        for path in path_list:
            tag_dict = {}
            path_pieces = path.split('/')
            for layer in path_pieces:
                layer = layer.lower()
                tag_data = layer.split(' ')[1:]

                # First pass: See if inheritance disabling is present.
                # If so, clear the dictionary before adding any tags.
                for tag in tag_data:
                    letter, value = tag.split('=', 1)
                    if letter == "i":
                        if value == "false" or value == "no":
                            tag_dict.clear()

                # Second pass: Add the tags.
                for tag in tag_data:
                    letter, value = tag.split('=', 1)
                    if letter == 's':
                        scale_list = [100.0]
                        for v in value.split(','):
                            if v:
                                scale_list.append(float(v))
                        if 's' in tag_dict:
                            tag_dict['s'].extend(scale_list)
                            tag_dict['s'] = list(set(tag_dict['s'])) # Remove duplicates.
                        else:
                            tag_dict['s'] = scale_list
                    elif letter == 'e':
                        if not value:
                            value = "png"
                        format_list = value.split(',')
                        if 'e' in tag_dict:
                            tag_dict['e'].extend(format_list)
                            tag_dict['e'] = list(set(tag_dict['e'])) # Remove duplicates.
                        else:
                            tag_dict['e'] = format_list
                    elif letter == 'm':
                        margin_list = []
                        if not value:
                            margin_list.append("0")
                        else:
                           margin_list = value.split(',')
                        if 'm' in tag_dict:
                            tag_dict['m'].extend(margin_list)
                            tag_dict['m'] = list(set(tag_dict['m']))
                        else:
                            tag_dict['m'] = margin_list
                    elif letter == 'i': # Prevent the i=false tag from leaking down
                        continue        # the path after it's been used to block
                    else:               # the parents' tags.
                        tag_dict[letter] = value
 
            # Next, check for changes from transform masks.
            tag_dict = self.getMaskPropertiesStart(path_pieces, tag_dict)

            tag_dict_list.append(tag_dict)
        return tag_dict_list


    def pathRecord(self, node, path, path_list, pathLen, coords_list):
        """
        Searches for all the node to leaf paths and stores them in path_list using storePath().
        storePath() takes in the entire paths (including all the tags at this step).

        Only grouplayers and paintlayers are checked for this step; filters aren't usable here.

        Coordinates are also found and inserted into coords_list.

        Reference: GeeksforGeeks solution to finding paths in a binary search tree
        """
        #layer_data = node.name().split(' ')
        if (len(path) > pathLen):
            path[pathLen] = node.name()
        else:
            path.append(node.name())
        pathLen += 1
        recordable_child_nodes = 0
        for c in node.childNodes():
            if c.type() == "grouplayer" or c.type() == "paintlayer":
                recordable_child_nodes += 1
            #elif c.type() == "transformmask": # EXPERIMENTAL
                #self.DEBUG_MESSAGE += "transform mask found!\n"
                #self.DEBUG_MESSAGE += c.toXML() + "\n\n\n"
                #xml_root = ET.fromstring(c.toXML())
                #for ft in xml_root.iter("free_transform"):
                #    for p in ft:
                #        self.DEBUG_MESSAGE += str(p.tag) + " : " + str(p.attrib) + "\n"
                    #for key in xml_child.tag:
                    #    self.DEBUG_MESSAGE += key + "\n"
                    #self.DEBUG_MESSAGE += xml_child.tag + " : " + xml_child.attrib + "\n"
        if recordable_child_nodes == 0:
            self.storePath(path, path_list, pathLen)
            coord_x = node.bounds().topLeft().x()
            coord_y = node.bounds().topLeft().y()
            coord_center = node.bounds().center()
            coords_list.append([coord_x, coord_y, coord_center])
        else:
            for i in node.childNodes():
                if i.type() == "grouplayer" or i.type() == "paintlayer":
                # Looks silly and work-aroundy but seems to work.
                # The pathbuilding gets messed up without this subtraction on path.
                    removeAmount = len(path) - pathLen
                    path = path[: len(path) - removeAmount]
                    self.pathRecord(i, path, path_list, pathLen, coords_list)


    def removeUnusedPaths(self, path_list, coords_list, tag_dict_list):
        """
        Copy over usable paths to different lists, which are returned.
        """
        smaller_path_list = []
        smaller_coords_list = []
        smaller_tag_dict_list = []
        for index, path in enumerate(path_list):
            if "e" in tag_dict_list[index]:
                if not "i" in tag_dict_list[index]:
                    smaller_path_list.append(path_list[index])
                    smaller_coords_list.append(coords_list[index])
                    smaller_tag_dict_list.append(tag_dict_list[index])
        return smaller_path_list, smaller_coords_list, smaller_tag_dict_list


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


    def modifyCoordinates(self, coords_list, tag_dict_list):
        """
        Modifies the coordinates
            0,1 : x,y on top left corner
              2 : QPoint of the center
        Step 1: Apply the margin tag if necessary.
                The Batch Exporter uses the smallest margin
                in the list by default, so that's what's used here.
                The center points wouldn't change since each set
                of 4 margins (around a single layer rectange) would be of equal size.
        Step 2: Scale the coordinates with the smallest
                given size from the 's=' layer tags
        """
        for i in range(len(coords_list)):
            scale = 1.0
            if "m" in tag_dict_list[i]:
                coords_list[i][0] -= int(min(tag_dict_list[i]["m"]))
                coords_list[i][1] -= int(min(tag_dict_list[i]["m"]))

            if "s" in tag_dict_list[i]:
                coords_list[i][0] = round(coords_list[i][0] * min(tag_dict_list[i]["s"]) / 100)
                coords_list[i][1] = round(coords_list[i][1] * min(tag_dict_list[i]["s"]) / 100)
                center_x_new = float(coords_list[i][2].x()) * min(tag_dict_list[i]["s"]) / 100
                center_y_new = float(coords_list[i][2].y()) * min(tag_dict_list[i]["s"]) / 100
                coords_list[i][2].setX(int(center_x_new))
                coords_list[i][2].setY(int(center_y_new))
        return coords_list

    def getModifierBlock(self, line):
        modifier_block = ""

        if "scaleX" in line[2] or "scaleY" in line[2]:
            xzoom = 1.0
            yzoom = 1.0
            if "scaleX" in line[2]:
                xzoom = float(line[2]["scaleX"])
                xzoom = round(xzoom, int(config_data["atl_zoom_decimal_places"]))
            if "scaleY" in line[2]:
                yzoom = float(line[2]["scaleY"])
                yzoom = round(yzoom, int(config_data["atl_zoom_decimal_places"]))
            if xzoom == yzoom and xzoom != 1.0:
                modifier_block += ((' ')*indent*2) + "zoom " + str(xzoom) + "\n"
            else:
                if xzoom != 1.0:
                    modifier_block += ((' ')*indent*2) + "xzoom " + str(xzoom) + "\n"
                if yzoom != 1.0:
                    modifier_block += ((' ')*indent*2) + "yzoom " + str(yzoom) + "\n"
        
        if "aZ" in line[2]:
            rounded_rot = round(line[2]["aZ"], int(config_data["atl_rotate_decimal_places"]))
            modifier_block += ((' ')*indent*2) + "rotate " + str(rounded_rot) + "\n"
        """
        if "transformedCenter" in line[2]:
            xoffset = line[2]["transformedCenter"][0]
            yoffset = line[2]["transformedCenter"][1]
            if xoffset == 0 and yoffset != 0:
                modifier_block += ((' ')*indent*2) + "yoffset " + str(yoffset) + "\n"
            elif yoffset == 0 and xoffset != 0:
                modifier_block += ((' ')*indent*2) + "xoffset " + str(xoffset) + "\n"
            elif xoffset != 0 and yoffset != 0:
                modifier_block += ((' ')*indent*2) + "offset (" + str(xoffset) + ", " + str(yoffset) + ")\n"
        """
        return modifier_block

    def getDataList(self, button_num, spacing_num):
        """
        Concept: 1) Get all the paths.
                 2) Get all the tags (with inheritance).
                 3) Filter the paths by checking them with tags.
                 4) Get the names of the layers.
                 5) Put the data into the list.
                 6) Modify the coordinates for margins and scale.
                 7) If 'align' type output is selected, swap out the xy pixel coordinates with align coordinates.

            path_list            (Unused paths and tags are filtered out.)
            path_list_with_tags  (Unused paths are filtered out,
                                  but tags (at the layers they are declared) are not.)
                                  Currently not in use, but the lines are commented out where
                                  they should be activated.
            tag_dict_list        (List where each index corresponds to the index of its path,
                                  and the content is a dictionary with the tags applicable to
                                  the final layer of that path, adjusted for Batch Exporter
                                  inheritance.)
            export_layer_list    (List of the names of the layers to be exported; no tags.)

            coords_list          (For each layer: x position, y position, and center point as a QPoint.
                                  Values are modified for the scale given by tag.)
        """
        data_list =  []
        export_layer_list = []
        coords_list = []
        path_list = []
        tag_dict_list = []
        coords_list = []
        currentDoc = KI.activeDocument()
        if currentDoc != None:
            root_node = currentDoc.rootNode()
        path = []
        #path_list_with_tags = []
        self.pathRecord(root_node, path, path_list, 0, coords_list)
        tag_dict_list = self.getTags(path_list)
        path_list, coords_list, tag_dict_list = self.removeUnusedPaths(path_list, coords_list, tag_dict_list)
        #path_list_with_tags = path_list
        path_list = self.removeTagsFromPaths(path_list)
        tag_dict_list = list(filter(None, tag_dict_list))
        coords_list = self.modifyCoordinates(coords_list, tag_dict_list)
        export_layer_list = self.getExportLayerList(path_list)

        for i,layer in enumerate(export_layer_list):
            data_list.append(tuple([layer, path_list[i], tag_dict_list[i], coords_list[i]]))

        if button_num == 3 or button_num == 4:
            data_list = calculateAlign(data_list, spacing_num)

        return data_list


    def getATL(self, curr_node):
        """
        NOTE: This is old. It will have to be rewritten to fit the new system.
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
    #QApplication.closeAllWindows() # not successful yet

def registerDocker():
    Krita.instance().addDockWidgetFactory(DockWidgetFactory\
("generateRenpyScripting", DockWidgetFactoryBase.DockRight\
 , GenerateRenpyScripting))

app_notifier.applicationClosing.connect(kritaClosingEvent) #EXPERIMENTAL
