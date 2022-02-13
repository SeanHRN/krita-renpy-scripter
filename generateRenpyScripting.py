from krita import *
import sys
from os.path import join
import os
import re
from PyQt5.QtWidgets import *
KI = Krita.instance()

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
    data_list = []
    layer_names = []
    all_coords = []
    currentDoc = KI.activeDocument()
    if currentDoc != None:
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
    return data_list

def writeData(input_data, path):
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

        exampleButton = QPushButton("Generate Ren'Py Scripting", mainWidget)
        exampleButton.clicked.connect(self.popup)

        mainWidget.setLayout(QVBoxLayout())
        mainWidget.layout().addWidget(exampleButton)

    def canvasChanged(self, canvas):
        pass

    def popup(self):
        data = getData()
        #TODO: Allow the user to choose the file path.
        #path = "C:/Users/seanc/OneDrive/Desktop/file_name.txt"
        writeData(data, path)
        QMessageBox.information(QWidget(), "Generate Ren'Py Scripting", "Ren'Py Scripting Generated!")

    def main():
        newDialog = QDialog()
        newDialog.setWindowTitle("Be like Gaston!")
        newDialog.exec_()


Krita.instance().addDockWidgetFactory(DockWidgetFactory\
("generateRenpyScripting", DockWidgetFactoryBase.DockRight\
 , GenerateRenpyScripting))

if __name__ == "__main__":
    main()
