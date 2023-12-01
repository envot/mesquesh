#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Python program to control MQTT topics.
# Klemens Schueppert : schueppi@envot.io

import readline
import time
import argparse
import sys
import json
import paho.mqtt.client as mqttClient


import inquirer  # noqa
from readchar import key

def process_input(self, pressed):
    question = self.question
    if pressed in ['k', key.UP]:
        if question.carousel and self.current == 0:
            self.current = len(question.choices) - 1
        else:
            self.current = max(0, self.current - 1)
        return
    if pressed in ['j', key.DOWN]:
        if question.carousel and self.current == len(question.choices) - 1:
            self.current = 0
        else:
            self.current = min(len(self.question.choices) - 1, self.current + 1)
        return
    if pressed == key.ENTER:
        value = self.question.choices[self.current]

        if value == inquirer.render.console._other.GLOBAL_OTHER_CHOICE:
            value = self.other_input()
            if not value:
                # Clear the print inquirer.text made, since the user didn't enter anything
                print(self.terminal.move_up + self.terminal.clear_eol, end="")
                return

        raise inquirer.errors.EndOfInput(getattr(value, "value", value))

    if pressed == key.CTRL_C:
        raise KeyboardInterrupt()

inquirer.render.console.List.process_input = process_input

LAST_PRINTS = []
PREFILL = ''

parser = argparse.ArgumentParser(description= 'Python program to control MQTT topics.')
parser.add_argument('-host', type=str, help='Host of MQTT Broker. Default: "localhost"')
parser.add_argument('-port', type=str, help='Port of MQTT Broker. Default: 1883')
args = parser.parse_args()

if args.host is None:
    args.host = "localhost"
if args.port is None:
    args.port = 1883

if sys.version_info[0] == 2:
    input_func = raw_input
elif sys.version_info[0] == 3:
    input_func = input
else:
    raise Exception('Python version not supported.')

def input_with_prefill(prompt, text):
    def hook():
        readline.insert_text(text)
        readline.redisplay()
    readline.set_pre_input_hook(hook)
    result = input_func(prompt)
    readline.set_pre_input_hook()
    return result


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

def print_topic_payload(client, topic, payload, skipCheck=False):
    if (client.printDollars or not ('$' in topic) or skipCheck) and (len(payload) > 0):
        print(color_text(topic, 'green')
            + ' : '
            + color_text(payload, 'red'))
        return topic

def on_message(client, userdata, message):
    try:
        client.data[message.topic] = message.payload.decode()
    except:
        client.data[message.topic] = str(message.payload)
    printPayload = client.data[message.topic]
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
client.printDollars = False

def rmdir_func(foldername, optionsArray, client):
    for option in optionsArray:
        if foldername == option[:len(foldername)]:
            client.publish(option, "", retain=True)
    reload_func(client)

def find_func(targetArray, optionsArray, client):
    global LAST_PRINTS
    LAST_PRINTS = []
    for option in optionsArray:
        if is_in(targetArray, option):
            result = print_topic_payload(client, option, client.data[option])
            if result != None:
                LAST_PRINTS.append(result)

def is_in(targetArray, option):
    for target in targetArray:
        if not target in option:
            return False
    return True

def print_change(client, inputArray):
    if len(inputArray) > 1:
        if inputArray[1].lower() in ['true', 'on', '1']:
            client.printMessage = True
            return True
        if inputArray[1].lower() in ['false', 'off', '0']:
            client.printMessage = False
            return True
        if inputArray[1].lower() in ['$']:
            if client.printDollars:
                client.printDollars = False
                print('Do not show $ topics.')
            else:
                client.printDollars = True
                print('Show $ topics.')
            return True
        print('Could not handle:'+inputArray[1])
    print('Write "print on" or "print off" of "print $" for toogle $.')

def publish_print(client, topic, payload):
    if payload == '':
        print('Remove '+color_text(topic,'green')+'.')
    else:
        print('Set '+color_text(topic,'green')
            +' to '+color_text(payload,'red'))
    client.publish(topic, payload, retain=True)
    if payload == '':
        reload_func(client)

def reload_func(client):
    time.sleep(0.1)
    client.unsubscribe("#")
    client.data = {}
    client.subscribe("#")

class MyCompleter(object):  # Custom completer
    def __init__(self, options):
        self.options = sorted(options)
        self.matches = []

    def complete(self, text, state):
        if state == 0:  # on first trigger, build possible matches
            if text:  # cache matches (entries that start with entered text)
                self.matches = []
                for option in self.options:
                    if text in option[0:len(text)]:
                        if option[len(text):].find('/') == -1:
                            self.matches.append(option)
                        else:
                            lenslash = len(text)+option[len(text):].find('/')+1
                            if not option[0:lenslash] in self.matches:
                                self.matches.append(option[0:lenslash])
            else:  # no text entered, all matches possible
                self.matches = ['help', 'rmdir', 'reload', 'print', 'backup']
                for option in self.options:
                    if not option.split('/')[0] in self.matches:
                        self.matches.append(option.split('/')[0])
        try:
            return self.matches[state]
        except IndexError:
            return None

time.sleep(0.5)

old_delims = readline.get_completer_delims()
for string2remove in ['/', '-', '$']:
    old_delims = old_delims.replace(string2remove, '')
readline.set_completer_delims(old_delims)

try:
    while True:
        optionsArray = ['help', 'find', 'rmdir', 'reload', 'print', 'backup', 'select']
        for i,val in enumerate(map(str, client.data.keys())):
            optionsArray.append(val)

        completer = MyCompleter(optionsArray)
        readline.set_completer(completer.complete)
        readline.parse_and_bind('tab: complete')

        new_input = input_with_prefill("Input:", PREFILL)
        PREFILL = ''
        inputArray = new_input.split(' ')
        if inputArray[0] == "rmdir":
            if len(inputArray) > 1:
                for topic2rm in inputArray[1:]:
                    rmdir_func(topic2rm, optionsArray, client)
            else:
                print("No topic given...")
        elif inputArray[0] in ['find', ':f']:
            if len(inputArray) > 1:
                if len(inputArray[1]) >1:
                    find_func(inputArray[1:], optionsArray, client)
            else:
                print("No search phrase given...")
        elif inputArray[0] in ['reload', ':r']:
            reload_func(client)
        elif inputArray[0] in ['backup', ':b']:
            with open('backup.json', 'w') as outfile:
                json.dump(client.data, outfile, indent=4)
            print("Backuped data to 'backup.json'.")
        elif inputArray[0] == "print":
            print_change(client, inputArray)
        elif inputArray[0] == "":
            print("")
            print("Type 'help' of ':h' for help.")
        elif inputArray[0] in ['help', ':h']:
            print("Read or modify directly MQTT topcis.")
            print("Use tab for auto completion.")
            print("'backup', ':b' all data into 'backup.json'.")
            print("'find', ':f' shows you all topics with the patterns.")
            print("'print', ':p' toggles printing the messages.")
            print("'rmdir' removes entire folders of topics.")
            print("'reload', ':r' refreshes the topics.")
            print("'select', ':s' offers you to select from last print.")
            print("'multiset', ':m' offers you to set all from last print"+
                " at once. Starting with '/' you can extend the topic")
            print("'exit', 'quit', ':q' , crtl-d or ctrl-c for program end.")
        elif inputArray[0] in ['exit', 'quit', ':q']:
            break
        elif inputArray[0] in ['select', ':s']:
            if len(LAST_PRINTS)>0:
                questions = [
                    inquirer.List(
                        "input",
                        message="What do you want to select?",
                        choices=LAST_PRINTS,
                    ),
                ]
                PREFILL = inquirer.prompt(questions)['input'] + '/set '
            else:
                print("No last prints available!")
        elif inputArray[0] in ['multiset', ':m']:
            if len(LAST_PRINTS)>0:
                if len(inputArray) == 1:
                    print("'multiset', ':m' offers you to set all from last print"+
                        " at once. Starting with '/' you can extend the topic")
                for topic in LAST_PRINTS:
                    if len(inputArray) == 2:
                        publish_print(client, topic, ' '.join(inputArray[1]))
                    else:
                        if inputArray[1][0] == '/':
                            publish_print(client, topic+inputArray[1], ' '.join(inputArray[2:]))
                        else:
                            publish_print(client, topic, ' '.join(inputArray[1:]))
            else:
                print("No last prints available!")
        elif len(inputArray) == 1 and not inputArray[0] =='':
            results = []
            for option in client.data:
                if inputArray[0] == option[:len(inputArray[0])]:
                    result = print_topic_payload(client, option, client.data[option],
                            skipCheck=('$' in inputArray[0]))
                    if result != None:
                        results.append(result)
            if len(results) > 1:
                LAST_PRINTS = results
        elif inputArray[0] in client.data:
            if len(inputArray) > 1:
                payload = ' '.join(inputArray[1:])
                publish_print(client, inputArray[0], payload)
        elif inputArray[0] not in optionsArray:
            if len(inputArray) > 1:
                publish_print(client, inputArray[0], ' '.join(inputArray[1:]))

except KeyboardInterrupt:
    pass
except EOFError:
    pass
print("\nExiting...")
