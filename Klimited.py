from FES import FES
from Queue import Queue
from Event import Event
from Customer import Customer
import numpy as np

class RovingServerQueue:
    def __init__(self, inputfile, maxTime):
        self.maxTime = maxTime
        with open(inputfile) as f:
            #params = f.read()
            #params = params.replace('\n', ' ').replace('\t', ' ').split(' ')
            params = f.read().splitlines()

        paramlist = []
        for line in params:
            line = line.replace('\t', ' ').split(' ')
            line = list(map(float, line))
            paramlist.append(line)

        self.n = len(paramlist[0]) #number of queues
        self.lams = paramlist[0] #lambdas
        self.muBs = paramlist[1] #mean service times
        self.muRs = paramlist[2] #mean switch times
        self.ks = paramlist[3] #k's
        self.ps = [] #rejoin probabilities
        self.k = 0
        for i in range(self.n):
            p = paramlist[4+i] + [np.round(1 - sum(paramlist[4+i]), 2)]
            self.ps.append(p)

        # self.lamOne = float(params[0])
        # self.lamTwo = float(params[1])
        # self.lamThree = float(params[2])
        # self.lamFour = float(params[3])
        # self.muBOne = float(params[4])
        # self.muBTwo = float(params[5])
        # self.muBThree = float(params[6])
        # self.muBFour = float(params[7])
        # self.muROne = float(params[8])
        # self.muRTwo = float(params[9])
        # self.muRThree = float(params[10])
        # self.muRFour = float(params[11])
        # self.kOne = float(params[12])
        # self.kTwo = float(params[13])
        # self.kThree = float(params[14])
        # self.kFour = float(params[15])
        # self.pOneOne = float(params[16])
        # self.pOneTwo = float(params[17])
        # self.pOneThree = float(params[18])
        # self.pOneFour = float(params[19])
        # self.pTwoOne = float(params[20])
        # self.pTwoTwo = float(params[21])
        # self.pTwoThree = float(params[22])
        # self.pTwoFour = float(params[23])
        # self.pThreeOne = float(params[24])
        # self.pThreeTwo = float(params[25])
        # self.pThreeThree = float(params[26])
        # self.pThreeFour = float(params[27])
        # self.pFourOne = float(params[28])
        # self.pFourTwo = float(params[29])
        # self.pFourThree = float(params[30])
        # self.pFourFour = float(params[31])
        #
        # self.pOneZero = 1 - (self.pOneOne + self.pOneTwo + self.pOneThree + self.pOneFour)
        # self.pTwoZero = 1 - (self.pTwoOne + self.pTwoTwo + self.pTwoThree + self.pTwoFour)
        # self.pThreeZero = 1 - (self.pThreeOne + self.pThreeTwo + self.pThreeThree + self.pThreeFour)
        # self.pFourZero = 1 - (self.pFourOne + self.pFourTwo + self.pFourThree + self.pFourFour)

        print('Initialize empty queue')
        self.initializeEmptySystem()
        print('schedule first arrivals')

        # self.scheduleArrivalEvent(1, self.lamOne)
        # self.scheduleArrivalEvent(1, self.lamTwo)
        # self.scheduleArrivalEvent(1, self.lamThree)
        # self.scheduleArrivalEvent(1, self.lamFour)

        for i in range(self.n): #schedule arrival in every queue
            lam = self.lams[i]
            self.scheduleArrivalEvent(i, lam)

        # print(self.currentTime)
        # for i in range(self.n):
        #     print(self.queues[i])
        # print(self.fes)
        # print('')

        while self.currentTime < maxTime:

            #get event
            currentEvent = self.fes.next()
            self.oldTime = self.currentTime
            self.currentTime = currentEvent.time
            self.processResults(self.currentTime - self.oldTime)

            if currentEvent.typ == "ARRIVAL" or currentEvent.typ == "REJOIN":

                if currentEvent.typ == "REJOIN":
                    customer = self.rejoincustomer
                else:
                    customer = Customer(self.currentTime, self.currentTime, currentEvent.queue, currentEvent.queue)

                if self.serverStatus[0] == 0:  #check if server is inactive

                    if self.serverStatus[1] == currentEvent.queue: #check if server is in same queue as event and can be helped immediately

                        # select the right parameters according to the given queue
                        queue = currentEvent.queue
                        muB = self.muBs[queue]
                        self.queues[queue].addCustomer(customer)

                        # if currentEvent.queue == 1:
                        #     queue = currentEvent.queue
                        #     mu = self.muBOne
                        #     self.queueOne.addCustomer(customer)
                        #
                        # elif currentEvent.queue == 2:
                        #     queue = currentEvent.queue
                        #     mu = self.muBTwo
                        #     self.queueTwo.addCustomer(customer)
                        #
                        # elif currentEvent.queue == 3:
                        #     queue = currentEvent.queue
                        #     mu = self.muBThree
                        #     self.queueThree.addCustomer(customer)
                        #
                        # elif currentEvent.queue == 4:
                        #     queue = currentEvent.queue
                        #     mu = self.muBFour
                        #     self.queueFour.addCustomer(customer)

                        self.serverStatus = (1, queue) #misschien fout
                        self.scheduleDepartureEvent(queue, muB)
                        self.processWaitingTime(customer)

                    else: #server inactive, wrong queue

                        serverqueue = self.serverStatus[1]
                        queue = currentEvent.queue
                        self.queues[queue].addCustomer(customer)
                        muR = self.muRs[queue]

                        # if currentEvent.queue == 1:
                        #     self.queueOne.addCustomer(customer)
                        #     mu = self.muROne
                        #
                        # elif currentEvent.queue == 2:
                        #     self.queueTwo.addCustomer(customer)
                        #     mu = self.muRTwo
                        #
                        # elif currentEvent.queue == 3:
                        #     self.queueThree.addCustomer(customer)
                        #     mu = self.muRThree
                        #
                        # elif currentEvent.queue == 4:
                        #     self.queueFour.addCustomer(customer)
                        #     mu = self.muRFour

                        if not self.fes.checkSwitch():

                            if self.queues[serverqueue].isempty() or self.k >= self.ks[serverqueue]:
                                self.scheduleSwitchEvent(serverqueue, muR)
                                self.serverStatus = (1, serverqueue)


                            # if serverqueue == 1:
                            #     if self.queueOne.isempty():
                            #         self.scheduleSwitchEvent(serverqueue, mu)
                            #         self.serverStatus = (1, serverqueue)
                            #
                            # elif serverqueue == 2:
                            #     if self.queueTwo.isempty():
                            #         self.scheduleSwitchEvent(serverqueue, mu)
                            #         self.serverStatus = (1, serverqueue)
                            #
                            # elif serverqueue == 3:
                            #     if self.queueThree.isempty():
                            #         self.scheduleSwitchEvent(serverqueue, mu)
                            #         self.serverStatus = (1, serverqueue)
                            #
                            # elif serverqueue == 4:
                            #     if self.queueFour.isempty():
                            #         self.scheduleSwitchEvent(serverqueue, mu)
                            #         self.serverStatus = (1, serverqueue)



                else: #server active

                    queue = currentEvent.queue
                    self.queues[queue].addCustomer(customer)

                    # if currentEvent.queue == 1:
                    #     self.queueOne.addCustomer(customer)
                    #
                    # elif currentEvent.queue == 2:
                    #     self.queueTwo.addCustomer(customer)
                    #
                    # elif currentEvent.queue == 3:
                    #     self.queueThree.addCustomer(customer)
                    #
                    # elif currentEvent.queue == 4:
                    #     self.queueFour.addCustomer(customer)


                if currentEvent.typ == "ARRIVAL":

                    #schedule new arrival
                    queue = currentEvent.queue
                    lam = self.lams[queue]
                    self.scheduleArrivalEvent(queue, lam)

                    # if currentEvent.queue == 1:
                    #     self.scheduleArrivalEvent(1, self.lamOne)
                    #
                    # elif currentEvent.queue == 2:
                    #     self.scheduleArrivalEvent(2, self.lamTwo)
                    #
                    # elif currentEvent.queue == 3:
                    #     self.scheduleArrivalEvent(3, self.lamThree)
                    #
                    # elif currentEvent.queue == 4:
                    #     self.scheduleArrivalEvent(4, self.lamFour)

            elif currentEvent.typ == 'DEPARTURE':
                #remove customer from queue

                if self.serverStatus[1] == currentEvent.queue:  # check if server is in same queue as event, wss onnodig

                    #serverqueue = self.serverStatus[1]
                    switch = range(0, (self.n+1))
                    #switch = [1, 2, 3, 4, 0]

                    queue = currentEvent.queue
                    customer = self.queues[queue].queue[0]

                    muB = self.muBs[queue]
                    muR = self.muRs[queue]
                    probs = self.ps[queue]
                    new_arrival = np.random.choice(switch, 1, p=probs)[0]

                    if new_arrival == self.n:
                        self.processSojournTime(customer)
                    else:
                        self.scheduleRejoinEvent(new_arrival, customer)

                    self.queues[queue].pop(0)
                    self.k += 1

                    if not self.queues[queue].isempty() and self.k < self.ks[queue]:
                        self.scheduleDepartureEvent(queue, muB)
                        self.processWaitingTime(customer)
                    else:
                        self.scheduleSwitchEvent(queue, muR)
                        self.serverStatus = (1, queue)


                    # if currentEvent.queue == 1:
                    #     self.queueOne.pop(0)
                    #     mu = self.muBOne
                    #     muR = self.muROne
                    #
                    #     probs = [self.pOneOne, self.pOneTwo, self.pOneThree, self.pOneFour, self.pOneZero]
                    #     new_arrival = np.random.choice(switch, 1, p = probs)[0]
                    #
                    #     if new_arrival == 0:
                    #         pass
                    #     else:
                    #         self.scheduleRejoinEvent(new_arrival)
                    #
                    #     if not self.queueOne.isempty():
                    #         #print(str(self.queueOne) + ' queue 1')
                    #         self.scheduleDepartureEvent(serverqueue, mu)
                    #     else:
                    #         self.scheduleSwitchEvent(serverqueue, muR)
                    #         self.serverStatus = (1, serverqueue)
                    #

                    # elif currentEvent.queue == 2:
                    #     self.queueTwo.pop(0)
                    #     mu = self.muBTwo
                    #     muR = self.muRTwo
                    #
                    #     probs = [self.pTwoOne, self.pTwoTwo, self.pTwoThree, self.pTwoFour, self.pTwoZero]
                    #     new_arrival = np.random.choice(switch, 1, p=probs)[0]
                    #
                    #     if new_arrival == 0:
                    #         pass
                    #     else:
                    #         self.scheduleRejoinEvent(new_arrival)
                    #
                    #     if not self.queueTwo.isempty():
                    #         #print(str(self.queueTwo) + ' queue 2')
                    #         self.scheduleDepartureEvent(serverqueue, mu)
                    #     else:
                    #         self.scheduleSwitchEvent(serverqueue, muR)
                    #         self.serverStatus = (1, serverqueue)
                    #
                    #
                    # elif currentEvent.queue == 3:
                    #     self.queueThree.pop(0)
                    #     mu = self.muBThree
                    #     muR = self.muRThree
                    #
                    #     probs = [self.pThreeOne, self.pThreeTwo, self.pThreeThree, self.pThreeFour, self.pThreeZero]
                    #     new_arrival = np.random.choice(switch, 1, p=probs)[0]
                    #
                    #     if new_arrival == 0:
                    #         pass
                    #     else:
                    #         self.scheduleRejoinEvent(new_arrival)
                    #
                    #     if not self.queueThree.isempty():
                    #         #print(str(self.queueThree) + ' queue 3')
                    #         self.scheduleDepartureEvent(serverqueue, mu)
                    #     else:
                    #         self.scheduleSwitchEvent(serverqueue, muR)
                    #         self.serverStatus = (1, serverqueue)
                    #
                    #
                    # elif currentEvent.queue == 4:
                    #     self.queueFour.pop(0)
                    #     mu = self.muBFour
                    #     muR = self.muRFour
                    #
                    #     probs = [self.pFourOne, self.pFourTwo, self.pFourThree, self.pFourFour, self.pFourZero]
                    #     new_arrival = np.random.choice(switch, 1, p=probs)[0]
                    #
                    #     if new_arrival == 0:
                    #         pass
                    #     else:
                    #         self.scheduleRejoinEvent(new_arrival)
                    #
                    #     if not self.queueFour.isempty():
                    #         #print(str(self.queueFour) + ' queue 4')
                    #         self.scheduleDepartureEvent(serverqueue, mu)
                    #     else:
                    #         self.scheduleSwitchEvent(serverqueue, muR)
                    #         self.serverStatus = (1, serverqueue)

                else: #server in wrong queue
                    raise ValueError('fout')
                    pass

            elif currentEvent.typ == 'SWITCH':

                queue = currentEvent.queue
                muB = self.muBs[queue]
                self.processCycleTime(queue)
                self.k = 0

                if not self.queues[queue].isempty():
                    self.scheduleDepartureEvent(queue, muB)
                    customer = self.queues[queue].queue[0]
                    self.processWaitingTime(customer)
                    self.serverStatus = (1, queue)
                else:
                    self.serverStatus = (0, queue)

                # if queue == 1:
                #     if not self.queueOne.isempty():
                #         self.scheduleDepartureEvent(queue, mu)
                #         self.serverStatus = (1, queue)
                #     else:
                #         self.serverStatus = (0, queue)
                #
                # if queue == 2:
                #     if not self.queueTwo.isempty():
                #         self.scheduleDepartureEvent(queue, mu)
                #         self.serverStatus = (1, queue)
                #     else:
                #         self.serverStatus = (0, queue)
                #
                # if queue == 3:
                #     if not self.queueThree.isempty():
                #         self.scheduleDepartureEvent(queue, mu)
                #         self.serverStatus = (1, queue)
                #     else:
                #         self.serverStatus = (0, queue)
                #
                # if queue == 4:
                #     if not self.queueFour.isempty():
                #         self.scheduleDepartureEvent(queue, mu)
                #         self.serverStatus = (1, queue)
                #     else:
                #         self.serverStatus = (0, queue)


            # print(self.currentTime)
            # print(self.queueOne)
            # print(self.queueTwo)
            # print(self.queueThree)
            # print(self.queueFour)
            # print(self.fes)
            # print('')

            # print(self.currentTime)
            # for i in range(self.n):
            #     print(self.queues[i])
            # print(self.fes)
            # print('')

        # print(self.currentTime)
        # print(self.queueOne)

        # print(self.queueThree)
        # print(self.queueFour)
        # print(self.fes)
        # print('')
        # print("Average queue length queue one: " + str(self.cumQueueOnelen / self.maxTime))
        # print("Average queue length queue two: " + str(self.cumQueueTwolen / self.maxTime))
        # print("Average queue length queue three: " + str(self.cumQueueThreelen / self.maxTime))
        # print("Average queue length queue four: " + str(self.cumQueueFourlen / self.maxTime))
        for i in range(self.n):
            print("Average queue length queue " + str(i) + ": " + str(self.cumQueueslen[i] / self.maxTime))
            print("Average waiting time queue " + str(i) + ": " + str(sum(self.waitingTimes[i]) / len(self.waitingTimes[i])))
            print("Average sojourn time queue " + str(i) + ": " + str(sum(self.sojournTimes[i]) / len(self.sojournTimes[i])))
            cycles = len(self.cycleTimes[i]) - 1
            cycletime = self.cycleTimes[i][cycles] - self.cycleTimes[i][0]
            #print(self.cycleTimes[i], cycles, cycletime)
            print("Average cycle time queue " + str(i) + ": " + str(cycletime / cycles))
            print('')


    def initializeEmptySystem(self):
        self.currentTime = 0

        self.queues = []
        self.cumQueueslen = []
        self.waitingTimes = []
        self.cycleTimes = []
        self.sojournTimes = []
        for i in range(self.n):
            self.queues.append(Queue())
            self.cumQueueslen.append(0)
            self.waitingTimes.append([])
            self.cycleTimes.append([])
            self.sojournTimes.append([])

        self.serverStatus = (0, 0) #(idle, queue 1)
        self.cycleTimes[0].append(0)
        self.fes = FES()

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
        for i in range(self.n):
            self.cumQueueslen[i] = self.cumQueueslen[i] + t * self.queues[i].size()
        # self.cumQueueOnelen = self.cumQueueOnelen + t * self.queueOne.size()
        # self.cumQueueTwolen = self.cumQueueTwolen + t * self.queueTwo.size()
        # self.cumQueueThreelen = self.cumQueueThreelen + t * self.queueThree.size()
        # self.cumQueueFourlen = self.cumQueueFourlen + t * self.queueFour.size()

    def processWaitingTime(self, customer):
        queue = customer.queue
        queueJoinTime = customer.queueJoinTime
        waitingTime = self.currentTime - queueJoinTime
        self.waitingTimes[queue].append(waitingTime)

    def processSojournTime(self, customer):
        queue = customer.queue
        arrivalTime = customer.arrivalTime
        sojournTime = self.currentTime - arrivalTime
        self.sojournTimes[queue].append(sojournTime)

    def processCycleTime(self, queue):
        self.cycleTimes[queue].append(self.currentTime)

    def scheduleDepartureEvent(self, queue, mu):
        # compute new departure time
        serviceTime = np.random.exponential(mu)
        # schedule arrival at currentTime + arrivaltime
        event = Event("DEPARTURE", self.currentTime + serviceTime, queue)
        self.fes.add(event)

    def scheduleSwitchEvent(self, queue, mu):
        switchTime = mu
        nextloc = queue + 1
        if nextloc > (self.n-1):
            nextloc = 0

        # if queue == 4:
        #     nextloc = 1
        # else:
        #     nextloc = queue + 1

        event = Event("SWITCH", self.currentTime + switchTime, nextloc)
        self.fes.add(event)

    def scheduleRejoinEvent(self, queue, customer):
        event = Event("REJOIN", self.currentTime, queue)
        self.rejoincustomer = Customer(customer.arrivalTime, self.currentTime, queue, customer.arrivalQueue)
        self.fes.add(event)

    pass

test = RovingServerQueue('input30.txt', 100000)