# Hue Control 

A Philips Hue Python3 API with command-line client.

*Notice: This project is brand-new and the API is still evolving. Nothing you see here is set in stone, there are no official releases, and you should absolutely not use this as a basis for anything important.*

[Skip to the command-line client documentation.](#hue-manager)

## Goals

This project aims to provide a complete Hue API for Python3 with an object-oriented interface and classes representing the major data objects used by the Philips Hue bridge. It also intends to provide more than just a raw, low-level API that wraps the bridge REST API. The long-term goal is to provide high-level functionality in addition to the low-level calls, so that developers do not need to write the same code patterns over and over, or be experts at the Hue bridge API in order to produce functional code.

It also provides a command-line client for managing multiple Hue bridges and their objects with a (mostly) simple set of subcommands and options.

## Python Requirements

I've tried to keep Python dependencies to a minimum. You'll need:

* isodate (for parsing ISO 8601 dates and times)
* requests 
* ssdp (for bridge discovery)

All of these can be installed using pip:

`$ pip3 install ssdp isodate requests`

## Bugs and Issue Reports

I can guarantee there are bugs.

# Hue Manager

A command-line client, _huemgr_, for controlling your Hue system with  supports for multiple bridges. Hue Manager has several subcommands that break down into three broad categories:

* Hue Bridge setup and configuration 
* Hue system control and management (lights, groups, scenes, etc.)
* Utility functions

> Hue Manager is a work in progress. There are no official releases yet, and the functionality and interface are still evolving.

## Getting Started

Use the `bridge-search` command to locate your bridge. If your bridge is not brand new, you can probably do a quick search which queries the MeetHue portal. This method won't return a bridge name, but it will give you the serial number and IP address. For example:

```
$ ./huemgr bridge-search --quick
Serial number f81270b97f9a at 10.0.0.1
Serial number 3d812d1f6c18 at 10.0.0.2
```

If the quick search fails, you can do a full search which will take about 30 seconds. A full search may not find all your bridges on the first try, so you can repeat it or specify a longer search interval.



_Note: The above serial numbers and IP addresses are made up for this example._

Once you have identified the bridge you wish to manage, use the `bridge-register` command.

```
$ ./huemgr bridge-register 10.0.0.1
Registering a new user on bridge at 10.0.0.1
Press the link button on the and hit <ENTER> to continue
```

Press the button on the bridge and Hue Manager will be registered to communicate with it.

Your bridge definitions are stored in $HOME/.huemgr using the INI file format. You can make changes here, but in general it's best to let Hue Manager do the work.

Hue Manager understands that a bridge's IP address may change, especially if it's using DHCP to get its address (which they are configured to do by default). If it detects an address change, it will try to locate the bridge on the network and will update the .huemgr configuration file, accordingly.

## Command Reference

> This documentation is not complete. For the full set of commands, see `huemgr --help`, though not all of them have been fully implemented.

* [Group management](#group-management)
* [Light management](#light-management)
* [Scene management](#scene-management)

----

### Group Management

* [**huemgr group**](#huemgr-group): show group information
* [**huemgr group-add**](#huemgr-group-add): add a group
* [**huemgr group-delete**](#huemgr-group-delete): delete a group
* [**huemgr group-lights**](#huemgr-group-lights): add/remove lights from a group
* [**huemgr group-rename**](#huemgr-group-rename): rename a group

#### huemgr group

Print group information and membership.

`usage: huemgr group [-b BRIDGE] [-r] [-R] [-s {name,id,type}] [id [id ...]]`

| option | description|
|---|---|
| id | Optional list of group IDs |
| -b BRIDGE<br/>--bridge BRIDGE | Bridge to use. Can specify a serial number, friendly name, or IP address |
| -r<br/>--raw  | Print raw response |
| -R<br/>--pretty | Like **--raw** but pretty-print the response |
| -s FIELD<br/>--sort FIELD | Sort list by the specified field. Can be one of: name, id, type |

With no arguments, this command will print every group known to the bridge along with its group type and member lights. Otherwise, the groups specified by the **id** list are retrieved. The output can be sorted by either name, id (the default), or the group type using **--sort**.

The **--raw** and **--pretty** options print the raw bridge data, as-is or formatted for greater readability, respectively.

Member lights are printed along with their current light state. The light state includes whether the light is on or off, its brightness and color settings, along with an approximate color name for color lights. See [Color Names](#color-names) for more information on how names are chosen.

----

#### huemgr group-add

Create a light group

`huemgr group-add [-b BRIDGE] [-c ROOM_CLASS] [-t TYPE] name lightid [lightid ...]`

| option | description |
|----|----|
| name | The name for the group. |
| lightid | One or more light ID's to add to the group. |
| -b BRIDGE<br/>--bridge BRIDGE | Bridge to use. Can specify a serial number, friendly name, or IP address |
| -c CLASS<br/>--room-class CLASS | An optional room class. Only valid when the group **--type** is Room. For a list of supported classes, run `huemgr room-classes`. If not specified, the room class defaults to Other. |
| -t GROUPTYPE<br/>--type GROUPTYPE | Set an optional group type, which can be one of: LightGroup, Room, Entertainment, Zone. If not specified, the group type defaults to LightGroup. |

----

#### huemgr group-delete

Delete a group.

`huemgr group-delete [-h] [-b BRIDGE] id [id ...]`

| option | description |
|----|----|
| id | The ID(s) of the group(s) to delete. |
| -b BRIDGE<br/>--bridge BRIDGE | Bridge to use. Can specify a serial number, friendly name, or IP address |

----

#### huemgr group-lights

Add, remove, and set the members of a light group.

`huemgr group-lights [-b BRIDGE] -g GROUPID [-a LIGHTID [LIGHTID ...]] [ -r LIGHTID [LIGHTID ...]] [-s LIGHTID [LIGHTID ...]]`

| option | description|
|---|---|
| id | Optional list of group IDs |
| -b BRIDGE<br/>--bridge BRIDGE | Bridge to use. Can specify a serial number, friendly name, or IP address |
| -a ID ...<br/>--add ID ... | Add one or more lights to the group |
| -g ID<br/>--groupid ID | **Required.** The ID of the group to modify |
| -r ID ...<br/>--remove ID ... | Remove one or more lights from the group |
| -s ID ...<br/>--set ID ... | Set the group membership to the given lights. Cannot be combined with **--add** or **--remove** |

This command edits the lights that are members of the group given by **--groupid**. THe **--groupid** argument is required.

You can both **--add** and **--remove** lights in one command, but these options cannot be combined with **--set**. The **--set** options explicitly sets the membership list to the given light ID's, completely replacing the old list with the new.

> A given light cannot be a member of more than one group with the type "Room". This restriction does not hold for other group types.

----

#### huemgr group-rename

Rename a group.

```
huemgr group-rename [-b BRIDGE] id name
```

| option | description |
|----|----|
| id | ID of group to rename |
| name | The new name for the group |
| -b BRIDGE<br/>--bridge BRIDGE | Bridge to use. Can specify a serial number, friendly name, or IP address |

Changes the name of group ID **id** to **name**.

----

### Light Management

These commands modify or manage light devices. A light is any device that can be turned on and off (e.g., the Hue Smart Plug is considered a light).

* [**huemgr light**](#huemgr-light): show light information
* [**huemgr light-add**](#huemgr-light-add): search for and add new lights
* [**huemgr light-power**](#huemgr-light-power): turn lights on and off
* [**huemgr light-rename**](#huemgr-light-rename): rename a light
* [**huemgr light-set**](#huemgr-light-set): set a light's state

-----

#### huemgr light

Print light information and state.

```
huemgr light [-b BRIDGE] [-r] [-R] [ -O | -X ] [-s {name,id}] [id [id ...]]
```
All arguments are optional.
| option | description |
|---|---|
| id | Optional list of light IDs |
| -b BRIDGE<br/>--bridge BRIDGE | Bridge to use. Can specify a serial number, friendly name, or IP address |
| -r<br/>--raw  | Print raw response |
| -O<br/>--on | Only show lights that are reachable and on. Cannot be combined with **--off** |
| -X<br/>--off | Only show lights that are reachable and off. Cannot be combined with **--on** |
| -R<br/>--pretty | Like **--raw** but pretty-print the results |
| -s FIELD<br/>--sort FIELD | Sort list by the specified field. Can be one of: name, id |

With no arguments, this command will print every light known to the bridge. Otherwise, the lights specified by the **id** list are retrieved. The output can be sorted by either name or id (the default) using **--sort**.

The **--raw** and **--pretty** options print the raw bridge data, as-is or formatted for greater readability, respectively.

The light state includes whether the light is on or off, its brightness and color settings, and an approximate color name for color lights. See [Color Names](#color-names) for more information on how names are chosen.

-----

#### huemgr light-add

Search for new lights and add them to the bridge. Use this to start a search for new lights, or to report lights that were discovered after the last search. Lights can also be added using their serial numbers.

Note: The act of searching for lights automatically adds them to the bridge.

```
huemgr light-add [-b BRIDGE] [-X] [serial [serial ...]]
```

| option | description |
|----|----|
| serial | Optional list of serial numbers to add (maximum of 10) |
| -b BRIDGE<br/>--bridge BRIDGE | Bridge to use. Can specify a serial number, friendly name, or IP address |
| -X<br/>--no-scan | Just report the light(s) found during hte last search without starting a new one |

With no arguments, this initiates a search for new lights in range of the bridge. Lights that are not currently "owned" by another Hue bridge will be added to the current bridge and reported. A typical light search runs for between 45 seconds and a minute.

The **--no-scan** option does not start a new search, and instead reports any lights that were found as a result of the _previous_ search.

The Hue bridge automatically adopts any unowned lights that it finds.

If a light was previously owned by another bridge, and it wasn't formally deleted from that bridge before being disconnected, then it may not show in in a search. In that case, you should specify the light's serial number as the **serial** argument. The bridge can search of up to 10 serial numbers at a time.

---

#### huemgr light-power

Power lights on and off.

```
huemgr light-power [-h] [-b BRIDGE] [-a ALL] [-t TRANSITION_TIME] [-B [BRIGHTNESS] | -X] [id [id ...]]
```

| option | description |
|---|---|
| id | The ID(s) of the light(s) to control. |
| -a<br/>--all | Control all lights on the bridge. |
| -b BRIDGE<br/>--bridge BRIDGE | Bridge to use. Can specify a serial number, friendly name, or IP address |
| -t SEC<br/>--transition-time SEC | Set transition time in seconds when turning a light off. This can be fractional in 0.1 second increments. This only applies to the **--off** option. |
| -B BRIGHTNESS<br/>--brightness BRIGHTNESS | Turn lights on to the given brightness level. |
| -X<br/>--off | Turn lights off instead of on |

This command turns lights on by default, and off if **--off** is specified. When turning lights off, a transition time can be set using the **--transition-time** option. You can give a fractional number of seconds in 0.1 second increments (a time of 3.27 seconds will be rounded to 3.3).

Lights are turned on to their previous brightness, though this can be overridden with the **--brightness** option, which is specified as a fractional number from 0 to 1. 

> Turning lights off using a transition time sets the power-on brightness to 0, so you'll need to explicitly use **--brightness** when turning them back on.

You must specify either a list of lights to control by their **id**, or **--all** to control all lights.

----

#### huemgr light-rename

Rename a light.

```
huemgr light-rename [-b BRIDGE] id name
```

| option | description |
|----|----|
| id | ID of light to rename |
| name | The new name for the light |
| -b BRIDGE<br/>--bridge BRIDGE | Bridge to use. Can specify a serial number, friendly name, or IP address |

Changes the name of light ID **id** to **name**.

----

#### huemgr light-set

Set a light's color, brightness, effect, and alert mode.

```
usage: huemgr light-set [-h] [-b BRIDGE] [-a] [-n COLOR_NAME] [-c COLOR_TEMPERATURE] [--xy XY] [-H HUE] [-S SATURATION] [-B BRIGHTNESS] [-A {none,select,lselect}] [-e {none,colorloop}] [-t TRANSITION_TIME] [id [id ...]]
```

| option | description |
|---|---|
| *General options* |
| -a<br/>--all | Set state for all lights on the bridge |
| -b BRIDGE<br/>--bridge BRIDGE | Bridge to use. Can specify a serial number, friendly name, or IP address |
|  -t SEC<br/>--transition-time SEC | Set transition time in seconds. Can be fractional in 0.1 second increments. |
| *Color options* |
| -c KELVIN<br/>--color-temperature KELVIN | Set a light color temperature in Kelvin from 2000 to 6500, or specify a +/- increment. |
| -n NAME<br/>--color-name NAME | Set a light to a known, named color (see [huemgr color-name](#huemgr-color-name) |
| --xy X,Y | Set xy color coordinates as a comma-separated pair, or specify a +/- increment. Cannot be combined with other color modes. |
| -B BRIGHTNESS<br/>--brightness BRIGHTNESS | Set a brightness from 0 to 1, or specify a +/- increment. |
| -H HUE<br/>--hue HUE | Set a color hue from 0 to 360, or specify a +/- increment. Hue can be fractional. Cannot be combined with other color modes. |
| -S SATURATION<br/>--saturation SATURATION | Set a color saturation from 0 to 1, or specify a +/- increment. Cannot be combined with other color modes (e.g. --xy or -c)
| *Effect options* |
| -A MODE<br/>--alert MODE | Set an alert effect. Can be "none" to cancel any active effects, "select" to flash off and on once, and "lselect" to flash off and on for 15 seconds. |
| -e MODE<br/>--dynamic-effect MODE | Set a dynamic effect. Can be "none" to cancel the active effect, or "colorloop" to cycle through all hues at the current brightness and saturation. The "colorloop" mode runs until it is canceled. |

This command sets the state of one or more lights. You can specify lights by **id**, or provide the **--all** option to set the state for all lights.

Lights will ignore states that do not apply to them. For example, a Hue Smart Plug will ignore all options, and a Hue White light only supports alert mode, transition time, and brightness.

Color temperatures are specified in degrees Kelvin, with 2000 corresponding to a very warm white, and 6500 corresponding to a cool white.

Color modes cannot be combined. Choosing a color option sets the specific color mode of the light (assuming that mode is supported).

| Color Options | Color Mode |
|---|---|
| --hue, --sat | HSB |
| --xy | XY |
| --color-temperature | Color Temperature |

A color can also be selected by name with the **--color-name** options. Selecting a color in this manner will set the color mode to HSB. See [Color Names](#color-names) for more information.

### Scene Management

* [huemgr scene](#huemgr-scene)
* [huemgr scene-delete](#huemgr-scene-delete)
* [huemgr scene-dump](#huemgr-scene-dump)
* [huemgr scene-load](#huemgr-scene-load)
* [huemgr scene-play](#huemgr-scene-play)
* huemgr scene-rename

----

#### huemgr scene

Print scene summaries with or without preset details.

`huemgr scene [-b BRIDGE] [-r] [-R] [-i] [-x] [-S] [-s {name,id,lastupdated}] [id [id ...]]`

| option | description |
|----|----|
| id | An optional list of scene IDs |
| -b BRIDGE<br/>--bridge BRIDGE | Bridge to use. Can specify a serial number, friendly name, or IP address |
| -i<br/>--ignore-autogenerated | Filter out the Hue app's auto-generated scenes from the scene list. These include the "standard" Hue app scenes (Bright, Concentrate, Dimmed, Energize, Nightlight, Read, Relax) that it auto-creates for each room, as well as the "Last on state" scenes used by dimmer switches. This may accidentally filter out scenes created by the user if they use a name that matches one of the standard scenes. |
| -r<br/>--raw  | Print raw response |
| -s FIELD<br/>--sort FIELD | Sort the output by one of the following fields: id, name, lastupdated. The default is to sort by ID. |
| -x<br/>--no-light-states | In a full scene listing, don't show the light state presets. Can't be combined with **--summary**.|
| -R<br/>--pretty | Like **--raw** but pretty-print the response |
| -S<br/>--summary | Only print a summary of the scene (id, name, type, and list of light IDs in the scene). Can't be combined with **--no-light-states**. |

Without any arguments, this command prints a complete listing of all scenes on the brigde, along with the light presets for each light in the scene. *This can take a very long time, as scene light states must be fetched individually. The more scenes you have on the bridge, the longer it takes. Since the Hue app creates multiple "default" scenes for each room, the more rooms you have, the more scenes you have, too, further slowing down this operation.*

For large Hue installs, it's generally better to use the **--summary** or **--no-light-states** options, in concert with the **--ignore-autogenerated** option, to get a quick listing of the scenes that are most important. Then re-run the command, providing a scene ID or list of IDs, to get detailed listings of the desired scenes.

Scene listings includes the following:

 * scene ID, which is a typically a random string up to 16 characters long
 * name
 * scene type
 * room class, for scenes that are type **Room**
 * if the scene is locked, the word "LOCKED"
 * the light IDs in the scene (**--summary** option only)
 * the lights in the scene (unless **--summary** is given):
   * light ID
   * name
   * bulb type
   * light state preset (unless **--no-light-state** is given)

A locked scene is one that is part of a rule or schedule. To unlock a scene, you must remove it from all of the rules and schedules that reference it.

----

#### huemgr scene-delete

Delete a scene from the bridge.

`huemgr scene-delete [-b BRIDGE] id [id ...]`

| option | description |
|----|----|
| id | The ID(s) of the scene(s) to delete. |
| -b BRIDGE<br/>--bridge BRIDGE | Bridge to use. Can specify a serial number, friendly name, or IP address |

Deletes one or more scenes from the bridge. Note that scenes that are locked cannot be deleted (see [huemgr scene](#huemgr-scene)).

----

#### huemgr scene-dump

Dump a scene definition as an INI file.

`huemgr scene-dump [-b BRIDGE] [-f FILE] id`

| option | description |
|----|----|
| id | The ID(s) of the scene(s) to delete. |
| -b BRIDGE<br/>--bridge BRIDGE | Bridge to use. Can specify a serial number, friendly name, or IP address |
| -f FILE<br/>--file FILE | Write the output to FILE. Without this option, the scene definition is printed to stdout. |

This command dumps a scene definition as an INI file. This file can be edited and then read back with [huemgr scene-load](#huemgr-scene-load) to modify the scene. This provides a simple method of making large-scale changes to a scene definition.

Certain scene parameters cannot be changed once the scene has been created. For informational purposes, these parameters are shown in a section named `[readonly]`:

 * recycle
 * type

See [huemgr scene-load](#huemgr-scene-load) for a full description of the INI file, and the meaning of each parameter including the above.

Some very old scenes, created before API version 1.11, may not have lightstates and will add the following to the `[readonly]` section:

`lightstates = false`

These scenes use version 1 of the scene format, where lightstates were stored in the cloud and sync'd to the Hue app. These scenes cannot be modified, only deleted.

----

#### huemgr scene-load

Create a new scene or modify an existing scene from an INI definition file.

`huemgr scene-load [-b BRIDGE] [-s SCENE_ID] file`

| option | description |
|----|----|
| file | The INI file containing a scene definition to load. |
| -b BRIDGE<br/>--bridge BRIDGE | Bridge to use. Can specify a serial number, friendly name, or IP address |
| -s SCENE_ID<br/>--scene-id SCENE_ID | An optional scene ID for a scene to replace. |

This command reads in a scene definition in INI format and either creates a new scene, or if the **--scene-id** parameter is given, replaces an existing scene with the new definition. When replacing an existing scene, the old light presets are completely replaced with the new ones, so incremental changes are not possible (you must completely define the replacement scene). For example, if you define a scene with light presets for lights 1, 2, and 5, and later redefine it with just 1 and 5, then light 2 will be removed from the scene.

##### INI File Format

the `huemgr scene-load` command expects to see an INI-style file with a `[scene]` section, an optional `[appdata]` section, and individual sections sections named `[light ID]` to describe a light preset state for the light with light id ID.

The `[scene]` section takes the following parameters:

| scene parameter | type | description |
|----|----|----|
| group | string | (required for GroupScenes) The group ID of the group that the scene is associated with. This only applies to scenes with a **type** of `GroupScene`. |
| name | string| (required) The name for the scene. Names can be up to 32 characters long. |
| recycle | boolean | (optional, new scenes only) User-created scenes are set to `false` by default. A scene with **recycle** set to `true` may be automatically deleted by the bridge when a new scene definition would exceed the bridge maximums (currently 200 scenes, and a total of 2048 light states across all scenes). |
| transitiontime | float | (optional) A transition time for the scene in seconds from 0 to . The minimum granularity is 1/10th of a second or 0.1 and values will be rounded to the nearest 1/10th. The default transition time is 0.4 seconds. |
| type | string | (optional, new scenes only) The scene type, which is either `GroupScene` or `LightScene`. If ommitted, the type defaults to `LightScene`. See below for a discussion on the two scene types. |

The `[appdata]` section is optional, but if it's present it takes the following two parameters, both of which are required:

| appdata parameter | type | description |
|----|----|----|
| version | integer | (required) The scene version number.
| data | string | (required) Vendor-specific data to associate with the scene. |

A scene's appdata is the responsibility of the application that created it. It is not used by the bridge, and serves only as a simple data store for the application itself.

The lightstates for each light participating in the scene are given in separate `[light ID]` sections, where the ID is replaced by the light's id (e.g. `[light 4]` for the light with ID 4). Each section can contain the following parameters:

| appdata parameter | type | color mode | description |
|----|----|----|----|
| bri | float | All | The light brightness between 0 and 1, with 0 being minimum brightness and 1 being full brightness. *Note that a brightness of 0 is not off!* |
| ct | integer | CT | A color temperature for the light in mireds (M). This is an integer from 153 (cool white) to 500 (warm white). Color temperature in Kelvin can be calculated from mireds as follows:<br/> K = 10<sup>6</sup>/M|.
| hue | float | HSB | The color hue as a floating point number between 0 and 360 (note that 360 is the same hue as 0). |
| on | bool | &mdash; | Set to `true` if the light should be turned on, and `false` if it should be turned off. |
| sat | float | HSB | The color saturation |
| transitiontime | float | &mdash; | (optional) A transition time for the light in seconds from 0 to 6553.5. The finest granularity is 0.1 and values will be rounded to the nearest interval (e.g., 4.36 will become 4.4). The default transition time is 0.4 seconds. |
| x | float | xy | The x coordinate of a color in the CIE xyY color space. This is a floating point number between 0 and 1. |
| y | float | xy | The y coordinate of a color in the CIE xyY color space. This is a floating point number between 0 and 1. |

##### Color Modes

You cannot combine color modes in a light state. If you specify a hue, which is the HSB (hue, saturation, brightness) color mode, you can't also provide an x or y coordinate in the CIE color space (the xy color mode). You also cannot combine a color temperature with a color setting.

Not all lights can use all color modes. The Hue Smart Plug, for instance, can't use any parameter other than **on**, the 1st generation Light Strips support HSB and xy colors but not color temperature, and so on. Lights will ignore parameters that do not apply to them.

##### Scene Types

_GroupScene_

A GroupScene is associated with a group on the bridge, and all lights in the group participate in the scene. If a light is not defined in the INI file, then its current state is used. Once a GroupScene is created, the group it's associated with cannot be changed.

When a group is deleted, all GroupScenes associated with that group are also deleted.

_LightScene_

A LightScene is the default scene type, and it can contain arbitrary lights. Only lightstates that are explicitly defined will be stored in the scene.

##### Example

This scene turns on a Hue Smart Plug, and four lights to about 2700K (the color of a typical incandescent lamp).

```
[scene]
name = Basement On
type = LightScene

[light 4]
on = True
bri = 1
ct = 370

[light 5]
on = True
bri = 1
ct = 370

[light 6]
on = True
bri = 1
ct = 370

[light 7]
on = True
bri = 1
ct = 370

; Smart plug
[light 45]
on = True
```

This configuration fades a light up over the course of 30 minutes:

```
[scene]
name = Wakeup 

; Hue white bulb
[light 2]
on = True
transitiontime = 1800
bri = 1
```

----

#### huemgr scene-play

Play a light scene.

`huemgr scene-play [-h] [-b BRIDGE] id [id ...]`

| option | description |
|----|----|
| id | The scene ID(s) of the scene(s) to recall |
| -b BRIDGE<br/>--bridge BRIDGE | Bridge to use. Can specify a serial number, friendly name, or IP address |

This command plays the given scenes. Scenes are recalled in the order they are given, so if a light appears in multiple scenes the last scene will win.

# Color Names

The color naming scheme used by Hue Manager and the huectl Python module is taken from the [Martian Color Wheel](http://warrenmars.com/visual_art/theory/colour_wheel/colour_wheel.htm), a 24-hue color wheel with two shades and two saturation levels per hue, designed by artist Warren Mars.

The names on this color wheel do not always accurately reflect the color emitted by a Hue lamp for a number of reasons, not the least of which is that the light color we see is influenced heavily by the surfaces it illuminates, but it does come close enough and functions as a reasonable "language" for describing colors in terms that are easily understood by a lay person. It is also the only serious attempt to assign workable, human-friendly names to colors via a (reasonably) [scientific process](http://warrenmars.com/visual_art/theory/colour_wheel/evolution/evolution.htm).

It's not perfect, but it's better than pretty much anything else out there.