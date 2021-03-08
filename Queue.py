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

    def isempty(self):
        if not self.queue:
            return True
        else:
            return False

    def __str__(self):
        return str(self.queue)