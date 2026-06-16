# RoboticHand
 This open-source robotic hand was designed and developed as part of a masters thesis in manufacturing technology at Aalborg University, 2026.

<img src="images/RoboticHand.PNG" width="425" height="859" />

## Grasping Images
<img src="images/Grasps.png" width="896" height="370" align=center/>

## Setup
    In order to set up the hand for use, you first must identify the Dynamixel Motor IDs that correspond to each degree of actuation. These must be entered into motor_config.py, into the "DEFAULT_CONFIG" field.

    Then ensure that the motors have been connected to the PCB connector for motor power input and that the USB is connected to your machine.

    Then turn on power from a standard lab power supply set at 12V and 10A, and make sure that the motors show a light indicating that they are turning on.

    All digits should be set to their most "open" configuration before initializing main.py. If a calibration.json file already exists in the repository, then the calibration routine will not be executed. To recalibrate, remove the calibration.json file and run:

   ```bash
   python main.py
   ```
    
    When the calibration is finished, the motion editor UI window will open.

## How to use
    If the setup steps above have already been performed, simply run the following command to open the motion editor UI:

   ```bash
   python main.py
   ```


## Dependencies
The code in this repository depends on the following packages:

![Python Version](https://img.shields.io/badge/Python-v.3.10.12%20-blue.svg)\
![Dynamixel SDK Version](https://img.shields.io/badge/Dynamixel_SDK-v.4.0.3%20-blue.svg)\
![PyQT5 Version](https://img.shields.io/badge/PyQT5-v.5.15.11%20-blue.svg)\
![NumPy Version](https://img.shields.io/badge/NumPy-v.1.26.0%20-blue.svg)



## Contributors
This repository and the robotic hand was designed and developed by Anders Bloch Lauridsen, Emil Faldt Jakobsen and Peter Plass Jensen in their Masters Thesis at Aalborg University.

<section id="sec_contributors">
<table>
  <tr> 
    <td align="center"><a target="_blank" rel="noreferrer noopener" href="https://github.com/EmilFaldt"><img src="https://avatars.githubusercontent.com/u/114581690?v=4" width="100px;" alt=""/><br/><sub><b>Emil Faldt</b></sub></a></br><a href="https://github.com/EmilFaldt" title=""></a></td>
    <td align="center"><a target="_blank" rel="noreferrer noopener" href="https://github.com/andersbloch09"><img src="https://avatars.githubusercontent.com/u/93762569?v=4" width="100px;" alt=""/><br/><sub><b>Anders Bloch Lauridsen</b></sub></a></br><a href="https://github.com/andersbloch09" title=""></a></td>
    <td align="center"><a target="_blank" rel="noreferrer noopener" href="https://github.com/Djauvel"><img src="https://avatars.githubusercontent.com/u/93127878?s=400&v=4" width="100px;" alt=""/><br/><sub><b>Peter Plass Jensen</b></sub></a></br><a href="https://github.com/Djauvel" title=""></a></td>
  </tr>
</table>
