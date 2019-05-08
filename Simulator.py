from random import randint

import null

class sharedMemory:

    #Class which maintains the shared memory.

    def __init__(self):
        self.data = [randint(0, 1000) for x in range(4)] #storing 4 randon numbers in the array.
        self.status = ["clean" for x in range(4)] #storing the status of shared memory location in the array.

class Bus:

    #Class which maintains the Bus Interaction

    def __init__(self, memory):
        self.memory = memory
        self.processors = []       #array for processors.
        self.instruction_processor = null
        self.instruction_type = null
        self.instruction_address = null
        self.instruction_value = null


    def instruction(self, processor, r_w, address,value):

        self.instruction_processor = processor #assigning the processor number.
        self.instruction_type = ("reads" if (r_w == 0) else "writes") # '0' -> reads, '1' -> '' writes.
        self.instruction_address = address #index of the sharedMemory array.
        self.instruction_value = value #values which is needed to be written.

        if r_w:
            #this is a write operation.
            self.processors[processor].writeValue(address,value)

        else:
             #this is a read operation.
             self.processors[processor].readValue(address)
        return


    def bus_snoop(self, processor_no ,address):

        flag = 0
        for processors in range(len(self.processors)):
            if(processors != processor_no): # if we find a copy in other processor's cache, we change their cache status bit to 'I' when we want to write.

                if(self.processors[processors].cache.address == address):
                    self.processors[processors].cache.state = "I"
                    flag = 1

        if flag == 1:
            return True
        else:
            return False

    def read_bus_snoop(self,processor_number, address):
        flag = 0
        for processors in range(len(self.processors)):
            if (processors != processor_number):

                if (self.processors[processors].cache.address == address):
                    if (self.processors[processors].cache.state == "I"):
                        continue
                    else:

                        # if we find a copy in other processor's cache, we change their cache status bit to 'S' when we want to read.
                        self.processors[processors].cache.state = "S"
                        if(self.memory.status[self.processors[processors].cache.address] == "dirty"):
                            self.memory.data[self.processors[processors].cache.address] = self.processors[processors].cache.value
                            self.memory.status[self.processors[processors].cache.address] = "clean"
                        flag = 1

        if flag == 1:
            return  True
        else:
            return False


class CPU:

    #Class which maintains the Processing Unit of the four cores.

    def __init__(self):

        self.memory = sharedMemory() #instance of the sharedMemory class

        self.bus = Bus(self.memory)

        self.processors = {}
        for processor_number in range(4):
            self.processors= Processor(processor_number, self.bus, self.memory)

    def printStatus(self):

        print("Main Memory : ")
        print(self.bus.memory.data)
        print(" ")

        if(self.bus.instruction_processor != null):

            if(str(self.bus.instruction_type) == "reads"):

                print("Instruction -> Processor_" + str(self.bus.instruction_processor) + " " +
                      str(self.bus.instruction_type) + " from address:" + str(self.bus.instruction_address))
            else:
                print("Instruction -> Processor_" + str(self.bus.instruction_processor) + " " +
                  str(self.bus.instruction_type) + " " + "value:" + str(
                self.bus.instruction_value) + " to address:" + str(self.bus.instruction_address))

        print(" ")

        for processor in range(len(self.bus.processors)):
            print("Processor number: "+str(processor))
            print("Cache State: " + self.bus.processors[processor].cache.state)


            if(self.bus.processors[processor].cache.address == null):
                print("Cache memory address: " + "empty")
            else:
                print("Cache memory address: " + str(self.bus.processors[processor].cache.address))

            if (self.bus.processors[processor].cache.value == null):
                print("Cache memory value: " + "empty")
            else:
                print("Cache memory value: " + str(self.bus.processors[processor].cache.value))

            print(" ")

        print("*******************************************************************************")



class Processor:

    def __init__(self, processor_number, bus, memory):

        self.cache = Cache()
        self.processor_number = processor_number
        self.bus = bus
        self.memory = memory
        self.bus.processors.append(self)


    def writeValue(self,address,value):

        if(self.cache.address == null):         #first time when the shared memory address block enter the cache of the processors

            if(self.bus.bus_snoop(self.processor_number,address)): # if there no copies of the shared memory address block

                self.cache.state = "E"
                self.cache.address = address
                self.cache.value = value
                self.memory.data[address] = value

            else:
                self.cache.state = "M"
                self.cache.address = address
                self.cache.value = value
                self.memory.status[address] = "dirty"

        elif(self.cache.address == address): # if we have copies of the address block

            if(self.cache.state == "S"): # if the cache status bit is 'S' change it to 'E'

                self.cache.state = "E"
                self.cache.value = value
                self.cache.address = address
                self.memory.data[address] = value
                self.bus.bus_snoop(self.processor_number,address)

            if (self.cache.state == "E"): # if the cache status bit is 'E' change it to 'M'

                self.cache.state = "M"
                self.cache.value = value
                self.cache.address = address

                if(self.memory.status[self.cache.address] == "clean"): # need to change the shared memory block address status as we are implementing WRITE BACK.
                    self.memory.status[self.cache.address] = "dirty"

                self.bus.bus_snoop(self.processor_number,address)

            if (self.cache.state == "M"): # if the cache status bit is 'M', we just update the value.

                self.cache.value = value
                self.cache.address = address
                self.bus.bus_snoop(self.processor_number,address)

        else: # need to replace the cache block with new shared memory address block.

            if(self.bus.bus_snoop(self.processor_number,address)):

                if(self.memory.status[self.cache.address] == "dirty" and self.cache.state != "I" ): # if the shared memory address block is dirty and
                    # cache status is either 'M' or 'E' or 'S', first we need to update the shared memory address block(WRITE BACK) and then copy the new value.

                    self.memory.data[self.cache.address] = self.cache.value
                    self.memory.status[self.cache.address] = "clean"


                self.memory.status[address] = "dirty"
                self.cache.state = "E"
                self.cache.value = value
                self.cache.address = address

            else:

                # we dont have an copies in other processor's cache, we just updated the shared memory address block and copy the value, change the cache's bit to 'm'
                self.memory.data[self.cache.address] = self.cache.value
                self.memory.status[self.cache.address] = "clean"

                self.cache.state = "M"
                self.cache.value = value
                self.cache.address = address
                self.memory.status[address] = "dirty"

        return

    def readValue(self,address):

        if (self.bus.read_bus_snoop(self.processor_number, address)):

            if(self.cache.state == "M"): # if the cache status bit is 'M', we need to WRITE BACK to the shared memory before we read the value and change the cache's status bit to 'S'.
                self.memory.data[self.cache.address] = self.cache.value
                self.memory.status[self.cache.address] = "clean"

            self.cache.state = "S"
            self.cache.address = address
            self.cache.value = self.memory.data[address]


        else:

            # if we are reading the value for the first time from the shared memory address block and don't have copies in any other processor's cache.
            if(self.cache.state == "M"):

                if(self.memory.status[self.cache.address] == "dirty"):

                    self.memory.data[self.cache.address] = self.cache.value
                    self.memory.status[self.cache.address]  = "clean"
                    self.cache.address = address
                    self.cache.value = self.memory.data[address]
                    self.cache.state = "E"
                return

            if(self.cache.state == "E"):

                self.cache.address = address
                self.cache.value = self.memory.data[address]
                return

            else:
                self.cache.state = "E"
                self.cache.address = address
                self.cache.value = self.memory.data[address]

        return



class Cache:

    #Cache which maintains the Processor Cache.
    def __init__(self):
        self.state = "I"
        self.value = null
        self.address = null





if __name__ == "__main__":

    cpu = CPU() #instance of CPU class.

    print("You can the test the Simulator with 'N' random instructions.")

    number_of_instructions = int(input("How many random instructions you want to execute?\n"))

    cpu.printStatus()  # calling the method which print the status of Processor Cache and Shared Memory.

    # Testing the simulator with N random inputs.

    for i in range(number_of_instructions):

        cpu.bus.instruction(randint(0, 3), randint(0, 1), randint(0, 3), randint(0, 1000)) # calling the instruction method
        cpu.printStatus()







