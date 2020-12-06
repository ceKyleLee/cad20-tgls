import os, sys
if "Preprocess" != os.path.basename(os.getcwd()):
    sys.path.append(os.path.abspath('..'))

from SDF.Delaytable import *
from util.Syntax import *
from util.util   import FileParser

DIVIDER = Literal("/")

class sdfParser(object):
    def __init__(self, filename: str):
        self.filename = filename
        self.dLibrary = dict()

        self.currInst : dInstance = None
        self.timescale: int       = 1
        
        self.testParser: ParserElement  = None
        self.parser    : ParserElement  = None
        self.Grammer()

    @staticmethod
    def getDelayTuple(t):
        return float(t[2])

    def parseTimescale(self, t: ParseResults):
        scale = { 
            "s" : 1e12, "ms": 1e9, "us": 1e6, 
            "ns": 1e3, "ps": 1e0,"fs": 1e-3 
        }
        self.timescale = int(t[0]) * scale[t[1]]
        return ""
    
    def parseInst(self, t: ParseResults):
        if len(t) < 4:
            return ""
        self.currInst = dInstance()
        self.dLibrary[t[2]] = self.currInst
        return ""
    
    def parseDelayTable(self, t: ParseResults):
        iPname = t[2][0]
        oPname = t[3]
        dTElem = t[4]
        if len(t[2]) > 1:
            iPname = t[2][1]
            if t[2][0] == "posedge":
                self.currInst.addIOdelay(iPname,oPname,dTElem, 0)
            else:
                self.currInst.addIOdelay(iPname,oPname,dTElem, 1)
        else:
            self.currInst.addIOdelay(iPname, oPname, dTElem)
        return ""

    def parseDelayTableElem(self, t: ParseResults):
        return dTableElem(list(map(lambda d: int(d*self.timescale), t)))

    def Grammer(self):
        def getDivder(t):
            global DIVIDER
            DIVIDER = Literal(t[2])
            return ""

        """ Header information """
        CELL = Keyword("CELL")
        headerKeyword = oneOf("DATE DESIGN SDFVERSION VENDOR PROGRAM VERSION PROCESS")
        headerInfo = (
            LPAR + headerKeyword + dblQuotedString + RPAR
        ).setName("header_info")

        rtriple = (
            number + COLON + number + COLON + number
        ).setParseAction(self.getDelayTuple)
        tripleKeyword = oneOf("VOLTAGE TEMPERATURE")
        tripleInfo = (
            LPAR + tripleKeyword + rtriple + RPAR
        ).setName("triple_info")

        """ Divder """
        divider = (
            LPAR + "DIVIDER" + Word(printables, excludeChars=')') + RPAR
        ).setName("divider").setParseAction(getDivder)


        """ Timescale """
        timeNum = oneOf("1 10 100")
        timeUnit = oneOf("s ms us ns ps fs")
        timescale = (
            LPAR + "TIMESCALE" + (timeNum + timeUnit).setParseAction(self.parseTimescale) + RPAR
        ).setName("timescale")

        header = ~CELL + (
            (tripleInfo | headerInfo | divider | timescale)
        ).setName("header_info")
        
        """ Delay declartion """
        cellT = (LPAR + "CELLTYPE" + dblQuotedString + RPAR).setName("CellType")
        instanceName = (LPAR + "INSTANCE" + Optional(identifier) + RPAR).setParseAction(self.parseInst)

        EDGEident = oneOf("posedge negedge")
        port_instance = (
            ZeroOrMore(identifier + DIVIDER) + identifier
        ).setName("port_instance")
        port_spec = (
            Group(port_instance)
            | (LPAR + EDGEident + port_instance + RPAR).setParseAction(lambda t: [t[1:-1]])
        ).setName("input_port")
        deval_list = OneOrMore(
            (
                LPAR + rtriple + RPAR
            ).setParseAction(lambda t: t[1])
        ).setName("delay_value").setParseAction(self.parseDelayTableElem)

        IOPATH = (
            LPAR + "iopath" + port_spec + port_instance + deval_list + RPAR
        ).setName("iopath").setParseAction(self.parseDelayTable) 
        INTERCONN = (
            LPAR + "INTERCONNECT" + ZeroOrMore(Word(printables, excludeChars='(')) + deval_list + RPAR
        ).setName("InterConnect")

        ABSOLUTE = (
            LPAR + "ABSOLUTE" + ZeroOrMore((IOPATH | INTERCONN)) + RPAR
        ).setName("Absolute")
        DELAY = (
            LPAR + "DELAY" + ABSOLUTE + RPAR
        ).setName("Delay")
        cellDecl = (
            LPAR + CELL + cellT + instanceName + DELAY + RPAR
        ).setName("cell_delay_declaration")
        Delayfile = (
            LPAR + "DELAYFILE" + ZeroOrMore(header) + ZeroOrMore(cellDecl) + RPAR
        )

        self.parser = Delayfile
        self.testParser = INTERCONN

    def parseString(self, tstring):
        StringParser(self.testParser, tstring)
    
    def parseFile(self) -> dict():
        FileParser(self.parser, self.filename, False)
        return self.dLibrary

if __name__ == "__main__":
    parser = sdfParser("../NV_nvdla_GEN.sdf")
    Library = parser.parseFile()
    for name, inst in Library.items():
        print(name)
        inst.showTable()
