
# TouchPortal-Windows-Media-Mixer

![Downloads](https://img.shields.io/github/downloads/KillerBOSS2019/TouchPortal-Windows-MediaMixer/total)
![Forks](https://img.shields.io/github/forks/KillerBOSS2019/TouchPortal-Windows-MediaMixer)
![Stars](https://img.shields.io/github/stars/KillerBOSS2019/TouchPortal-Windows-MediaMixer)
![License](https://img.shields.io/github/license/KillerBOSS2019/TouchPortal-Windows-MediaMixer)
- [TouchPortal Windows Media Mixer](#TouchPortal-Windows-Media-Mixer)
  - [Description](#description)
  - [Settings Overview](#Settings-Overview)
  - [Features](#Features)
    - [Actions](#actions)
    - [States](#states)
    - [Events](#events)
  - [Installation Guide](#installation)
  - [Bugs and Support](#Bugs-and-Suggestion)
  - [License](#license)
  

# Description
This is an example plugin for Touch Portal. It demonstrates the basics of how to create a plugin, and how to communicate with Touch Portal.
    
## Settings Overview
### ignore list
| Read-only | Type | Default Value |
| --- | --- | --- |
| False | text | Enter '.exe' name seperated by a comma for more then 1 |

A list of processes to ignore when searching for audio processes. This is useful if you have a process that is not an audio process, but is still playing audio. You can add the name of the process to this list and Touch Portal will ignore it when searching for audio processes.


# Features

## Actions
<table>
<tr valign='buttom'><th>Action Name</th><th>Description</th><th>Format</th><th nowrap>Data<br/><div align=left><sub>choices/default (in bold)</th><th>On<br/>Hold</sub></div></th></tr>
<tr valign='top'><td>AppMute</td><td>Mute/Unmute process volume</td><td>[2] Program:[1]</td><td><ul start=0>
<li>[appChoice] Type: choice &nbsp; 
&lt;empty&gt;</li>
<li>[OptionList] Type: choice &nbsp; 
<b>Toggle</b> ['Mute', 'Unmute', 'Toggle']</li>
</ul></td>
<td align=center>No</td>
<tr valign='top'><td>Inc/DecrVol</td><td>Increase/Decrease process volume</td><td>[2][1]Volume to[3]</td><td><ul start=0>
<li>[AppChoice] Type: choice &nbsp; 
&lt;empty&gt;</li>
<li>[OptionList] Type: choice &nbsp; 
<b>Increase</b> ['Increase', 'Decrease', 'Set']</li>
<li>[Volume] Type: number &nbsp; 
<b>10</b> (0-100)</li>
</ul></td>
<td align=center>Yes</td>
<tr valign='top'><td>ChangeOut/Input</td><td>Change Default Audio Devices</td><td>Set Audio [1] [2] to [3]</td><td><ul start=0>
<li>[optionSel] Type: choice &nbsp; 
<b>Pick One</b> ['Output', 'Input']</li>
<li>[deviceOption] Type: choice &nbsp; 
&lt;empty&gt;</li>
<li>[setType] Type: choice &nbsp; 
<b>Default</b> ['Default', 'Communications']</li>
</ul></td>
<td align=center>No</td>
</table>

### States
 <b>Base Id:</b> com.github.KillerBOSS2019.WinMediaMixer.

| Id | Name | Description | DefaultValue |
| --- | --- | --- | --- |
| .state.currentFocusedAPP | FocusedAPP | Volume Mixer: current focused app |  |



### Events

<b>Base Id:</b> com.github.KillerBOSS2019.WinMediaMixer.

<table>
<tr valign='buttom'><th>Id</th><th>Name</th><th nowrap>Evaluated State Id</th><th>Format</th><th>Type</th><th>Choice(s)</th></tr>
<tr valign='top'><td>.event.testEvent</td><td>testEvent</td><td>com.github.KillerBOSS2019.WinMediaMixer.state.currentFocusedAPP</td><td>Test Event $val</td><td>choice</td><td>Test 1, Test 2, Test 3</td></tr>
</table>


# Installation
1. Download .tpp file
2. in TouchPortal gui click gear icon and select 'Import Plugin'
3. Select the .tpp file
4. Click 'Import'
# Bugs and Suggestion
Open an [issue](https://github.com/KillerBOSS2019/TouchPortal-Windows-MediaMixer/issues) or join offical [TouchPortal Discord](https://discord.gg/MgxQb8r) for support.


# License
This plugin is licensed under the [GPL 3.0 License] - see the [LICENSE](LICENSE) file for more information.

