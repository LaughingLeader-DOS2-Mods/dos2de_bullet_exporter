# Divinity Bullet Exporter for Blender 2.79

This is a simple addon for Blender 2.79 that allows you to export bullet/bin files for Divinity: Original Sin 2, for both Classic and the Definitive Edition.

## Features:  
* Export Blender Game physics to .bullet, and optionally convert that .bullet to .bin, for the Definitive Edition.
* Automatically rotate the object for DOS2's Y-Up world (Blender is Z-Up).
* Use the layer name or active object name when exporting.


## Installing

### Manual  
* Navigate to [dos2_bullet_exporter.py](https://github.com/LaughingLeader-DOS2-Mods/DOS2-Bullet-Exporter/blob/master/dos2_bullet_exporter.py).
* Right click "Raw", then select "Save Link As...".
* Save the addon somewhere where you can find it again.
* Refer to Blender's guide for installing addons here: [Install from File](https://docs.blender.org/manual/en/latest/preferences/addons.html#header).

## Using this Addon

Once you have the addon installed/activated, select the object you want to export physics for, and select File -> Export -> Divinity Physics.

### Setting up Models for Bullet Creation  
* In Blender, switch the Engine at the top to "Blender Game".
* Select your mesh object, navigate to the "Physics" tab (the last tab).
* Copy these settings for most non-primitive meshes:  
[![](https://i.imgur.com/Zvqfovdl.jpg)](https://i.imgur.com/Zvqfovd.png)
* Export the .bullet file when ready.

#### Compatible Collision Bounds  
* Box
* Convex Hull
* Sphere

The other bound types may cause crashes inside the Divinity Editor.

### Bin Conversion Setup  
* Open dos2_bullet_exporter.py in a text editor.
* Search for `Default Properties Start`. These properties are the default, visible properties on the left when exporting.
* Find the property for `binutil_path`, and change the `default` value to the location of Larian's bin utility program. This program is located in the Definitive Edition editor folder:
```
The Divinity Engine 2\DefEd\LSPakUtilityBulletToPhysX.exe
```
* Now when "Convert to Bin" is enabled, the .bullet file will be created, sent to LSPakUtilityBulletToPhysX to convert it to .bin, and finally deleted.

### Note: Importing Bin Files into The Divinity Engine 2
* As of version 3.6.30.672 (12/11/2018), the "Add Physics Resource" file browser defaults to .bullet types only. You can work around this by manually entering your file names into the open dialog, like so:

[![Importing Bin Files](https://i.imgur.com/PCnqEOVl.jpg)](https://i.imgur.com/PCnqEOV.png)

## Credits
This is a modified version of V0idExp's original bullet exporter addon, located here: [https://github.com/V0idExp/blender-bullet-export](https://github.com/V0idExp/blender-bullet-export)
