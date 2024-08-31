"""
Krita Ren'Py Scripter V2

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
from collections import defaultdict, OrderedDict
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
    "string_posxy" : \
        "{FOUR_SPACE_INDENT}show {image}:\n{EIGHT_SPACE_INDENT}pos ({xcoord}, {ycoord})\n",
    "string_xposxyposy" : \
        "{FOUR_SPACE_INDENT}show {image}:\n{EIGHT_SPACE_INDENT}xpos {xcoord} ypos {ycoord}\n",
    "string_atsetposxy": \
        "{FOUR_SPACE_INDENT}show {image}:\n{EIGHT_SPACE_INDENT}at setPos({xcoord}, {ycoord})\n",
    "string_alignxy"  : \
        "{FOUR_SPACE_INDENT}show {image}:\n{EIGHT_SPACE_INDENT}align ({xcoord}, {ycoord})\n",
    "string_xalignxyaligny" : \
        "{FOUR_SPACE_INDENT}show {image}:\n{EIGHT_SPACE_INDENT}xalign {xcoord} yalign {ycoord}\n",
    "string_normalimagedef" : "image {image} = \"{path_to_image}.{file_extension}\"\n",
    "string_layeredimagedef" : "Value not used, but key is.",
    "align_decimal_places" : "3",
    "atl_zoom_decimal_places" : "3",
    "atl_rotate_decimal_places" : "3",
    "directory_starter" : "",
    "lock_windows_to_front" : "true",
    "posxy_button_text" : "pos (x, y)",
    "xposxyposy_button_text" : "xpos x ypos y",
    "atsetposxy_button_text" : "at setPos(x, y)",
    "alignxy_button_text" : "align (x, y)",
    "xalignxyaligny_button_text" : "xalign x yalign y",
    "customize_button_text" : "Customize",
    "script_window_w_size_multiplier" : "1.1",
    "script_window_h_size_multiplier" : "0.8",
    "script_font_size" : "10",
    "script_preferred_font" : "Monospace"
}

button_display_set = {"string_posxy", "string_xposxyposy", \
                      "string_atsetposxy", "string_alignxy", "string_xalignxyaligny"}

button_display_align_set = {"string_alignxy", "string_xalignxyaligny"}

button_define_set = {"string_normalimagedef", "string_layeredimagedef"}

button_settings_set = {"default", "customize"}

# Sets to serve as a tag thesaurus
rpli_set       = {"rpli", "rli", "li"}               # layeredimage (the start)
rplidef_set    = {"rplidef", "rid", "rlid", "df"}    # default
rplialways_set = {"rplial", "ral", "rpalways", "al"} # always
rpliattrib_set = {"rpliatt", "rpliat", "rat", "rt"}  # attribute
rpligroup_set  = {"rpligroup", "rplig", "rig", "gr"} # group
RPLI_LIST = [rpli_set, rplidef_set, rplialways_set, rpliattrib_set, rpligroup_set]
RPLI_MAIN_TAG = "rpli"
RPLIDEF_MAIN_TAG = "rplidef"
RPLIALWAYS_MAIN_TAG = "rplial"
RPLIATTRIB_MAIN_TAG = "rpliatt"
RPLIGROUP_MAIN_TAG = "rpligroup"
RPLI_MAIN_TAG_LIST = [RPLI_MAIN_TAG, RPLIDEF_MAIN_TAG, \
RPLIALWAYS_MAIN_TAG, RPLIATTRIB_MAIN_TAG, RPLIGROUP_MAIN_TAG]
# Additionally, rpligroupchild is a special tag to be used
# for catching when an rpliatt should be INDENTed in the scripting.


# Synonyms for true and false for rpli tags
value_true_set = {"true", "t", "yes", "y", "1"}
value_false_set = {"false", "f", "no", "n", "0"}
VALUE_TRUE_MAIN_TAG = "true"
VALUE_FALSE_MAIN_TAG = "false"

attribute_chain_set = {"chain", "ch", "c", "at", "attr"}
layer_exclude_set = {"exclude", "ex", "x",}
LAYER_EXCLUDE_MAIN_TAG = "exclude"
format_set = {"png", "webp", "jpg", "jpeg"}
format_tag_set = {"e=png", "e=webp", "e=jpg", "e=jpeg"}
hidden_set = {"gecko", "data structure", "dinuguanggal", \
              "dinu", "d++", "manananggal", "dinuguan", "leaf", "segfault"}
INDENT = 4
MSG_TIME = 8000
OUTER_DEFAULT_ALIGN_DECIMAL_PLACES = 3


def sortListByPriority(values: Iterable[T], priority: List[T]) -> List[T]:
    """
    sortListByPriority(values: <list to sort>, priority: <sublist>)
    """
    priority_dict = {k: i for i, k in enumerate(priority)}
    def priority_getter(value):
        return priority_dict.get(value, len(values))
    return sorted(values, key=priority_getter)

def closestNum(num_list, value):
    """
    Find the number in the list closest to the given value.
    """
    return num_list[min(range(len(num_list)), key = lambda i: abs(num_list[i]-value))]

def truncate(number, digit_count):
    """ Truncate a number to the digit count. """
    step = 10.0 ** digit_count
    return math.trunc(step * number) / step

def calculateAlign(data_list, spacing_num, decimal_place_count):
    """
    calculateAlign converts the pos(x,y) coordinates
    in the data list into align(x,y) coordinates
    by comparing the center point of each image
    to a finite set of values from 0.0 to 1.0.
    """
    width, height = 1, 1
    curr_doc = KI.activeDocument()
    if curr_doc is not None:
        width = curr_doc.width()
        height = curr_doc.height()
    step = 1.0 / (spacing_num - 1)
    spacing_list = []
    for i in range(spacing_num):
        spacing_list.append(truncate(i*step, decimal_place_count))
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
        """Modifiers for incrementing the spinbox."""
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
    def __init__(self, parent=None):
        super(TextOutput, self).__init__(parent)
        close_notifier.viewClosed.connect(self.close)

    def setupUi(self, ScriptBox, script_font_size, script_preferred_font):
        """
        If the preferred font can't be accessed, let Qt find a monospace font.
        """
        self.script_box = ScriptBox
        self.script = ""
        self.text_edit = QTextEdit()
        font = QFont(script_preferred_font)
        font.setStyleHint(QFont.Monospace)
        self.text_edit.setCurrentFont(font)
        self.text_edit.setPlainText(self.script)
        self.text_edit.setFontPointSize(script_font_size)
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
        self.script_box.close()

class TextSignalEmitter(QObject):
    custom_signal = pyqtSignal(str)

class FormatMenu(QWidget):
    """
    Window that should open when called from the docker.
    The configs are loaded from the external file configs.json if possible;
    if not possible, default_configs_dict is used.
    default_configs_dict is also used for lines that aren't filled in.
    If an incorrect value for a true/false field or a numeric field is given,
    use the default setting.
    """
    def __init__(self, parent=None):
        super(FormatMenu, self).__init__(parent)
        self.setWindowTitle("Choose Your Format!")
        self.DEBUG_MESSAGE = ""
        self.text_signal_emitter = TextSignalEmitter()
        self.config_data = default_configs_dict
        try:
            configs_file = open(os.path.join(\
                os.path.dirname(os.path.realpath(__file__)), "configs.json"), encoding="utf-8")
            imported_configs = json.load(configs_file)
            self.config_data = imported_configs
            for key, value in default_configs_dict.items():
                if not key in self.config_data:
                    self.config_data[key] = value
                elif value in value_true_set or value in value_false_set:
                    if not self.config_data[key].lower() in value_true_set \
                        and not self.config_data[key].lower() in value_true_set:
                        self.config_data[key] = value
                elif value.isnumeric():
                    if not self.config_data[key].isnumeric():
                        self.config_data[key] = value
        except IOError:
            pass
        self.createFormatMenuInterface()

    def createFormatMenuInterface(self):
        """
        Create the format menu.
        """
        main_layout = QVBoxLayout()
        pos_layout = QHBoxLayout()
        align_layout = QHBoxLayout()
        spacing_layout = QHBoxLayout()
        image_definition_layout = QHBoxLayout()
        settings_layout = QHBoxLayout()

        pos_label = QLabel("pos")
        posxy_button = QPushButton(self.config_data["posxy_button_text"], self)
        posxy_button.clicked.connect(lambda: self.process("string_posxy"))
        xposxyposy_button = QPushButton(self.config_data["xposxyposy_button_text"], self)
        xposxyposy_button.clicked.connect(lambda: self.process("string_xposxyposy"))
        atsetposxy_button = QPushButton(self.config_data["atsetposxy_button_text"],self)
        atsetposxy_button.clicked.connect(lambda: self.process("string_atsetposxy"))
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
        alignxy_button = QPushButton(self.config_data["alignxy_button_text"],self)
        alignxy_button.clicked.connect(lambda: self.process("string_alignxy"))
        xalignxyaligny_button = QPushButton(self.config_data["xalignxyaligny_button_text"],self)
        xalignxyaligny_button.clicked.connect(lambda: self.process("string_xalignxyaligny"))
        image_definition_label = QLabel("Image Definition")
        normal_image_def_button = QPushButton("Normal Images")
        normal_image_def_button.setToolTip(\
            "Script the definitions of individual images in Ren'Py\nusing \
the Krita layer structure for the directory.")
        normal_image_def_button.clicked.connect(lambda: self.process("string_normalimagedef"))
        layered_image_def_button = QPushButton("Layered Image")
        layered_image_def_button.setToolTip(\
            "Script the definition of a Ren'Py layeredimage\nusing \
the Krita layer structure for the directory.")
        layered_image_def_button.clicked.connect(lambda: self.process("string_layeredimagedef"))
        settings_label = QLabel("Settings")
        self.default_button = QPushButton("Default")
        self.default_button.setToolTip("Revert output text format to the default configurations.\n\
This will overwrite your customizations.")
        self.default_button.clicked.connect(self.settingDefault)
        self.customize_button = QPushButton(self.config_data["customize_button_text"], self)
        self.customize_button.setToolTip(\
            "Open configs.json in your default text editor\nto make changes to the output formats.")
        self.customize_button.clicked.connect(self.settingCustomize)
        main_layout.addWidget(pos_label)
        pos_layout.addWidget(posxy_button)
        pos_layout.addWidget(xposxyposy_button)
        pos_layout.addWidget(atsetposxy_button)
        main_layout.addLayout(pos_layout)
        main_layout.addWidget(align_label)
        spacing_layout.setContentsMargins(0,0,0,0)
        spacing_layout.addWidget(spacing_label)
        spacing_layout.addWidget(self.spacing_number_label)
        spacing_layout.addWidget(self.spacing_slider)
        spacing_layout.addWidget(self.rule_of_thirds_check)
        main_layout.addLayout(spacing_layout)
        align_layout.addWidget(alignxy_button)
        align_layout.addWidget(xalignxyaligny_button)
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

    def process(self, button_chosen):
        """
        Gets the script and then directs it to the TextOutput window.
        A reference to the FormatMenu (the self) is passed
        so that the first window can be closed from TextOutput.
        """
        self.refreshConfigData()
        out_script = self.writeScript(button_chosen, self.spacing_slider.value())
        self.text_signal_emitter.custom_signal.emit(out_script)
    
    def writeScript(self, button_chosen, spacing_num):
        """
        Do nothing if the data_list isn't populated.

        Each line in data_list:
            line[0] - Name of the layer with no meta tags
            line[1] - Directory from /images/ to /layername/, with no file extension.
            line[2] - Dictionary of meta tags applicable to the layer.
            line[3] - Tuple containing xcoord, ycoord, and center point (as a QPoint)
            line[4] - Directory from /images/ to /layername/, with tags.

        Image Definition:
                - Format Priority:
                      - If both png and jpg are requested for a single image,
                        the jpg line will be written but commented out.
                      - If webp is requested, it takes priority over png,
                        though webp isn't actually supported by the Batch Exporter plugin;
                        it's just preferred for Ren'Py.
                      - Any unrecognized format get a commented out line.
        """
        script = ""

        data_list = []
        rpli_data_list = []
        data_list, rpli_data_list = self.getDataList(button_chosen, spacing_num)
        #self.DEBUG_MESSAGE += "checking the rpli_data_list:" + "\n"
        #for r in rpli_data_list:
        #    self.DEBUG_MESSAGE += "layer name: " + str(r[0]) + "  /////  directory: " + str(r[1]) + "\n"

        script += self.DEBUG_MESSAGE
        if len(data_list) == 0:
            script += \
                "Cannot find layers to script. \
                    Check whether your target layers have Batch Exporter format.\n"
            return script

        ATL_dict = {}
        curr_doc = KI.activeDocument()

        if button_chosen == "string_normalimagedef": # Normal Images
            for line in data_list:
                name_to_print = line[0]
                dir_to_print = line[1]
                if "attribute_chain_name" in line[2]:
                    name_to_print = line[2]["attribute_chain_name"]
                if "layers_to_exclude_dir" in line[2]:
                    for layer in line[2]["layers_to_exclude_dir"]:
                        dir_to_print = dir_to_print.replace(layer, "", 1)
                        dir_to_print = dir_to_print.replace("//", "/", 1)
                if "e" in line[2]:
                    line[2]["e"] = \
                        sortListByPriority(values=line[2]["e"], \
                                           priority=["webp","png","jpg","jpeg"])
                    line_format_set = set(line[2]["e"])
                    chosen_format = ""
                    if "webp" in line_format_set:
                        chosen_format = "webp"
                    elif "png" in line_format_set:
                        chosen_format = "png"
                    elif "jpg" in line_format_set or "jpeg" in line_format_set:
                        chosen_format = "jpg"
                    for f in line[2]["e"]:
                        if f != chosen_format:
                            script += '#'
                        text_to_add = self.config_data["string_normalimagedef"].format\
                            (image=name_to_print,path_to_image=dir_to_print,file_extension=f)
                        text_to_add = text_to_add.replace("/.", ".", 1) # To handle edge case:
                        script += text_to_add                           # The leaf node is excluded
                else:                                                   # from an attribute chain.
                    script += "### Error: File format not defined for layer " + name_to_print + "\n"
        elif button_chosen == "string_layeredimagedef": # Layered Image
            script += self.writeLayeredImage(rpli_data_list)

        # For image position scripting
        else:
            for line in data_list:
                name_to_print = line[0]
                if "attribute_chain_name" in line[2]:
                    name_to_print = line[2]["attribute_chain_name"]
                modifier_block = self.getModifierBlock(line)
                if button_chosen in button_display_set:
                    script += self.config_data[button_chosen].format\
(FOUR_SPACE_INDENT=(' '*INDENT),image=name_to_print,EIGHT_SPACE_INDENT=' '*(INDENT*2),\
xcoord=str(line[3][0]),ycoord=str(line[3][1]))
                if not button_chosen in button_display_align_set:
                    script += modifier_block

        return script

    def writeLayeredImage(self, rpli_data_list):
        """
        Pre-requisite: rpli_data_list is sorted.
        Ignore duplicate lines.
        """
        script = ""
        if len(rpli_data_list) == 0:
            script += "No Ren'Py Layered Image elements found!\nCheck your tags!\n"
        was_written = set()
        for r in rpli_data_list:
            #script += "r[0]: " + str(r[0]) + "\n"
            #script += "r[1]: " + str(r[1]) + "\n"
            dir_to_print = r[1]
            if "layers_to_exclude_dir" in r[2]:
                for layer in r[2]["layers_to_exclude_dir"]:
                    if layer in r[1]:
                        dir_to_print = dir_to_print.replace(layer, "", 1)
                        dir_to_print = dir_to_print.replace("//", "/", 1)
            if not r[1] in was_written:
                was_written.add(r[1])
            else: # ignore duplicate lines
                continue
            def_add_on = ""
            image_add_on_list = []
            if "e" in r[2]:
                r[2]["e"] = sortListByPriority(\
                    values=r[2]["e"], priority=["webp","png","jpg","jpeg"])
                formats = set(r[2]["e"])
                chosen_format = ""
                if "webp" in formats:
                    chosen_format = "webp"
                elif "png" in formats:
                    chosen_format = "png"
                elif "jpg" in formats or "jpeg" in formats:
                    chosen_format = "jpg"
                for f in r[2]["e"]:
                    to_add = dir_to_print
                    pound = ""
                    if f != chosen_format:
                        pound = "#"
                    image_add_on_list.append(pound + "\"" + to_add + "." + f + "\"")
            if RPLI_MAIN_TAG in r[2] and r[2][RPLI_MAIN_TAG] == VALUE_TRUE_MAIN_TAG:
                script += "layeredimage " + r[0] + ":\n"
            elif RPLIALWAYS_MAIN_TAG in r[2] and r[2][RPLIALWAYS_MAIN_TAG] == VALUE_TRUE_MAIN_TAG:
                script += \
                    (" " * INDENT * 2) + "always:\n" + \
                        (" " * INDENT * 3) + r[0] + ":\n"
                for i in image_add_on_list:
                    script += (" " * INDENT * 4) + i + "\n"
            elif RPLIGROUP_MAIN_TAG in r[2] and r[2][RPLIGROUP_MAIN_TAG] == VALUE_TRUE_MAIN_TAG:
                script += (" " * INDENT * 2) + "group " + r[0] + ":\n"
            elif RPLIATTRIB_MAIN_TAG in r[2] and r[2][RPLIATTRIB_MAIN_TAG] == VALUE_TRUE_MAIN_TAG:
                if RPLIDEF_MAIN_TAG in r[2] and r[2][RPLIDEF_MAIN_TAG] == VALUE_TRUE_MAIN_TAG:
                    def_add_on = " default"
                if "rpligroupchild" in r[2] and r[2]["rpligroupchild"] == VALUE_TRUE_MAIN_TAG:
                    script += (" " * INDENT)
                script += \
                    (" " * INDENT * 2) + "attribute " + r[0] + def_add_on + ":\n"
                for i in image_add_on_list:
                    i = i.replace("/.", ".", 1) # To handle edge case: The leaf node is excluded.
                    script += (" " * INDENT * 4) + i + "\n"

        return script

    def storePath(self, direc, path_list):
        """
        Store given path into the final path_list
        (starting with the optional directory_starter instead of root)
        """
        try:
            starter = self.config_data["directory_starter"]
        except KeyError:
            starter = ""
        direc[0] = starter
        if starter:
            path_list.append('/'.join(direc))
        else:
            path_list.append('/'.join(direc[1:]))

    def updateMaskPropertiesDict(self, tag_dict, tm_node):
        """
        Helper function to make sure the transform properties update correctly
        in a given dictionary.

        The node passed in must be a transform mask.

        Property                            : Data Type
                                              (Not in the original XML string,
                                               but instead how it's stored)
        scaleX and scaleY (xzoom and yzoom) : floats

        transformedCenter (x and y) : int array of [x, y]
        (not offset)

        scaleX and scaleY: Multiply the new scale by the existing scale.
        basic:
        #tag_dict[p.tag] = p.attrib
        """
        xml_root = ET.fromstring(tm_node.toXML())
        for ft in xml_root.iter("free_transform"):
            for p in ft:
                #self.DEBUG_MESSAGE += p.tag + "   :  " + str(p.attrib) + "\n"
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
                if p.tag == "transformedCenter":
                    if "transformedCenter" in tag_dict.keys():
                        new_x = tag_dict["transformedCenter"][0] + int(float(p.attrib["x"]))
                        new_y = tag_dict["transformedCenter"][0] + int(float(p.attrib["y"]))
                        tag_dict["transformedCenter"] = [new_x, new_y]
                    else:
                        tag_dict["transformedCenter"] = [int(float(p.attrib["x"])), int(float(p.attrib["y"]))]

        return tag_dict


    def getMaskPropertiesRecursion(self, search_path_pieces, tag_dict, curr_node):
        """
        Check through a path and pick up the transform mask properties for that path's tag_dict.
        Case 1: The mask is a sibling layer, so it applies to all its siblings.
        Case 2: The mask is a child layer, so it applies only to its parent.

        Check for case 1 before descending.
        At the end of the path, case 2 will be seen if it's there.
        
        For now, all the XML info under "free_transform" is added to the dictionary.

        The recursion halts because the list of layers
        in the path to explore decreases with each call.
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
                    if check_layer.name() == search_path_pieces[0]:
                    # Implicitly, this should only ever be a group or a paint layer.
                    #if check_layer.type() == "grouplayer" or check_layer.type() == "paintlayer":
                        curr_node = check_layer
                        self.getMaskPropertiesRecursion(search_path_pieces[1:], tag_dict, curr_node)


    def getMaskPropertiesStart(self, path_pieces, tag_dict):
        """
        At this point, the paths are defined with or without the prefix directory_starter.
        Case 1: directory_starter is non-empty, so skip over it to search the layers.
        Case 2: directory_starter is empty, so the first part of path_pieces is where the
                search must start.
        """
        curr_doc = KI.activeDocument()
        if curr_doc is not None:
            curr_node = curr_doc.rootNode()
        #self.DEBUG_MESSAGE += "path pieces: \n"
        #self.DEBUG_MESSAGE += str(path_pieces) + "\n"
        if self.config_data["directory_starter"]:
            #self.DEBUG_MESSAGE += str(path_pieces[1:]) + "\n"
            self.getMaskPropertiesRecursion(path_pieces[1:], tag_dict, curr_node)
        else:
            #self.DEBUG_MESSAGE += str(path_pieces) + "\n"
            self.getMaskPropertiesRecursion(path_pieces, tag_dict, curr_node)           

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

        Boolean rpli_mode
                    True: Get tags for Ren'Py Layered Images and image file formats.
                    False - Get the tags for everything except Ren'Py Layered Images.
        
        Value of 'True' for excluding a layer from a directory should have the
        same effect as a value of 'False' for including the layer in a name chain.

        """
        tag_dict_list = []
        for path in path_list:
            tag_dict = {}
            path_pieces = path.split("/")#(os.path.sep)
            for layer in path_pieces:
                layer = layer.lower()
                individual_layer_name = layer.split(' ')[0]
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
                if rpli_mode:
                    if "rpligroupchild" in tag_dict:
                        tag_dict.pop("rpligroupchild")
                    for main_tag in RPLI_MAIN_TAG_LIST:
                        if main_tag in tag_dict.keys():
                            if main_tag == RPLIGROUP_MAIN_TAG:
                                tag_dict["rpligroupchild"] = VALUE_TRUE_MAIN_TAG
                            tag_dict.pop(main_tag)

                # Second pass: See if inheritance disabling is present.
                # If so, clear the dictionary before adding any tags.
                if not rpli_mode:
                    for tag in tag_data:
                        letter = ""
                        value = ""
                        try:
                            letter, value = tag.split('=', 1)
                        except ValueError:
                            self.DEBUG_MESSAGE += "Error: letter,value parse failed in getTags()."
                            continue
                        if letter == "i":
                            if value in value_false_set:
                                tag_dict.clear()
                                break

                # Third pass: Add the tags.
                # Turn true/false values into true/false (as opposed to t/f, yes/no, etc.)
                scale_tag_found = False
                for tag in tag_data:
                    letter, value = tag.split('=', 1)
                    #self.DEBUG_MESSAGE += "letter/value is: " + letter + " : " + value + "\n"

                    if value.lower() in value_true_set:
                        value = VALUE_TRUE_MAIN_TAG
                    elif value.lower() in value_false_set:
                        value = VALUE_FALSE_MAIN_TAG

                    if not rpli_mode:
                        if letter == 's':
                            scale_tag_found = True
                            scale_list = [100.0]
                            for v in value.split(','):
                                if v.replace(".", "").isnumeric():
                                    scale_list.append(float(v))
                                else:
                                    self.DEBUG_MESSAGE += \
                                        "#Error: Non-numeric value given as scale: " + str(v)
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
                                            # the parents' tags.
                        elif letter in attribute_chain_set and value in value_true_set:
                            if "attribute_chain_name" not in tag_dict:
                                tag_dict["attribute_chain_name"] = individual_layer_name
                            else:
                                tag_dict["attribute_chain_name"] += (" " + individual_layer_name)
                        elif (letter in attribute_chain_set and value in value_false_set) \
                            or (letter in layer_exclude_set and value in value_true_set):
                            if "layers_to_exclude_dir" not in tag_dict:
                                tag_dict["layers_to_exclude_dir"] = [individual_layer_name]
                            else:
                                tag_dict["layers_to_exclude_dir"].append(individual_layer_name)
                        else:  # Don't save rpli tags if not using that mode.
                            if not letter in rpli_set:
                                tag_dict[letter] = value
                    elif rpli_mode:
                        if letter in rpli_set:
                            if value in value_true_set:
                                tag_dict[RPLI_MAIN_TAG] = VALUE_TRUE_MAIN_TAG
                            else:
                                tag_dict[RPLI_MAIN_TAG] = VALUE_FALSE_MAIN_TAG
                        elif letter in rplidef_set:
                            tag_dict[RPLIDEF_MAIN_TAG] = value
                        elif letter in rplialways_set:
                            tag_dict[RPLIALWAYS_MAIN_TAG] = value
                        elif letter in rpliattrib_set:
                            tag_dict[RPLIATTRIB_MAIN_TAG] = value
                        elif letter in rpligroup_set:
                            tag_dict[RPLIGROUP_MAIN_TAG] = value
                        elif letter == 'e':
                            if not value:
                                value = "png"
                            format_list = value.split(',')
                            if 'e' in tag_dict:
                                tag_dict['e'].extend(format_list)
                                tag_dict['e'] = list(set(tag_dict['e']))
                            else:
                                tag_dict['e'] = format_list
                        elif (letter in layer_exclude_set and value in value_true_set) \
                            or (letter in attribute_chain_set and value in value_false_set):
                            if "layers_to_exclude_dir" not in tag_dict:
                                tag_dict["layers_to_exclude_dir"] = [individual_layer_name]
                            else:
                                tag_dict["layers_to_exclude_dir"].append(individual_layer_name)
                        else:
                            continue
                if not scale_tag_found:      # Ensure that the default scale of 100
                    tag_dict['s'] = [100.0]  # exists if nothing is specified.

            # Next, check for changes from transform masks.
            tag_dict = self.getMaskPropertiesStart(path_pieces, tag_dict)

            tag_dict_list.append(tag_dict)
        return tag_dict_list

    def findGroupPositionRecursion(self, node, curr_coords):
        """
        Layers that are using alpha inheritance (like overlays) shouldn't affect coordinates.
        """
        check_coords = curr_coords
        if node.type() == "grouplayer":
            for i in node.childNodes():
                check_coords = self.findGroupPositionRecursion(i, check_coords)
        elif node.type() == "paintlayer" and not node.inheritAlpha():
            if node.bounds().topLeft().x() < check_coords[0]:
                check_coords[0] = node.bounds().topLeft().x()
            if node.bounds().topLeft().y() < check_coords[1]:
                check_coords[1] = node.bounds().topLeft().y()
            if node.bounds().bottomRight().x() > check_coords[2]:
                check_coords[2] = node.bounds().bottomRight().x()
            if node.bounds().bottomRight().y() > check_coords[3]:
                check_coords[3] = node.bounds().bottomRight().y()
        return check_coords


    def findGroupPositionStart(self, node):
        """
        Starts with the canvas's dimensions as the large values to beat (by being lesser than).
         x,y: The coordinates of the top left corner of the composite group
         center: A QPoint for the coordinates of the center of the composite group,
                 calculated as the average of the top left corner and the bottom right corner.
                 Hopefully the rounding is accurate.
        coords_to_check: [topLeftX, topLeftY, bottomRightX, bottomRightY]
        coords_to_return: [topLeftX, topLeftY, QPoint of center]
        """
        coords_to_check = []
        center_x = 0
        center_y = 0
        curr_doc = KI.activeDocument()
        if curr_doc is not None:
            coords_to_check = [curr_doc.width(),curr_doc.height(),0,0]
            coords_to_check = self.findGroupPositionRecursion(node, coords_to_check)
            center_x = int((coords_to_check[0] + coords_to_check[2])/2)
            center_y = int((coords_to_check[1] + coords_to_check[3])/2)
        coords_to_return = [coords_to_check[0], coords_to_check[1], QPoint(center_x, center_y)]
        return coords_to_return

    def pathRecord(self, node, path, path_list, path_len, coords_list, rpli_path_list):
        """
        Searches for all the node to leaf paths and stores them in path_list using storePath().
        storePath() takes in the entire paths (including all the tags at this step).

        Only grouplayers and paintlayers are checked for this step; filters aren't usable here.

        Coordinates are also found and inserted into coords_list.

        Reference: GeeksforGeeks solution to finding paths in a binary search tree

        New concept: Record an additional list for the Ren'Py layered image tags
        since the required behavior for layered images isn't the same when it comes to
        inheritance. There needs to be dictionaries for non-leaf layers (i.e. groups).
        """
        if len(path) > path_len:
            path[path_len] = node.name().lower()
        else:
            path.append(node.name().lower())
        recordable_child_nodes = 0
        for c in node.childNodes():
            if c.type() == "grouplayer" or c.type() == "paintlayer":
                recordable_child_nodes += 1
                if c.type() == "grouplayer":   # Case: The tagged image is a group.
                    for f in format_tag_set:   # Get coords from the group's content
                        if f in c.name().lower():
                            self.storePath(path + [c.name().lower()], path_list)
                            new_coords = self.findGroupPositionStart(c)
                            if not new_coords:
                                self.DEBUG_MESSAGE += \
                            "Error: Cannot get the coordinates for group layer [" + c.name() + "]\n"
                            else:
                                coords_list.append([new_coords[0],new_coords[1],new_coords[2]])
                            break
        if recordable_child_nodes == 0: # Case: End of path reached
            for f in format_tag_set:
                if f in node.name().lower():
                    self.storePath(path, path_list)
                    coords_list.append([node.bounds().topLeft().x(), \
                                node.bounds().topLeft().y(), \
                                    node.bounds().center()])
                    break
        else:
            path_len += 1
            for i in node.childNodes(): # Case: Send the child nodes through the recursion.
                tag_data = i.name().lower().split(' ')[1:]
                letter_data = []
                value_data = []
                for tag in tag_data:
                    try:
                        letter, value = tag.split('=', 1)
                        letter_data.append(letter)
                        value_data.append(value)
                    except ValueError:
                        continue
                if i.type() == "grouplayer" or i.type() == "paintlayer":
                    self.pathRecord(i, (path+[i.name().lower()]), \
                                    path_list, path_len, coords_list, rpli_path_list)
                    for rl in RPLI_LIST:
                        for tag in rl:
                            if tag in letter_data and \
                                    value_data[letter_data.index(tag)] in value_true_set:
                                self.storePath((path+[i.name().lower()]),rpli_path_list)
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
        for index in range(len(path_list)):
            if "e" in tag_dict_list[index] and not "i" in tag_dict_list[index]:
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
            layers = path.split("/")
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
            layer_data = path.split("/")
            layer_name_to_export = layer_data[-1]
            export_layer_list.append(layer_name_to_export)
        return export_layer_list

    def modifyCoordinates(self, coords_list, tag_dict_list):
        """
        Modifies the coordinates
            0,1 : x,y on top left corner
              2 : QPoint of the center
        Step 1: Check for changes from adding margins.
                The Batch Exporter uses the smallest margin
                in the list by default, so that's what's used here.
                The center points wouldn't change since each set
                of 4 margins (around a single layer rectange) would be of equal size.
        Step 2: Check for changes from transform masks.
        Step 3: Check for the t tag (meaning set the coordinates to 0 if it's True).
        Step 4: Scale the coordinates with the smallest
                given size from the 's=' layer tags
        Step 5: Remove negative values for the coordinates.
                This is because Krita crops out material
                not on the canvas when it's exporting the images.

        New, simplified version - C0200
        """
        for i, coords in enumerate(coords_list):
            if "m" in tag_dict_list[i]:
                pixel_subtract_amount = int(min(tag_dict_list[i]["m"]))
                coords[0] -= pixel_subtract_amount
                coords[1] -= pixel_subtract_amount

            if "transformedCenter" in tag_dict_list[i]:
                diff_x = tag_dict_list[i]["transformedCenter"][0] - coords[0]
                diff_y = tag_dict_list[i]["transformedCenter"][1] - coords[1]
                coords[0] += diff_x
                coords[1] += diff_y
                coords[2].setX(coords[2].x() + diff_x)
                coords[2].setY(coords[2].y() + diff_y)

            if "t" in tag_dict_list[i] and tag_dict_list[i]["t"] in value_false_set:
                coords[0] = 0
                coords[1] = 0
                coords[2] = QPoint(0,0)
                curr_doc = KI.activeDocument()
                if curr_doc is not None:
                    coords[2].setX(int(curr_doc.width()/2))
                    coords[2].setY(int(curr_doc.height()/2))

            if "s" in tag_dict_list[i]:
                coords[0] = round((coords[0] * min(tag_dict_list[i]["s"])) / 100)
                coords[1] = round((coords[1] * min(tag_dict_list[i]["s"])) / 100)
                center_x_new = float(coords[2].x()) * min(tag_dict_list[i]["s"]) / 100
                center_y_new = float(coords[2].y()) * min(tag_dict_list[i]["s"]) / 100
                coords[2].setX(int(center_x_new))
                coords[2].setY(int(center_y_new))

            if coords[0] < 0:
                coords[0] = 0
            if coords[1] < 0:
                coords[1] = 0

        return coords_list

    def getModifierBlock(self, line):
        """
        Zoom and Rotate are handled here.
        transformedCenter will instead modify xpos and ypos.
        """
        modifier_block = ""
        # For checking the contents
        #modifier_block += "~ ~ ~\n"
        #for key,value in line[2].items():
        #    modifier_block += key + " : " + str(value) + "\n"
        #modifier_block += "~ ~ ~"
    
        # Zoom
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
                modifier_block += ((' ')*INDENT*2) + "zoom " + str(xzoom) + "\n"
            else:
                if xzoom != 1.0:
                    modifier_block += ((' ')*INDENT*2) + "xzoom " + str(xzoom) + "\n"
                if yzoom != 1.0:
                    modifier_block += ((' ')*INDENT*2) + "yzoom " + str(yzoom) + "\n"
        # Rotate
        if "aZ" in line[2]:
            rounded_rot = round(line[2]["aZ"], int(self.config_data["atl_rotate_decimal_places"]))
            modifier_block += ((' ')*INDENT*2) + "rotate " + str(rounded_rot) + "\n"

        return modifier_block

    def sortRpliData(self, rpli_data_list):
        """
        This is an unusual sorting algorithm that positions data lines such that parent
        layers would come sooner than their child layers, AND would not be swapped
        with layers of different paths. It's meant to get the order of the list
        to be the same as the Krita layer stack (though in reverse order since
        Ren'Py displays the bottommost image declarations at the front, and
        drawing programs do the opposite, though it wouldn't matter for a layered image
        declaration block.
        """
        #self.DEBUG_MESSAGE += "list before sorting:\n"
        #for d in rpli_data_list:
        #    self.DEBUG_MESSAGE += str(d[1]) + "\n"
        s_list = rpli_data_list
        list_sorted = False
        swap_occurred = False
        c = len(s_list)-1
        while not list_sorted:
            curr_line = s_list[c][3]
            comp_line = s_list[c-1][3]
            #self.DEBUG_MESSAGE += "Comparing " + curr_line + " with " + comp_line  + "\n"
            if curr_line in comp_line and curr_line < comp_line:
                s_list[c], s_list[c-1] = s_list[c-1], s_list[c]
                #self.DEBUG_MESSAGE += "SWAP!\n"
                swap_occurred = True
            else:
                #self.DEBUG_MESSAGE += "no swap\n"
                swap_occurred = False
            c = c - 1
            if c == 0:
                if swap_occurred:
                    c = len(s_list)-1
                else:
                    list_sorted = True

        #self.DEBUG_MESSAGE += "sorted list:\n"
        #for l in s_list:
        #    self.DEBUG_MESSAGE += str(l[1]) + "\n"
        #return s_list

    def getDataList(self, button_chosen, spacing_num):
        """
        Concept: 1) Get all the paths.
                 2) Get all the tags (with inheritance).
                 3) Filter the paths by checking them with tags.
                 4) Get the names of the layers.
                 5) Put the data into the list.
                 6) Modify the coordinates for margins and scale.
                 7) If 'align' type output is selected, swap out the xy pixel coordinates with align coordinates.

        data_list: #TODO: This information seems to be outdated.
            [0] name of layer
            [1] directory
            [2] tag_dict_list        (List where each index corresponds to the index of its path,
                                      and the content is a dictionary with the tags applicable to
                                      the final layer of that path, adjusted for Batch Exporter
                                      inheritance.)
            [3] coords_list          (For each layer: x position, y position, and center point as a QPoint.
                                      Values are modified for the scale given by tag.)
            [4] path_list_with_tags  (Unused paths are filtered out,
                                      but tags (at the layers they are declared) are not.)
        rpli_data_list:
            [0] name of layer
            [1] directory
            [2] rpli_tag_dict_list
            [3] rpli_path_list_with_tags

        There is an additional configs load for align_decimal_places here
        because self.config_data fails out here.

        """
        data_list =  []
        rpli_data_list = []
        export_layer_list = []
        coords_list = []
        path_list = []
        rpli_path_list = []
        tag_dict_list = []
        coords_list = []
        curr_doc = KI.activeDocument()
        if curr_doc is not None:
            root_node = curr_doc.rootNode()
        path = []
        path_list_with_tags = []
        self.pathRecord(root_node, path, path_list, 0, coords_list, rpli_path_list)
        tag_dict_list = self.getTags(path_list, False)
        rpli_tag_dict_list = self.getTags(rpli_path_list, True)
        path_list, coords_list, tag_dict_list = \
            self.removeUnusedPaths(path_list, coords_list, tag_dict_list)
        path_list_with_tags = path_list
        rpli_path_list_with_tags = rpli_path_list
        path_list = self.removeTagsFromPaths(path_list)
        rpli_path_list = self.removeTagsFromPaths(rpli_path_list)
        tag_dict_list = list(filter(None, tag_dict_list))
        rpli_tag_dict_list = list(filter(None, rpli_tag_dict_list))
        coords_list = self.modifyCoordinates(coords_list, tag_dict_list)
        export_layer_list = self.getExportLayerList(path_list)
        rpli_export_layer_list = self.getExportLayerList(rpli_path_list)

        for i,layer in enumerate(export_layer_list):
            data_list.append(tuple([layer.lower(), path_list[i].lower(), \
                                    tag_dict_list[i], coords_list[i], path_list_with_tags[i]]))

        for i,layer in enumerate(rpli_export_layer_list):
            rpli_data_list.append(tuple([layer.lower(), rpli_path_list[i].lower(), \
                                         rpli_tag_dict_list[i], rpli_path_list_with_tags[i]]))

        if rpli_data_list:
            self.sortRpliData(rpli_data_list)

        if button_chosen in button_display_align_set:
            align_decimal_places = OUTER_DEFAULT_ALIGN_DECIMAL_PLACES
            try:
                configs_file = open(\
                    os.path.join(os.path.dirname(\
                        os.path.realpath(__file__)), "configs.json"), encoding="utf-8")
                imported_configs = json.load(configs_file)
                align_decimal_places = int(imported_configs["align_decimal_places"])
            except KeyError:
                align_decimal_places = int(default_configs_dict["align_decimal_places"])
            data_list = calculateAlign(data_list, spacing_num, align_decimal_places)

        return data_list, rpli_data_list

    def ruleOfThirdsFlag(self):
        """
        The elif part covers the case where the user tries to uncheck the box
        by directly clicking it (which would be while the slider is at 4),
        which shouldn't have an effect since the slider bar would be in the same position.
        """
        if self.rule_of_thirds_check.isChecked():
            self.spacing_slider.setSliderPosition(4)
        elif self.spacing_slider.value() == 4:
            self.rule_of_thirds_check.setChecked(True)


    def updateSpacingValue(self):
        """
        Maintains the rule of thirds checkbox.
        """
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
(os.path.realpath(__file__)), "configs.json"), 'w', encoding="utf-8") as f:
            json.dump(default_configs_dict, f, indent=2)
        self.text_signal_emitter.custom_signal.emit(\
            "Configurations reverted to default!\nChanges to lock_windows_to_front \
                and button names require a reset to this window!")

    def settingCustomize(self):
        """
        Ideally, refreshConfigData() would be called soon after webbrowser.open(),
        but I don't think there is a signal for right after the user edits the external file.

        Idea: Update the buttons with the customized template text.
        """
        webbrowser.open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "configs.json"))
    
    def refreshConfigData(self):
        """
        Function to reload the config dict after it has been customized.
        """
        try:
            configs_file = open(os.path.join(os.path.dirname(\
                os.path.realpath(__file__)), "configs.json"), encoding="utf-8")
            imported_configs = json.load(configs_file)
            self.config_data = imported_configs
            #TODO: refresh buttons
            self.update()
        except IOError:
            pass

class ScriptBox(QWidget):
    """
    Idea: Put the pop-up windows into a single box.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Choose Your Format!")
        self.config_data = default_configs_dict
        try:
            configs_file = open(os.path.join(\
                os.path.dirname(os.path.realpath(__file__)), "configs.json"), encoding="utf-8")
            imported_configs = json.load(configs_file)
            self.config_data = imported_configs
        except IOError:
            pass
        if self.config_data["lock_windows_to_front"] in value_true_set:
            self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.format_menu = None
        self.output_window = None
        self.createScriptBox()
        try:
            width_to_use = int(self.width() * float(\
                self.config_data["script_window_w_size_multiplier"]))
        except ValueError:
            width_to_use = self.width()
        try:
            height_to_use = int(self.height() * float(\
                self.config_data["script_window_h_size_multiplier"]))
        except ValueError:
            height_to_use = self.height()
        self.resize(width_to_use, height_to_use)
        if self.config_data["customize_button_text"].lower() in hidden_set\
              and not self.format_menu is None:
            self.dinu()
        if "comic sans" in self.config_data["script_preferred_font"].lower():
            self.jokeFont()
        close_notifier.viewClosed.connect(self.close)

    def createScriptBox(self):
        """
        The output window's close button is connected to the main box.
        """
        self.output_window = TextOutput(self)
        self.output_window.setupUi(self, \
                                   float((self.config_data["script_font_size"])), \
                                    self.config_data["script_preferred_font"])
        self.format_menu = FormatMenu(self)
        self.format_menu.text_signal_emitter.custom_signal.connect(self.output_window.receiveText)
        script_box_layout = QHBoxLayout()
        script_box_layout.addWidget(self.format_menu)
        script_box_layout.addWidget(self.output_window)
        self.setLayout(script_box_layout)

    #coding=utf-8
    def dinu(self):
        """
        Dinu has taken over this plugin.
        """
        d =r"""
                  /\
                  ||
                _/||\_
            _  // || \\  _
            \\//  ||  \\//
            /\/   ||   \/\
           _-/</> || <\>\-_
          / /</>  ||  <\>\ \
        <==/<|>   ||   <|>\==>
          \\ <\>  ||  </> //.
          .\\ <\> || </> //
          . /\   /[]\   /\
        _ ./ /\ O || O /\ \  _
        \\/ // \  ||  / \\ \//.
         \\//__/\ || /\__\\//
              .  \||/  .      .
        .     .   \/          .
      ERROR: SEGMENTATION FAULT
                                """
        self.output_window.receiveText(d)

    def jokeFont(self):
        """
        Maybe it's the way you're dressed.
        """
        self.output_window.receiveText("Okay, funny person.")

class RenameWorkerThread(QThread):
    """
    Class to handle the rename recursion process in its own thread.
    """
    def __init__(self, dir_name, export_dir_name, suffix, new_folder_name):
        self.dir_name = dir_name
        self.export_dir_name = export_dir_name
        self.suffix = suffix
        self.new_folder_name = new_folder_name
        self.file_found = False
        super().__init__()

    def run(self):
        """
        Define and call run() because QThreads call it.
        """
        self.renameRecursion(self.dir_name, self.export_dir_name, self.suffix, self.new_folder_name)

    def renameRecursion(self, dir_name, export_dir_name, suffix, folder_name):
        """
        Performs the file copies with renaming.
        """
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
        self.config_data = default_configs_dict
        try:
            configs_file = open(os.path.join(\
                os.path.dirname(os.path.realpath(__file__)), "configs.json"), encoding="utf-8")
            imported_configs = json.load(configs_file)
            self.config_data = imported_configs
        except IOError:
            pass
        if self.config_data["lock_windows_to_front"] in value_true_set:
            self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.createScaleCalculateBox()
        close_notifier.viewClosed.connect(self.close)
        self.status_signal_emitter = TextSignalEmitter()
        self.status_signal_emitter.custom_signal.connect(self.receiveStatus)


    def createScaleCalculateBox(self):
        """
        Creates the Scale Calculator menu.
        """
        preset_label_layout = QHBoxLayout()
        preset_width_label = QLabel("Width")
        preset_height_label = QLabel("Height")
        percentage_label = QLabel("Scale Percentage")
        self.status_bar = QStatusBar()
        size_layout = QGridLayout()
        self.line_width = QLineEdit(parent=self)
        self.line_width.textEdited[str].connect(lambda: self.lineEdited(self.line_width.text(), 0))
        self.line_height = QLineEdit(parent=self)
        self.line_height.textEdited[str].connect(\
            lambda: self.lineEdited(self.line_height.text(), 1))
        curr_doc = KI.activeDocument()
        if curr_doc is not None:
            self.line_width.setText(str(float(curr_doc.width()))+" px")
            self.line_height.setText(str(float(curr_doc.height()))+" px")
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
the suffix '_@[scale]x'.\nThis button will make KRS copy over the batch-exported \
images of the currently selected scale to a new folder in which they don't have that suffix,\n\
so that those images may be transferred to your Ren'Py project without having to \
rename them manually.")
        rename_button.clicked.connect(self.renameClicked)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.onClose)
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
        curr_doc = KI.activeDocument()
        if curr_doc is not None:
            flip_d = 1-d
            scale = float(value/((curr_doc.width()*flip_d)+(curr_doc.height()*d)))
            self.scale_box_percent.setValue(scale * 100.0)

    def calculatorScaleChanged(self):
        """
        Updates the width XOR the height on display.
        This is called when the scale box is directly modified,
        or when either of the dimension boxes is edited.
        Only the box that is not focused is edited by this function
        since the user would be editing the focused box.
        """
        curr_doc = KI.activeDocument()
        scale = float(self.scale_box_percent.value() / 100.0)
        if curr_doc is not None:
            width = round((float(curr_doc.width()) * scale), 1)
            height = round((float(curr_doc.height()) * scale), 1)
            if not self.line_width.hasFocus():
                self.line_width.setText(str(width) + " px")
            if not self.line_height.hasFocus():
                self.line_height.setText(str(height) + " px")

    def receiveStatus(self, value):
        """
        Receives the signal for the status message.
        """
        self.status_bar.showMessage(value, MSG_TIME)

    def renamerFinished(self, file_found, dir_to_check, folder_name):
        """
        Displays the status bar message in the scale calculator + file renamer window.
        """
        if file_found is False:
            self.status_bar.showMessage("No files to copy and rename have been found! \
                                        Check your scale tag(s) and file directory.", MSG_TIME)
            if os.path.exists(dir_to_check) and os.path.isdir(dir_to_check):
                shutil.rmtree(dir_to_check)
        else:
            self.status_bar.showMessage(f"Files have been copied \
and renamed at {folder_name}!", MSG_TIME)

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
        if scale != 1.0:
            suffix = "_@" + str(scale) + "x"
            new_folder_name = "_krs_x" + str(scale)
            export_dir_name = os.path.join(dir_name + new_folder_name)
            Path(export_dir_name).mkdir(parents=True, exist_ok=True)
            self.worker = RenameWorkerThread(dir_name, export_dir_name, suffix, new_folder_name)
            self.worker.start()
            self.worker.finished.connect(lambda: \
                                         self.renamerFinished(self.worker.file_found, \
export_dir_name, ("export"+new_folder_name)))
        else:
            self.status_bar.showMessage("Requested scale is 100%; no need to rename the images!")

    def renameClicked(self):
        """
        TODO: Add a window that asks if this is what the user wants.
        """
        if KI.activeDocument() is not None:
            self.recursiveRenameStart()

class KritaRenpyScripter(DockWidget):
    """
    Class for the dock widget. The windows are called from here.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Krita Ren'Py Scripter")
        self.createInterface()
        self.script_box = None

    def showErrorMessage(self, to_print):
        msg = QMessageBox()
        msg.setText(to_print)
        msg.exec_()

    def createInterface(self):
        scripter_button = QPushButton("Scripter")
        scripter_button.clicked.connect(self.startScriptBox)

        calculate_button = QPushButton("Scale Calculator and Renamer")
        calculate_button.clicked.connect(self.startScaleCalculateBox)

        main_layout = QVBoxLayout()
        main_layout.addWidget(scripter_button)
        main_layout.addWidget(calculate_button)

        mainWidget = QWidget(self)
        mainWidget.setLayout(main_layout)
        self.setWidget(mainWidget)


    def startScriptBox(self):
        self.script_box = ScriptBox()
        self.script_box.show()

    def startScaleCalculateBox(self):
        self.scale_calculate_box = ScaleCalculateBox()
        self.scale_calculate_box.show()


    # notifies when views are added or removed
    # 'pass' means do not do anything
    def canvasChanged(self, canvas):
        pass

    #def closeEvent(self, event):
    #    if not set.script_box is None:
    #        self.script_box.close()

def registerDocker():
    Krita.instance().addDockWidgetFactory(DockWidgetFactory\
("krita_renpy_scripter", DockWidgetFactoryBase.DockRight\
 , KritaRenpyScripter))
