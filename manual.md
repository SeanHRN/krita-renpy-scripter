# Generate Ren'Py Scripting
by Sean Castillo

This plugin uses the layer name syntax for krita-batch-exporter by GDQuest
to generate a block of text for a Ren'Py script for moSean comics.
By default, the pos (x,y) coordinates in the block are how the content of each layer
appears on Krita's canvas; specifically, the coordinates refer to the top left corner
of the bounding box for all non-transparent pixels in that layer.

In order for a layer to be included, it must be toggled visible and follow the [krita-batch-exporter syntax](https://github.com/GDquest/krita-batch-exporter/blob/master/batch_exporter/Manual.md),
i.e. contain "e=png" or "e=jpg" directly following the actual name of the layer.

A pause statement is printed at the end.

## Properties
 - s  - 'size' in scale percentage
 - m - 'margin' width in pixels

The minimum listed size is used for the Ren'Py block.
This is because I use downscaled versions of my images for Ren'Py (fitted for 1920x1080 px).

Currently, the margin option nudges the (x,y) coordinates of the image up and left that many pixels.

## Ren'Py Format
The output is written for my particular way of using Ren'Py:

    # Empty Line
    show background:
        pos (0, 0)
    show character:
        pos (500, 500)
    # Empty Line
    pause

## Example
If the layer is named:

    'Gaston e=png s=100,50'
then the output block would be:

## Known Issue

 - Invalid text tags aren't compatible.
