class dTableElem(object):
    def __init__(self, delays: list):
        self.delays = delays
    
    def getTable(self):
        if   len(self.delays) == 1:
            return [self.delays[0]] * 6
        elif len(self.delays) == 2:
            return [self.delays[0], self.delays[1], self.delays[0], self.delays[0], self.delays[1], self.delays[1]]
        elif len(self.delays) == 3:
            race1 = self.delays[0] if self.delays[0] < self.delays[2] else self.delays[2]
            race2 = self.delays[1] if self.delays[1] < self.delays[2] else self.delays[2]
            return [self.delays[0], self.delays[1], race1         , self.delays[0], race2         , self.delays[1]]
        elif len(self.delays) == 6:
            race1 = self.delays[0] if self.delays[0] < self.delays[2] else self.delays[2]
            race2 = self.delays[0] if self.delays[0] > self.delays[3] else self.delays[3]
            race3 = self.delays[1] if self.delays[1] < self.delays[4] else self.delays[4]
            race4 = self.delays[1] if self.delays[1] > self.delays[5] else self.delays[5]
            return [self.delays[0], self.delays[1], race1         , race2         , race3         , race4         ]
    
    def __str__(self):
        return " ".join(map(str, self.getTable()))

class dTable(object):
    def __init__(self, edge: bool = False):
        self.table = [None, None] if edge else [None] 

    def addDelay(self, dElem: dTableElem, tpos: int = 0):
        self.table[tpos] = dElem

    def isDumb(self) -> bool:
        if len(self.table):
            return False
        return True

    def max(self) -> int:
        if len(self.table) == 1:
            return max(self.table[0].getTable())
        return max(max(self.table[0].getTable()), max(self.table[1].getTable()))

    def __str__(self):
        if self.isDumb():
            return ("0 " * 12)[:-1]
        
        if len(self.table) == 1:
            interStr = str(self.table[0])
            return interStr + " " + interStr
        return str(self.table[0]) + " " + str(self.table[1])


dumb_dTable = dTable()
dumb_dTable.table = []

class dInstance(object):
    def __init__(self):
        self.ioTable = dict()

    def addIOdelay(self, iPname: str, oPname: str, delay: dTableElem, edge: int = -1):
        iTable: dict = self.ioTable.setdefault(iPname, dict())
        if edge < 0: # No edge specified
            iTable.setdefault(oPname, dTable()).addDelay(delay)
        else:
            iTable.setdefault(oPname, dTable(True)).addDelay(delay, edge)

    def getIODelay(self, iPname: str, oPname: str) -> dTable:
        if iPname not in self.ioTable or oPname not in self.ioTable[iPname]:
            return dumb_dTable
        return self.ioTable[iPname][oPname]

    def getTable(self, iOrder: list, oPname: str) -> list:
        return map(lambda iPname: self.getIODelay(iPname, oPname), iOrder)

    def showTable(self) -> str:
        for iPname, oTable in self.ioTable.items():
            for oPname, Table in oTable.items():
                print(f"{iPname:>2} to {oPname:>2}: " + str(Table))