
# mqttcast
# (c) Copyright Si Dunford, June 2020
# VERSION 0.3

"""
CHANGES
26 JUN 2020  V0.0  INITIAL VERSION
27 JUN 2020  V0.1  Added Basic (string) and Extended (json) command support:
             V0.2  Added reboot and quit
28 JUN 2020  V0.3  Added forward,rewind,start,end,replay,seek and skip
                   Fixed several bugs
                   Published to GITHUB
"""

import configparser, json, sys, time
import pychromecast
import paho.mqtt.client as paho
import traceback

APPNAME = 'mqttcast'
devices = {}
config = configparser.ConfigParser()
mqtt=None

def on_connect( client, userdata, flags, rc ):
    print( "- MQTT connected with result code "+str(rc))
    print( "- Subscribing to chromecast/+/command" )
    client.subscribe( "chromecast/+/command" )
        
def on_message( client, userdata, msg ):
    try:   
        #topic = msg.topic
        name = msg.topic.split("/")[1]
        device_name = get_name( name )
        if device_name in devices:
            device = devices[ device_name ]
            payload = msg.payload.decode()
            try:
                action = json.loads(payload)
            except ValueError:
                action = { "action":payload }
            print( "MSG: "+name+" // " + str(action) ) 
            device.command( action )
          
    except Exception as e:
        #exception_type, exception_object, exception_traceback = sys.exc_info()
        print( "ON_MESSAGE EXCEPTION" )
        #print( str(e)+" at line "+str(exception_traceback.tb_lineno) )
        traceback.print_exc()

supported_actions = { 'continue', 'end', 'forward', 'mute', 'pause', 'play', 'quit', 'reboot', 'replay', 'rewind', 'seek', 'skip', 'start', 'stop', 'unmute', 'volume', 'voldown', 'volup' }
class Chromecast:
    
    def __init__( self, name, device ):
        self.name = name
        self.device = device
        device.wait()
        #self.sendDeviceStatus()
        self.device.register_status_listener(self)
        self.device.media_controller.register_status_listener(self)
    
    def close( self ):
        pass
    
    def new_media_status( self, status ):
        print( "MEDIA STATUS:"+str(status) )
        retval = mqtt.publish( "chromecast/{}/media-status".format(self.device.name), str(status) )
            
    def new_cast_status( self, status ):
        print( "CAST STATUS:"+str(status) )
        retval = mqtt.publish( "chromecast/{}/cast-status".format(self.device.name), str(status) )
    
    def command( self, action ):
        # Dispatch method:
        cmd = action.get( 'action','' ).lower()
        data = action.get( 'data','' )
        meta = action.get( 'meta','' )
        # Prevent command injection
        if cmd in supported_actions:
            # Get the method from 'self'. Default to a lambda.
            method = getattr( self, "action_"+cmd, lambda: "action_invalid" )
            # Call the method as we return it
            return method( data, meta )

    def action_invalid( self, data, meta ):
        print( "INVALID COMMAND")

    def action_continue( self, data, meta ):
        self.device.media_controller.play()

    def action_end( self, data, meta ):
        # Seek to end of the current media
        duration = self.device.media_controller.status.duration
        self.device.media_controller.seek( duration )
        
    def action_forward( self, data, meta ):
        try:
            skip = int( data )
        except ValueError:
            skip = 30
        if skip==0: skip = 30
        duration = self.device.media_controller.status.duration
        time = self.device.media_controller.status.current_time
        seek = min(time + skip, duration )
        self.device.media_controller.seek( seek )
                
    def action_mute( self, data, meta ):
        self.device.set_volume_muted(True)
    
    def action_pause( self, data, meta ):
        self.device.media_controller.pause()
    
    def action_play( self, url, meta ):
        if url=='':
            self.device.media_controller.play()
        else:
            self.device.media_controller.play_media( url, meta )

    def action_quit( self, data, meta ):
        self.device.quit_app()

    def action_reboot( self, data, meta ):
        self.device.reboot()
    
    def action_replay( self, data, meta ):
        # Seek to start of the current media
        self.device.media_controller.seek( 0 )

    def action_rewind( self, data, meta ):
        try:
            skip = int( data )
        except ValueError:
            skip = 30
        if skip==0: skip = 30
        time = self.device.media_controller.status.current_time
        seek = max(time - skip, 0 )
        self.device.media_controller.seek( seek )

    def action_seek( self, data, meta ):
        seek = float( data )
        self.device.media_controller.seek( seek )
        
    def action_skip( self, data, meta ):
        # Seek to end of the current media
        duration = self.device.media_controller.status.duration
        self.device.media_controller.seek( duration )
    
    def action_start( self, data, meta ):
        # Seek to start of the current media
        self.device.media_controller.seek( 0 )
        
    def action_stop( self, data, meta ):
        self.device.media_controller.stop()

    def action_unmute( self, data, meta ):
        self.device.set_volume_muted(False)
        
    def action_volume( self, level, meta ):
        # level must be between 0 and 1
        level = min(float( level ) / 10,1)
        self.device.set_volume(level)
    
    def action_voldown( self, data, meta ):
        self.device.volume_down()
    
    def action_volup( self, data, meta ):
        self.device.volume_up()
    
#cast.media_controller.play_media(args.url, "audio/mp3")

    
#def list_devices():
#     print("Currently known cast devices:")
#     for name, service in listener.services.items():
#         print("-> "+str(name)+"\n   "+str(service))

# Look up friendly name and return device name
def get_name( friendly ):
    for device in devices:
        if devices[device].device.name==friendly:
            return device
    return None

def publish_status( status, device ):
    topic = "chromecast/{}/device-status".format(device.name)
    message = {
        'status':status,
        'name':device.name,
        'type':device.cast_type,
        'model':device.model_name,
        'host':device.host
    }
    retval = mqtt.publish( topic, json.dumps( message ) )
    
def add_callback(name):
    #https://www.reddit.com/r/homeautomation/comments/4fc01z/quick_question_for_openhab_users/d28vnc4/
    #https://www.domoticz.com/forum/viewtopic.php?t=7022&start=20
    #https://community.openhab.org/t/google-cast-audio-chromecast-control/9991
    
    #name is the dictionary key to find
    #the chromecast metadata in listener.services.
    
    if name not in devices and name in listener.services:
        device = pychromecast.get_chromecast_from_host(listener.services[name])
        print( "ADDING NEW DEVICE: "+device.name )
        #print( listener.services[name] )
        print( str(device) )
        #print( device.name, device.cast_type )
        devices[name] = Chromecast( name, device )
        publish_status( "online", device )
        #retval = mqtt.publish( "chromecast/{}/device".format(device.name), "ONLINE" )    

def remove_callback(name, service):
    #print("Lost cast device {} {}".format(name, service))
    if name in devices:
        publish_status( "offline", devices[name].device )
        print( str(devices[name].device) )
        #retval = mqtt.publish( "chromecast/{}/device".format(devices[name].name), "OFFLINE" )
        devices[name].close()
        del devices[name]
    #list_devices()

def update_callback(name):
    #print("Update cast device {}".format(name))
    if name in devices:
        print( str(devices[name].device) )
        publish_status( "update", devices[name].device )
        #retval = mqtt.publish( "chromecast/{}/device".format(devices[name].name), "UPDATE" )

"""
class StatusListener:
    def __init__(self, name, cast):
        self.name = name
        self.cast = cast

    def new_cast_status(self, status):
        print("[", time.ctime(), " - ", self.name, "] status chromecast change:")
        print(status)


class StatusMediaListener:
    def __init__(self, name, cast):
        self.name = name
        self.cast = cast

    def new_media_status(self, status):
        print("[", time.ctime(), " - ", self.name, "] status media change:")
        print(status)
"""

def Main():
    global mqtt
    config.read('config.ini')
    
    # Default MQTT section
    if not 'mqtt' in config:
        config['mqtt']={}
    host = config['mqtt']
    
    # MQTT
    mqtt = paho.Client( APPNAME, clean_session=False )
    hostname = host.get('host','127.0.0.1')
    hostport = host.getint('port',1883)
    if 'username' in host:
        username = host.get('username','user')
        password = host.get('password','password')
        print( "- MQTT: "+username+"@"+hostname+":"+str(hostport) )    
        mqtt.username_pw_set( username, password )
    else:
        print( "- MQTT: "+hostname+":"+str(hostport) )    
        
    try:

        mqtt.connect( hostname, hostport , 60 )
    except Exception as e:
        #logging.critical( str(e) )
        print( e )
        sys.exit()
        
    mqtt.on_connect = on_connect
    mqtt.on_message = on_message
    mqtt.loop_forever()
    mqtt.disconnect()
    
    #while True:
    #    time.sleep(1)

if __name__=="__main__":

    # Start Chromecast discovery
    listener = pychromecast.CastListener(add_callback, remove_callback, update_callback)
    browser = pychromecast.discovery.start_discovery(listener)

    try:
        Main()
    except KeyboardInterrupt:
        pass

    pychromecast.stop_discovery(browser)
