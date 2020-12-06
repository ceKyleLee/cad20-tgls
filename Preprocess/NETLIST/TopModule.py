import os, sys
if "Preprocess" != os.path.basename(os.getcwd()):
    sys.path.append(os.path.abspath('..'))

from NETLIST.Instance  import Instance
from NETLIST.Wire      import Wire, Bus
from util.util import valueZ

class TopModule(object):
    def __init__(self, vlibrary):
        self.instList:  list = list() # Only contains combinational instances
        self.wireList:  dict = dict() # Provided for searching net by name
        self.connected: dict = dict()
        self.vlibrary = vlibrary

    # For parsing netlist
    def addWire(self, wire: Wire):
        self.wireList[wire.name] = wire

    def addInst(self, inst: Instance):
        if not inst.isSeq():
            self.instList.append(inst)

    def getWire(self, Wname: str) -> Wire:
        return self.wireList[Wname]

    def addConn(self, lwire: Wire, rwire: Wire):
        self.connected[lwire] = rwire
        lwire.merge(rwire)

    # For output intermediate file
    def connGraph(self) -> set:
        # Get first level of instance
        currLayer: list = list()
        for inst in self.instList:
            if inst.isRoot():
                currLayer.append(inst)

        # BFS and reduce table
        instLayerList:dict = dict()
        nextLevel    :list = list()

        while len(currLayer):
            for inst in currLayer:
                if inst.simulated():
                    print(f"Error: Level {inst.level} exist loop at {str(inst.vtable)}:{inst.name} -> {inst.iPort}")
                else:
                    if inst.setConstPort(self.vlibrary): # Reduce table, False if instance has constant output
                        inst.setLevel()
                        instLayerList.setdefault(inst.level, list()).append(inst)
                    nextLevel.extend(filter(lambda inst: inst.ready(), inst.simulate()))
            currLayer = nextLevel
            nextLevel = list()

        # Sort Wires
        self.singleWireList:list = list()
        
        for wire in self.wireList.values():
            self.singleWireList.extend(wire[-1])

        return instLayerList, self.singleWireList

    def getInputWire(self):
        return filter(lambda wire: not isinstance(wire, int) and wire.fanin == None, self.singleWireList)

    def ReassignWire(self):
        iWire = list()
        oWire = list()
        aWire = list()

        # Classify wires
        for wire in self.wireList.values():
            if wire.isInput(): # Input wire
                iWire.append(wire) 
            else: # Output wire
                if isinstance(wire, Bus):
                    oWire.append(wire)
                    for subW in wire[-1]:
                        if subW.isDisconn():
                            subW.setInit(valueZ)
                        if subW.getInit() != -1:
                            aWire.append(subW)
                else:
                    if not wire.isDisconn():
                        oWire.append(wire)
                        if wire.isAssigned():
                            aWire.append(wire)

        # Assign new symbol with serial(0~3 preserved)
        serial = 4
        for wire in iWire + oWire:
            if isinstance(wire, Bus):
                for subW in wire[-1]:
                    subW.symbol = str(serial)
                    serial += 1
            else:
                wire.symbol = str(serial)
                serial += 1

        # Set assignment 
        Assignment = set()
        for lwire, rwire in self.connected.items():
            if rwire in self.connected:
                rwire = self.connected[rwire]
            Assignment.add(f"{lwire.symbol} {rwire.symbol}")

        for wire in aWire:
            Assignment.add(f"{wire.symbol} {wire.init}")

        return serial-4, iWire, oWire, Assignment
