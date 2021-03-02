class Customer:

    def __init__(self, arr, queue):
        self.arrivalTime = arr
        self.queue = queue

    def __str__(self):
        return "Customer arrived at " + str(self.arrivalTime) + " at queue " + str(self.queue)