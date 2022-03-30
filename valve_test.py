
import valve


#iC_instance = iC.iControl()
v = valve.drainValve('COM3')

v.get_state()
v.open()
v.close()