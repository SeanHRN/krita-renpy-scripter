from krita import *
import sys
from os.path import join
import os
import re
currentDoc = Krita.instance().activeDocument()

file_name = "file_name.txt"
#complete_name = os.path.join(save_path, file_name)

def debugger():
    for f in os.listdir(r"C:\Users\seanc\OneDrive\Desktop"):
        print(f)

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

def doThing():
    # get list of layer names
    layer_names = []
    coord = []
    root_node = currentDoc.rootNode()
    for i in root_node.childNodes():
        if i.visible() == True:
            layer_names.append(i.name())
            coord_x = i.bounds().topLeft().x()
            coord_y = i.bounds().topLeft().y()
            print(f"appending ({coord_x}, {coord_y})")
            coord.append([coord_x, coord_y])
    file1 = open(r"C:/Users/seanc/OneDrive/Desktop/file_name.txt", "w")
    file1.write("\n")
    for name, coordinates in zip(layer_names, coord):
        if name.find(" e=") != -1:
            size_list = parseValuesIntoList(name, "s=")
            if size_list:
                coordinates[0] = round(coordinates[0] * (min(size_list)/100))
                coordinates[1] = round(coordinates[1] * (min(size_list)/100))

            margin_list = parseValuesIntoList(name, "m=")
            if margin_list:
                print("margin list found")
                coordinates[0] += max(margin_list)
                coordinates[1] += max(margin_list)
            else:
                print("no margin list")

            name = name[0:name.find(" e=")]

        file1.write(f"show {name}:\n    pos({coordinates[0]},{coordinates[1]})\n")
    file1.write("\n")
    file1.write('pause')
    file1.close()

def main():
    doThing()
    #debugger()
if __name__ == "__main__":
    main()
