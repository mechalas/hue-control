# Hue Control 

A Philips Hue Python3 API with command-line client.

*Notice: This project is brand-new and the API is still evolving. Nothing you see here is set in stone, there are no official releases, and you should absolutely not use this as a basis for anything important.*

## Goals

This project aims to provide a complete Hue API for Python3 with an object-oriented interface and classes representing the major data objects used by the Philips Hue bridge. It also intends to provide more than just a raw, low-level API that wraps the bridge REST API. The long-term goal is to provide high-level functionality in addition to the low-level calls, so that developers do not need to write the same code patterns over and over, or be experts at the Hue bridge API in order to produce functional code.

It also provides a command-line client for managing multiple Hue bridges and their objects with a (mostly) simple set of subcommands and options.

## Python Requirements

I've tried to keep Python dependencies to a minimum. You'll need:

* isodate (for parsing ISO 8601 dates and times)
* ssdp (for bridge discovery)

Both can be installed using pip.

## Command-line Client: What's working so far

* Hue bridge discovery
* Hue bridge/account setup (there may be a bug in here)
* Listing most major bridge objects, including:
  * Configuration (and whitelist)
  * Lights
  * Groups
  * Scenes
  * Schedules
  * Sensors
  * Rules
  * Resourcelinks (raw only)
* Light functions:
  * Power on/off 
  * Change brightness, color (and color mode), dynamic effect, alert effect
  * Rename
* Scene functions:
  * Delete
  * Recall/play
  * Rename

Output is messy as many objects the __str__ overloads which are currently printing class decorators and other verbosity that is not human-friendly but useful for debugging and development.

## Bugs and Issue Reports

I can guarantee there are bugs. If you are thinking of filing an issue, chances are it's a little premature to do so because I am refactoring as I go along and with each new piece of the API I learn that I need to rethink what I've done before. Usually just a little, but sometimes, a whole lot. So, yeah, there are bugs. When things stabilize more, then we can talk.

## It would be great if this could...

Yes, it would. But I am not there yet. Right now my priorities are:

1. Getting the core API in place and stabilized.
1. Getting the high-level API at least designed.
1. Cleaning up problems on my own Hue bridges caused by poorly-behaved apps that have abused the API in the past and left me, the user, to deal with it.
1. Not causing those same problems for someone else.


