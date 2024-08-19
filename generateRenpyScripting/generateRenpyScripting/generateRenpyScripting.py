"""
Generate Ren'Py Scripting V2

@author Sean Castillo

Credits
Delena Malan website: Function to sort a list with a sublist given priority.
"""

from krita import DockWidget, DockWidgetFactory, DockWidgetFactoryBase, Krita

from PyQt5.QtWidgets import (
    QPushButton,
    QLabel,
    QLineEdit,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QGroupBox,
    QWidget,
    QDoubleSpinBox,
    QApplication,
    QMessageBox,
    QSlider,
    QCheckBox,
    QTextEdit,
    QApplication,
    QMainWindow,
    QStatusBar
)

from PyQt5 import QtCore

from PyQt5.QtGui import *

from PyQt5.QtCore import Qt, QEvent, QPoint, pyqtSignal, QObject, QThread

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
open_notifier = KI.notifier()
open_notifier.setActive(True)
close_notifier = KI.notifier()
close_notifier.setActive(True)

default_configs_dict = {
    "string_xposypos" : "{four_space_indent}show {image}:\n{eight_space_indent}pos ({xcoord}, {ycoord})\n",
    "string_atsetposxy": "{four_space_indent}show {image}:\n{eight_space_indent}at setPos({xcoord}, {ycoord})\n",
    "string_alignxy"  : "{four_space_indent}show {image}:\n{eight_space_indent}align ({xcoord}, {ycoord})\n",
    "string_xalignyalign" : "{four_space_indent}show {image}:\n{eight_space_indent}xalign {xcoord} yalign {ycoord}\n",
    "string_normalimagedef" : "image {image} = \"{path_to_image}.{file_extension}\"\n",
    "string_layeredimagedefstart" : "layeredimage {overall_image}:\n",
    "atl_zoom_decimal_places" : "3",
    "atl_rotate_decimal_places" : "3"
}
default_button_text_dict = {
    "pos_button_text" : "pos (x, y)",
    "setpos_button_text" : "at setPos(x, y)",
    "align_button_text" : "align (x, y)",
    "xalignyalign_button_text" : "xalign x yalign y"
}

# For parameterizing the menu text to allow customization,
# but it's currently not in use because the buttons aren't updatable.
replacer_dict = {
    "{xcoord}" : "x",
    "{ycoord}" : "y"
}

# Sets to serve as a tag thesaurus
rpli_set       = {"rpli", "rli"}               # layeredimage (the start)
rplidef_set    = {"rplidef", "rid", "rlid"}    # default
rplialways_set = {"rplial", "ral", "rpalways"} # always
rpliattrib_set = {"rpliatt", "rpliat"}         # attribute
rpligroup_set  = {"rpligroup", "rplig"}        # group
rpli_list = [rpli_set, rplidef_set, rplialways_set, rpliattrib_set, rpligroup_set]
rpli_main_tag = "rpli"
rplidef_main_tag = "rplidef"
rplialways_main_tag = "rplial"
rpliattrib_main_tag = "rpliatt"
rpligroup_main_tag = "rpligroup"
rpli_main_tag_list = [rpli_main_tag, rplidef_main_tag, \
rplialways_main_tag, rpliattrib_main_tag, rpligroup_main_tag]
# Additionally, rpligroupchild is a special tag to be used
# for catching when an rpliatt should be indented in the scripting.


# Synonyms for true and false for rpli tags
value_true_set = {"true", "t", "yes", "y"}
value_false_set = {"false", "f", "no", "n"}
value_true_main_tag = "true"
value_false_main_tag = "false"

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
        align_modified_data_list.append(tuple((line[0],line[1],line[2],modified_coords, line[4])))
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
    def __init__(self):
        super().__init__()
        close_notifier.viewClosed.connect(self.close)

    def setupUi(self, MainBox):
        self.main_box = MainBox
        self.script = ""
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(self.script)
        self.copy_button = QPushButton("Copy To Clipboard")
        self.copy_button.clicked.connect(self.copyText)
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.onClose)

        textOutputLayout = QVBoxLayout()
        textOutputLayout.addWidget(self.text_edit)
        textOutputLayout.addWidget(self.copy_button)
        textOutputLayout.addWidget(self.close_button)
        self.setLayout(textOutputLayout)

    def receiveText(self, value):
        self.text_edit.setPlainText(value)

    def copyText(self):
        clipboard = QApplication.clipboard()
        clipboard.clear(mode=clipboard.Clipboard)
        clipboard.setText(self.text_edit.toPlainText(), mode=clipboard.Clipboard)

    def onClose(self):
        self.main_box.close()

class TextSignalEmitter(QObject):
    custom_signal = pyqtSignal(str)

class FormatMenu(QWidget):
    """
    Window that should open when called from the docker.
    The configs are loaded from the external file configs.json if possible;
    if not possible, default_configs_dict is used.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Choose Your Format")
        self.createFormatMenuInterface()
        self.DEBUG_MESSAGE = ""
        self.text_signal_emitter = TextSignalEmitter()
        self.config_data = default_configs_dict
        try:
            configs_file = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "configs.json"))
            imported_configs = json.load(configs_file)
            self.config_data = imported_configs
        except IOError:
            pass

    def createFormatMenuInterface(self):
        main_layout = QVBoxLayout()
        pos_layout = QHBoxLayout()
        align_layout = QHBoxLayout()
        spacing_layout = QHBoxLayout()
        image_definition_layout = QHBoxLayout()
        settings_layout = QHBoxLayout()

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
statements to Rule of Thirds intersections.\nThis is equivalent to using 4 spaces.")
        self.rule_of_thirds_check.setChecked(False)
        self.rule_of_thirds_check.toggled.connect(self.ruleOfThirdsFlag)
        align_button = QPushButton("align (x, y)")
        align_button.clicked.connect(lambda: self.process(3))
        xalignyalign_button = QPushButton("xalign x yalign y")
        xalignyalign_button.clicked.connect(lambda: self.process(4))
        image_definition_label = QLabel("Image Definition")
        normal_image_def_button = QPushButton("Normal Images")
        normal_image_def_button.setToolTip("Generate the definitions of individual images in Ren'Py\nusing \
the Krita layer structure for the directory.")
        normal_image_def_button.clicked.connect(lambda: self.process(5))
        layered_image_def_button = QPushButton("Layered Image")
        layered_image_def_button.setToolTip("Generate the definition of a Ren'Py layeredimage\nusing \
the Krita layer structure for the directory.")
        layered_image_def_button.clicked.connect(lambda: self.process(6))
        settings_label = QLabel("Output Settings")
        self.default_button = QPushButton("Default")
        self.default_button.setToolTip("Revert output text format to the default configurations.\n\
This will overwrite your customizations.")
        self.default_button.clicked.connect(self.settingDefault)
        self.customize_button = QPushButton("Customize", self)
        self.customize_button.setToolTip("Open configs.json in your default text editor\nto make changes to the output formats.")
        self.customize_button.clicked.connect(self.settingCustomize)
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
        settings_layout.addWidget(self.default_button)
        main_layout.addLayout(settings_layout)
        self.setLayout(main_layout)

    def process(self, button_num):
        """
        Gets the script and then directs it to the TextOutput window.
        A reference to the FormatMenu (the self) is passed
        so that the first window can be closed from TextOutput.
        """
        self.refreshConfigData()
        out_script = self.writeScript(button_num, self.spacing_slider.value())
        self.text_signal_emitter.custom_signal.emit(out_script)
    
    def writeScript(self, button_num, spacing_num):
        """
        Do nothing if the data_list isn't populated.

        Each line in data_list:
            line[0] - Name of the layer with no meta tags
            line[1] - Directory from /images/ to /layername/, with no file extension.
            line[2] - Dictionary of meta tags applicable to the layer.
            line[3] - Tuple containing xcoord, ycoord, and center point (as a QPoint)
            line[4] - Directory from /images/ to /layername/, with tags.

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

        data_list, rpli_data_list = self.getDataList(button_num, spacing_num)
        #self.DEBUG_MESSAGE += "checking the rpli_data_list:" + "\n"
        #for r in rpli_data_list:
        #    self.DEBUG_MESSAGE += "layer name: " + str(r[0]) + "  /////  directory: " + str(r[1]) + "\n"

        script += self.DEBUG_MESSAGE
        if len(data_list) == 0:
            script += "Cannot find layers to script. Check whether your target layers have Batch Exporter format.\n"
            return script

        ATL_dict = {}
        currentDoc = KI.activeDocument()

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
                        script += self.config_data["string_normalimagedef"].format\
(image=line[0],path_to_image=line[1],file_extension=f)
                else:
                    script += "### Error: File format not defined for layer " + line[0] + "\n"
        elif button_num == 6: # Layered Image
            script += self.writeLayeredImage(rpli_data_list)

        # For image position scripting
        else:
            for line in data_list:
                modifier_block = self.getModifierBlock(line)
                if button_num == 1:
                    script += self.config_data["string_xposypos"].format\
(four_space_indent=(' '*indent),image=line[0],eight_space_indent=' '*(indent*2),\
xcoord=str(line[3][0]),ycoord=str(line[3][1]))
                    script += modifier_block
                elif button_num == 2:
                    script += self.config_data["string_atsetposxy"].format\
(four_space_indent=(' '*indent),image=line[0],eight_space_indent=' '*(indent*2),\
xcoord=str(line[3][0]),ycoord=str(line[3][1]))
                    script += modifier_block
                elif button_num == 3:
                    script += self.config_data["string_alignxy"].format\
(four_space_indent=(' '*indent),image=line[0],eight_space_indent=' '*(indent*2),\
xcoord=str(line[3][0]),ycoord=str(line[3][1]))
                elif button_num == 4:
                    script += self.config_data["string_xalignyalign"].format\
(four_space_indent=(' '*indent),image=line[0],eight_space_indent=' '*(indent*2),\
xcoord=str(line[3][0]),ycoord=str(line[3][1]))

        return script

    def writeLayeredImage(self, rpli_data_list):
        """
        Pre-requisite: rpli_data_list is sorted.
        """
        script = ""
        for r in rpli_data_list:
            script += r[1] + "\n"
        for r in rpli_data_list:
#            script += "\n"
#            script += "layer     : " + r[0] + "\n"
#            script += "directory :    " + r[1] + "\n"
#            script += "key, value:\n"
#            for key, value in r[2].items():
#                script += key + " : " + value + "\n"
#            script += "\n"
            if rpli_main_tag in r[2] and r[2][rpli_main_tag] == value_true_main_tag:
                script += "layeredimage " + r[0].split(' ')[0] + ":\n"
            elif rpligroup_main_tag in r[2] and r[2][rpligroup_main_tag] == value_true_main_tag:
                script += (" " * indent * 2) + "group " + r[0].split(' ')[0] + "\n"
            elif rpliattrib_main_tag in r[2] and r[2][rpliattrib_main_tag] == value_true_main_tag:
                if "rpligroupchild" in r[2] and r[2]["rpligroupchild"] == value_true_main_tag:
                    script += (" " * indent)
                script += (" " * indent * 2) + "attribute " + r[0].split(' ')[0] + "\n"
        return script

    def storePath(self, dir, path_list, path_len):
        """
        Concept: Store each max-length path into the final path_list (starting with images instead of root).
        """
        #self.DEBUG_MESSAGE += "From storePath(): " + ''.join(path_list) + "\n"
        to_insert = "images/"
        for i in dir[1 : path_len-1]:
            to_insert = to_insert + (i + "/")
        image_file_name = dir[path_len-1]
        to_insert = to_insert + image_file_name
        path_list.append(to_insert)


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
        """
        currentDoc = KI.activeDocument()
        if currentDoc != None:
            curr_node = currentDoc.rootNode()
        self.getMaskPropertiesRecursion(path_pieces[1:], tag_dict, curr_node)

        return tag_dict


    def getTags(self, path_list, rpli_mode):
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

        new concept: bool rpli_mode - True: Get tags for Ren'Py Layered Images and nothing else. False - The opposite.

        """
        tag_dict_list = []
        for path in path_list:
            #self.DEBUG_MESSAGE += "path: " + str(path) + "\n"
            tag_dict = {}
            path_pieces = path.split('/')
            for layer in path_pieces:
                layer = layer.lower()
                tag_data = layer.split(' ')[1:]

                # First pass: Filter out unusable pieces of text from the layer name.
                usable_tag_data = []
                for tag in tag_data:
                    try:
                        letter, value = tag.split('=',1)
                        usable_tag_data.append(tag)
                    except ValueError:
                        continue
                tag_data = usable_tag_data

                # Experimental pass: remove rpli tags so they wouldn't be inherited.
                 # HIGHLY EXPERIMENTAL FOR ATTRIBUTE INDENTATION
                if rpli_mode == True:
                    if "rpligroupchild" in tag_dict:
                        tag_dict.pop("rpligroupchild")
                    for main_tag in rpli_main_tag_list:
                        if main_tag in tag_dict.keys():
                            if main_tag == rpligroup_main_tag:
                                tag_dict["rpligroupchild"] = value_true_main_tag
                            tag_dict.pop(main_tag)

                # Second pass: See if inheritance disabling is present.
                # If so, clear the dictionary before adding any tags.
                if rpli_mode == False:
                    for tag in tag_data:
                        letter, value = tag.split('=', 1)
                        if letter == "i":
                            if value in value_false_set:
                                tag_dict.clear()

                # Third pass: Add the tags.
                # Turn true/false values into true/false (as opposed to t/f, yes/no, etc.)
                for tag in tag_data:
                    letter, value = tag.split('=', 1)
                    #self.DEBUG_MESSAGE += "letter/value is: " + letter + " : " + value + "\n"

                    if value in value_true_set:
                        value = value_true_main_tag
                    elif value in value_false_set:
                        value = value_false_main_tag

                    if rpli_mode == False:
                        if letter == 's':
                            scale_list = [100.0]
                            for v in value.split(','):
                                if v.replace(".", "").isnumeric():
                                    scale_list.append(float(v))
                                else:
                                    self.DEBUG_MESSAGE += "#Error: Non-numeric value given as scale: " + str(v)
                                    self.DEBUG_MESSAGE += " on layer: " + layer + "\n"
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
                    elif rpli_mode == True:
                        if letter in rpli_set:
                            if value.lower() in value_true_set:
                                tag_dict[rpli_main_tag] = value_true_main_tag
                            else:
                                 tag_dict[rpli_main_tag] = value_false_main_tag
                        elif letter in rplidef_set:
                            tag_dict[rplidef_main_tag] = value
                        elif letter in rplialways_set:
                            tag_dict[rplialways_main_tag] = value
                        elif letter in rpliattrib_set:
                            tag_dict[rpliattrib_main_tag] = value
                        elif letter in rpligroup_set:
                            tag_dict[rpligroup_main_tag] = value
                        else:
                            continue
                    

            # Next, check for changes from transform masks.
            tag_dict = self.getMaskPropertiesStart(path_pieces, tag_dict)

            tag_dict_list.append(tag_dict)
        return tag_dict_list


    def pathRecord(self, node, path, path_list, path_len, coords_list, rpli_path_list):
        """
        Searches for all the node to leaf paths and stores them in path_list using storePath().
        storePath() takes in the entire paths (including all the tags at this step).

        Only grouplayers and paintlayers are checked for this step; filters aren't usable here.

        Coordinates are also found and inserted into coords_list.

        Reference: GeeksforGeeks solution to finding paths in a binary search tree

        TODO: New concept: Record an additional list for the Ren'Py layered image tags
        since the required behavior for layered images isn't the same when it comes to
        inheritance. There needs to be dictionaries for non-leaf layers (i.e. groups).
        """
        #layer_data = node.name().split(' ')
        if (len(path) > path_len):
            path[path_len] = node.name()
        else:
            path.append(node.name())
        path_len += 1
        recordable_child_nodes = 0
        coord_x = node.bounds().topLeft().x()
        coord_y = node.bounds().topLeft().y()
        coord_center = node.bounds().center()
        for c in node.childNodes():
            #EXPERIMENTAL
            #for list in rpli_list:
            #   for tag in list:
            #       if tag in c.name():
            #           temp_path = path
            #           temp_path.append(c.name())
            #           self.storePath(temp_path, rpli_path_list, path_len+1) #EXPERIMENTAL
            #           self.DEBUG_MESSAGE += "tag is: " + tag + " in the layer " + c.name() + " so adding rpli: " + '~'.join(temp_path) + "\n"
            #           rpli_coords_list.append([coord_x, coord_y, coord_center])
            if c.type() == "grouplayer" or c.type() == "paintlayer":
                recordable_child_nodes += 1
            #elif c.type() == "transformmask": # Toggle this on
            #    self.checkTransformMask(c)    # to check transform mask XML
        if recordable_child_nodes == 0:

            self.storePath(path, path_list, path_len)
            coords_list.append([coord_x, coord_y, coord_center])
        else:
            for i in node.childNodes():
                if i.type() == "grouplayer" or i.type() == "paintlayer":
                    layer_name = i.name().lower()
                    tag_data = layer_name.split(' ')[1:]
                    letter_data = []
                    value_data = []
                    for tag in tag_data:
                        letter, value = tag.split('=', 1)
                        letter_data.append(letter)
                        value_data.append(value)
                # Looks silly and work-aroundy but seems to work.
                # The pathbuilding gets messed up without this subtraction on path.
                    remove_amount = len(path) - path_len # This is always either 0 or 1.
                    path = path[: len(path) - remove_amount]
                    self.pathRecord(i, path, path_list, path_len, coords_list, rpli_path_list)
                    for list in rpli_list:
                        for tag in list:
                            if tag in letter_data and value_data[letter_data.index(tag)] in value_true_set:
                                temp_path = path
                                temp_path.append(layer_name)
                                self.storePath(temp_path, rpli_path_list, path_len+1)
                                #self.DEBUG_MESSAGE += "tag is: " + tag + " in the layer " + i.name() + " so adding rpli: " + '~'.join(temp_path) + "\n"
                                #rpli_coords_list.append([coord_x, coord_y, coord_center])
                                break

    def checkTransformMask(self, c):
        """
        Dev method to print out the contents of the XML of a transform mask.
        c is the transform mask, given by the search in pathRecord().
        """
        self.DEBUG_MESSAGE += "transform mask found!\n"
        self.DEBUG_MESSAGE += c.toXML() + "\n\n\n"
        xml_root = ET.fromstring(c.toXML())
        for ft in xml_root.iter("free_transform"):
            for p in ft:
                self.DEBUG_MESSAGE += str(p.tag) + " : " + str(p.attrib) + "\n"

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
        """
        Order of Property Application in Ren'Py
        crop, corner1, corner2
        xysize, size, maxsize
        zoom, xzoom, yzoom
        point_to
        orientation
        xrotate, yrotate, zrotate
        rotate
        zpos
        matrixtransform, matrixanchor
        zzoom
        perspective
        nearest, blend, alpha, additive, shader
        matrixcolor
        GL Properties, Uniforms
        position properties
        show_cancels_hide
        """
        modifier_block = ""
        # zoom
        if "scaleX" in line[2] or "scaleY" in line[2]:
            xzoom = 1.0
            yzoom = 1.0
            if "scaleX" in line[2]:
                xzoom = float(line[2]["scaleX"])
                xzoom = round(xzoom, int(self.config_data["atl_zoom_decimal_places"]))
            if "scaleY" in line[2]:
                yzoom = float(line[2]["scaleY"])
                yzoom = round(yzoom, int(self.config_data["atl_zoom_decimal_places"]))
            if xzoom == yzoom and xzoom != 1.0:
                modifier_block += ((' ')*indent*2) + "zoom " + str(xzoom) + "\n"
            else:
                if xzoom != 1.0:
                    modifier_block += ((' ')*indent*2) + "xzoom " + str(xzoom) + "\n"
                if yzoom != 1.0:
                    modifier_block += ((' ')*indent*2) + "yzoom " + str(yzoom) + "\n"
        # Rotate
        if "aZ" in line[2]:
            rounded_rot = round(line[2]["aZ"], int(self.config_data["atl_rotate_decimal_places"]))
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

    def sortRpliData(self, rpli_data_list):
        self.DEBUG_MESSAGE += "list before sorting:\n"
        for d in rpli_data_list:
            self.DEBUG_MESSAGE += str(d[1]) + "\n"
        s_list = rpli_data_list
        top_counter = len(s_list)-1
        c = len(s_list)-1
        list_sorted = False
        while not list_sorted:
            part_sorted = False
            while not part_sorted:
                curr_line = s_list[c][1]
                comp_line = s_list[c-1][1]
                self.DEBUG_MESSAGE += "Comparing " + curr_line + " with " + comp_line  + "\n"
                if curr_line in comp_line and curr_line < comp_line:
                    s_list[c], s_list[c-1] = s_list[c-1], s_list[c]
                    self.DEBUG_MESSAGE += "SWAP!\n"
                else:
                    self.DEBUG_MESSAGE += "no swap\n"
                    c = c-1
                    part_sorted = True
            if c == 0:
                list_sorted = True
            #list_sorted = True #debugging

        #while c > 0:
        #    curr_line = s_list[c]
        #    part_sorted = False
        #    while not part_sorted:
        #        if curr_line in s_list[c-1] and curr_line < s_list[c-1]:
        #            s_list[c-1], s_list[c] = s_list[c], s_list[c-1]
        #        else:
        #            c = c-1
        #            part_sorted = True
        self.DEBUG_MESSAGE += "sorted list:\n"
        for l in s_list:
            self.DEBUG_MESSAGE += str(l[1]) + "\n"
        #return s_list

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
            tag_dict_list        (List where each index corresponds to the index of its path,
                                  and the content is a dictionary with the tags applicable to
                                  the final layer of that path, adjusted for Batch Exporter
                                  inheritance.)
            export_layer_list    (List of the names of the layers to be exported; no tags.)
            coords_list          (For each layer: x position, y position, and center point as a QPoint.
                                  Values are modified for the scale given by tag.)
        """
        data_list =  []
        rpli_data_list = []
        export_layer_list = []
        coords_list = []
        path_list = []
        rpli_path_list = []
        tag_dict_list = []
        coords_list = []
        #rpli_coords_list = []
        currentDoc = KI.activeDocument()
        if currentDoc != None:
            root_node = currentDoc.rootNode()
        path = []
        path_list_with_tags = []
        self.pathRecord(root_node, path, path_list, 0, coords_list, rpli_path_list)
        tag_dict_list = self.getTags(path_list, False)
        rpli_tag_dict_list = self.getTags(rpli_path_list, True)
        path_list, coords_list, tag_dict_list = self.removeUnusedPaths(path_list, coords_list, tag_dict_list)
        path_list_with_tags = path_list
        rpli_path_list_with_tags = rpli_list
        path_list = self.removeTagsFromPaths(path_list)
        #rpli_path_list = self.removeTagsFromPaths(rpli_path_list)
        tag_dict_list = list(filter(None, tag_dict_list))
        rpli_tag_dict_list = list(filter(None, rpli_tag_dict_list))
        coords_list = self.modifyCoordinates(coords_list, tag_dict_list)
        export_layer_list = self.getExportLayerList(path_list)
        rpli_export_layer_list = self.getExportLayerList(rpli_path_list)

        for i,layer in enumerate(export_layer_list):
            data_list.append(tuple([layer, path_list[i], tag_dict_list[i], coords_list[i], path_list_with_tags[i]]))

        for i,layer in enumerate(rpli_export_layer_list):
            rpli_data_list.append(tuple([layer, rpli_path_list[i], rpli_tag_dict_list[i]]))

        self.sortRpliData(rpli_data_list)

        if button_num == 3 or button_num == 4:
            data_list = calculateAlign(data_list, spacing_num)

        return data_list, rpli_data_list

    def ruleOfThirdsFlag(self):
        """
        The elif part covers the case where the user tries to uncheck the box
        by directly clicking it (which would be while the slider is at 4),
        which shouldn't have an effect since the slider bar would be in the same position.
        """
        if self.rule_of_thirds_check.isChecked() == True:
            self.spacing_slider.setSliderPosition(4)
        elif self.spacing_slider.value() == 4:
            self.rule_of_thirds_check.setChecked(True)


    def updateSpacingValue(self):
        self.spacing_number_label.setText(str(self.spacing_slider.value()))
        if self.spacing_slider.value() == 4:
            self.rule_of_thirds_check.setChecked(True)
        else:
            self.rule_of_thirds_check.setChecked(False)

    def settingDefault(self):
        """
        Behavior for the default button
        """
        self.config_data = default_configs_dict
        with open(os.path.join(os.path.dirname\
(os.path.realpath(__file__)), "configs.json"), 'w') as f:
            json.dump(default_configs_dict, f)
        self.text_signal_emitter.custom_signal.emit("Configurations reverted to default!")

    def settingCustomize(self):
        """
        Ideally, refreshConfigData() would be called soon after webbrowser.open(),
        but I don't think there is a signal for right after the user edits the external file.

        Idea: Update the buttons with the customized template text. It would likely be complicated.
              It would use the setText() call below.
        """
        webbrowser.open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "configs.json"))
        #self.pos_button_text = "NEWBUTTONNAME"
        #self.pos_button.setText(self.pos_button_text)
    
    def refreshConfigData(self):
        """
        Function to reload the config dict after it has been customized.
        """
        try:
            configs_file = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "configs.json"))
            imported_configs = json.load(configs_file)
            self.config_data = imported_configs
        except IOError:
            pass

class MainBox(QWidget):
    """
    Idea: Put the pop-up windows into a single box.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Choose Your Format!")
        self.createMainBox()
        self.format_menu = None
        self.outputWindow = None
        close_notifier.viewClosed.connect(self.close)
    
    def createMainBox(self):
        """
        The output window's close button is connected to the main box.
        """
        self.output_window = TextOutput()
        self.output_window.setupUi(self)
        self.format_menu = FormatMenu()
        self.format_menu.text_signal_emitter.custom_signal.connect(self.output_window.receiveText)
        main_box_layout = QHBoxLayout()
        main_box_layout.addWidget(self.format_menu)
        main_box_layout.addWidget(self.output_window)
        self.setLayout(main_box_layout)

class RenameWorkerThread(QThread):
    """
    """
    def __init__(self, dir_name, export_dir_name, suffix, new_folder_name):
        self.dir_name = dir_name
        self.export_dir_name = export_dir_name
        self.suffix = suffix
        self.new_folder_name = new_folder_name
        self.file_found = False
        super().__init__()

    def run(self):
        self.renameRecursion(self.dir_name, self.export_dir_name, self.suffix, self.new_folder_name)

    def renameRecursion(self, dir_name, export_dir_name, suffix, folder_name):
      for filename in os.listdir(dir_name):
            f = os.path.join(dir_name, filename)
            if filename.find(suffix) != -1:
                if os.path.isfile(f):
                    if not self.file_found:
                        self.file_found = True
                    exp_fname, exp_ext = os.path.splitext(filename)
                    exp_fname = exp_fname[:exp_fname.find(suffix)]
                    exp_fname += exp_ext
                    dst = os.path.join(export_dir_name, exp_fname)
                    shutil.copy(f, dst)
            elif os.path.isdir(f):
                if filename == folder_name:
                    continue
                else:
                    sub_export_dir_name = os.path.join(export_dir_name, filename)
                    Path(sub_export_dir_name).mkdir(parents=True, exist_ok=False)
                    self.renameRecursion(f, sub_export_dir_name, suffix, folder_name)

class ScaleCalculateBox(QWidget):
    """
    When image document is closed and the calculator window is still open:
        - The scale is set to 100%.
        - When another document is opened while the same calculator window is still open:
            - The dimensions are updated for that document.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Check Your Scale!")
        self.createScaleCalculateBox()
        close_notifier.viewClosed.connect(self.close)
        self.status_signal_emitter = TextSignalEmitter()
        self.status_signal_emitter.custom_signal.connect(self.receiveStatus)


    def createScaleCalculateBox(self):
        preset_label_layout = QHBoxLayout()
        preset_width_label = QLabel("Width")
        preset_height_label = QLabel("Height")
        percentage_label = QLabel("Scale Percentage")
        self.status_bar = QStatusBar()
        size_layout = QGridLayout()
        self.line_width = QLineEdit(parent=self)
        self.line_width.textEdited[str].connect(lambda: self.lineEdited(self.line_width.text(), 0))
        self.line_height = QLineEdit(parent=self)
        self.line_height.textEdited[str].connect(lambda: self.lineEdited(self.line_height.text(), 1))
        currentDoc = KI.activeDocument()
        if currentDoc != None:
            self.line_width.setText(str(float(currentDoc.width()))+" px")
            self.line_height.setText(str(float(currentDoc.height()))+" px")
        button_1280_w = QPushButton("1280")
        button_1280_w.clicked.connect(lambda: self.dimensionSet(1280,0))
        button_720_h = QPushButton("720")
        button_720_h.clicked.connect(lambda: self.dimensionSet(720,1))
        button_1920_w = QPushButton("1920")
        button_1920_w.clicked.connect(lambda: self.dimensionSet(1920,0))
        button_1080_h = QPushButton("1080")
        button_1080_h.clicked.connect(lambda: self.dimensionSet(1080,1))
        button_2560_w = QPushButton("2560")
        button_2560_w.clicked.connect(lambda: self.dimensionSet(2560,0))
        button_1440_h = QPushButton("1440")
        button_1440_h.clicked.connect(lambda: self.dimensionSet(1440,1))
        button_3840_w = QPushButton("3840")
        button_3840_w.clicked.connect(lambda: self.dimensionSet(3840,0))
        button_2160_h = QPushButton("2160")
        button_2160_h.clicked.connect(lambda: self.dimensionSet(2160,1))
        rename_button = QPushButton("Rename Batch-Exported Files Of That Scale Percentage")
        rename_button.setToolTip("The Batch Exporter labels exported files with \
the suffix '_@[scale]x'.\nThis button will make GRS copy over the batch-exported \
images of the currently selected scale to a new folder in which they don't have that suffix,\n\
so that those images may be transferred to your Ren'Py project without having to \
rename them manually.")
        rename_button.clicked.connect(lambda: self.renameClicked())
        close_button = QPushButton("Close")
        close_button.clicked.connect(lambda: self.onClose())
        size_layout.addWidget(preset_width_label,0,0)
        size_layout.addWidget(self.line_width,0,1)
        size_layout.addWidget(button_1280_w,0,2)
        size_layout.addWidget(button_1920_w,0,3)
        size_layout.addWidget(button_2560_w,0,4)
        size_layout.addWidget(button_3840_w,0,5)
        size_layout.addWidget(preset_height_label,1,0)
        size_layout.addWidget(self.line_height,1,1)
        size_layout.addWidget(button_720_h,1,2)
        size_layout.addWidget(button_1080_h,1,3)
        size_layout.addWidget(button_1440_h,1,4)
        size_layout.addWidget(button_2160_h,1,5)
        size_layout.addWidget(percentage_label,2,0)
        percentage_label.setToolTip("Check the image's dimensions \
at the given scale.\nHold Alt to increment by 0.01%.\nHold Shift to increment \
by 0.1%.\nHold Ctrl to edit by 10%.")
        self.scale_box_percent = CustomDoubleSpinBox(self)
        self.scale_box_percent.setRange(0.0, 1000.0)
        self.scale_box_percent.setValue(100.0)
        self.scale_box_percent.valueChanged[float].connect(self.calculatorScaleChanged)
        size_layout.addWidget(self.scale_box_percent)
        scale_top_layout = QVBoxLayout()
        scale_top_layout.addLayout(preset_label_layout)
        scale_top_layout.addLayout(size_layout)
        scale_top_layout.addWidget(rename_button)
        scale_top_layout.addWidget(close_button)
        scale_top_layout.addWidget(self.status_bar)
        self.setLayout(scale_top_layout)

    def onClose(self):
        self.close()

    def lineEdited(self, line, dimension):
        """
        Function to handle the case where the user hits backspace
        and gets rid of all the usable text, which cannot be converted
        into a float. dimensionSet() is called for the custom dimension
        inputs from here.
        Regex: Filter anything other than numbers with/without a decimal point.
        The code after filters all but the first . occurrence.
        """
        line_to_text = re.sub("[^\.\d]",'',str(line))
        line_parts = line_to_text.split('.')
        line_to_text = line_parts[0] + '.' + ''.join(line_parts[1:])
        if line_to_text == "" or line_to_text == ".":
            line_to_text = "0.0"
        self.dimensionSet(float(line_to_text), dimension)

    def dimensionSet(self, value, d):
        """
        d(imension): 0: width, 1: height
        """
        currentDoc = KI.activeDocument()
        if currentDoc != None:
            flip_d = 1-d
            scale = float(value/((currentDoc.width()*flip_d)+(currentDoc.height()*d)))
            self.scale_box_percent.setValue(scale * 100.0)

    def calculatorScaleChanged(self):
        """
        Updates the width XOR the height on display.
        This is called when the scale box is directly modified,
        or when either of the dimension boxes is edited.
        Only the box that is not focused is edited by this function
        since the user would be editing the focused box.
        """
        currentDoc = KI.activeDocument()
        scale = float(self.scale_box_percent.value() / 100.0)
        if currentDoc != None:
            width = round((float(currentDoc.width()) * scale), 1)
            height = round((float(currentDoc.height()) * scale), 1)
            if self.line_width.hasFocus() == False:
                self.line_width.setText(str(width) + " px")
            if self.line_height.hasFocus() == False:
                self.line_height.setText(str(height) + " px")

    def nothing(self): # for debugging
        pass

    def receiveStatus(self, value):
        self.status_bar.showMessage(value, 5000)

    def renamerFinished(self, file_found, dir_to_check, folder_name):
        """
        """
        if file_found == False:
            self.status_bar.showMessage("No files to copy and rename have been found!", 5000)
            if os.path.exists(dir_to_check) and os.path.isdir(dir_to_check):
                shutil.rmtree(dir_to_check)
        else:
            self.status_bar.showMessage("Files have been copied and renamed at {folder}!".\
format(folder=folder_name), 5000)

    def recursiveRenameStart(self):
        """
        Uses data_list to get the layer names and the scales.
        A folder named after the scale from scale_box_percent is created.
        The images of that scale are copied over with the scale tag removed from
        their names.
        The data_list gives the scale list in numbers out of 100, so this function
        divides those numbers by 100 to get the multiplier for the folder name.

        Uses a RenameWorkerThread to handle the renaming/directory copying
        because handling it directly in this class prevented
        the status_bar from correctly updating.

        Pre-requisite: KI.activeDocument() != None
        """
        dir_name = os.path.dirname(KI.activeDocument().fileName())
        dir_name = os.path.join(dir_name, "export")
        scale = float(self.scale_box_percent.value() / 100.0)
        suffix = "_@" + str(scale) + "x"
        new_folder_name = "grs_x" + str(scale)
        export_dir_name = dir_name + os.sep + new_folder_name
        Path(export_dir_name).mkdir(parents=True, exist_ok=True)
        self.worker = RenameWorkerThread(dir_name, export_dir_name, suffix, new_folder_name)
        self.worker.start()
        self.worker.finished.connect(lambda: self.renamerFinished(self.worker.file_found, export_dir_name, new_folder_name))

    def renameClicked(self):
        """
        TODO: Add a window that asks if this is what the user wants.
        """
        if KI.activeDocument() != None:
            self.recursiveRenameStart()

class GenerateRenpyScripting(DockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generate Ren'Py Scripting")
        self.createInterface()
        self.main_box = None

    def showErrorMessage(self, toPrint):
        msg = QMessageBox()
        msg.setText(toPrint)
        msg.exec_()

    def createInterface(self):
        generate_button = QPushButton("Scripting Generator")
        generate_button.clicked.connect(self.startMainBox)

        calculate_button = QPushButton("Scale Calculator and Renamer")
        calculate_button.clicked.connect(self.startScaleCalculateBox)

        main_layout = QVBoxLayout()
        main_layout.addWidget(generate_button)
        main_layout.addWidget(calculate_button)

        mainWidget = QWidget(self)
        mainWidget.setLayout(main_layout)
        self.setWidget(mainWidget)


    def startMainBox(self):
        self.main_box = MainBox()
        self.main_box.show()
    
    def startScaleCalculateBox(self):
        self.scale_calculate_box = ScaleCalculateBox()
        self.scale_calculate_box.show()


    # notifies when views are added or removed
    # 'pass' means do not do anything
    def canvasChanged(self, canvas):
        pass

    def closeEvent(self, event):
        if not set.main_box is None:
            self.main_box.close()

def registerDocker():
    Krita.instance().addDockWidgetFactory(DockWidgetFactory\
("generateRenpyScripting", DockWidgetFactoryBase.DockRight\
 , GenerateRenpyScripting))