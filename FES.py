import heapq


class FES:
    def __init__(self):
        self.events = []

    def add(self, event):
        heapq.heappush(self.events, event)
        # rewrite this to insert an event at a certain time

    def next(self):
        return heapq.heappop(self.events)

    def isEmpty(self):
        return len(self.events) == 0

    def getLength(self):
        return len(self.events)

    def checkSwitch(self):
        for event in self.events:
            if event.typ == 'SWITCH':
                return True
        return False

    def __str__(self):
        # Note that if you print self.events, it would not appear to be sorted
        # (although they are sorted internally).
        # For this reason we use the function 'sorted'
        s = ''
        sortedEvents = sorted(self.events)
        for e in sortedEvents:
            s += str(e) + '\n'
        return s