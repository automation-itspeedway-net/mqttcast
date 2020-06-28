# mqttcast
Control all of your Chromecast and google home speakers from MQTT.

STATUS:  STABLE BETA
VERSION: 0.3

KNOWN BUGS:
* chromecast/{name}/device-status is OBJECT not JSON
* chromecast/{name}/cast-status is OBJECT not JSON
* Has not been tested as a daemon
* Logging is currently to screen.
* Device LWT is not currently implemented
* Application LWT is not implemented

PRE-REQUISITES:

    Python version 3

INSTALLATION:

    mkdir ~/modules
    cd ~/modules
    python3 -m venv venv
    . ./venv/bin/activate
    
    pip install wheel
    pip install paho-mqtt
    pip install pychromecast
    
    git clone https://github.com/automation-itspeedway-net/mqttcast.git

CONFIGURATION:

Configuration is only required if mqttcast is not installed on your MQTT server, or you are using authentication. In these cases, you must create a config.ini file in the mqttcast folder containing the required information:

    nano ~/modules/mqttcast/config.ini
    
    [mqtt]
    host=192.168.1.1
    port=1883
    username=MyUsername
    password=MyPassword

RUN AS AN APPLICATION:

    cd ~/modules
    ./venv/bin/python mqttcast/mqttcast.py

RUN AS A DAEMON (SERVICE):

    Untested

MQTT

mqttcast subscribes to commands on the following topic(s):

    chromecast/{name}/command
    
mqttcast updates the following topics:

    chromecast/{name}/device-status
    chromecast/{name}/cast-status
   
SUPPORTED ACTIONS:

mqttcast supports Simple actions in String format, but Extended actions must be in JSON format. 
To control a Chromecast called "Tatooine" you simply need to publish commands to its topic:

    chromecast/Tatooine/command

String format commands:

    pause       - Pause the media
    continue    - Continue after media has been paused
    play        - Continue after media has been paused    
    stop        - Stop playing the current media
    
    volup       - Increase volume by 1
    voldown     - Decrease volume by 1

    mute        - Enable Mute
    unmute      - Disable Mute

    start       - Seek to the start of the media (see also "replay")
    end         - Seek to the end of the media (see also "skip")
    replay      - Seek to the start of the media (see also "start")
    skip        - Seek to the end of the media (see also "end")

    forward     - Fast Forward 30 seconds (See JSON for further options)
    rewind      - Rewind 30 seconds (See JSON for further options)

    quit        - Disconnect current application
    reboot      - Reboot device

JSON format actions:

    Actions in JSON format support three attributes, "action", "data" and "meta".

    action:     This is the same as the string "action"
    data:       (Optional), only used by "play", "forward", "rewind", "seek" and "volume"
    meta:       (Optional), only used by "play"
    
    Extended commands include:

    play
        "data" is the URL of the media, 
        "meta" is the encoding type ("audio/mp3"|"video/mp4")
    volume  
        "data" is the volume between 0 and 10
    forward
        "data" is optional duration in seconds. 
        Default is 30 seconds
    rewind  
        "data" is optional duration in seconds. 
        Default is 30 seconds
    seek    
        "data" is the position in seconds

    All of the Simple functions can be encoded into JSON simply by sending them as actions, for example: { "action":"pause" }
    
Examples:
    
    { "action":"play", 
      "data":"http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
      "meta":"video/mp4" }
    
    { "action":"seek", "data":40 }


