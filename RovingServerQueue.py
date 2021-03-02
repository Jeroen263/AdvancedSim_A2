import FES
import Queue
import Event
import Customer
import numpy as np

class RovingServerQueue:
    def __init__(self, inputfile, maxTime):
        self.maxTime = maxTime
        with open(inputfile) as f:
            params = f.read()
            params = params.replace('\n', ' ').replace('\t', ' ').split(' ')
        self.lamOne = params[0]
        self.lamTwo = params[1]
        self.lamThree = params[2]
        self.lamFour = params[3]
        self.muBOne = params[4]
        self.muBTwo = params[5]
        self.muBThree = params[6]
        self.muBFour = params[7]
        self.muROne = params[8]
        self.muRTwo = params[9]
        self.muRThree = params[10]
        self.muRFour = params[11]
        self.kOne = params[12]
        self.kTwo = params[13]
        self.kThree = params[14]
        self.kFour = params[15]
        self.pOneOne = params[16]
        self.pOneTwo = params[17]
        self.pOneThree = params[18]
        self.pOneFour = params[19]
        self.pTwoOne = params[20]
        self.pTwoTwo = params[21]
        self.pTwoThree = params[22]
        self.pTwoFour = params[23]
        self.pThreeOne = params[24]
        self.pThreeTwo = params[25]
        self.pThreeThree = params[26]
        self.pThreeFour = params[27]
        self.pFourOne = params[28]
        self.pFourTwo = params[29]
        self.pFourThree = params[30]
        self.pFourFour = params[31]

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

            if currentEvent.typ == 'ARRIVAL':

                customer = Customer(self.currentTime, currentEvent.queue)

                if self.serverStatus[0] == 0:

                    if self.serverStatus[1] == currentEvent.queue:

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

                        self.serverStatus = queue #?? fout
                        self.scheduleDepartureEvent(queue, mu)

                    else:
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

                        #self.serverStatus ==
                        self.scheduleSwitchEvent(queue, mu)


                else:
                    if currentEvent.queue == 1:
                        self.queueOne.addCustomer(customer)

                    elif currentEvent.queue == 2:
                        self.queueTwo.addCustomer(customer)

                    elif currentEvent.queue == 3:
                        self.queueThree.addCustomer(customer)

                    elif currentEvent.queue == 4:
                        self.queueFour.addCustomer(customer)

                if currentEvent.queue == 1:
                    self.scheduleArrivalEvent(1, self.lamOne)

                elif currentEvent.queue == 2:
                    self.scheduleArrivalEvent(2, self.lamTwo)

                elif currentEvent.queue == 3:
                    self.scheduleArrivalEvent(4, self.lamThree)

                elif currentEvent.queue == 4:
                    self.scheduleArrivalEvent(1, self.lamFour)

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
        arrivalTime = np.random.exponential(1 / lam)
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
        # schedule arrival at currentTime + arrivaltime
        event = Event("DEPARTURE", self.currentTime + serviceTime, queue)

    def scheduleSwitchEvent(self, queue, mu):
        switchTime = np.random.exponential(mu)

        if queue == 4:
            nextloc = 1
        else:
            nextloc = queue + 1

        event = Event("SWITCH", self.currentTime + switchTime, queue)


    pass

test = RovingServerQueue('input30.txt')