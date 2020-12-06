import sys

from NETLIST.netlistParser import netlistParser
from VLIB.libraryParser    import libraryParser
from SDF.sdfParser         import sdfParser

# Parse .gv, .vlib, .sdf file and return the topModule of .gv with all graph been connected
def parser(gvFile, vlibFile, sdfFile):
    vParser  = libraryParser(vlibFile)
    dParser  = sdfParser(sdfFile)

    # Parsing library
    vlibrary = vParser.parseFile()
    dlibrary = dParser.parseFile()

    nParser  = netlistParser(gvFile, vlibrary, dlibrary)
    netlist = nParser.parseFile()
    instList, wireList = netlist.connGraph()

    return netlist, vlibrary, instList, wireList

def WirePrograming(BlockList, WireLimit):
    # Wire Programing
    WireInRam  = list()
    reqWire    = set()
    WireAction = list()
    for block in BlockList:
        reqWire = set()
        for gate in block:
            for wire in gate.getIWire():
                wire.popOutInst(gate)
                reqWire.add(wire)

        PopWire = list()
        DelWire = list()
        AddWire = list(filter(lambda wire: wire not in WireInRam, reqWire))
        nxtWireInRam = list(reqWire) + list(map(lambda inst: inst.getOWire(), block))

        for wire in list(filter(lambda wire: wire not in reqWire, WireInRam)):
            if not len(wire.fanout):
                DelWire.extend(wire.getConn())
                PopWire.append(wire)
            else: 
                if len(nxtWireInRam) < WireLimit:
                    nxtWireInRam.append(wire)
                else:
                    PopWire.append(wire)
        WireInRam = nxtWireInRam
        
        WireAction.append(list(map(lambda alist: [len(alist)] + alist, (PopWire, DelWire, AddWire))))
    return WireAction

def CPUPreprocess_v2(rootWire: list, WireLimit: int ,ThreadLimit: int):
    assert(WireLimit >= ThreadLimit*7)
    CPUThreshHold = 625
    StartCPUBlock = -1
    BlockList = list()
    simNUM = 2
    instReady = set()
    for wire in rootWire:
        wire.setReady(simNUM)
        instReady.update(filter(lambda inst: inst.ready(simNUM), wire.fanout))

    newBlock = list()
    while len(instReady):
        if   len(instReady) >= ThreadLimit:
            for _ in range(ThreadLimit):
                newBlock.append(instReady.pop())

        elif len(instReady):
            newBlock  = list(instReady)
            instReady = set()


        if StartCPUBlock < 0 and len(newBlock) <= CPUThreshHold:
            StartCPUBlock = len(BlockList)

        BlockList.append(newBlock)

        for iList in map(
            lambda inst: filter(
                lambda subinst: subinst.ready(simNUM),
                inst.simulate(simNUM)
            ), newBlock):
            instReady.update(set(iList))
        newBlock = list()

    WireAction = WirePrograming(BlockList, WireLimit)
    if StartCPUBlock <= 0:
        StartCPUBlock = int(len(BlockList)/8)
    return BlockList, WireAction, StartCPUBlock

def outputFile(netlist, vlib, blocklist, WireAction, ThreadLimit, CPUStartBlock, outfilepath, DEBUG: bool = False):
    endChar = '\n'
    if DEBUG:
        endChar = '\n'
    wireNum, iWire, oWire, aWire = netlist.ReassignWire()
    blockNum = len(blocklist)
    evalNum  = vlib.BaseSize()
    evalList = vlib.getEvalFunc()

    with open(outfilepath, 'w') as f:
        f.write(f"{wireNum} {len(iWire)} {len(oWire)} {len(aWire)} {evalNum} {blockNum} {CPUStartBlock}")
        f.write(endChar)

        if DEBUG:
            f.write("$ EvalFunc:\n")
        f.write(endChar.join(map(lambda table: f"{table[0]} " + "".join(map(str, table[1:])), evalList)))
        f.write(endChar)

        if DEBUG:
            f.write("$ Assignment:\n")
        f.write(endChar.join(aWire))
        f.write(endChar)

        if DEBUG:
            f.write("$ Input wire:\n")
        f.write(endChar.join(map(lambda w: w.inter(DEBUG), iWire)))
        f.write(endChar)

        if DEBUG:
            f.write("$ Output wire:\n")
        f.write(endChar.join(map(lambda w: w.inter(DEBUG), oWire)))
        f.write(endChar)
    
        for bnum, block in enumerate(zip(blocklist, WireAction)):
            if DEBUG:
                f.write(f"$ Block {bnum}\n") 
            instlist, waction = block # waction = (PopWire, DelWire, AddWire)
            for action in waction:
                f.write(" ".join(map(lambda wire: str(wire.symbol) if not isinstance(wire, int) else str(wire), action)))
                f.write(endChar)
            f.write(endChar.join(map(lambda inst: inst.inter(DEBUG), instlist)))
            f.write(endChar)
            for _ in range(ThreadLimit - len(instlist)):
                f.write(str(evalNum) + endChar)
    return 

def Contest(gvFile, vlibFile, sdfFile, outFile, deBugFile=None):
    threadlimit = 10000
    wirelimit = threadlimit*9
    netlist, vlib, instList, wireList = parser(gvFile, vlibFile, sdfFile)
    BlockList, WireAction, CPUStartBlock = CPUPreprocess_v2(netlist.getInputWire(), wirelimit, threadlimit)
    # print("BFS, Block")
    # print(f"{len(instList)}, {len(BlockList)}")
    if deBugFile != None:
        outputFile(netlist, vlib, BlockList, WireAction, threadlimit,CPUStartBlock ,deBugFile, True)
    outputFile(netlist, vlib, BlockList, WireAction, threadlimit, CPUStartBlock, outFile, False)
    return 

if __name__ == "__main__":
    if len(sys.argv) > 5:
        Contest(sys.argv[1], sys.argv[3], sys.argv[2], sys.argv[4], sys.argv[5])
    else:
        Contest(sys.argv[1], sys.argv[3], sys.argv[2], sys.argv[4])