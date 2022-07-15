from math import trunc
import serial
import time
import keyboard


class PeriPump:

    def __init__(self,com_port): # at the moment, one object for all pumps in the setup
        self.pump_arduino = serial.Serial(port=com_port, baudrate=9600)
        time.sleep(4) # time for Arduino connection to start up
        self.volPerStep1 = 0 # units of mL per step
        self.volPerStep2 = 0
        self.volPerStep3 = 0
        self.volPerStep4 = 0
        self.volPerStep5 = 0
        print('Initialisation complete, serial connection established')


    def prime(self, pump_no): 
        print('Priming the line.  Press and hold \'p\' to stop pumping when the line is fully primed.')
        while True:
            print('Pumping...')
            self.runPump(pump_no,'c',steps='500')
            time.sleep(1)
            if keyboard.is_pressed('p'):
                print('Pumping ended')
                break


    def calibrate(self, pump_no, cal_steps): # add a default value?
        print(f'Calibration started.  Running the pump for {cal_steps} steps...')
        self.runPump(pump_no, 'c', steps=cal_steps)
        volume = float(input('Enter the volume dispensed in mL:'))
        if pump_no == 1:
            self.volPerStep1 = volume/int(cal_steps) # in units of mL per step
            print(f'This corresponds to {self.volPerStep1} mL per step for pump 1.  The value has been saved.')
        if pump_no == 2:
            self.volPerStep1 = volume/int(cal_steps) # in units of mL per step
            print(f'This corresponds to {self.volPerStep2} mL per step for pump 2.  The value has been saved.')
        if pump_no == 3:
            self.volPerStep1 = volume/int(cal_steps) # in units of mL per step
            print(f'This corresponds to {self.volPerStep3} mL per step for pump 3.  The value has been saved.')
        if pump_no == 4:
            self.volPerStep1 = volume/int(cal_steps) # in units of mL per step
            print(f'This corresponds to {self.volPerStep4} mL per step for pump 4.  The value has been saved.')
        if pump_no == 5:
            self.volPerStep1 = volume/int(cal_steps) # in units of mL per step
            print(f'This corresponds to {self.volPerStep5} mL per step for pump 5.  The value has been saved.')
            

    def runPump(self, pump_no, direction, volume=None, steps=None): # direction and steps must be inputted as strings -> allow for volume input as well.

        # some of the below needs to be elsewhere or?
        command_len = 10 # can send (MESSAGE_LEN-1) characters (including < and >) -> max message length # do I still need to specify this?
        data = '' # for incoming serial data
        incoming = '' # for storing the character from the data sent from the Arduino
        message = [""]*3 # string for the message
        last_message = '' # for storing the most recent message sent over from the Arduino 
        tick = 0
        complete = 0 # is 1 if the message is complete (a '>' character has been received), otherwise is 0
        commandPassed = False # boolean to store if a command has been sent to the Arduino

        while True: # function repeats over and over until 'return' is hit when "<d>" received from Arduino

            if (self.pump_arduino.in_waiting == 0 and (last_message == '' or last_message == "<e>" or last_message == "<i>") and commandPassed == False):
                # format of command to send: e.g. <1c600> or <3a500>; first digit = pump number, a = anticlockwise, c = clockwise, number = no of steps to run
                if volume != None and steps == None:
                    if pump_no == 1:
                        if self.volPerStep1 == 0:
                            print("Calibration has not been done yet for this pump... setting volPerStep to default of 0.00085")
                            self.volPerStep1 = 0.00085
                        steps = trunc(int(volume)/self.volPerStep1)
                    if pump_no == 2:
                        if self.volPerStep2 == 0:
                            print("Calibration has not been done yet for this pump... setting volPerStep to default of 0.00085")
                            self.volPerStep2 = 0.00085
                        steps = trunc(int(volume)/self.volPerStep2)
                    if pump_no == 3:
                        if self.volPerStep3 == 0:
                            print("Calibration has not been done yet for this pump... setting volPerStep to default of 0.00085")
                            self.volPerStep3 = 0.00085
                        steps = trunc(int(volume)/self.volPerStep3)
                    if pump_no == 4:
                        if self.volPerStep4 == 0:
                            print("Calibration has not been done yet for this pump... setting volPerStep to default of 0.00085")
                            self.volPerStep4 = 0.00085
                        steps = trunc(int(volume)/self.volPerStep4)
                    if pump_no == 5:
                        if self.volPerStep5 == 0:
                            print("Calibration has not been done yet for this pump... setting volPerStep to default of 0.00085")
                            self.volPerStep5 = 0.00085
                        steps = trunc(int(volume)/self.volPerStep5)
                    print(f'Volume {volume} mL converted to {steps} steps.')
                    y = '<' + str(pump_no) + direction + str(steps) + '>' 
                elif volume != None and steps != None:
                    print(f'Both volume and steps provided in runPump(). Only one should be provided.  Please check.')
                    return
                elif volume == None and steps == None:
                    print('Neither volume nor steps has been provided for runPump()')
                    return
                elif volume == None and steps != None:
                    print(f'{steps} steps will be sent to Arduino.')
                    y = '<' + str(pump_no) + direction + str(steps) + '>' 
                x = str(y) # can remove this?
                print(f'Command being sent to Arduino is: {x}')
                commandPassed = True

                if len(x) > command_len-1:
                    print('Command too long!')
                else:
                    self.pump_arduino.write(str.encode(x))
                    print('Sent')

            while (self.pump_arduino.in_waiting == 0):
                print("Waiting for response message from arduino...")
                time.sleep(1)

            print(f'Arduino in waiting value is: {self.pump_arduino.in_waiting}')

            while (self.pump_arduino.in_waiting > 0):
                # read the incoming byte:
                data = self.pump_arduino.read()
                # get just the character out:
                incoming = chr(data[-1])
                
                if (incoming != '\n' and incoming !='\r'): # new line character will be ignored
                    
                    # message is complete and incoming is not a start character... don't do anything
                    if (complete == 1 and incoming != '<'):
                        pass 
                    # start character given; start building the message
                    elif (incoming == '<'):
                        message = [""]*3
                        tick = 0
                        complete = 0
                        message[tick] = incoming
                        tick += 1
                    # end character given, message is complete
                    elif (incoming == '>' and tick < 3 and message[0] == '<') :
                        message[tick] = incoming
                        complete = 1
                    # building the message
                    elif (incoming != '<' and incoming != '>' and tick < 3 and message[0] == '<'):
                        message[tick] = incoming
                        tick += 1
                    # no start character has been seen... don't add anything to the message
                    elif (incoming != '<' and incoming != '>' and tick < 3 and message[0] != '<'):
                        pass 
                    # too many characters given; empty the message
                    elif (tick >= 3):
                        message = [""]*3
                        tick = 0
                        complete = 0

                    if complete == 1:
                        if (message[0] == '<' and message[1] == 'b' and message[2] == '>'):
                            print('Arduino busy')
                            last_message = "<b>"
                        elif (message[0] == '<' and message[1] == 'd' and message[2] == '>'):
                            print('Arduino done with task')
                            last_message = "<d>"
                            return # ends the function if a task has been completed by the arduino (i.e. the pumping is done)
                        elif (message[0] == '<' and message[1] == 'c' and message[2] == '>'):
                            print('Arduino has received a complete command that is ready to action')
                            last_message = "<c>"
                        elif (message[0] == '<' and message[1] == 'i' and message[2] == '>'):
                            print('Arduino currently has an incomplete command...')
                            last_message = "<i>"
                        elif (message[0] == '<' and message[1] == 'e' and message[2] == '>'):
                            print('Command is empty on the Arduino')
                            last_message = "<e>"
                        elif (message[0] == '<' and message[1] == 'w' and message[2] == '>'):
                            print('Warning - command send to the Arduino is complete but given pump direction not readable.  Command will be removed.')
                            last_message = "<w>"
                        else:
                            print(f'Current message is {message}, complete but not known.')
                    else:
                        print('Arduino is sending data...')
            