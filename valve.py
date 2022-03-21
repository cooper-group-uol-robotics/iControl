import serial
import time

class drainValve:

    # check that all this actually works with the Arduino...
    '''
    For controlling the OptiMax bottom drain valve via Arduino 

    Valve states to read from the Arduino:
    1 = open (static)
    0 = closed (static)

    The valve state is always CLOSED (1) when an instance of the class is created
    '''

    def __init__(self, com_port):
        self.valve_state = 0
        self.arduino = serial.Serial(port=com_port, baudrate=115200, timeout = None)
        time.sleep(3)

    def get_state(self):
        time.sleep(2)
        #self.arduino.reset_output_buffer()
        self.arduino.write(str.encode('2'))   # this doesn't seem to be updating and reading new data properly...
        time.sleep(2)
        incoming_data = str(self.arduino.read(3))
        print(incoming_data)
        if '1' in incoming_data:
            self.valve_state = 1    # 1 = open
            print(f'valve state is {self.valve_state}, open')
            return 1
        if '0' in incoming_data:
            self.valve_state = 0    # 0 = closed
            print(f'valve state is {self.valve_state}, closed')
            return 0
        if '4' in incoming_data:
            print('Arduino giving an open error')
            exit()
        if '5' in incoming_data:
            print('Arduino giving a close error')
            exit()
        if '6' in incoming_data:
            print('it is going into the if statement...')
            exit()
        else:
            print('incoming data from Arduino does not make sense')


    def open(self):

        if self.valve_state == 0:
            print('valve is currently closed, okay to open')
            #self.arduino.reset_output_buffer()
            self.arduino.write(str.encode('1'))
            time.sleep(3)
            while self.valve_state == 0:
                incoming_data = str(self.arduino.read(3)) #getting 1 here!!!
                if ('1' in incoming_data):
                    self.valve_state = 1
                print(f'incoming data: {incoming_data}') 
  
            if self.valve_state == 1:
                print('valve should be open now')
            else:
                print(f'error - arduino does not say valve is in open state - giving state as {self.valve_state}')
        elif self.valve_state == 1:
            print('valve is already open, cannot send open command!')
        else:
            print(f'do not recognise current valve state: {self.valve_state}')


    def close(self):

        if self.valve_state == 1:
            print('valve is currently open, okay to close')
            self.arduino.write(str.encode('0'))
            time.sleep(3)
            while self.valve_state == 1:
                incoming_data = str(self.arduino.read(3)) 
                if ('0' in incoming_data):
                    self.valve_state = 0
                print(f'incoming data: {incoming_data}') 

            if self.valve_state == 0:
                print('valve should be closed now')
            else:
                print('error - arduino does not say valve is in closed state')
        elif self.valve_state == 0:
            print('valve is already closed, cannot send close command!')
        else:
            print(f'do not recognise current valve state: {self.valve_state}')


    # def check_done(self):

    #     self.get_state()

    #     while self.valve_state == 2 or self.valve_state == 3:
    #         self.valve_state = self.arduino.read()

    #     if self.valve_state == 0:
    #         print('Valve is now open and static')
    #     if self.valve_state == 1:
    #         print('Valve is now closed and static')

    #     return True

