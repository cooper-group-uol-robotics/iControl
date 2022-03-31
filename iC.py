import os
import psutil
import time
import pywinauto
from pywinauto.application import Application
from pywinauto.application import WindowSpecification
import valve
import pump
import logging
import subprocess

logger = logging.getLogger()

def wait_until(check, value, timeout, period=0.25):
  mustend = time.time() + timeout
  while time.time() < mustend:
    if check == value:
        return True
    time.sleep(period)
  return False


class iControl:

  # standard iControl path is a class attribute (same for all instances of the class)
  standard_iControl_path = 'C:\Program Files\METTLER TOLEDO\iControl 6.1\iControl64.exe'

  def __init__(self):
      # iControl_path is an instance attribute (can be different for each instance of the class)
      self.iControl_path = iControl.standard_iControl_path
      self.path_found = False
      self.app = None
      self.experiment_ready = False
      self.experiment_running = False
      self.valve = None
      self.pump = None

  def set_iControl_path(self, path):
    self.iControl_path = path

  def initialise_valve(self, com_port):
    self.valve = valve.drainValve(com_port)

  def initialise_pump(self, com_port):
    self.pump = pump.PeriPump(com_port)
    x = input("Prime pump line?")
    if x == "y":
      self.pump.prime()
    x = input("Calibrate?")
    if x == 'y':
      print("Calibrating with 10000 motor steps")
      self.pump.calibrate('10000')

  def find_path(self):
    '''
    Checks if iControl64.exe is at standard file location
    Finds it if not and sets the iControl path to that
    '''

    if os.path.isfile(self.iControl_path):
        print(f'iControl64.exe file is at expected location: {self.iControl_path}')
        self.path_found = True
    else:
        print('iControl64.exe file is not at expected location - searching rest of computer...')
        for root, dirs, files in os.walk('/'):
            for name in files:
                if name == 'iControl64.exe':
                    new_path = os.path.join(root, name)
                    self.set_iControl_path(new_path)
                    print(f'iControl file found at: {self.iControl_path}')
                    self.path_found = True
                    break
        
    if self.path_found == False:
      print('.exe file for running iControl cannot be found on this computer!')
    elif self.path_found == True:
      print('.exe file found, you are all good to open iControl')


  def open_iControl(self):
    '''
    Checks if iControl is open
    Opens it from the correct .exe file
    Searches for the Trail Version window and 'Welcome to iControl' tutorial window and closes these if open
    '''

    # check if iControl is already open on the computer - returns a boolean -> potentially replace with is_process_running() from pywinauto
    iControl_open = 'iControl64.exe' in (i.name() for i in psutil.process_iter())

    # check if the iControl64.exe file exists
    if self.path_found == True:
      # if iControl is open, connect to it
      if iControl_open == True:
        print('iControl is already open')
        self.app = Application(backend="uia").connect(path=self.iControl_path)
      # if iControl is not open, open it
      elif iControl_open == False:
        print(f'Opening iControl from {self.iControl_path}')
        self.app = Application(backend="uia").start(self.iControl_path) 
        # Give the application time to open
        time.sleep(10)
    else:
      print('Failed to open iControl as the .exe file does not exist')


    # Print list of open windows
    dialogs = self.app.windows()
    print(f'the open windows are: {dialogs}')

    for window in dialogs:
        string_window = str(window)
        print(string_window)
        if 'Trial' in string_window:
            self.app.Trial_Version.Activate_Later_Button.click() 
            print('Trial version window was there but has now been closed via Activate Later button')
            break

    self.app.iControl.wait('visible', timeout = 15) # Waits for the main window to load
    print('done with waiting...')

    dialogs = self.app.windows()
    print(f'the open windows are: {dialogs}')

    # check if the 'Welcome to iControl' window is there and if it is then close it
    try:
        welcome = pywinauto.findwindows.find_element(title='Welcome to iControl') # throws an exception if 'Welcome to iControl' window not present
        check = self.app.iControl.Welcome_to_iControl.ShowWelcomeScreenAtStartUpCheckBox.get_toggle_state()
        if check == 1:
            self.app.iControl.Welcome_to_iControl.ShowWelcomeScreenAtStartUpCheckBox.toggle()
        unchecked = wait_until(check, 0, 5)
        if unchecked == True:
          print('\'Welcome to iControl\' window should now be closed')
          self.app.iControl.Welcome_to_iControl.Close_Button.click()
        elif unchecked == False:
          print('Error unchecking tick box in \'Welcome to iControl\' window')
    except Exception:
        print('\'Welcome to iControl\' window is already closed')


  def open_experiment(self, experiment_name): 
    '''
    Opens an experiment that has already been run so that the user can see its data
    '''

    # check that we are connected to the process and connect if not
    if self.app == None:
      self.app = Application(backend="uia").connect(path=self.iControl_path)

    self.app.iControl.Open_Experiment_Button.click()
    # self.app.Open.Folder_View.iControl_Experiments.invoke() -> not needed if it goes straight into iControl Experiments file
    print(f'Looking for: {experiment_name} ...')
    experiment = self.app.Open.Folder_View.child_window(title_re=f'{experiment_name}.*', control_type='ListItem').wrapper_object()
    print(experiment)
    experiment.invoke()

    print(f'The experiment \'{experiment_name}\'is now open')


  def design_experiment(self):
    '''
    Allows the user to design a new experiment
    ADD IN LETTING THE USER CHOOSE AN EXPERIMENT TEMPLATE TO OPEN
    '''

    # check that we are connected to the process and connect if not
    if self.app == None:
      self.app = Application(backend="uia").connect(path=self.iControl_path)

    self.app.iControl.Design_Experiment_Button.click()
    self.app.Design_New_Experiment.OK_Button.click()

    print('Now please go to iControl to design your experiment and return here when complete')
    print('Use \'Operator Method\' for valve integration and type \'valve open\' or \'valve close\' into the \'Message\' box')
    print('CHECK THAT VALVE IS CLOSED BEFORE RUNNING - the program assumes the drain valve starts in the closed state')
    text = input('When you are finished designing your experiment, please type \'y\' and press enter.  Any other value will store the experiment as not ready and the run_experiment method will not work.')
    if text == 'y':
      self.experiment_ready = True
    else:
      print('Experiment not ready - you will not be able to run the run_experiment method')


  def run_experiment(self):
    '''
    Starts running the experiment
    Check for the Operator Message window and carries out commands listed in that
    ADD IN CHECK FOR END OF EXPERIMENT
    '''

    # check that we are connected to the process and connect if not
    if self.app == None:
      self.app = Application(backend="uia").connect(path=self.iControl_path)

    if self.experiment_ready == True:
      
      # find the Experiment tab in top tool bar
      experiment_tab = self.app.Dialog.child_window(title_re=f'Experiment.*', control_type='Menu').wrapper_object() 

      # for loop to find which item the 'Start / Continue' button is in the Experiment tab
      for item in experiment_tab.items(): 
        item_string = str(item)
        if 'Start / Continue' in item_string:
          num = experiment_tab.items().index(item)
          print(f'Index number for Start button is: {num}')

      start_button = experiment_tab.items()[num]
      time.sleep(3)
      print(start_button)
      start_button.invoke()
      print('Just pressed start button, experiment should begin running now')

      self.experiment_running = True

      while self.experiment_running == True:
        # waits 3 seconds in between looks for the Operator Message window
        time.sleep(3)  
        try:
          # exception thown if Operator Message window is not present
          operator_message = self.app.One_or_More_User_Responses_Required.ListBox.ListItem.Operator_Message 
          # prints True when Operator Message window is there
          print(f'Operator message exists = {operator_message.exists()}') 
          message_string = str(operator_message.class_name) # probably not the best way of doing it, but works for getting to the text in the message box
          print(message_string)

          # if statements for reading message in the operator message window.  Add other things here for the pump.
          # maybe turn into switch/case when lots of options
          if 'open valve' in message_string:
            self.valve.open()
          elif 'close valve' in message_string:
            self.valve.close()
          elif 'dispense' in message_string:
            index_1 = message_string.index("dispense") + 9
            index_2 = message_string.index("ml") - 1
            vol = str(message_string[index_1:index_2])
            self.pump.runPump('c',volume = vol)
          else:
            print('Not a valid message in the Operator Message text box')

          operator_message = self.app.One_or_More_User_Responses_Required.OK_Button.click()  #clicks 'Okay' button to close Operator Message
          print('Clicked \'Okay\' to close Operator Message window, experiment continuing')
        except Exception as e:
          print('Operator Message box not present right now')

        # check that experiment is still running here or we will stay in this while loop forever - how?
        # CHECK WHEN EXPERIMENT HAS ENDED!
        # remember to CLOSE valve / check that it is closed at the end of the experiment
    
    else:
      print('Experiment not ready')

        


