class Queue:

    def __init__(self):
        self.queue = []

    def size(self):
        return len(self.queue)

    def addCustomer(self, customer):
        self.queue.append(customer)

    def removeCustomer(self):

        pass

    def pop(self, i):
        self.queue.pop(i)