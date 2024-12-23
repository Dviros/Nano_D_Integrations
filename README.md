# Nano_D_Integrations
This repo is all about integrations revolving the amazing Binaris Nano_D++.

## What integrations are currently supported?
- Apple Music - macOS only

### What do we need to do?
- Set your specific profile with 0 active actions from the keypad
- Download the `profile.json` and the Python script, running it in a terminal using `screen`

### How to use this script?
- Create a new folder and a virtual environment using Python 3:
  ```sh
  python3 -m venv binaris
  source binaris/bin/activate
  ```
- Use pip3 to install:
  ```sh
  pip3 install pyserial esptool
  ```
- Call the script using `screen`:
  ```sh
  screen -dmS myscript python3 runner.py
  ```

### Important notes
1. Only a single app can communicate over serial, meaning that you cannot use the Binaris Configurator together with the script.
2. To kill the script, use `screen -r` and press `ctrl+c`.
3. The script will boot the Nano_D++ in the correct mode using `esptool`.

### Customizing profile.json
You can modify the `profile.json` to suit your specific needs by changing the commands and key mappings.
