class Customer:

    def __init__(self, arr, arrq, queue, arrqueue):
        self.arrivalTime = arr
        self.queueJoinTime = arrq
        self.queue = queue
        self.arrivalQueue = arrqueue

    def __str__(self):
        return "Customer arrived at " + str(self.arrivalTime) + " at queue " + str(self.queue)