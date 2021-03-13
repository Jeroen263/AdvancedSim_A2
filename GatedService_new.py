from FES import FES
from Queue import Queue
from Event import Event
from Customer import Customer
import numpy as np
import matplotlib.pyplot as plt

class GatedService:
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
            self.processQueueLength(self.currentTime - self.oldTime) #add queue length

            if currentEvent.typ == "ARRIVAL" or currentEvent.typ == "REJOIN": #check if event type is arrival or rejoin

                if currentEvent.typ == "REJOIN": #if rejoin, keep old customer
                    customer = self.rejoincustomer
                else: #else make new customer
                    customer = Customer(self.currentTime, self.currentTime, currentEvent.queue, currentEvent.queue)

                if self.inactive:  #check if servers are inactive (first event)

                    self.inactive = False

                    if self.serverStatus == currentEvent.queue: #check if a server is in same queue as event

                        # select the right parameters according to the given queue
                        queue = currentEvent.queue
                        muB = self.muBs[queue]
                        self.queues[queue].addCustomer(customer) #add customer to queue
                        self.gated = 1 #help only customer currently in queue

                        self.scheduleDepartureEvent(queue, muB) #schedule departure event
                        self.processWaitingTime(customer) #add waiting time

                    else: #servers inactive, wrong queue

                        queue = currentEvent.queue #get queue of event
                        serverqueue = self.serverStatus #get queue of server
                        self.queues[queue].addCustomer(customer) #add customer to queue
                        muR = self.muRs[serverqueue]

                        self.scheduleSwitchEvent(serverqueue, muR) #schedule switch event

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
                self.k += 1 #increment customers served in queue

                if ((not self.queues[queue].isempty()) or (new_arrival == queue)) and (self.k < self.gated):
                    #if queue is not empty or customer joins same queue and num of served customers less than k
                    self.scheduleDepartureEvent(queue, muB) #keep serving queue, schedule next departure
                    self.processWaitingTime(customer)
                else:
                    self.scheduleSwitchEvent(queue, muR) #schedule switch if queue is empty

            elif currentEvent.typ == "SWITCH": #if event type is switch

                #get params
                queue = currentEvent.queue #server switches to this queue
                self.serverStatus = queue
                muB = self.muBs[queue]
                muR = self.muRs[queue]
                self.gated = len(self.queues[queue].queue) #determine gate position at end of current queue
                self.k = 0 #reset number of customers served in current queue
                self.processCycleTime(queue) #save time for calculating cycle time

                if not self.queues[queue].isempty(): #if queue is not empty
                    self.scheduleDepartureEvent(queue, muB) #serve customer, schedule departure
                    customer = self.queues[queue].queue[0]
                    self.processWaitingTime(customer) #process customer waiting time
                else:
                    self.scheduleSwitchEvent(queue, muR) #schedule another switch event

            # print(self.currentTime)
            # for i in range(self.n):
            #     print(self.queues[i])
            # print(self.serverStatus)
            # print(self.k, self.gated)
            # print(self.fes)
            # print('')


        fig1, axs1 = plt.subplots(2, 2)
        fig2, axs2 = plt.subplots(2, 2)
        axes = [[0,0], [0,1], [1,0], [1,1]]
        colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red']

        for i in range(self.n): #print all interesting performance measures and create plots
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

            axs1[axes[i][0], axes[i][1]].plot(self.waitingTimes[i], color=colors[i])

            axs2[axes[i][0], axes[i][1]].hist(self.waitingTimes[i], bins=range(int(min(self.waitingTimes[i])), int(max(self.waitingTimes[i])) + 1, 1), color=colors[i])

        plt.show()


    def initializeEmptySystem(self): #initialize empty system
        self.currentTime = 0 #set time to 0
        self.k = 0 #initialize number of customers served in queue
        self.gated = 0 #initialize gate threshold

        self.queues = []
        self.cumQueueslen = []
        self.waitingTimes = []
        self.cycleTimes = []
        self.sojournTimes = []
        for i in range(self.n): #create queues and performance measure variables
            self.queues.append(Queue())
            self.cumQueueslen.append(0)
            self.waitingTimes.append([])
            self.cycleTimes.append([])
            self.sojournTimes.append([])

        self.serverStatus = 0 #initialize server at queue 0
        self.cycleTimes[self.serverStatus].append(0) #first cycle time
        self.inactive = True #servers are inactive initially
        self.fes = FES() #create future event set

    def scheduleArrivalEvent(self, queue, lam):
        arrivalTime = np.random.exponential(1/lam) #take arrival time from distribution

        event = Event("ARRIVAL", self.currentTime + arrivalTime, queue) #schedule arrival event
        self.fes.add(event)

    def processQueueLength(self, t):
        for i in range(self.n): #add queue length to corresponding queue
            self.cumQueueslen[i] = self.cumQueueslen[i] + t * self.queues[i].size()

    def processWaitingTime(self, customer):
        queue = customer.queue #get queue
        queueJoinTime = customer.queueJoinTime #get time customer joined the queue
        waitingTime = self.currentTime - queueJoinTime #calculate waiting time
        self.waitingTimes[queue].append(waitingTime) #add waiting time

    def processSojournTime(self, customer):
        queue = customer.queue #get queue
        arrivalTime = customer.arrivalTime #get arrival time in system of customer
        sojournTime = self.currentTime - arrivalTime #calculate sojourn time
        self.sojournTimes[queue].append(sojournTime) #add sojourn time

    def processCycleTime(self, queue):
        self.cycleTimes[queue].append(self.currentTime) #add time of cycle completion

    def calculateCycleTime(self, queue):
        timestamps = self.cycleTimes[queue] #get times of finished cycles
        lenOfCycles = np.zeros(len(timestamps)-1) #intialize cycle times array
        for i in range(len(timestamps)-1): #calculate cycle times
            lenOfCycles[i] = timestamps[i+1] - timestamps[i]
        return lenOfCycles #return cycle times

    def scheduleDepartureEvent(self, queue, mu):
        # compute new departure time
        serviceTime = np.random.exponential(mu)
        # schedule arrival at currentTime + arrivaltime
        event = Event("DEPARTURE", self.currentTime + serviceTime, queue)
        self.fes.add(event) #add to future event set

    def scheduleSwitchEvent(self, queue, mu):
        switchTime = mu #switch time is discrete
        nextloc = queue + 1 #switch to next queue
        if nextloc > (self.n-1): #make sure queue exists
            nextloc = 0

        event = Event("SWITCH", self.currentTime + switchTime, nextloc) #schedule switch event
        self.fes.add(event) #add to future event set

    def scheduleRejoinEvent(self, queue, customer):
        event = Event("REJOIN", self.currentTime, queue) #schedule rejoin event
        self.rejoincustomer = Customer(customer.arrivalTime, self.currentTime, queue, customer.arrivalQueue) #save customer data
        self.fes.add(event) #add to future event set

    def calculateCI(self, data, z):
        avg = sum(data) / len(data) #get mean
        stdev = np.std(data) #get standard deviation
        halfWidth = z * stdev / np.sqrt(len(data)) #get halfwidth
        ci = (avg-halfWidth, avg+halfWidth) #get ci
        return ci #return ci


np.random.seed(10)
test = GatedService('input30.txt', 100)