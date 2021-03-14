from FES import FES
from Queue import Queue
from Event import Event
from Customer import Customer
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

class RovingServerQueue:
    def __init__(self, inputfile, maxTime, servers):
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
        self.servers = servers #number of servers, should be less or equal than number of queues
        if self.servers >= self.n:
            print('Too many servers specified, setting amount of servers equal to number of queues minus 1')
            self.servers = self.n - 1
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

                    if currentEvent.queue in self.serverStatus: #check if a server is in same queue as event

                        # select the right parameters according to the given queue
                        queue = currentEvent.queue
                        muB = self.muBs[queue]
                        self.queues[queue].addCustomer(customer) #add customer to queue

                        self.scheduleDepartureEvent(queue, muB) #schedule departure event
                        self.processWaitingTime(customer) #add waiting time

                        for status in self.serverStatus:
                            if not (status == queue):
                                muR = self.muRs[status]  # get switchtime
                                self.scheduleSwitchEvent(status, muR)

                    else: #servers inactive, wrong queue

                        queue = currentEvent.queue #get queue of event
                        self.queues[queue].addCustomer(customer) #add customer to queue

                        for status in self.serverStatus:
                            muR = self.muRs[status]  # get switchtime
                            self.scheduleSwitchEvent(status, muR)


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

            elif currentEvent.typ == "SWITCH": #if event type is switch

                #get params
                queue = currentEvent.queue #server switches to this queue
                oldqueue = queue-1 #queue server is in before switch
                if oldqueue < 0:
                    oldqueue = self.n - 1

                while queue in self.serverStatus: #make sure no other server is in queue already
                    queue += 1
                    queue = queue % (self.n)

                self.serverStatus = np.where(self.serverStatus == oldqueue, queue, self.serverStatus) #change server status

                muB = self.muBs[queue]
                muR = self.muRs[queue]
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
            # print(self.fes)
            # print('')

        #calculate performance measures and make plots
        self.calculateCycleTime()
        self.calculateMovingAverage(self.waitingTimes, self.meanWaitingTimes)
        self.calculateMovingAverage(self.sojournTimes, self.meanSojournTimes)
        self.calculateMovingAverage(self.cycleLengths, self.meanCycleTimes)
        self.makeLinePlot(self.meanWaitingTimes, 'Mean waiting times of customers', 'Customer', 'Waiting time')
        self.makeLinePlot(self.meanSojournTimes, 'Mean sojourn times of customers', 'Customer', 'Sojourn time')
        self.makeLinePlot(self.meanCycleTimes, 'Mean cycle time', 'Cycle', 'Time')
        self.makeHistogram(self.waitingTimes, 'Distribution of waiting times', 'Waiting time', 'Number of customers')
        self.makeHistogram(self.waitingTimes, 'Distribution of sojourn times', 'Sojourn time', 'Number of customers')
        self.makeHistogram(self.waitingTimes, 'Distribution of cycle times', 'Cycle time', 'Number of cycles')

        for i in range(self.n): #print all interesting performance measures
            print("Average queue length queue " + str(i) + ": " + str(self.cumQueueslen[i] / self.maxTime))
            print("Average waiting time queue " + str(i) + ": " +str(sum(self.waitingTimes[i]) / len(self.waitingTimes[i]))
                  + ' ' + str(self.calculateCI(self.waitingTimes[i], 1.96)))
            print("Average sojourn time queue " + str(i) + ": " + str(sum(self.sojournTimes[i]) / len(self.sojournTimes[i]))
                  + ' ' + str(self.calculateCI(self.sojournTimes[i], 1.96)))
            print("Average cycle time queue " + str(i) + ": " + str(sum(self.cycleLengths[i]) / len(self.cycleLengths[i]))
                  + ' ' + str(self.calculateCI(self.cycleLengths[i], 1.96)))
            print('')


    def initializeEmptySystem(self): #initialize empty system
        self.currentTime = 0 #set time to 0

        self.queues = []
        self.cumQueueslen = []
        self.waitingTimes = []
        self.cycleTimes = []
        self.sojournTimes = []
        self.meanWaitingTimes = []
        self.meanCycleTimes = []
        self.meanSojournTimes = []
        for i in range(self.n): #create queues and performance measure variables
            self.queues.append(Queue())
            self.cumQueueslen.append(0)
            self.waitingTimes.append([])
            self.cycleTimes.append([])
            self.sojournTimes.append([])
            self.meanWaitingTimes.append([])
            self.meanCycleTimes.append([])
            self.meanSojournTimes.append([])


        self.serverStatus = np.zeros(self.servers, dtype=int)
        for i in range(self.servers):
            self.serverStatus[i] = i #distribute servers over queues
            self.cycleTimes[i].append(0)  #initialize first cycle in queues with server

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

    def calculateCycleTime(self):
        self.cycleLengths = []
        for queue in range(self.n):
            timestamps = self.cycleTimes[queue] #get times of finished cycles
            lenOfCycles = np.zeros(len(timestamps)-1) #intialize cycle times array
            for i in range(len(timestamps)-1): #calculate cycle times
                lenOfCycles[i] = timestamps[i+1] - timestamps[i]

            self.cycleLengths.append(lenOfCycles)
            #lenOfCycles #return cycle times

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

    # def calculateMeanWaitingTime(self):
    #     for queue in range(self.n):
    #         self.meanWaitingTimes[queue] = np.cumsum(self.waitingTimes[queue])
    #         for i in range(len(self.meanWaitingTimes[queue])):
    #             self.meanWaitingTimes[queue][i] = self.meanWaitingTimes[queue][i] / (i+1)

    def calculateMovingAverage(self, data, out):
        for queue in range(self.n):
            out[queue] = np.cumsum(data[queue])
            for i in range(len(out[queue])):
                out[queue][i] = out[queue][i] / (i+1)

    def makeHistogram(self, data, title, xlabel, ylabel):
        colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown', 'tab:pink']
        for queue in range(len(data)):
            plt.figure()
            plt.hist(data[queue], bins=range(int(min(data[queue])), int(max(data[queue])) + 1, 1), color=colors[queue])
            queuetitle = title + ' queue ' + str(queue+1)
            plt.title(queuetitle)
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            plt.savefig('images/' + queuetitle.replace(' ', '_') + '.png')
            #plt.show()

    def makeLinePlot(self, data, title, xlabel, ylabel):
        plt.figure()
        for queue in range(len(data)):
            plt.plot(data[queue], label='Queue ' + str(queue + 1))

        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.legend()
        plt.savefig('images/' + title.replace(' ', '_') + '.png')
        #plt.show()


np.random.seed(10)
test = RovingServerQueue('input30 test3.txt', 1000000, 1)