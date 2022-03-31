from math import trunc
import serial
import time
import keyboard


class PeriPump:

    def __init__(self,com_port):
        self.pump_arduino = serial.Serial(port=com_port, baudrate=9600)
        time.sleep(4) # time for Arduino connection to start up
        self.volPerStep = 0 # units of mL per step


    def prime(self): 
        print('Priming the line.  Press and hold \'p\' to stop pumping when the line is fully primed.')
        while True:
            print('Pumping...')
            self.runPump('c',steps='500')
            time.sleep(1)
            if keyboard.is_pressed('p'):
                print('Pumping ended')
                break


    def calibrate(self, cal_steps): # add a default value?
        print(f'Calibration started.  Running the pump for {cal_steps} steps...')
        self.runPump('c',steps=cal_steps)
        volume = float(input('Enter the volume dispensed in mL:'))
        self.volPerStep = volume/int(cal_steps) # in units of mL per step
        print(f'This corresponds to {self.volPerStep} mL per step.  The value has been saved.')
            

    def runPump(self, direction, volume=None, steps=None): # direction and steps must be inputted as strings -> allow for volume input as well.

        # some of the below needs to be elsewhere or?
        command_len = 10 # can send (COMMAND_LEN-1) characters (including < and >) -> max command length
        data = '' # for incoming serial data
        incoming = ''
        command = [""]*command_len # string for the command
        last_command = ''
        tick = 0
        complete = 0 # is 1 if the command is complete (a '>' character has been received), otherwise is 0
        commandPassed = False

        while True: # function repeats over and over until 'return' is hit when "<d>" received from Arduino

            if (self.pump_arduino.in_waiting == 0 and (last_command == '' or last_command == "<e>" or last_command == "<i>") and commandPassed == False):
                # format of command to send: <c600> or <a500>, a = anticlockwise, c = clockwise, number = no of steps to run
                if volume != None and steps == None:
                    if self.volPerStep == 0:
                        print("Calibration has not been done yet... setting volPerStep to default of 0.00085")
                        self.volPerStep = 0.00085
                    steps = trunc(int(volume)/self.volPerStep)
                    print(f'Volume {volume} mL converted to {steps} steps.')
                    y = '<' + direction + str(steps) + '>' 
                elif volume != None and steps != None:
                    print(f'Both volume and steps provided in runPump(). Only one should be provided.  Please check.')
                    return
                elif volume == None and steps == None:
                    print('Neither volume nor steps has been provided for runPump()')
                    return
                elif volume == None and steps != None:
                    print(f'{steps} steps will be sent to Arduino.')
                    y = '<' + direction + steps + '>' 
                x = str(y)
                print(f'Command being sent to Arduino is: {x}')
                commandPassed = True

                if len(x) > command_len-1:
                    print('Command too long!')
                else:
                    self.pump_arduino.write(str.encode(x))
                    print('Sent')

            while (self.pump_arduino.in_waiting == 0):
                print("Waiting for response from arduino...")
                time.sleep(1)

            print(f'Arduino in waiting value is: {self.pump_arduino.in_waiting}')

            while (self.pump_arduino.in_waiting > 0):
                # read the incoming byte:
                data = self.pump_arduino.read()
                # get just the character out:
                incoming = chr(data[-1])
                
                if (incoming != '\n' and incoming !='\r'): # new line character will be ignored
                    
                    # command is complete and incoming is not a start character... don't do anything
                    if (complete == 1 and incoming != '<'):
                        pass 
                    # start character given; start building the command
                    elif (incoming == '<'):
                        command = [""]*command_len
                        tick = 0
                        complete = 0
                        command[tick] = incoming
                        tick += 1
                    # end character given, command is complete
                    elif (incoming == '>' and tick < (command_len-1) and command[0] == '<') :
                        command[tick] = incoming
                        complete = 1
                    # building the command
                    elif (incoming != '<' and incoming != '>' and tick < (command_len-1) and command[0] == '<'):
                        command[tick] = incoming
                        tick += 1
                    # no start character has been seen... don't add anything to the command
                    elif (incoming != '<' and incoming != '>' and tick < (command_len-1) and command[0] != '<'):
                        pass 
                    # too many characters given; empty the command
                    elif (tick >= (command_len-1)):
                        command = [""]*command_len
                        tick = 0
                        complete = 0

                    if complete == 1:
                        if (command[0] == '<' and command[1] == 'b' and command[2] == '>'):
                            print('Arduino busy')
                            last_command = "<b>"
                        elif (command[0] == '<' and command[1] == 'd' and command[2] == '>'):
                            print('Arduino done with task')
                            last_command = "<d>"
                            return # ends the function if a task has been completed by the arduino (i.e. the pumping is done)
                        elif (command[0] == '<' and command[1] == 'c' and command[2] == '>'):
                            print('Arduino has received a complete command that is ready to action')
                            last_command = "<c>"
                        elif (command[0] == '<' and command[1] == 'i' and command[2] == '>'):
                            print('Arduino currently has an incomplete command...')
                            last_command = "<i>"
                        elif (command[0] == '<' and command[1] == 'e' and command[2] == '>'):
                            print('Command is empty on the Arduino')
                            last_command = "<e>"
                        elif (command[0] == '<' and command[1] == 'w' and command[2] == '>'):
                            print('Warning - command on the Arduino is complete but given pump direction not readable.  Command will be removed.')
                            last_command = "<w>"
                        else:
                            print(f'Current command is {command}, complete but not known.')
                    else:
                        print('Arduino is sending data...')