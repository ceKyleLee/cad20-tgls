import os, sys
if "Preprocess" != os.path.basename(os.getcwd()):
    sys.path.append(os.path.abspath('..'))

from util.util import getVecIndex, getVecRange

class Wire(object):
    def __init__(self, name: str):
        self.name  : str = name
        self.symbol: str = ""

        self.fanin          = None
        self.fanout  : set  = set()
        self.init    : int  = -1
        self.isinput : bool = False
        self.connWire: set  = set([self])

        # For construct graph
        self.ready: int  = 0
        self.level: dict = dict()

    # Change property of Wire only
    # Can only be called outside the class
    def setInInst(self, inst):
        for wire in self.connWire:
            if not inst.isSeq():
                wire.fanin   = inst
            else: # Pseudo primary input
                wire.isinput = True
                wire.ready   = 1
                wire.fanin   = None

    def setOutInst(self, inst):
        for wire in self.connWire:
            if not inst.isSeq():
                wire.fanout.add(inst)

    def setInit(self, value: int):
        for wire in self.connWire:
            wire.init  = value
            wire.ready = True
            # Assigned wire should not connect to any ouput port
            wire.fanin = None 

    def setInput(self):
        for wire in self.connWire:
            wire.isinput = True
            wire.ready   = 1
            # Input wire should not connect to any ouput port
            wire.fanin   = None

    def setReady(self, r = 1):
        for wire in self.connWire:
            wire.ready = r

    def popOutInst(self, inst):
        for wire in self.connWire:
            wire.fanout.discard(inst)

    def merge(self, other):
        if  self.isInput() or other.isInput():
            other.setInput(), self.setInput()

        if   self.isAssigned() : other.setInit(self.init)
        elif other.isAssigned(): self.setInit(other.init)

        if   self.fanin  != None: other.setInInst(self.fanin)
        elif other.fanin != None: self.setInInst(other.fanin)

        if  not len(self.fanout): 
            for inst in self.fanout: other.setOutInst(inst)
        if  not len(other.fanout):
            for inst in other.fanout: self.setOutInst(inst)
        
        self.connWire.update(other.connWire)
        other.connWire.update(self.connWire)

    # Check Wire property
    def isInput(self)    -> bool:
        return self.isinput

    def isReady(self, r = 1) -> bool:
        return self.ready == r

    def isAssigned(self) -> bool:
        return  (self.init != -1) and (not self.isinput)

    def isDisconn(self)  -> bool:
        return (len(self.fanout) == 0 and self.fanin == None) \
            and (not self.isinput) \
            and (not self.isAssigned())

    def getInit(self)     -> int:
        return self.init

    def __getitem__(self, index):
        return [self]

    # For set operation
    def __eq__(self, other):
        if isinstance(other, Wire): 
            return self.name == other.name
        return False

    def __hash__(self):
        return hash(self.name)

    def LessThen(self, other):
        n = 0
        sLen  = len(self.level)
        oLen  = len(other.level)
        sList = sorted(list(self.level))
        oList = sorted(list(other.level))
        while True:
            if   n == sLen and n == oLen:
                return len(self.level[sList[0]]) <= len(other.level[oList[0]])
            if   n == sLen: return True
            elif n == oLen: return False

            if   sList[n] < oList[n]: return True
            elif sList[n] > oList[n]: return False
            else: n += 1

    # Preprocess operation
    def setLevel(self, inst):
        self.level.setdefault(inst.level, list()).append(inst)

    def getConn(self):
        return self.connWire

    # For output intermediate file
    def inter(self, DEBUG = False):
        if DEBUG:
            return f"1 {self.name} {self.symbol}"
        return f"1 {self.name}"

class Bus(object):
    def __init__(self, name: str, msb: int, lsb: int):
        self.name:  str = name
        self.msb :  int = msb
        self.lsb :  int = lsb
        self.width: int = abs(msb-lsb) + 1
        
        # Name the subnet with "bus name + [no]"
        self.subWire = [
            Wire(self.name + '[{}]'.format(vecIndex)) 
            for vecIndex in getVecRange(self.msb, self.lsb)
        ]

    def setInput(self):
        for subW in self.subWire:
            subW.setInput()

    def connect(self):
        for subW in self.subWire:
            subW.connect()

    def isInput(self) -> bool:
        for subW in self.subWire:
            if subW.isInput():
                return True
        return False

    def isDisconn(self) -> bool:
        for subW in self.subWire:
            if not subW.isDisconn():
                return False
        return True

    def __getitem__(self, index):
        if isinstance(index, slice):
            return [self[i] for i in getVecRange(index.start, index.stop)]
        elif index < 0:
            return self.subWire
        return self.subWire[getVecIndex(self.msb, self.lsb, index)]

    # For output intermediate file
    def inter(self, DEBUG = False):
        if DEBUG:
            return f"{str(self.width)} {self.name} [{str(self.msb)}:{str(self.lsb)}] " + " ".join(list(map(lambda net: str(net.symbol), self.subWire)))
        return f"{str(self.width)} {self.name} {str(self.msb)} {str(self.lsb)}"
