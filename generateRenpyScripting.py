from krita import *
import sys
from os.path import join, exists
import webbrowser
from PyQt5.QtWidgets import *
KI = Krita.instance()
default_outfile_name = "rpblock.txt"
indent = 4
align_values_p1 = [0.0, 0.5, 1.0]
align_values_p2 = [0.0, 0.25, 0.5, 0.75, 1.0]
align_values_p3 = [0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0]
align_values = [align_values_p1, align_values_p2, align_values_p3]

def parseValuesIntoList(name, sub_to_check):
    list = []
    if name.lower().find(sub_to_check) != -1:
        properties = name.lower()[name.lower().find(" " + sub_to_check):]
        if properties.find("=") != -1:
            properties = properties[properties.find("=")+1:]
        stopper = len(properties)
        for element in range (0, len(properties)):
            if properties[element].isalpha():
                stopper = element
                break
        properties = properties[:stopper]
        properties = properties.replace(" ","")
        list = [float(n) for n in properties.split(",")]
    return list


def parseLayersCoords(layer, layer_name_list, coordinates_list):
    if layer.visible() == True:
        layer_name_sublist = []
        coordinates_sublist = []
        lower_n = layer.name().lower()
        if lower_n.find(" e=") != -1:
            layer_name_list.append(layer.name())
            coord_x, coord_y = 0, 0
            if lower_n.find(" t=false") == -1 and lower_n.find(" t=no") == -1:
                coord_x = layer.bounds().topLeft().x()
                coord_y = layer.bounds().topLeft().y()
            coordinates_list.append([coord_x, coord_y])
        elif layer.type() == "grouplayer":
            for child in layer.childNodes():
                parseLayersCoords(child, layer_name_sublist, coordinates_sublist)
        layer_name_list.extend(layer_name_sublist)
        coordinates_list.extend(coordinates_sublist)

def closestNum(num_list, value):
    return num_list[min(range(len(num_list)), key = lambda i: abs(num_list[i]-value))]

#
def calculateAlign(data_list, precision_level):
    """
    calculateAlign converts the pos(x,y) coordinates
    in the data list into align(x,y) coordinates.
    """
    width, height = 1, 1
    currentDoc = KI.activeDocument()
    if currentDoc != None:
        width = currentDoc.width()
        height = currentDoc.height()

    new_data_list = []
    for d in data_list:
        xalign = closestNum(align_values[precision_level-1], (d[1] / width))
        yalign = closestNum(align_values[precision_level-1], (d[2] / height))
        new_data_list.append(tuple((d[0],xalign,yalign)))
    return new_data_list

def getData(button_num, precision_level):
    file_open = False
    data_list = []
    layer_names = []
    all_coords = []
    currentDoc = KI.activeDocument()
    if currentDoc != None:
        file_open = True
        root_node = currentDoc.rootNode()
        for i in root_node.childNodes():
            parseLayersCoords(i, layer_names, all_coords)

    for name, coord_indv in zip(layer_names, all_coords):
        if name.lower().find(" e=") != -1:
            margin_list = parseValuesIntoList(name, "m=")
            if margin_list:
                coord_indv[0] -= max(margin_list)
                coord_indv[1] -= max(margin_list)
            size_list = parseValuesIntoList(name, "s=")
            if size_list:
                coord_indv[0] = round(coord_indv[0] * (min(size_list)/100))
                coord_indv[1] = round(coord_indv[1] * (min(size_list)/100))
            name = name[0:name.lower().find(" e=")]
            data_list.append(tuple((name, coord_indv[0], coord_indv[1])))

    if button_num == 2:
        data_list = calculateAlign(data_list, precision_level)
    return file_open, data_list


def writeData(input_data, path, format_num):
    outfile = open(path, "w")
    outfile.write("\n")
    prefix = "pos"
    if format_num == 2:
        prefix = "align"
    for d in input_data:
        outfile.write(f"{' ' * indent}show {d[0]}:\n")
        outfile.write(f"{' ' * (indent * 2)}{prefix} ({str(d[1])}, {str(d[2])})\n")
    outfile.write("\n")
    outfile.write(f"{' ' * indent}pause")
    outfile.close()




class GenerateRenpyScripting(DockWidget):
    title = "Generate Ren'Py Scripting"

    def __init__(self):
        super().__init__()
        self.setWindowTitle(self.title)
        self.createInterface()

    def createInterface(self):


        pos_button = QPushButton("Generate pos(x,y) Scripting")
        pos_button.clicked.connect(lambda: self.process(1))

        align_button = QPushButton("Generate align(x,y) Scripting")
        align_button.clicked.connect(lambda: self.process(2))


        self.precision_slider = QSlider(Qt.Horizontal, self)
        self.precision_slider.setGeometry(30, 40, 200, 30)
        self.precision_slider.setRange(1, 3)
        self.precision_slider.setValue(3)
        self.precision_slider.setFocusPolicy(Qt.NoFocus)
        self.precision_slider.setPageStep(3)
        self.precision_slider.setTickPosition(QSlider.TicksBelow)
        self.precision_slider.setTickInterval(3)
        self.precision_slider.valueChanged[int].connect(self.updatePrecisionValue)
        self.precision_text = QLabel("align() precision: ",self)
        self.precision_number_label = QLabel(f"{self.precision_slider.value()}", self)
        self.precision_number_label.setAlignment(Qt.AlignVCenter)

        self.filename_line = QLineEdit()
        self.filename_line.setText(default_outfile_name)

        top_layout = QVBoxLayout()
        precision_layout = QHBoxLayout()
        #last_layout = QVBoxLayout()

        top_layout.addWidget(pos_button)
        top_layout.addWidget(align_button)

        precision_layout.addWidget(self.precision_text)
        precision_layout.addWidget(self.precision_number_label)
        precision_layout.addWidget(self.precision_slider)
        top_layout.addLayout(precision_layout)

        top_layout.addWidget(self.filename_line)

        mainWidget = QWidget(self)
        mainWidget.setLayout(top_layout)
        self.setWidget(mainWidget)


    def updatePrecisionValue(self):
        self.precision_number_label.setText(str(self.precision_slider.value()))

    def process(self, button_num):
        file_open_test_result, data = getData(button_num, self.precision_slider.value())
        push_message = ""
        path = ""
        if file_open_test_result == True:
            path = str(QFileDialog.getExistingDirectory(None, "Select a save location."))
            outfile_name = default_outfile_name
            if self.filename_line.text() != "":
                outfile_name = self.filename_line.text()
            path += "/" + outfile_name
            writeData(data, path, button_num)
            outfile_exists = exists(path)
            if outfile_exists:
                webbrowser.open(path)
    #        else:
    #            push_message = "Failure: Open a Krita document."
    #            QMessageBox.information(QWidget(), "Generate Ren'Py Scripting", push_message)

    def canvasChanged(self, canvas):
        pass

def registerDocker():
    Krita.instance().addDockWidgetFactory(DockWidgetFactory\
("generateRenpyScripting", DockWidgetFactoryBase.DockRight\
 , GenerateRenpyScripting))
