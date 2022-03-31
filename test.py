
import pump
import valve
import time

v = valve.drainValve('COM4')
p = pump.PeriPump('COM3')

p.runPump('c',steps='5000')
time.sleep(1)
v.open()
time.sleep(4)
v.close()