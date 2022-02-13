# Generate Ren'Py Scripting
by Sean Castillo

Uses the layer name syntax for krita-batch-exporter by GDQuest
to generate a block of text for a Ren'Py script for moSean comics.

In order for a layer to be utilized, it must be toggled visible
and follow the krita-batch-exporter syntax, i.e. contain "e=png"
or "e=jpg" directly following the actual name of the layer.

The Ren'Py block is populated with pos(x,y) statements that are adjusted
to the top left corner of the bounding box of each layer's contents.

A pause statement is printed at the end.

## Properties
s - 'size' in scale percentage
m - 'margin' width in pixels

The minimum listed size is used for the Ren'Py block.
This is because I use downscaled versions of my images for Ren'Py.

Currently, the margin option nudges the image up and left that many pixels.

## Example
If the layer is named:
'Gaston e=png s=100,50'
