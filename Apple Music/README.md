## How to use this script?
- Create a new folder and a virtual environment using python3:
```python3 -m venv binaris```
```source esptool/bin/activate```

- Use pip3 to install:
```pip3 install pyserial esptool```

- Call the script using screen:
```screen -dmS myscript python3 runner.py```


#### Important notes:
1. Only a single app can communicate over serial, meaning that you cannot use the Binaris Configurator together with the script.
2. In order to kill the script, you need to use ```screen -r``` and press ```ctrl+c```.
3. The script will boot the Nano_D++ in the correct mode using the esptool.
