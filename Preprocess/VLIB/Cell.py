import os, sys
if "Preprocess" != os.path.basename(os.getcwd()):
    sys.path.append(os.path.abspath('..'))

from VLIB.Evaluation import EvalFunc, decoder, encoder
from util.util       import vDecoder

class Gate(object):
    def __init__(self, iWires: list, oWname:str, Gname: str):
        self.iWname: list = iWires
        self.oWname: str  = oWname
        self.Gname : str  = Gname
        self.serial: int  = -1
        self.child : list = None

    def route(self, gateList: dict):
        self.child = [gateList.get(name, name) for name in self.iWname]

    def iPname(self) -> list:
        ipname = set()
        for wire in self.child:
            if isinstance(wire, str): ipname.add(wire)
            else:         ipname.update(wire.iPname())
        return sorted(list(ipname))

    def oPname(self) -> str:
        return self.oWname

    def getEvalfunc(self) -> str:
        inList = list()
        for wire in self.child:
            if isinstance(wire, str): # input wire of cell
                inList.append(wire)
            else: # Child gate
                inList.append(wire.getEvalfunc())
        
        return EvalFunc.generate(self.Gname, inList)

    def getTable(self, iPval: list = None):
        iPname = self.iPname()
        iPlen = len(iPname)
        evalFunc = eval("lambda " + ",".join(iPname) + ": " + self.getEvalfunc())

        if iPval == None: patternList = range(4**iPlen)
        else:             patternList = encoder(iPval)

        for pattern in patternList:
            yield evalFunc(*list(decoder(pattern, iPlen)))

    def setSer(self, s: int):
        self.serial = s

    def funcSer(self) -> int:
        return self.serial

    # For debug
    def show(self, prefix = ""):
        for wire in self.child:
            if not isinstance(wire, str):
                wire.show(prefix)
        print(prefix + str(self))

    def __str__(self):
        return f"{self.Gname} (" + ", ".join(self.iWname) + f") -> {self.oWname}"

class Cell(object):
    def __init__(self, name: str, iPname: list, oPname: str, 
                isseq: bool = False, funcSer: int = -1):
        self.name:    str  = name + "[" + oPname + "]"
        self.ipname:  list = iPname
        self.opname:  str  = oPname
        self.isseq:   bool = isseq
        self.funcser: int  = funcSer

    def iPname(self) -> list:
        return self.ipname

    def oPname(self) -> str:
        return self.opname

    def funcSer(self) -> int:
        return self.funcser

    def isSeq(self) -> bool:
        return self.isseq

    # For debug
    def __str__(self):
        return self.name

    def show(self, prefix = ""):
        print(prefix + self.name)
        print(prefix + "\tInput:  " + ", ".join(self.ipname))
        print(prefix + "\tOutput: " + self.opname)

class Library(object):
    def __init__(self):
        self.gateBase     = list()
        self.stdLibrary   = dict()
        self.cellTemplate = dict()

    def addSeqCell(self, name: str, iPname: list, oPnameList: list):
        self.stdLibrary[name] = [Cell(name, iPname, oPname, True) for oPname in oPnameList]

    def addCmbCell(self, name: str, outputGate: list):
        tempName = "_".join(name.split("_")[:-1])

        # Cell is not defined in template, add new template cell
        if tempName not in self.cellTemplate: 
            cellList = list()
            for gate in outputGate:
                gate.setSer(len(self.gateBase))
                self.gateBase.append(gate)
                cellList.append(
                    Cell(tempName, gate.iPname(), gate.oPname(), False, gate.funcSer())
                )
            self.cellTemplate[tempName] = cellList

        self.stdLibrary[name] = self.cellTemplate[tempName]

    def reduceTable(self, cell: Cell, iPval: list):
        newName = cell.name + "".join(map(str, iPval))
        if newName not in self.stdLibrary:
            # Generate new truth table (with len of input pins)
            newGate = list(self.gateBase[cell.funcSer()].getTable(iPval))
            if -1 not in iPval:
                return int(newGate[0])

            newiPname = [Pname for Pval, Pname in zip(iPval, cell.iPname()) if Pval < 0]
            newTable  = [len(newiPname)] + newGate
            # Append new cell into standard library
            self.stdLibrary[newName] = Cell(
                newName, newiPname, cell.oPname(), False, len(self.gateBase))
            self.gateBase.append(newTable)

        return self.stdLibrary[newName]

    def BaseSize(self) -> int:
        return int(len(self.gateBase))

    def getCell(self, name: str) -> list:
        return self.stdLibrary[name]

    def getEvalFunc(self) -> str:
        for gate in self.gateBase:
            if isinstance(gate, list):
                yield gate
            else:
                iPname = sorted(list(gate.iPname()))
                result = [len(iPname)]
                result.extend(gate.getTable())
                yield result

    # For debug
    def show(self):
        print(f"Cell in VLIB file: {len(self.stdLibrary)}")
        print(f"Cell template count: {len(self.cellTemplate)}")
        for name, cellList in self.cellTemplate.items():
            print(name + f" output: {len(cellList)}")
            for cell in cellList:
                cell.show("\t")
                self.gateBase[cell.funcSer()].show("\t\t")
            print()
    
    def showTruthTable(self):
        for cellList in self.cellTemplate.values():
            for cell in cellList:
                table = self.gateBase[cell.funcSer()]
                if not isinstance(table, list):
                    table = list(table.getTable())

                print(cell.name, "funcSer: " + str(cell.funcSer()))
                print("\t" + "".join(map(str,table)))
                print("\t" + " ".join(map(lambda p: f"{p:>2}", cell.iPname())) + f" {cell.oPname():>2}")
                for pattern in encoder([-1]*len(cell.iPname())):
                    print('\t' + " ".join(
                        map(lambda v: " " + vDecoder[v], decoder(pattern, len(cell.iPname())))
                    ) + "  " + vDecoder[table[pattern]])
                print()
