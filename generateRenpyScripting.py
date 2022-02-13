from krita import *
import sys
from os.path import join
import os
import re
from PyQt5.QtWidgets import *
KI = Krita.instance()
outfile_name = "rpblock.txt"

def parseValuesIntoList(name, sub_to_check):
    list = []
    if name.find(sub_to_check) != -1:
        properties = name[name.find(" " + sub_to_check):]
        if properties.find("=") != -1:
            properties = properties[properties.find("=")+1:]
        print("properties: " + properties)
        stopper = len(properties)
        for element in range (0, len(properties)):
            if properties[element].isalpha():
                stopper = element
        properties = properties[:stopper]
        properties = properties.replace(" ","")
        print("stripped properties: " + properties)
        list = [int(n) for n in properties.split(",")]
    return list


def getData():
    file_open = False
    data_list = []
    layer_names = []
    all_coords = []
    currentDoc = KI.activeDocument()

    if currentDoc != None:
        file_open = True
        root_node = currentDoc.rootNode()
        for i in root_node.childNodes():
            if i.visible() == True:
                layer_names.append(i.name())
                coord_x = i.bounds().topLeft().x()
                coord_y = i.bounds().topLeft().y()
                print(f"appending ({coord_x}, {coord_y})")
                all_coords.append([coord_x, coord_y])

    for name, coord_indv in zip(layer_names, all_coords):
        if name.find(" e=") != -1:
            size_list = parseValuesIntoList(name, "s=")
            if size_list:
                coord_indv[0] = round(coord_indv[0] * (min(size_list)/100))
                coord_indv[1] = round(coord_indv[1] * (min(size_list)/100))

            margin_list = parseValuesIntoList(name, "m=")
            if margin_list:
                print("Margin list found for layer: " + name)
                print("Nudging the coord_indv Up-Left by max value margin.")
                coord_indv[0] -= max(margin_list)
                coord_indv[1] -= max(margin_list)

            name = name[0:name.find(" e=")]

            data_list.append(tuple((name, coord_indv[0], coord_indv[1])))
    return file_open, data_list


def writeData(input_data, path):
    print(path)
    out_file = open(path, "w")
    out_file.write("\n")
    for d in input_data:
        out_file.write(f"show {d[0]}:\n    pos({str(d[1])}, {str(d[2])}) \n")
    out_file.write("\n")
    out_file.write("pause")
    out_file.close()


class GenerateRenpyScripting(DockWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generate Ren'Py Scripting")
        mainWidget = QWidget(self)
        self.setWidget(mainWidget)

        button = QPushButton("Generate Ren'Py Scripting", mainWidget)
        button.clicked.connect(self.popup)

        mainWidget.setLayout(QVBoxLayout())
        mainWidget.layout().addWidget(button)


    def canvasChanged(self, canvas):
        pass


    def popup(self):
        file_open_test_result, data = getData()
        push_message = ""
        if file_open_test_result == True:
            path = str(QFileDialog.getExistingDirectory(None, "Select a save location."))
            path += "/" + outfile_name
            writeData(data, path)
            push_message = f"Success: Ren'Py Script Block Written to path: {path}"
        else:
            push_message = "Failure: Open a Krita document."
        QMessageBox.information(QWidget(), "Generate Renpy Scripting", push_message)


    def main():
        newDialog = QDialog()
        newDialog.setWindowTitle("Untitled!")
        newDialog.exec_()


Krita.instance().addDockWidgetFactory(DockWidgetFactory\
("generateRenpyScripting", DockWidgetFactoryBase.DockRight\
 , GenerateRenpyScripting))


if __name__ == "__main__":
    main()
