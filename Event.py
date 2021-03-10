class Event:
    def __init__(self, typ, time, queue):
        self.typ = typ  # type 1: ARRIVAL, type 2: DEPARTURE, type 3: SWITCH, type 3: REJOIN
        self.time = time  # real positive number
        self.queue = queue  # 0, 1, 2, ..., n-1

    def __lt__(self, other):
        return self.time < other.time

    def __str__(self):
        return self.typ + " of new customer " + ' at t = ' + str(self.time) +  ' in queue ' + str(self.queue)