from FES import FES
from Queue import Queue
from Event import Event
from Customer import Customer
import numpy as np
import matplotlib.pyplot as plt

class RovingServerQueue:
    def __init__(self, inputfile, maxTime):
        self.maxTime = maxTime #max time specified
        with open(inputfile) as f:
            params = f.read().splitlines() #read input file of parameters

        paramlist = []
        for line in params: #process input file
            line = line.replace('\t', ' ').split(' ')
            line = list(map(float, line))
            paramlist.append(line)

        #define all parameters
        self.n = len(paramlist[0]) #number of queues
        self.lams = paramlist[0] #lambdas
        self.muBs = paramlist[1] #mean service times
        self.muRs = paramlist[2] #mean switch times
        self.ks = paramlist[3] #k's
        self.ps = [] #rejoin probabilities
        for i in range(self.n):
            p = paramlist[4+i] + [np.round(1 - sum(paramlist[4+i]), 2)]
            self.ps.append(p)

        self.switch = range(0, (self.n + 1)) #list of queue numbers used for scheduling rejoin event

        print('Initialize empty queue')
        self.initializeEmptySystem()
        print('schedule first arrivals')

        for i in range(self.n): #schedule arrival in every queue
            lam = self.lams[i]
            self.scheduleArrivalEvent(i, lam)

        while self.currentTime < maxTime: #loop until max time reached

            #get event
            currentEvent = self.fes.next()
            self.oldTime = self.currentTime #set old time
            self.currentTime = currentEvent.time #set current time
            self.processResults(self.currentTime - self.oldTime) #add queue length

            if currentEvent.typ == "ARRIVAL" or currentEvent.typ == "REJOIN": #check if event type is arrival or rejoin

                if currentEvent.typ == "REJOIN": #if rejoin, keep old customer
                    customer = self.rejoincustomer
                else: #else make new customer
                    customer = Customer(self.currentTime, self.currentTime, currentEvent.queue, currentEvent.queue)

                if self.serverStatus[0] == 0:  #check if server is inactive (first event)

                    if self.serverStatus[1] == currentEvent.queue: #check if server is in same queue as event

                        # select the right parameters according to the given queue
                        queue = currentEvent.queue
                        muB = self.muBs[queue]
                        self.queues[queue].addCustomer(customer) #add customer to queue

                        self.serverStatus = (1, queue) #set server status to active
                        self.scheduleDepartureEvent(queue, muB) #schedule departure event
                        self.processWaitingTime(customer) #add waiting time

                    else: #server inactive, wrong queue

                        serverqueue = self.serverStatus[1] #get queue of server
                        queue = currentEvent.queue #get queue of event
                        self.queues[queue].addCustomer(customer) #add customer to queue
                        muR = self.muRs[serverqueue] #get switchtime

                        #if self.fes.checkSwitch(): #if no switch is scheduled yet, schedule switch
                            #raise ValueError('fout')
                        #niet nodig

                        if self.queues[serverqueue].isempty(): #only schedule switch if queue of server is empty
                            self.scheduleSwitchEvent(serverqueue, muR) #schedule switch
                            self.serverStatus = (1, serverqueue) #set server status to active

                else: #server active

                    queue = currentEvent.queue
                    self.queues[queue].addCustomer(customer) #add customer to queue

                if currentEvent.typ == "ARRIVAL": #if event is arrival, schedule next arrival

                    #schedule new arrival
                    queue = currentEvent.queue
                    lam = self.lams[queue]
                    self.scheduleArrivalEvent(queue, lam)

            elif currentEvent.typ == "DEPARTURE": #if event type is departure

                queue = currentEvent.queue #get queue
                customer = self.queues[queue].queue[0] #get customer

                #get params
                muB = self.muBs[queue]
                muR = self.muRs[queue]
                probs = self.ps[queue]
                new_arrival = np.random.choice(self.switch, 1, p=probs)[0] #pick a queue to rejoin

                if new_arrival == self.n: #if customer leaves system
                    self.processSojournTime(customer) #add sojourn time
                else:
                    self.scheduleRejoinEvent(new_arrival, customer) #schedule rejoin

                self.queues[queue].pop(0) #remove customer from queue

                if (not self.queues[queue].isempty()) or (new_arrival == queue): #if queue is not empty or customer joins same queue
                    self.scheduleDepartureEvent(queue, muB) #keep serving queue, schedule next departure
                    self.processWaitingTime(customer)
                else:
                    self.scheduleSwitchEvent(queue, muR) #schedule switch if queue is empty
                    #self.serverStatus = (1, queue) #set server to active
                    #niet nodig

            elif currentEvent.typ == "SWITCH": #if event type is switch

                #get params
                queue = currentEvent.queue #server switches to this queue
                muB = self.muBs[queue]
                muR = self.muRs[queue]
                self.processCycleTime(queue) #save time for calculating cycle time
                self.serverStatus = (1, queue) #add server to next queue

                if not self.queues[queue].isempty(): #if queue is not empty
                    self.scheduleDepartureEvent(queue, muB) #serve customer, schedule departure
                    customer = self.queues[queue].queue[0]
                    self.processWaitingTime(customer) #process customer waiting time
                    #self.serverStatus = (1, queue) #set server to active
                else:
                    self.scheduleSwitchEvent(queue, muR) #schedule another switch event
                    #self.serverStatus = (1, queue) #set server to active
                    #should add switch event here

            print(self.currentTime)
            for i in range(self.n):
                print(self.queues[i])
            print(self.fes)
            print('')

        plt.figure()

        for i in range(self.n):
            print("Average queue length queue " + str(i) + ": " + str(self.cumQueueslen[i] / self.maxTime))
            print("Average waiting time queue " + str(i) + ": " +str(sum(self.waitingTimes[i]) / len(self.waitingTimes[i]))
                  + ' ' + str(self.calculateCI(self.waitingTimes[i], 1.96)))
            print("Average sojourn time queue " + str(i) + ": " + str(sum(self.sojournTimes[i]) / len(self.sojournTimes[i]))
                  + ' ' + str(self.calculateCI(self.sojournTimes[i], 1.96)))

            # cycles = len(self.cycleTimes[i]) - 1
            # cycletime = self.cycleTimes[i][cycles] - self.cycleTimes[i][0]
            # print(self.cycleTimes[i], cycles, cycletime)
            # print("Average cycle time queue " + str(i) + ": " + str(cycletime / cycles))

            cycles = self.calculateCycleTime(i)
            print("Average cycle time queue " + str(i) + ": " + str(sum(cycles) / len(cycles))
                  + ' ' + str(self.calculateCI(cycles, 1.96)))
            print('')

            plt.plot(self.waitingTimes[i])
            plt.show()

            plt.hist(self.waitingTimes[i], bins=range(int(min(self.waitingTimes[i])), int(max(self.waitingTimes[i])) + 1, 1))
            plt.show()






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

    def calculateCycleTime(self, queue):
        timestamps = self.cycleTimes[queue]
        lenOfCycles = np.zeros(len(timestamps)-1)
        for i in range(len(timestamps)-1):
            lenOfCycles[i] = timestamps[i+1] - timestamps[i]
        return lenOfCycles

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

        event = Event("SWITCH", self.currentTime + switchTime, nextloc)
        self.fes.add(event)

    def scheduleRejoinEvent(self, queue, customer):
        event = Event("REJOIN", self.currentTime, queue)
        self.rejoincustomer = Customer(customer.arrivalTime, self.currentTime, queue, customer.arrivalQueue)
        self.fes.add(event)

    def calculateCI(self, data, z):
        avg = sum(data) / len(data)
        stdev = np.std(data)
        halfWidth = z * stdev / np.sqrt(len(data))
        ci = (avg-halfWidth, avg+halfWidth)
        return ci

    pass

np.random.seed(10)
test = RovingServerQueue('input30.txt', 100)