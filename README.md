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

All of these can be installed using pip.

## Bugs and Issue Reports

I can guarantee there are bugs.

## It would be great if this could...

Yes, it would. But I am not there yet. Right now my priorities are:

1. Getting the core API in place and stabilized.
1. Getting the high-level API at least designed.
1. Cleaning up problems on my own Hue bridges caused by poorly-behaved apps that have abused the API in the past and left me, the user, to deal with it.
1. Not causing those same problems for someone else.

# Hue Manager

A command-line client, _huemgr_, for controlling your Hue system with  supports for multiple bridges. Hue Manager has several subcommands that break down into three broad categories:

* Hue Bridge setup and configuration 
* Hue system control and management (lights, groups, scenes, etc.)
* Utility functions

*Hue Manager is a work in progress. There are no official releases yet, and the functionality and interface is still evolving.*

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

### Light Management

These commands modify or manage light devices. A light is any device that can be turned on and off (e.g., the Hue Smart Plug is considered a light).

-----

#### huemgr light

Print a light or lights and their current light state.

```
huemgr light [-b BRIDGE] [-r] [-R] [-s {name,id}] [id [id ...]]
```
All arguments are optional.
| option | description |
|---|---|
| id | Optional list of light IDs |
| -b BRIDGE, --bridge BRIDGE | Bridge to use. Can specify a serial number, friendly name, or IP address |
| -r, --raw  | Print raw response |
| -R, --pretty | Pretty-print raw response |
| -s {name,id}, --sort {name,id} | Sort list by the specified field |

With no arguments, this command will print every light known to the bridge. Otherwise, the lights specified by the **id** list are retrieved. The output can be sorted by either name or id (the default) using **--sort**.

The **--raw** and **--pretty** options print the raw bridge data, as-is or formatted for greater readability, respectively.

A bridge other than the default bridge can be specified with **--bridge**.

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
| -b BRIDGE, --bridge BRIDGE | Bridge to use. Can specify a serial number, friendly name, or IP address |
| -X, --no-scan | Just report the light(s) found during hte last search without starting a new one |

With no arguments, this initiates a search for new lights in range of the bridge. Lights that are not currently "owned" by another Hue bridge will be added to the current bridge and reported. A typical light search runs for between 45 seconds and a minute.

The **--no-scan** option does not start a new search, and instead reports any lights that were found as a result of the _previous_ search.

The Hue bridge automatically adopts any unowned lights that it finds.

If a light was previously owned by another bridge, and it wasn't formally deleted from that bridge before being disconnected, then it may not show in in a search. In that case, you should specify the light's serial number as the **serial** argument. The bridge can search of up to 10 serial numbers at a time.

---

#### light-power

Power lights on and off.

```
huemgr light-power [-h] [-b BRIDGE] [-a ALL] [-t TRANSITION_TIME] [-B [BRIGHTNESS] | -X] [id [id ...]]
```

| option | description |
|---|---|
| id | The ID(s) of the light(s) to control. |
| -a, --all | Control all lights on the bridge. |
| -t TRANSITION_TIME, --transition-time TRANSITION_TIME | Set transition time in seconds. This can be fractional, but the minimum granularity is 1/10th of a second, so .1 seconds (100 ms). This only applies to the **--off** option. |
| -B [BRIGHTNESS], --brightness [BRIGHTNESS] | Turn lights on to the given brightness level. |
| -X, --off | Turn lights off instead of on |

This command turns lights on by default, and off if **--off** is specified. When turning lights off, a transition time can be set using the **--transition-time** option. You can give a fractional number of seconds in 0.1 second increments (a time of 3.27 seconds will be rounded to 3.3).

Lights are turned on to their previous brightness, though this can be overridden with the **--brightness** option, which is specified as a fractional number from 0 to 1. 

> Turning lights off using a transition time sets the power-on brightness to 0, so you'll need to explicitly use **--brightness** when turning them back on.

You must specify either a list of lights to control by their **id**, or **--all** to control all lights.
