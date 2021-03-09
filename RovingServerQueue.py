from FES import FES
from Queue import Queue
from Event import Event
from Customer import Customer
import numpy as np

class RovingServerQueue:
    def __init__(self, inputfile, maxTime):
        self.maxTime = maxTime
        with open(inputfile) as f:
            params = f.read()
            params = params.replace('\n', ' ').replace('\t', ' ').split(' ')
        self.lamOne = float(params[0])
        self.lamTwo = float(params[1])
        self.lamThree = float(params[2])
        self.lamFour = float(params[3])
        self.muBOne = float(params[4])
        self.muBTwo = float(params[5])
        self.muBThree = float(params[6])
        self.muBFour = float(params[7])
        self.muROne = float(params[8])
        self.muRTwo = float(params[9])
        self.muRThree = float(params[10])
        self.muRFour = float(params[11])
        self.kOne = float(params[12])
        self.kTwo = float(params[13])
        self.kThree = float(params[14])
        self.kFour = float(params[15])
        self.pOneOne = float(params[16])
        self.pOneTwo = float(params[17])
        self.pOneThree = float(params[18])
        self.pOneFour = float(params[19])
        self.pTwoOne = float(params[20])
        self.pTwoTwo = float(params[21])
        self.pTwoThree = float(params[22])
        self.pTwoFour = float(params[23])
        self.pThreeOne = float(params[24])
        self.pThreeTwo = float(params[25])
        self.pThreeThree = float(params[26])
        self.pThreeFour = float(params[27])
        self.pFourOne = float(params[28])
        self.pFourTwo = float(params[29])
        self.pFourThree = float(params[30])
        self.pFourFour = float(params[31])

        self.pOneZero = 1 - (self.pOneOne + self.pOneTwo + self.pOneThree + self.pOneFour)
        self.pTwoZero = 1 - (self.pTwoOne + self.pTwoTwo + self.pTwoThree + self.pTwoFour)
        self.pThreeZero = 1 - (self.pThreeOne + self.pThreeTwo + self.pThreeThree + self.pThreeFour)
        self.pFourZero = 1 - (self.pFourOne + self.pFourTwo + self.pFourThree + self.pFourFour)

        print('Initialize empty queue')
        self.initializeEmptySystem()
        print('schedule first arrivals')
        self.scheduleArrivalEvent(1, self.lamOne)
        self.scheduleArrivalEvent(2, self.lamThree)
        self.scheduleArrivalEvent(4, self.lamTwo)
        self.scheduleArrivalEvent(3, self.lamFour)

        while self.currentTime < maxTime:

            #get event
            currentEvent = self.fes.next()
            self.oldTime = self.currentTime
            self.currentTime = currentEvent.time
            self.processResults(self.currentTime - self.oldTime)

            if currentEvent.typ == "ARRIVAL" or currentEvent.typ == "REJOIN":

                customer = Customer(self.currentTime, currentEvent.queue)

                if self.serverStatus[0] == 0:  #check if server is inactive

                    if self.serverStatus[1] == currentEvent.queue: #check if server is in same queue as event

                    # select the right parameters according to the given queue
                        if currentEvent.queue == 1:
                            queue = currentEvent.queue
                            mu = self.muBOne
                            self.queueOne.addCustomer(customer)

                        elif currentEvent.queue == 2:
                            queue = currentEvent.queue
                            mu = self.muBTwo
                            self.queueTwo.addCustomer(customer)

                        elif currentEvent.queue == 3:
                            queue = currentEvent.queue
                            mu = self.muBThree
                            self.queueThree.addCustomer(customer)

                        elif currentEvent.queue == 4:
                            queue = currentEvent.queue
                            mu = self.muBFour
                            self.queueFour.addCustomer(customer)

                        self.serverStatus = (1, queue) #misschien fout
                        self.scheduleDepartureEvent(queue, mu)

                    else: #server inactive, wrong queue

                        serverqueue = self.serverStatus[1]

                        if currentEvent.queue == 1:
                            self.queueOne.addCustomer(customer)
                            mu = self.muROne

                        elif currentEvent.queue == 2:
                            self.queueTwo.addCustomer(customer)
                            mu = self.muRTwo

                        elif currentEvent.queue == 3:
                            self.queueThree.addCustomer(customer)
                            mu = self.muRThree

                        elif currentEvent.queue == 4:
                            self.queueFour.addCustomer(customer)
                            mu = self.muRFour

                        if not self.fes.checkSwitch():

                            if serverqueue == 1:
                                if self.queueOne.isempty():
                                    self.scheduleSwitchEvent(serverqueue, mu)
                                    self.serverStatus = (1, serverqueue)

                            elif serverqueue == 2:
                                if self.queueTwo.isempty():
                                    self.scheduleSwitchEvent(serverqueue, mu)
                                    self.serverStatus = (1, serverqueue)

                            elif serverqueue == 3:
                                if self.queueThree.isempty():
                                    self.scheduleSwitchEvent(serverqueue, mu)
                                    self.serverStatus = (1, serverqueue)

                            elif serverqueue == 4:
                                if self.queueFour.isempty():
                                    self.scheduleSwitchEvent(serverqueue, mu)
                                    self.serverStatus = (1, serverqueue)



                else: #server active
                    if currentEvent.queue == 1:
                        self.queueOne.addCustomer(customer)

                    elif currentEvent.queue == 2:
                        self.queueTwo.addCustomer(customer)

                    elif currentEvent.queue == 3:
                        self.queueThree.addCustomer(customer)

                    elif currentEvent.queue == 4:
                        self.queueFour.addCustomer(customer)


                if currentEvent.typ == "ARRIVAL":
                    #schedule new arrival
                    if currentEvent.queue == 1:
                        self.scheduleArrivalEvent(1, self.lamOne)

                    elif currentEvent.queue == 2:
                        self.scheduleArrivalEvent(2, self.lamTwo)

                    elif currentEvent.queue == 3:
                        self.scheduleArrivalEvent(3, self.lamThree)

                    elif currentEvent.queue == 4:
                        self.scheduleArrivalEvent(4, self.lamFour)

            elif currentEvent.typ == 'DEPARTURE':
                #remove customer from queue

                if self.serverStatus[1] == currentEvent.queue:  # check if server is in same queue as event, wss onnodig

                    serverqueue = self.serverStatus[1]
                    switch = [1, 2, 3, 4, 0]

                    if currentEvent.queue == 1:
                        self.queueOne.pop(0)
                        mu = self.muBOne
                        muR = self.muROne

                        probs = [self.pOneOne, self.pOneTwo, self.pOneThree, self.pOneFour, self.pOneZero]
                        new_arrival = np.random.choice(switch, 1, p = probs)[0]

                        if new_arrival == 0:
                            pass
                        else:
                            self.scheduleRejoinEvent(new_arrival)

                        if not self.queueOne.isempty():
                            #print(str(self.queueOne) + ' queue 1')
                            self.scheduleDepartureEvent(serverqueue, mu)
                        else:
                            self.scheduleSwitchEvent(serverqueue, muR)
                            self.serverStatus = (1, serverqueue)


                    elif currentEvent.queue == 2:
                        self.queueTwo.pop(0)
                        mu = self.muBTwo
                        muR = self.muRTwo

                        probs = [self.pTwoOne, self.pTwoTwo, self.pTwoThree, self.pTwoFour, self.pTwoZero]
                        new_arrival = np.random.choice(switch, 1, p=probs)[0]

                        if new_arrival == 0:
                            pass
                        else:
                            self.scheduleRejoinEvent(new_arrival)

                        if not self.queueTwo.isempty():
                            #print(str(self.queueTwo) + ' queue 2')
                            self.scheduleDepartureEvent(serverqueue, mu)
                        else:
                            self.scheduleSwitchEvent(serverqueue, muR)
                            self.serverStatus = (1, serverqueue)


                    elif currentEvent.queue == 3:
                        self.queueThree.pop(0)
                        mu = self.muBThree
                        muR = self.muRThree

                        probs = [self.pThreeOne, self.pThreeTwo, self.pThreeThree, self.pThreeFour, self.pThreeZero]
                        new_arrival = np.random.choice(switch, 1, p=probs)[0]

                        if new_arrival == 0:
                            pass
                        else:
                            self.scheduleRejoinEvent(new_arrival)

                        if not self.queueThree.isempty():
                            #print(str(self.queueThree) + ' queue 3')
                            self.scheduleDepartureEvent(serverqueue, mu)
                        else:
                            self.scheduleSwitchEvent(serverqueue, muR)
                            self.serverStatus = (1, serverqueue)


                    elif currentEvent.queue == 4:
                        self.queueFour.pop(0)
                        mu = self.muBFour
                        muR = self.muRFour

                        probs = [self.pFourOne, self.pFourTwo, self.pFourThree, self.pFourFour, self.pFourZero]
                        new_arrival = np.random.choice(switch, 1, p=probs)[0]

                        if new_arrival == 0:
                            pass
                        else:
                            self.scheduleRejoinEvent(new_arrival)

                        if not self.queueFour.isempty():
                            #print(str(self.queueFour) + ' queue 4')
                            self.scheduleDepartureEvent(serverqueue, mu)
                        else:
                            self.scheduleSwitchEvent(serverqueue, muR)
                            self.serverStatus = (1, serverqueue)

                else: #server in wrong queue
                    raise ValueError('fout')
                    pass

            elif currentEvent.typ == 'SWITCH':

                queue = currentEvent.queue

                if queue == 1:
                    if not self.queueOne.isempty():
                        self.scheduleDepartureEvent(queue, mu)
                        self.serverStatus = (1, queue)
                    else:
                        self.serverStatus = (0, queue)

                if queue == 2:
                    if not self.queueTwo.isempty():
                        self.scheduleDepartureEvent(queue, mu)
                        self.serverStatus = (1, queue)
                    else:
                        self.serverStatus = (0, queue)

                if queue == 3:
                    if not self.queueThree.isempty():
                        self.scheduleDepartureEvent(queue, mu)
                        self.serverStatus = (1, queue)
                    else:
                        self.serverStatus = (0, queue)

                if queue == 4:
                    if not self.queueFour.isempty():
                        self.scheduleDepartureEvent(queue, mu)
                        self.serverStatus = (1, queue)
                    else:
                        self.serverStatus = (0, queue)


            # print(self.currentTime)
            # print(self.queueOne)
            # print(self.queueTwo)
            # print(self.queueThree)
            # print(self.queueFour)
            # print(self.fes)
            # print('')

        # print(self.currentTime)
        # print(self.queueOne)
        # print(self.queueTwo)
        # print(self.queueThree)
        # print(self.queueFour)
        # print(self.fes)
        # print('')
        print("Average queue length queue one: " + str(self.cumQueueOnelen / self.maxTime))
        print("Average queue length queue two: " + str(self.cumQueueTwolen / self.maxTime))
        print("Average queue length queue three: " + str(self.cumQueueThreelen / self.maxTime))
        print("Average queue length queue four: " + str(self.cumQueueFourlen / self.maxTime))


    def initializeEmptySystem(self):
        self.currentTime = 0
        self.queueOne = Queue()
        self.queueTwo = Queue()
        self.queueThree = Queue()
        self.queueFour = Queue()

        self.serverStatus = (0, 1) #(idle, queue 1)
        self.fes = FES()
        self.cumQueueOnelen = 0
        self.cumQueueTwolen = 0
        self.cumQueueThreelen = 0
        self.cumQueueFourlen = 0

    def scheduleArrivalEvent(self, queue, lam):
        # compute new arrival time
        if lam == 0:
            arrivalTime = 0
        else:
            arrivalTime = np.random.exponential(1/lam)

        # schedule arrival at currentTime + arrivaltime
        event = Event("ARRIVAL", self.currentTime + arrivalTime, queue)
        self.fes.add(event)

    def processResults(self, t):
        self.cumQueueOnelen = self.cumQueueOnelen + t * self.queueOne.size()
        self.cumQueueTwolen = self.cumQueueTwolen + t * self.queueTwo.size()
        self.cumQueueThreelen = self.cumQueueThreelen + t * self.queueThree.size()
        self.cumQueueFourlen = self.cumQueueFourlen + t * self.queueFour.size()

    def scheduleDepartureEvent(self, queue, mu):
        # compute new departure time
        serviceTime = np.random.exponential(mu)
        # print('')
        # print('service time:')
        # print(serviceTime)
        # print('')
        # schedule arrival at currentTime + arrivaltime
        event = Event("DEPARTURE", self.currentTime + serviceTime, queue)
        self.fes.add(event)

    def scheduleSwitchEvent(self, queue, mu):
        switchTime = mu

        if queue == 4:
            nextloc = 1
        else:
            nextloc = queue + 1

        event = Event("SWITCH", self.currentTime + switchTime, nextloc)
        self.fes.add(event)

    def scheduleRejoinEvent(self, queue):
        event = Event("REJOIN", self.currentTime, queue)
        self.fes.add(event)

    pass

test = RovingServerQueue('input30.txt', 10000)