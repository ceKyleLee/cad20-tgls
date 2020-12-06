import os, sys
if "Preprocess" != os.path.basename(os.getcwd()):
    sys.path.append(os.path.abspath('..'))

from NETLIST.TopModule import TopModule
from NETLIST.Instance  import Instance
from NETLIST.Wire      import Wire, Bus

from util.util   import FileParser, StringParser, vEncoder
from util.Syntax import *

class netlistParser:
    def __init__(self, filename: str, vlibrary, dlibrary):
        self.filename: str = filename
        self.TopModule: TopModule = TopModule(vlibrary)
        self.connectedWire: dict = dict()

        # Library
        self.vlibrary = vlibrary
        self.dlibrary = dlibrary

        # Setup grammer
        self.Grammer()

    # Declare a new wire (single net or bus)
    def parseWire(self, t: ParseResults):
        if len(t) > 3: # Bus 
            msb, lsb = int(t[1][1]), int(t[1][3])
            for name in t[2]:
                bus = Bus(name, msb, lsb)
                self.TopModule.addWire(bus)
                if t[0] == "input":
                    bus.setInput()

        else: # Net
            for name in t[1]:
                wire = Wire(name)
                self.TopModule.addWire(wire)

                if t[0] == "input":
                    wire.setInput()

        return ''

    # Assign the values to wires
    def parseAssign(self, t: ParseResults):
        for wire, value in zip(t[0], t[2]):
            if isinstance(value, Wire):
                self.TopModule.addConn(wire, value)
            else:
                wire.setInit(vEncoder[value])
        return ""

    # Declare a new instances with specified cell type and port connection
    def parseInst(self, t):
        vtableList = self.vlibrary.getCell(t[0])

        for instDecl in t[1]:
            name = instDecl[0]
            for vtable in vtableList:
                if vtable.oPname() not in list(zip(*instDecl))[0]: # output pin is unconnected
                    continue
                # Search for delay table
                dtable = self.dlibrary.get(name, None)
                inst = Instance(name + f"[{vtable.oPname()}]", vtable, dtable)
                # Update nets connected to the ports of inst
                for Pname, wire in instDecl[1:]:
                    inst.addPortWire(Pname, wire)

                if not vtable.isSeq():
                    self.TopModule.addInst(inst)
        return ""

    # Get the nets declared before by the given name and index selector (optional) for 
    # assignment, port connection of inst ... etc.
    # Always return a list (which contains maybe one or more nets)
    def getWire(self, t: ParseResults):
        wireList = list()
        wire = self.TopModule.getWire(t[0])
        if isinstance(wire, Bus): # Bus
            if len(t) > 1: # Exist selector
                if len(t[1]) > 1: # Slice
                    wireList += wire[int(t[1][0]):int(t[1][1])]
                else: # Index
                    wireList.append(wire[int(t[1][0])])
            else: # The whole bus
                wireList += wire[-1]
        else: # Single wire
            wireList.append(wire)
        return wireList
    
    def Grammer(self):
        subscrIdentifier.setParseAction(self.getWire)

        """ port """
        portRef  = IDENTIFIER + Optional(subscrRef)
        portExpr = (portRef | (LBRACE + delimitedList(portRef) + RBRACE)).setName("port_expression")
        port = Group(portExpr | (DOT + identifier + Group(LPAR + portExpr + RPAR))).setName("port")

        """ module item """
        paramAssignmt = (
            identifier + EQ + expr
        ).setName("param_assignment")
        parameterDecl = (
            "parameter" + delimitedList(paramAssignmt) + SEMI
        ).setName("parameter_declaration")

        rang = Group(LBRACK + expr + COLON + expr + RBRACK).setParseAction(lambda t:t)
        inputDecl = (
            "input"  + Optional(rang) + Group(delimitedList(identifier)) + SEMI
        ).setName("input_declaration").setParseAction(self.parseWire)
        outputDecl = (
            "output" + Optional(rang) + Group(delimitedList(identifier)) + SEMI
        ).setName("output_declaration").setParseAction(self.parseWire)
        inoutDecl = (
            "inout"  + Optional(rang) + Group(delimitedList(identifier)) + SEMI
        ).setName("inout_declaration")
        wireDecl = (
            "wire"   + Optional(rang) + Group(delimitedList(identifier)) + SEMI
        ).setName("wire_declaration").setParseAction(self.parseWire)

        assignment = (
            Group(lvalue) + EQ + Group(expr)
        ).setName("assignment").setParseAction(self.parseAssign)
        continuousAssign = (
            "assign" + delimitedList(assignment) + SEMI
        ).setName("continuousAssign")


        paraValAssign = ("#" + LPAR + delimitedList( expr ) + RPAR)
        modPortConn = (expr | empty).setName("module_port_connection")
        namedPortConn = (
            DOT + IDENTIFIER + 
            LPAR + Group(expr) + RPAR
        ).setName("named_port_connection").setParseAction(lambda t: [t[1], t[3]])

        modConn = (LPAR + 
            (delimitedList(Group(namedPortConn)) | delimitedList(Group(modPortConn))) + 
        RPAR).setName("list_of_module_connections").setParseAction(lambda t: t[1:-1])
        modInst = Group(IDENTIFIER+Optional(rang)+modConn).setName("module_instance") # instname + port connections

        modInstantiation = (
            IDENTIFIER + # cell type
            Optional(paraValAssign) + 
            Group(delimitedList(modInst)) + 
            SEMI
        ).setName("module_instantiation").setParseAction(self.parseInst)

        """ module """
        nameofModule = identifier
        portList = (LPAR + delimitedList(port) + RPAR).setName("list_of_ports").setParseAction(lambda t: '')
        moduleItem = ~Keyword("endmodule") + (
            parameterDecl       
            | inputDecl         
            | outputDecl        
            | inoutDecl         
            | wireDecl          
            | continuousAssign  
            | modInstantiation  
        ).setName("module_item")

        module = (
            "module" + identifier + Optional(portList) + SEMI + 
            ZeroOrMore(moduleItem) + "endmodule"
        ).setName("module")

        verilogBNF = OneOrMore(module) + StringEnd()
        verilogBNF.ignore(cppStyleComment)
        self.parser     = verilogBNF
        self.testParser = wireDecl

    def test(self, tstring):
        StringParser(self.testParser, tstring)
        return self.TopModule
    
    def parseFile(self):
        FileParser(self.parser, self.filename)
        return self.TopModule


if __name__ == "__main__":
    v = netlistParser("../NV_nvdla_GEN.gv", dict(), dict(), dict(), dict())
    # v.parseFile()
    tstring = " \
wire   [33:0] cacc2csb_resp_pd;\n\
"
# wire   cacc2csb_resp_valid, csb2cacc_req_pvld, cmac_a2csb_resp_valid;\n\
    for wire in v.test(tstring).wireList.values():
        print(str(wire))
