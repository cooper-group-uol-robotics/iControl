import serial
import time

class drainValve:
    '''
    For controlling the OptiMax bottom drain valve via Arduino 

    Commands to send to the Arduino:
    <o> = open valve
    <c> = cose valve

    Valve states that the Arduino can report:
    <O> = valve is open
    <C> = valve is closed 
    (note uppercase here versus lowercase for movement commands)

    The valve state is always CLOSED when an instance of the class is created
    '''

    def __init__(self, com_port):
        self.valve_state = "<C>" # closed
        self.arduino = serial.Serial(port=com_port, baudrate=9600, timeout = None)
        time.sleep(3)

    def query_arduino(self, instructions): # instructions should be string; <s> or <o> or <c>

        # some of the below needs to be elsewhere or?
        command_len = 5 # can send (COMMAND_LEN-1) characters (including < and >) -> max command length
        data = '' # for incoming serial data
        incoming = ''
        command = [""]*command_len # string for the command
        last_command = ''
        tick = 0
        complete = 0 # is 1 if the command is complete (a '>' character has been received), otherwise is 0
        commandPassed = False

        while True: # function repeats over and over until 'return' is hit when "<d>" received from Arduino

            if (self.arduino.in_waiting == 0 and (last_command == '' or last_command == "<e>" or last_command == "<i>") and commandPassed == False):
                
                print(f'Command being sent to Arduino is: {instructions}')
                commandPassed = True

                if len(instructions) > command_len-1:
                    print('Command too long!')
                else:
                    self.arduino.write(str.encode(instructions))
                    print('Command sent')

            while (self.arduino.in_waiting == 0):
                print("Waiting for data from arduino...")
                time.sleep(1)

            print(f'Arduino in waiting value is: {self.arduino.in_waiting}')

            while (self.arduino.in_waiting > 0):
                # read the incoming byte:
                data = self.arduino.read()
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
                            print('Warning - command is complete but does not make sense or trying to open valve when closed etc..  Command will be removed.')
                            last_command = "<w>"
                        elif (command[0] == '<' and command[1] == 'C' and command[2] == '>'):
                            print("Valve is currently closed")
                            self.valve_state = "<C>"
                        elif (command[0] == '<' and command[1] == 'O' and command[2] == '>'):
                            print("Valve is currently open")
                            self.valve_state = "<O>"
                        else:
                            print(f'Current command is {command}, complete but not known.')
                    #else:
                    #    print('Arduino is sending data...')


    def get_state(self):
        self.query_arduino("<s>")
        print(f"Current valve state is: {self.valve_state}")
        return self.valve_state


    def open(self):
        self.get_state()
        if self.valve_state == "<C>":
            print("Valve is currently closed, okay to open")
            self.query_arduino("<o>")
            self.get_state()
            if self.valve_state == "<O>":
                print("Valve should be open now.")
        else:
            print("Valve state is not closed - hence cannot open it.")


    def close(self):
        self.get_state()
        if self.valve_state == "<O>":
            print("Valve is currently open, okay to close")
            self.query_arduino("<c>")
            self.get_state()
            if self.valve_state == "<C>":
                print("Valve should be closed now.")
        else:
            print("Valve state is not open - hence cannot close it.")


