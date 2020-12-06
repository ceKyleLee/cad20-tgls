import os, sys
if "Preprocess" != os.path.basename(os.getcwd()):
    sys.path.append(os.path.abspath('..'))

from VLIB.Cell       import Library, Gate
from VLIB.Evaluation import EvalFunc

from util.util   import FileParser, StringParser
from util.Syntax import *


class libraryParser:
    def __init__(self, filename: str):
        self.filename = filename
        self.library  = Library()

        # Parsing token
        self.currName: str  = ""
        self.currisSeq:bool = True
        self.gateList: dict = dict()
        self.inPorts:  list = list()
        self.outPorts: list = list()

        self.Grammer()

    def parsePort(self, inout: bool):
        def addPort(t: ParseResults):
            if inout:
                self.inPorts.extend(t[-2])
            else:
                self.outPorts.extend(t[-2])
            return ""
        return addPort

    # Initial a new cell
    def parseModuleDecl(self, t: ParseResults):
        self.currName  = t[1]
        self.currisSeq = False
        self.gateList.clear()
        self.inPorts.clear()
        self.outPorts.clear()
        return ""

    # Add cell into library
    def addModule(self, t: ParseResults):
        if self.currisSeq:
            self.library.addSeqCell(self.currName, self.inPorts, self.outPorts)
        else:
            for gate in self.gateList.values():
                gate.route(self.gateList)
            self.library.addCmbCell(
                self.currName, [gate for gate in self.gateList.values() if gate.oPname() in self.outPorts])
        return ""

    # Get primitive in modules
    def parseGate(self, t: ParseResults):
        if t[0] in EvalFunc.SeqUDP:
            self.currisSeq = True

        if not self.currisSeq:
            Gtype = t[0]
            param = t[-2]
            self.gateList[param[0]] = Gate(param[1:], param[0], Gtype)
        return ""

    def parseEvent(self, t: ParseResults):
        self.currisSeq = True
        return ""

    def parseReg(self, t: ParseResults):
        self.currisSeq = True
        return ""

    def parseSupply(self, t:ParseResults):
        return ""

    def Grammer(self):
        """ compiler directives """ # 3.7.4 19.1 19.8
        compilerDirective = Combine(
            "`"
            + oneOf("timescale celldefine endcelldefine")
            + restOfLine
        ).setName("DIRECTIVE")


        """ port """ # A.1.3
        portRef  = IDENTIFIER + Optional(subscrRef) # port_reference
        portExpr = (portRef | (LBRACE + delimitedList(portRef) + RBRACE)).setName("port_expression")
        port = Group(portExpr | (DOT + identifier + Group(LPAR + portExpr + RPAR))).setName("port")
        portList = (LPAR + delimitedList(port) + RPAR).setName("list_of_ports")

        """ statements """
        # A.6.5
        eventExpr = Forward().setName("event_expression")
        eventTerm = (
            ("posedge" + expr) | ("negedge" + expr) | expr | (LPAR + eventExpr + RPAR)
        )
        eventExpr << Group(delimitedList(eventTerm, Keyword("or")))
        eventControl = (
            Literal("@") + ((LPAR + eventExpr + RPAR) | identifier | "*")
        ).setName("event_control")
        
        # A.8.5 net_lvalue variable_lvalue
        lvalue = (subscrIdentifier + Optional(ZeroOrMore(expr) + subscrRef) | concat)
        # A.6.2
        # net_assignment blocking_assignment
        assignment = (lvalue + EQ + Group(expr)).setName("assignment")
        nbAssignment = (lvalue + "<="  + expr).setName("nonblocking_assignment")
        continuousAssign = (
            "assign" + delimitedList(Group(assignment)) + SEMI
        ).setName("continuous_assign")
        
        # A.6.4
        stmt = Forward().setName("statement")
        stmtOrNull = stmt | SEMI # statement_or_null
        stmt << Group(
            ("begin" + ZeroOrMore(stmt) + "end").setName("seq_block")
            | ("if" + Group(LPAR + expr + RPAR)
                + stmtOrNull
                + Optional("else" + stmtOrNull)
            ).setName("conditional_statement")
            | ("assign" + assignment + SEMI).setName("procedural_continuous_assignments")
            | (assignment + SEMI)
            | (nbAssignment + SEMI)
        )
        
        # A.6.2
        alwaysStmt = (
            "always" + Optional(eventControl) + stmt
        ).setName("always_construct").setParseAction(self.parseEvent)


        """ module item """
        # A.2.5
        dimension = Group(LBRACK + expr + COLON + expr + RBRACK).setName("dimension").setParseAction(lambda t: [[t[0][1], t[0][3]]])
        rang = Group(LBRACK + expr + COLON + expr + RBRACK).setName("range").setParseAction(lambda t: [[t[0][1], t[0][3]]])
        # A.2.1.2
        inputDecl = (
            "input" + Optional(rang) + Group(delimitedList(identifier)) + SEMI
        ).setName("input_declaration").setParseAction(self.parsePort(True))
        outputDecl = (
            "output" + Optional(rang) + Group(delimitedList(identifier)) + SEMI
        ).setName("output_declaration").setParseAction(self.parsePort(False))

        # A.2.4
        netDeclAssign = (identifier + Group((EQ + expr).setParseAction(lambda t: t[1:]))).setName("net_decl_assignment")
        # A.2.2.1 net_type
        nettype = oneOf("supply1  wire")
        # A.2.1.3
        netDecl = (
            nettype + Optional(rang) + Group(delimitedList(Group(netDeclAssign)) | delimitedList(identifier)) + SEMI
        ).setName("net_declaration").setParseAction(self.parseSupply)

        regDecl = (
            "reg" + Optional(rang) + Group(delimitedList(Group(identifier + dimension) | identifier)) + SEMI
        ).setName("reg_declaration").setParseAction(self.parseReg)

        """ primitive instantiation """
        # A.3.4 n_input_gatetype n_output_gatetype
        gateType = oneOf("and  nand  or  nor  xor  xnor  buf  not")
        # A.3.1
        # n_input_gate_instance n_output_gate_instance
        gateInst = (
            LPAR + Group(delimitedList(expr)) + RPAR
        ).setName("gate_instance").setParseAction(lambda t: t[1:-1])

        gateDecl = (
            gateType + delimitedList(gateInst) + SEMI
        ).setName("gate_instantiation").setParseAction(self.parseGate)

        """ module instantiation """ # A.4.1
        # parameter_value_assignment

        modPortConn = (expr | empty).setName("ordered_port_connection")
        namedPortConn = (
            "." + IDENTIFIER +
            LPAR + (expr | empty) + RPAR
        ).setName("named_port_connection").setParseAction(lambda t: t[1:])
        modConn = Group((LPAR + 
            (delimitedList(Group(namedPortConn)) | delimitedList((modPortConn))) +
        RPAR).setParseAction(lambda t: t[1:-1])
        ).setName("list_of_port_connections")
        
        modInst = ((IDENTIFIER+Optional(rang))+modConn).setName("module_instance")
        modInstantiation = (
            IDENTIFIER + 
            delimitedList(modInst) +
            SEMI
        ).setName("module_instantiation").setParseAction(self.parseGate)

        """ specify """
        # A.7.4
        pathDelayValue = (
            (LPAR + delimitedList(mintypmaxExpr | expr) + RPAR)
            | delimitedList(mintypmaxExpr | expr)
        ).setName("path_delay_value")
        # edge_identifier
        edgeIdentifier = Keyword("posedge") | Keyword("negedge")
        # polarity_operator
        polarityOp = oneOf("+  -")
        edgeSensitivePathDecl = (
            LPAR + Optional(edgeIdentifier) + subscrIdentifier + "=>"
            + LPAR + subscrIdentifier + Optional(polarityOp) + COLON + expr + RPAR
            + RPAR + EQ + pathDelayValue + SEMI
        ).setName("edge_sensitive_path_declaration")
        # A.7.2
        # Optional(edgeIdentifier) is not mentioned in the Standard ?
        pathDescr = (
            LPAR+ Optional(edgeIdentifier) + subscrIdentifier + Optional(polarityOp) + "=>" + subscrIdentifier + RPAR
        ).setName("parallel_path_description")
        pathDecl = (pathDescr + EQ + pathDelayValue + SEMI).setName("simple_path_declaration")
        # A.7.5.3
        # scalar_constant
        scalarConst = Regex("0|1('[Bb][01xX])?")
        # scalar_timing_check_condition
        timCheckCondTerm = (expr + oneOf("==  ===  !=  !==") + scalarConst) | (Optional("~") + expr)
        # timing_check_condition
        timCheckCond = Forward()
        timCheckCond << ((LPAR + timCheckCond + RPAR) | timCheckCondTerm)
        # edge_descriptor
        edgeDescr = Regex("01|10|[xXzZ][01]|[01][xXzZ]").setName("edge_descriptor")
        # timing_check_event_control
        timCheckEventControl = Group(
            Keyword("posedge") | Keyword("negedge") | (Keyword("edge") + LBRACK + delimitedList(edgeDescr) + RBRACK)
        )
        timCheckEvent = Group(
            Optional(timCheckEventControl) + subscrIdentifier + Optional("&&&" + timCheckCond)
        ).setName("timing_check_event")
        controlledTimingCheckEvent = Group(
            timCheckEventControl + subscrIdentifier + Optional("&&&" + timCheckCond)
        ).setName("controlled_timing_check_event")
        # A.7.5.2
        notifyRegister = identifier # notifier
        timCheckLimit = expr # timing_check_limit
        # A.7.5.1
        systemTimingCheck1 = Group(
            "$setup" + LPAR + timCheckEvent + COMMA + timCheckEvent + COMMA + timCheckLimit
            + Optional(COMMA + notifyRegister) + RPAR + SEMI
        )
        systemTimingCheck2 = Group(
            "$hold" + LPAR + timCheckEvent + COMMA + timCheckEvent + COMMA + timCheckLimit
            + Optional(COMMA + notifyRegister) + RPAR + SEMI
        )
        systemTimingCheck7 = Group(
            "$setuphold" + LPAR + timCheckEvent + COMMA + timCheckEvent + COMMA + timCheckLimit + COMMA + timCheckLimit
            + Optional(COMMA + notifyRegister) + RPAR + SEMI
        )
        systemTimingCheck6 = Group(
            "$recovery" + LPAR + controlledTimingCheckEvent + COMMA + timCheckEvent + COMMA + timCheckLimit
            + Optional(COMMA + notifyRegister) + RPAR + SEMI
        )
        systemTimingCheck4 = Group(
            "$width" + LPAR + controlledTimingCheckEvent + COMMA + timCheckLimit
            + Optional(COMMA + expr + COMMA + notifyRegister) + RPAR + SEMI
        )
        systemTimingCheck = (
            FollowedBy("$")
            + (
                systemTimingCheck1
                | systemTimingCheck2
                | systemTimingCheck7
                | systemTimingCheck6
                | systemTimingCheck4
            )
        ).setName("system_timing_check")
        # A.7.1
        specifyItem = ~Keyword("endspecify") + Group(
            edgeSensitivePathDecl
            | pathDecl
            | systemTimingCheck
        ).setName("specify_item")
        specifyBlock = Group(
            "specify" + ZeroOrMore(specifyItem) + "endspecify"
        ).setName("specify_block")

        """ module """
        # A.1.4
        moduleItem = ~Keyword("endmodule") + Group(
            inputDecl
            | outputDecl            # port_declaration
            | netDecl
            | regDecl               # module_or_generate_item_declaration
            | continuousAssign
            | gateDecl              # module_or_generate_item
            | alwaysStmt
            | specifyBlock          # non_port_module_item
            | modInstantiation
        ).setName("module_item")
        # A.1.2 module_declaration
        module = (
            ("module" + (identifier).setName("module_identifier") + Optional(portList) + SEMI).setParseAction(self.parseModuleDecl)
            + ZeroOrMore(moduleItem) + "endmodule"
        ).setName("module").setParseAction(self.addModule)

        """ UDP """
        # A.5.3
        # level_symbol
        levelSymbol = oneOf("0  1  x  X  ?  b  B")
        # level_input_list
        levelInputList = OneOrMore(levelSymbol)
        # output_symbol
        outputSymbol = oneOf("0  1  x  X")
        # combinational_entry
        combEntry = Group(Group(levelInputList) + COLON + outputSymbol + SEMI).setName("combEntry")
        # edge_symbol
        edgeSymbol = oneOf("r  R  f  F  p  P  n  N  *")
        # edge_indicator
        edge = Group(LPAR + levelSymbol + levelSymbol + RPAR) | Group(edgeSymbol)
        # edge_input_list
        edgeInputList = ZeroOrMore(levelSymbol) + edge + ZeroOrMore(levelSymbol)
        # seq_input_list
        seqInputList = edgeInputList | levelInputList
        # sequential_entry
        seqEntry = Group(Group(seqInputList) + COLON + levelSymbol + COLON + (outputSymbol | "-") + SEMI).setName("seqEntry")
        udpTableDefn = (
            "table" + Group(OneOrMore(combEntry | seqEntry)) + "endtable"
        ).setName("udp_body")
        # A.5.2 udp_port_declaration
        udpDecl = outputDecl | inputDecl | regDecl
        # A.5.1 udp_declaration
        udp = (
            "primitive" + (identifier).setName("udp_identifier") + portList + SEMI
            + OneOrMore(udpDecl) + udpTableDefn + "endprimitive"
        ).setName("udp")

        # A.1.2 description
        verilogBNF = OneOrMore(module | udp) + StringEnd()
        verilogBNF.ignore(cppStyleComment)
        verilogBNF.ignore(compilerDirective)
        self.testParser = module
        self.parser = verilogBNF

    def test(self, tstring):
        StringParser(self.testParser, tstring)

    def parseFile(self) -> Library:
        FileParser(self.parser, self.filename)
        return self.library

if __name__ == "__main__":
    v = libraryParser("../GENERIC_STD_CELL.vlib")
    library: Library = v.parseFile()
    library.reduceTable(library.getCell("GEN_OR3_D2")[0], [3, -1, -1])
    library.showTruthTable()
