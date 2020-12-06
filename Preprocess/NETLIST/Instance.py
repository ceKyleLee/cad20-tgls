import os, sys
if "Preprocess" != os.path.basename(os.getcwd()):
    sys.path.append(os.path.abspath('..'))

from NETLIST.Wire import Wire
from util.util    import vEncoder

class Instance(object):
    def __init__(self, name: str, vtable, dtable):
        # Instance info
        self.name   = name
        self.vtable = vtable
        self.dtable = dtable

        # Port info
        self.iPname: list = vtable.iPname()
        self.oPname: str  = vtable.oPname()
        self.iPort : dict = dict()
        self.oPort : Wire = None

        # Graph info
        self.level: int = -1

    def isSeq(self) -> bool:
        return self.vtable.isSeq()

    # Parsing operation
    def addPortWire(self, Pname: str, WireList: list):
        if Pname == self.oPname: # Connect to output pin
            for wire in WireList:
                if isinstance(wire, Wire):
                    wire.setInInst(self)
                self.oPort = wire

        elif Pname in self.iPname: # Connect to input pin 
            for wire in WireList:
                if isinstance(wire, Wire):
                    wire.setOutInst(self)
                else: # Input pin received a constant
                    wire = vEncoder[wire]
                self.iPort[Pname] = wire
        else:
            pass

    # Reduce table operation
    # Done before connection
    def setConstPort(self, vlib) -> bool:
        existConst = False

        if self.oPort.init != -1: return False

        for Pname in self.iPname:
            wire = self.iPort[Pname]
            if isinstance(wire, Wire):
                if wire.getInit() != -1:
                    self.iPort[Pname] = wire.getInit()
                    existConst = True
            else:
                existConst = True

        if existConst:
            return self.reduceTable(vlib)
        return True

    def reduceTable(self, vlib) -> bool:
        iPval = [
            self.iPort[Pname] if isinstance(self.iPort[Pname], int) else -1 
                for Pname in self.iPname
        ]
        self.vtable = vlib.reduceTable(self.vtable, iPval)
        self.iPname = sorted([Pname for Pname in self.iPname if not isinstance(self.iPort[Pname], int)])

        if isinstance(self.vtable, int): 
            self.oPort.setInit(self.vtable)
            for wire in self.iPort.values():
                if not isinstance(wire, int):
                    wire.popOutInst(self)
            return False

        return True

    # Preprocess operation
    def isRoot(self):
        for wire in self.iPort.values():
            if isinstance(wire, Wire):
                if wire.fanin != None:
                    return False
        return True

    def simulate(self, r=1) -> set:
        self.oPort.setReady(r)
        return self.oPort.fanout

    def simulated(self, r=1) -> bool:
        return self.oPort.isReady(r)

    def ready(self, r=1) -> bool:
        for wire in self.iPort.values():
            if (not isinstance(wire, int)) and (not wire.isReady(r)):
                return False
        return True

    def setLevel(self):
        for wire in self.iPort.values():
            if isinstance(wire, Wire) and wire.fanin != None:
                if wire.fanin.level > self.level:
                    self.level = wire.fanin.level
        self.level += 1

        for wire in self.iPort.values():
            if isinstance(wire, Wire):
                wire.setLevel(self)

    def getIWire(self):
        for Pname in self.iPname:
            yield self.iPort[Pname]

    def getOWire(self):
        return self.oPort

    # Hash operation
    def __eq__(self, other):
        if isinstance(other, Instance):
            return self.name == other.name
        return False

    def __hash__(self):
        return hash(self.name)

    # For output intermediate file
    def inter(self, DEBUG:bool = False):
        # print(self.name, self.iPname, self.iPort)
        DelayTableString = " ".join(map(str, self.dtable.getTable(self.iPname, self.oPname)))
        WireString = " ".join(
            list(map(
                lambda Pname: self.iPort[Pname].symbol if not isinstance(self.iPort[Pname], int) else str(self.iPort[Pname]), self.iPname
            )) + [self.oPort.symbol]
        )

        result = ""
        if DEBUG:
            result = f"$ inst {self.name}\n"
        result += str(self.vtable.funcSer()) + " " + WireString
        if len(self.iPname):
            result += " " + DelayTableString

        return result
