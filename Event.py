class Event:
    def __init__(self, typ, time, queue):
        self.typ = typ  # type 1: ARRIVAL, type 2: DEPARTURE, type3: SWITCH
        self.time = time  # real positive number
        self.queue = queue  # 1, 2, 3, 4

    def __lt__(self, other):
        return self.time < other.time

    def __str__(self):
        return self.typ + " of new customer " + ' at t = ' + str(self.time)