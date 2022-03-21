
import valve
import time

#iC_instance = iC.iControl()
valve_inst = valve.drainValve('COM3')

#iC_instance.initialise_valve('COM3')
#iC_instance.find_path()
#iC_instance.open_iControl()
#iC_instance.open_experiment('experiment name)
#iC_instance.design_experiment()
#iC_instance.run_experiment()

valve_inst.get_state()
valve_inst.open()
time.sleep(5)
valve_inst.close()