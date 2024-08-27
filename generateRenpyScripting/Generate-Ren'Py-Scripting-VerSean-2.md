

**Generate Ren’Py Scripting** is a [Krita](https://krita.org/en/) plugin that creates text of two different formats:
- Scripting to display images in a Ren’Py project just as they positionally appear as individual layers in a Krita document, calculated to the correct coordinates at whichever scale you specify. Advanced ATL display behavior, such as motions, must still be written manually.
- Scripting to define the images for a Ren’Py project by using the Krita document’s layer stack as the name of the file directory.

For both formats, the resulting text is written onto the plugin’s window, ready to copy and paste into your Ren’Py file!

Additionally, GRS has a calculator to help you determine which scale to use to fit the dimensions of your project.

While this plugin was made initially for my motion graphics comic (composite image panels primarily with `pos` statements), I've expanded it with features that creators of the more standard "visual novel" format Ren'Py projects may find useful too!

VerSean 2 has been fully-reworked to be far more efficient to use, to take sharply reduced space on Krita's docker, to be more feature-packed, and to be highly customizable.
## Batch Exporter Synergy
---
GRS is designed to work in tandem with the [Krita Batch Exporter](https://github.com/GDQuest/krita-batch-exporter) plugin by[ GDQuest](https://www.gdquest.com/), for these reasons:
- That plugin is officially included in Krita.
- Batch exporting is a perfect fit for Ren'Py projects.
- The metadata tag system has several applications that are useful for GRS's needs, detailed below in the [[#Tag System]] section.

## The Two Components
---
**Scripting Generator**

The window for outputting Ren'Py scripting. Access to its settings is also provided there.

**Scale Calculator and Renamer**

- Calculator
	- Use this to check the dimensions of the canvas at different scales.
- Renamer
	- Use this to create copies of the images batch exported by KBE, with KBE's scale syntax removed. Those copies would then be ready to transfer to your Ren'Py project directory.

## The Flow
---
With all those features, using this plugin goes something like this:
1. Use GRS's calculator to determine which image scale you want to use.
2. Update your layers' scale tags.
3. Use KBE to export the images.
4. Use GRS's renamer to make copies of those exported images with the scales removed from the names. Transfer the copies to your Ren'Py project directory.
5. Use GRS's scripting generator to write the display text and/or image definitions. Copy and paste the output into your Ren'Py text files, wherever you need it.

---

# The Features In Detail
- [[#Scripting Generator]]
	- [[#`zoom`, `rotate`, And Additional `pos` Via Transformation Mask]]
	- [[#Texture Overlay Compatibility Feature]]
	- [[#Chain System]]
	- [[#Exclude System]]
	- [[#File Format Priority System]]
	- [[#Settings]]
	- [[#Tag System]]
		- [[#Tags Originally From Krita Batch Exporter]]
		- [[#Additional Tags For Generate Ren'Py Scripting]]
- [[#Scale Calculator]]
- [[#Renamer]]
- [[#Features To Consider / Were Considered]]
- [[#Gone From VerSean 1]]
- [[#Credits]]
- [[#License]]

## Scripting Generator
---
- **ATL Display Scripting**
	- `pos` **Output**
		- To display images at the given x, y coordinates.
		- Three formats: `pos (x, y)` `xpos x ypos y` `at setPos(x, y)`
	- `align` **Output**
		- To display images aligned to divisions on the canvas space. The divisions are picked with the "Spacing Count" slider.
			- For example, 4 spacings would be across `[0.0, 0.333, 0.666, 1.0]` both horizontally and vertically, which would be "rule of thirds" alignment.
				- There is also a dedicated Rule of Thirds toggle, which sets the count to 4.
		- Two formats: `align (x, y)` and `xalign x yalign y`
- **Image Definition**
	- GRS uses Krita's layer stack to determine the directory paths for the image files.
	- **Two Formats**
		- **Normal Images**
			- This is the basic `image exampleguy = "characters/exampleguy.png"` syntax.
		- **Layered Images**
			- This is for Ren'Py's layered image system. Since it works using tags, see [[#Additional Tags For Generate Ren'Py Scripting]] to see how to use it.

## `zoom`, `rotate`, And Additional `pos` Via Transformation Mask
---
Krita's non-destructive editing feature, transformation masks, can be used to declare ATL statements for `zoom` and `rotate`. You can also move an image through the transformation mask to override the `xpos` and `ypos` coordinates used for scripting.

Example: If you use a transformation mask to rotate an image clockwise by 30 degrees, the script for that image gets the statement `rotate 30.0`.
- Note that a direct rotation on the actual image layer as a destructive edit will not yield this piece of output.

## Texture Overlay Compatibility Feature
---
 When a group is tagged as scriptable with `e=`, the coordinates are calculated from all the contents. An issue would arise if a layer being used for a texture overlay were to distort the perceived coordinates; if the texture layer is as big as the canvas, the coordinates would always be retrieved as `(0, 0)`! To prevent that issue, GRS excludes layers that have [Alpha Inheritance](https://docs.krita.org/en/tutorials/clipping_masks_and_alpha_inheritance.html) toggled on, since that is what a texture overlay would be using.

## Chain System
---
Ren'Py supports show statements such as `show exampleguy happy` and image definition states such as `image exampleguy happy = "exampleguy/expression/happy.png"`. I call that "chain naming" or "state naming" since I don't know of an official term.

In order to script that way, GRS uses a special tag: `chain=true`/`ch=t`/`c=t`.
Rules within a path in the layer stack:
- Each layer with the tag set to true will be included in the "chain".
- Each layer without the tag will be excluded from the name of the image, but not the path of the image file.
- Each layer with the `chain` tag set to `false` like so: `chain=false`/`ch=f`/`c=f` will be excluded from both the name of the image and the path of the image file.
#### Example
Suppose the layer stack is this:
`Mark c=t`
`+-- expression`
    `+-- angry e=png c=t`

The display scripting would have:
`show mark angry:`

The image definition scripting would have:
`image mark angry = "mark/expression/angry.png"`

If you meant to use `expression`as a layer group just for organization in Krita, and you don't want it to be in your directory definition. Exclude it by using the tag: `expression c=f`
Now the image definition scripting would be:
`image mark angry = "mark/angry.png"`

## Exclude System
---
If you wish to exclude layer names from the scripting for any reason, this is an option. Maybe, like in the Chain example, you have a group meant solely to organize within the Krita file. The `chain=false` tag can be used that way, but the `exclude=true` tag will give the same result while being easier to understand in some situations, since it's not flavored to chain names.

To be clear, `exclude=true` has the same effect as `chain=false` wherever it is used.

`exclude=true` $\equiv$ `ex=t` $\equiv$ `x=t` $\equiv$ `c=f` $\equiv$ `ch=f` $\equiv$ `chain=false`

## File Format Priority System
---
File Format Priority System: If more than one file format is requested, scripting for both is written, with all but the highest priority commented out:

`webp` > `png` > `jpg/jpeg`

However, `webp` (a popular pick for Ren'Py projects) is exported by Krita but not by KBE; I'll see if I can contribute `webp` support.

## Settings
---
Access to the settings file `configs.json` is provided in the Scripting Generator window. The button will open it in your default editor. Aside from the script output template settings, changes will first be applied when you open a new window scripting.

The `Default` button reverts all settings to their default values.

`configs.json` includes:

| Setting                         | Default Value                                                       | What It Does                                                                                                                                                                                                                                                                                                      |
| ------------------------------- | ------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| string_posxy                    | The default template string for `pos (x, y)`                        | Defines scripting template for `pos (x, y)`                                                                                                                                                                                                                                                                       |
| string_xposxyposy               | The default template string for `xpos x ypos y`                     | Defines scripting template for `xpos x ypos y`                                                                                                                                                                                                                                                                    |
| string_atsetposxy               | The default template string for at `setPos(x, y)`                   | Defines scripting template for `setPos(x, y)`                                                                                                                                                                                                                                                                     |
| string_alignxy                  | The default template string for `align (x, y)`                      | Defines scripting template for `align (x, y)`                                                                                                                                                                                                                                                                     |
| string_xalignxyaligny           | The default template string for `xalign x yalign y`                 | Defines scripting template for `xalign x yalign y`                                                                                                                                                                                                                                                                |
| string_normalimagedef           | The default template string for `image:` (normal image definition.) | Defines scripting template for `image:` (normal image definition)                                                                                                                                                                                                                                                 |
| string_layeredimagedef          | Value not used, but key is.                                         | The name of the setting is used in the code, but the value isn't used; there isn't much to customize with Ren'Py's layered image definition.                                                                                                                                                                      |
| align_decimal_places            | 3                                                                   | Number of decimal places for `align` scripting                                                                                                                                                                                                                                                                    |
| atl_zoom_decimal_places         | 3                                                                   | Number of decimal places for `zoom`                                                                                                                                                                                                                                                                               |
| atl_rotate_decimal_places       | 3                                                                   | Number of decimal places for `rotate`                                                                                                                                                                                                                                                                             |
| directory_starter               | Blank                                                               | Optional field to add a prefix directory to the image definition output. Ren'Py finds the folder `images` automatically and therefore doesn't need `images` in the definitions, but perhaps you may need a different folder at the start, such as `sprites`. This is where you add it.                            |
| lock_windows_to_front           | true                                                                | If `true`, the pop-out windows for this plugin will be pushed to the front as much as the system will allow, though they will also cover non-Krita objects on the screen. If `false`, the windows won't be pushed forward beyond Krita, but they will also move back whenever you click the focus away from them. |
| posxy_button_text               | pos (x, y)                                                          | Text for pos type 1 button                                                                                                                                                                                                                                                                                        |
| xposxyposy_button_text          | xpos x ypos y                                                       | Text for pos type 2 button                                                                                                                                                                                                                                                                                        |
| atsetposxy_button_text          | at setPos(x, y)                                                     | Text for pos type 3 button                                                                                                                                                                                                                                                                                        |
| alignxy_button_text             | align (x, y)                                                        | text for align type 1 button                                                                                                                                                                                                                                                                                      |
| xalignxyaligny_button_text      | xalign x yalign y                                                   | text for align type 2 button                                                                                                                                                                                                                                                                                      |
| customize_button_text           | Customize                                                           | Text for the Customize button                                                                                                                                                                                                                                                                                     |
| script_window_w_size_multiplier | 1.3                                                                 | Initial window width = default width * this value                                                                                                                                                                                                                                                                 |
| script_window_h_size_multiplier | 0.7                                                                 | Initial window height = default height * this value                                                                                                                                                                                                                                                               |
| script_font_size                | 11                                                                  | Output font size                                                                                                                                                                                                                                                                                                  |
| script_preferred_font           | Monospace                                                           | Specific output font Qt will try to find before searching for the system's available monospace font.                                                                                                                                                                                                              |

# Tag System
---
These may be added to the Krita layer names.

### Tags Originally From Krita Batch Exporter

| **Tag**                                                           | **Krita Batch Exporter Application**                                                                                                                         | **Generate Ren'Py Scripting Application**                                                     |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------- |
| `[e=png,jpg]`                                                     | Specifies which of the two supported image file formats to pick for the export, and also marks layers to be be exported with the `Export All Layers` option. | Marks the layer to be used in the Ren'Py scripting.                                           |
| `[s=30,70]`                                                       | Size, a.k.a. Scale in percentage.                                                                                                                            | Adjusts the output coordinates to account for that change.                                    |
| `[p=path/to/custom/export/directory]` or `[p="path with spaces"]` | Custom output path.                                                                                                                                          | Unused.                                                                                       |
| `t=false` or `t=no`                                               | Disable trimming the exported layer to the bounding box of the content.                                                                                      | Sets the output coordinates to 0 because the entire canvas size is used for the image output. |
| `i=false` or `i=no`                                               | Disable parent metadata inheritance for a layer.                                                                                                             | Compatible.                                                                                   |

## Additional Tags For Generate Ren'Py Scripting
---
Most of these are for Ren'Py's [Layered Image](https://www.renpy.org/doc/html/layeredimage.html) feature. Layer names can get too long, and too much writing would defeat the purpose of having automation, so GRS uses a thesaurus system to accept numerous names for the same tasks. This allows you to choose your preferred balance between clear and compact. All of these take `true`/`false` values.

| **Tags**                    | **Generate Ren'Py Scripting Application**                                                                                               |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `rpli`, `rli`, `li`         | layered image (this layer group is the start of the definition)                                                                         |
| `rplidef, rid, rlid, df`    | default                                                                                                                                 |
| `rplial, ral, rpalways, al` | always                                                                                                                                  |
| `rpliatt, rpliat, at`       | attribute                                                                                                                               |
| `rpligroup, rplig, gr`      | group                                                                                                                                   |
| `chain, ch, c`              | Marks the layer's name for the chain system                                                                                             |
| `exclude, ex, x`            | Marks the layer's name to be excluded from output. This has the inverse effect of the `chain` tag. `exclude=true`$\equiv$`chain=false`. |
Internally, any of these tags you use would be converted to the leftmost tag on the list.
This feature has also been used for the `true`/`false` values themselves:

| **Value** | **Can Also Be Named** |
| --------- | --------------------- |
| `true`    | `t`, `yes`, `y`, `1`  |
| `false`   | `f`, `no`, `n`, `0`   |
#### Example
These layer names
`Exampleguy e=png rpli=true`
`Exampleguy e=png rli=y`
`Exampleguy e=png li=t`
are functionally identical.

## Scale Calculator
---
Since images as game/novel assets are often drawn at resolutions greater than the target resolution of the project, GRS has a scale calculator to check the pixel dimensions of the canvas at different scales.
- Between `Width`, `Height`, and `Scale Percentage`: edit one box, and the other two will be updated instantly.
- You may either type in the values or use the buttons for common Ren'Py project dimensions.
	- For example, if you need to know which scale percentage would make the canvas 1080px tall, use the `Height->1080` button.
- The `Scale Percentage` section has a spin box with arrows to increment the values, with keyboard-accessible modifiers:
	- Hold Alt: Increment by 0.01%
	- Hold Shift: Increment by 0.1%
	- Mouse Click/Arrow Key Only: Increment by 1%
	- Hold Ctrl: Increment by 10%

## Renamer
---
Krita Batch Exporter saves the images with a tag that indicates the scale.
Example: `exampleguy_@0.3x.png`  for the layer `exampleguy e=png s=30`.
GRS's Renamer creates copies of the images with the `_@0.3x` portion of the name removed, so that the files are named how you probably want them to be, and ready to transfer to your Ren'Py project. The images are saved in a folder named, in this example, `export_grs_x0.3`. The targeted scale is the one in the Scale Calculator's `Scale Percentage` box. 

### Features To Consider / Were Considered
---
- Add webp support to KBE.
- Ability to modify a Krita document so that a corresponding Ren'Py file is automatically updated, or can be updated at a button press
	- That would be even quicker than the current copy/paste method, and it seems plausible with something like the configs file to hold the file paths, but I think the copy/paste method is a lot safer since it's intrinsically a verification system. On top of that, I think it's likely that most users would have their whole project's images spread across many Krita documents, all to be defined in a single or few Ren'Py file(s).
- `alpha` (Opacity) ATL feature, like how there currently is `zoom` and `rotate`
	- I was interested in making it possible to change the opacity of a layer to your liking within Krita, and then have GRS write the scripting to give the same appearance in Ren'Py. That's not feasible since Krita would also use that opacity condition for the image export.
		- Example if the script allowed this: You choose 50% opacity. The image itself will be exported at 50% opacity, and GRS would also yield the script with `alpha 0.5`, which means in Ren'Py the image would ultimately display at 25% opacity, on top of being capped at a max of 50%.
	- I could add a tag for opacity, but then you might as well just edit the script manually.
- Scripting for Ren'Py's [Built-in Transforms](https://www.renpy.org/doc/html/transforms.html#built-in-transforms)
	- In the context of how those are actually used in projects, I think it would be more efficient to just write those manually along with your dialogue.
- Utilizing KBE's custom path export tag to override the default image definition file location
	- I don't think that's necessary when GRS already bases the image directory on the layer stack, but maybe there's a situation where someone would want that.
- Having an "Are you sure?" verification screen for the Renamer
	- That's probably not necessary since the copy system makes the Renamer non-destructive, and by having to manually type in the scale, the user is already verifying.

### Gone From VerSean 1
---
- The ability to write additional ATL statements as invisible layers. It's less work and cleaner on the Krita document to just write those manually into the scripting. While now the only additional ATL statements are `zoom` and `rotate` via transform mask, those are the two that I was able to fit in a way that meshes with how Krita is used.

## Credits
---
[SeanHRN](https://krita-artists.org/u/seanhrn/activity/portfolio)

[Krita](https://krita.org/en/)

[Function to sort a list with a priority list](https://www.delenamalan.co.za/til/2020-11-13-sorting-a-list-by-priority-in-python.html)
- [Delena Malan](https://github.com/delenamalan)

[Krita Batch Exporter](https://github.com/GDQuest/krita-batch-exporter)
- [GDQuest](https://www.gdquest.com/)

Support from the [Ren'Py Discord](https://discord.com/invite/6ckxWYm) community! 
## License
---
[GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html)