# Change Log

# v1.6
 - Added Additional ATL System.

# v1.5.3
 - Fixed error from using `t=false`.

# v1.5.2
 - Added handling for when user tries to use the image renamer when none of the layer names is valid
 - Added handling for when user tries to use the image renamer when a document isn't active

# v1.5.1
 - Changed an instance of int() to float() for scale to correct an exporting issue.
 - Altered the smallest scale calculation to accommodate 200% (from 100%).

# v1.5
 - Calculator Rework
     - Now uses floats because the Batch Exporter will soon allow non-whole number scale percentages.
     - Modifier key increment system: Hold a key to change the scale box's arrow increments.
         - Alt: 0.01%
         - Shift: 0.1%
         - Default: 1.0%
         - Ctrl: 10%
     - Width and Height numbers are now in editable text boxes.
         - Edit Width: Scale and Height will automatically update.
         - Edit Height: Scale and Width will automatically update.
     - Scale limit increased from 100% to 200% to allow dimension calculation for small upscaling.
     - Added a tooltip.
 - Added [xalign x yalign y] as an export option.
 - Layer name parsing now uses a dictionary system to be more \
robust and better for additional tag implementations.
# v1.4
 - `Rename Batch-Exported Files` is now a button instead of a checkbox.
 - `Rename Batch-Exported Files` now works with layers that were exported as groups into folders.
 - Minor code improvements: `"/"` -> `os.sep` and `min()` instead of a loop.

# v1.3
 - Fixed size parsing issue.
 - New feature: `Rename Batch-Exported Files` (until I have a more accurate name): \
 Copies the smallest scale batch-exported images to a folder where they don't have \
 the Batch Exporter's `_x[scale]` suffix in their names.

# v1.1.2
 - Added the in-Krita manual html file.

# v1.1
 - Scale Percentage Size Calculator properly updates the dimensions when a \
new document is loaded, when the user switches between active documents, \
and when all documents are closed.
 - Several GUI tweaks:
     - The export options are on a single line.
     - Instances of `pos(x, y)` and `align(x, y)` have been given a space between pos/align and the left parenthesis to look a bit nicer and be consistent with the output style: `pos (x, y)` and `align (x, y)`
     - `Scale Dimensions` is now capitalized to be consistent with the rest of the text.
