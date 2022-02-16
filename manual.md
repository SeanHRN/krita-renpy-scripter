# Generate Ren'Py Scripting
by Sean Castillo
Version 1.0

This plugin uses the layer name syntax for the [Krita Batch Exporter](https://github.com/GDQuest/krita-batch-exporter) by GDQuest to generate a block of text for a Ren'Py script. The block is saved into a file and then automatically opened in the default program for that file extension (e.g. Notepad for .txt on Windows) so that the user may immediately copy and paste the text into a Ren'Py script file. The goal is to coordinate the composed images as they appear in Krita to display the same way in Ren'Py as efficiently as possible by getting the coordinates and doing the bulk of the typing automatically.

The text is formatted for how I script my motion comic in Ren'Py (the major distinction being primarily using `pos()` statements rather than Ren'Py's [usual transforms](https://www.renpy.org/doc/html/transforms.html)). To change the output for your project's needs, edit the `outfile.write()` lines in `writeData()`.

By default, the pos (x,y) coordinates in the block are how the content of each layer appears on Krita's canvas; the coordinates refer to the top left corner of the bounding box for all non-transparent pixels in that layer.

In order for a layer to be included, it must be toggled visible and follow the [krita-batch-exporter syntax](https://github.com/GDquest/krita-batch-exporter/blob/master/batch_exporter/Manual.md),
i.e. contain "e=png" or "e=jpg" directly following the actual name of the layer.

A pause statement is included at the end.

## Properties
 - s  - 'size' in scale percentage
 - m - 'margin' width in pixels

The minimum listed size is used for the Ren'Py block.
This is because I use downscaled versions of my images for Ren'Py (fitted for 1920x1080 px).

Currently, the margin option nudges the (x,y) coordinates of the image up and left that many pixels.

## Ren'Py Format
    # Empty Line
        show background:
            pos (0, 0)
        show character:
            pos (500, 500)
    # Empty Line
        pause
The block starts one indent in because it would be pasted into a Ren'Py script under a label statement.

## Example With Krita
Here's a screenshot of a panel from *Homeless Rice Ninja: The Rocky Road*.
![Screenshot](https://photos.app.goo.gl/TYuChbJQ8ywPDxn58)
[Here's a recording of the panel in motion.](https://youtu.be/c4oeaK74Zl4)

To test this plugin, I remade the panel.
The full-sized Krita document for this image is 5103x2873 px.
![Layer Stack](https://photos.app.goo.gl/4Mv7oWfahgFH599eA)
I renamed the layers to match how I name the images in Ren'Py. For example, p8p3hrn means "Page 8 Panel 3 HRN". I chose 38% as the scale because that fits my target resolution of 1920x1080 px.

Here's the resulting rpblock.txt:

    show p8p3bg:
        pos (0, 0)
    show p8p3mg:
        pos (304, 184)
    show p8p3hh:
        pos (834, 306)
    show p8p3hrn:
        pos (476, 202)
    show p8p3fg:
        pos (0, 87)

    pause

![Made with automatically-generated script.](https://photos.app.goo.gl/yv4jQksq1Px5Pb1e8)

It doesn't have the fog because I handle scrolling graphics separately, but all the other components are properly displayed!

 - For the first version of the image, each component's PNG was manually cropped to reduce empty space. For the remade version, I ran Krita Batch Exporter to get the PNGs with automatic and precise trimming so that the PNGs would work with the coordinates printed by Generate Ren'Py Scripting. That's why there may be slight differences.
 -  37.6249% would be significantly more accurate than 38%, but Krita Batch Exporter doesn't allow non-integer values for percentage, unfortunately.
 - rpblock.txt does start with the empty line, but I don't know how to get that to work in Markdown yet.

## Notes

 - The manual for Krita Batch Exporter is [here](https://github.com/GDQuest/krita-batch-exporter/blob/master/batch_exporter/Manual.md).
 - This plugin allows non-integer values for size percentage via `round()`, but Krita Batch Exporter does not.
 - Metadata tags are case-insensitive in this plugin but case-sensitive in Krita Batch Exporter.
 - If a group layer and its contained layer both have metadata, the group properties have priority.

## Features To Possibly Implement

 - GUI text bar to notify the user of success/failure in export to match Krita Batch Exporter's design. Currently, a separate window opens if the user tries to run the plugin when a Krita file hasn't been opened, and the only notification of success is the automatic file opening.
 - Provide multiple export templates that may be selected with radio buttons.

## That's It!
Feedback would be greatly appreciated.
See more of *Homeless Rice Ninja: The Rocky Road* [here](https://seanhrn.itch.io/homeless-rice-ninja-the-rocky-road). I post character art on my Krita-Artists [page](https://krita-artists.org/u/hydrone/activity/portfolio).
