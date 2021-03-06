#!/usr/bin/env python3
# -*- coding: utf-8 -*- 

# Python program to control MQTT topics.
# Klemens Schueppert : schueppi@envot.io

import paho.mqtt.client as mqttClient
import readline
import time
import argparse
import sys
import json


parser = argparse.ArgumentParser(description= 'Python program to control MQTT topics.')
parser.add_argument('-host', type=str, help='Host of MQTT Broker. Default: "localhost"')
parser.add_argument('-port', type=str, help='Port of MQTT Broker. Default: 1883')
args = parser.parse_args()

if args.host == None:
    args.host = "localhost"
if args.port == None:
    args.port = 1883

if sys.version_info[0] == 2:
    input_func = raw_input
elif sys.version_info[0] == 3:
    input_func = input
else:
    raise Exception('Python version not supported.')

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe("#")
    else:
        print("Connection failed")

def color_text(text, color='green'):
    colorDict = {
        'green' : ['\x1b[1;32;40m','\x1b[0m'],
        'red' : ['\x1b[1;31;40m', '\x1b[0m'],
        }
    return (colorDict[color][0]
        +text
        +colorDict[color][1])

def print_topic_payload(client, topic, payload):
    print(color_text(topic, 'green')
            + ' : '
            + color_text(payload, 'red'))

def on_message(client, userdata, message):
    client.data[message.topic] = message.payload.decode('ascii')
    printPayload = message.payload.decode('ascii')
    if message.topic.split('/')[-1] == 'logs':
        printPayload = printPayload.split('\n')[-1]
    if client.printMessage:
        print_topic_payload(client, message.topic, printPayload)

client = mqttClient.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(args.host, int(args.port))
client.loop_start()
client.data = {}
client.printMessage = False

def rmdir_func(foldername, optionsArray, client):
    for option in optionsArray:
        if foldername == option[:len(foldername)]:
            client.publish(option, "", retain=True)

def print_change(client, inputArray):
    if len(inputArray) > 1:
        if inputArray[1].lower() in ['true', 'on', '1']:
            client.printMessage = True
            return True
        if inputArray[1].lower() in ['false', 'off', '0']:
            client.printMessage = False
            return True
        print('Could not handle:'+inputArray[1])
    print('Write "print on" or "print off".')

def reload_func(client):
    time.sleep(0.1)
    client.unsubscribe("#")
    client.data = {}
    client.subscribe("#")

class MyCompleter(object):  # Custom completer
    def __init__(self, options):
        self.options = sorted(options)

    def complete(self, text, state):
        #print text
        #print self.options
        if state == 0:  # on first trigger, build possible matches
            if text:  # cache matches (entries that start with entered text)
                self.matches = [s for s in self.options 
                                    if text in s]
            else:  # no text entered, all matches possible
                self.matches = self.options[:]

        # return match indexed by state
        try: 
            return self.matches[state]
        except IndexError:
            return None

time.sleep(2)

old_delims = readline.get_completer_delims()
for string2remove in ['/', '-', '$']:
    old_delims = old_delims.replace(string2remove, '')
readline.set_completer_delims(old_delims)

try:
    while True:
        optionsArray = ['help', 'rmdir', 'reload', 'print', 'backup']
        for i,val in enumerate(map(str, client.data.keys())):
            optionsArray.append(val)
        
        completer = MyCompleter(optionsArray)
        readline.set_completer(completer.complete)
        readline.parse_and_bind('tab: complete')
        
        new_input = input_func("Input:")
        inputArray = new_input.split(' ')
        if inputArray[0] == "rmdir":
            if len(inputArray) > 1:
                for topic2rm in inputArray[1:]:
                    rmdir_func(topic2rm, optionsArray, client)
                reload_func(client)
            else:
                print("No topic given...")
        if inputArray[0] == "reload":
            reload_func(client)
        if inputArray[0] == "backup":
            with open('backup.json', 'w') as outfile:
                json.dump(client.data, outfile, indent=4)
            print("Backuped data to 'backup.json'.")
        if inputArray[0] == "print":
            print_change(client, inputArray)
        if inputArray[0] == "":
            print("")
            print("Type 'help' for help.")
        if inputArray[0] == "help":
            print("Read or modify directly MQTT topcis.")
            print("Use tab for auto completion.")
            print("With 'print' you can enable and disable printing the messages.")
            print("'rmdir' removes entire folders of topics.")
            print("'reload' refreshes the topics.")
            print("'exit', 'quit' or ctrl-c for program end.")
        if inputArray[0] in ["exit", "quit"]:
            break
        else:
            if len(inputArray) == 1 and not inputArray[0] =='':
                for option in client.data:
                    if inputArray[0] == option[:len(inputArray[0])]:
                        print_topic_payload(client, option, client.data[option])
            if inputArray[0] in client.data:
                if len(inputArray) > 1:
                    payload = ' '.join(inputArray[1:])
                    if payload == '':
                        print('Remove '+color_text(inputArray[0],'green')+'.')
                    else:
                        print('Set '+color_text(inputArray[0],'green')
                            +' to '+color_text(payload,'red'))
                    client.publish(inputArray[0], payload, retain=True)
                    if payload == '':
                        reload_func(client)
            elif inputArray[0] not in optionsArray:
                if len(inputArray) > 1:
                    print('Create '+color_text(inputArray[0], 'green')
                            +' with '+color_text(' '.join(inputArray[1:]), 'red'))
                    client.publish(inputArray[0], ' '.join(inputArray[1:]), retain=True)

except KeyboardInterrupt:
    pass
except EOFError:
    pass
print("\nExiting...")
