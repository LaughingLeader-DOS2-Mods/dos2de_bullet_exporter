# Divinity Physics Exporter for Blender 2.79

This is a simple addon for Blender 2.79 that allows you to export bullet/bin files for Divinity: Original Sin 2, for both Classic and the Definitive Edition.

## Features:  
* Export Blender Game physics to .bullet, and optionally convert that .bullet to .bin, for the Definitive Edition.
* Automatically rotate the object for DOS2's Y-Up world (Blender is Z-Up).
* Use the layer name or active object name when exporting.  
* _**\*New\***_ Export meshes with minimal setup necessary - The exporter will default to Static/Convex Mesh (or whatever you set it to) and automatically join meshes / parent them if enabled. This all happens to copies, so as to not modify your actual objects.

## Installing

### Manual Method  
* Download this repository as a zip (using the green Clone or download button).
* Save the addon somewhere where you can find it again.
* Extract the zip.
* Copy the folder `dos2de_bullet_exporter`. Make sure this is the folder with the scripts under it (dos2de_bullet_exporter\__init__.py etc).
* Paste the `dos2de_bullet_exporter` folder into your addons folder. Default pathway:
```
C:\Users\Username\AppData\Roaming\Blender Foundation\Blender\2.79\scripts\addons\
```
* (Optional) Refer to Blender's guide for installing addons here: [Install from File](https://docs.blender.org/manual/en/latest/preferences/addons.html#header). It has a tip section for setting up a separate scripts/addons folder, outside of your appdata.

### Cloning  
* In Blender, navigate to File -> User Preferences -> File.
* The pathway for "Scripts" is where Blender will read new addon folders from. Add a pathway if it's blank.
* [Clone the repository](https://help.github.com/articles/cloning-a-repository/).
* Create a junction to the `dos2de_bullet_exporter` inside your scripts/addons folder.
  * You can create a junction with this command line command:
```
mklink /j "C:\Path1\dos2de_bullet_exporter" "C:\Path2\scripts\addons\dos2de_bullet_exporter"
```
| Rename | Description |
| --- | ----------- |
| Path1 | This should be the path where you cloned the repo. We want to junction the io_scene_dos2de folder inside that contains all the py scripts.|
| Path2 | This is where your scripts/addons folder for Blender is. Either the AppData folder, or the custom scripts folder you set. We want to junction the dos2de_bullet_exporter folder with the py scripts to this folder. |
  * Alternatively, this program allows junction/symlink creation via right clicking files/folders in a file explorer: [Link Shell Extension](http://schinagl.priv.at/nt/hardlinkshellext/linkshellextension.html#download)
    * With this program installed, right click the io_scene_dos2de folder and select "Pick Link Source", then go to scripts/addons, right click the background, and select Drop As... -> Junction.

### Activating the Addon  
* In Blender, navigate to File -> User Preferences -> Add-ons
* Either search for "Divinity", or click Community, then Import-Export.
* Check the checkbox next to "Divinity Physics Exporter".

## Using this Addon

### Exporting
To export physics files, simply click on File -> Export -> Divinity Physics.

By default, the exporter will export all visible meshes on active layers using the default physics settings set in the addon preferences (Static physics, Convex Hull shape). These settings are the most commonly used ones for exporting to the Divinity Engine. Convex Hull uses the shape of your mesh for the shape of the physics.

### Automatic Bin Conversion
Once you have the addon installed/activated, be sure to check out the Preferences screen (expand the dropdown For Divinity Physics Exporter in your User Preferences) to point it to LSPakUtilityBulletToPhysX.exe if you want to convert your .bullet files to .bin (what Divinity does when importing .bullet).

By default, LSPakUtilityBulletToPhysX.exe is located at:
```
The Divinity Engine 2\DefEd\LSPakUtilityBulletToPhysX.exe
```

### Setting up Models for Bullet Creation  
As of 6/12/2019, this addon no longer requires you to set up your models, and will do some default things to speed up the process for you:

* Combine Visible Meshes  
This addon creates temporary copies which it then exports. By enabling this option, the mesh copies will all be joined into one mesh, saving you the step of having to possibly duplicate your meshes and join them separately (if you wanted to keep them separate in the actual visual resource).

* Automatic Armature Parenting  
The mesh copies created will be parented to an armature if not already. This is purely for the Blender Game bullet exporter, but it saves you from having to do it yourself.

* Default to Project Folder  
If the [Divinity Collada Exporter](https://github.com/LaughingLeader-DOS2-Mods/dos2de_collada_exporter) is active and set up with project folders, this addon will find the Assets/Physics folder and default to that location if this setting is enabled.

### Note: Importing Bin Files into The Divinity Engine 2
* As of version 3.6.30.672 (12/11/2018), the "Add Physics Resource" file browser defaults to .bullet types only. You can work around this by manually entering your file names into the open dialog, like so:

[![Importing Bin Files](https://i.imgur.com/PCnqEOVl.jpg)](https://i.imgur.com/PCnqEOV.png)

Overwriting the bins directly automatically updates the resources, whereas overwriting the bullet resources instead _does not_ force the bins to be reconverted in the editor.  
For that reason, I recommend setting up and using the bin conversion option in the exporter, as it saves you the pain of having to reimport/delete your physics resources in the Divinity Engine to update them.

## Credits
This is a modified version of V0idExp's original bullet exporter addon, located here: [https://github.com/V0idExp/blender-bullet-export](https://github.com/V0idExp/blender-bullet-export)
