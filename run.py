import iC

x = ''

c = iC.iControl()

# valve on COM4, pump on COM3
c.initialise_valve('COM4')
c.initialise_pump('COM3')

while x != 'y':
    x = input("Is the experiment ready to run?  Press 'y' and then press enter if so.")

if x == 'y':
    c.run_experiment()






