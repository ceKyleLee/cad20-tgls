def StringParser(parser, tstring: str):
    """Only use one grammer to parse string 
    """
    import pprint
    pp = pprint.PrettyPrinter(indent = 4)
    print(pp.pformat(parser.parseString(tstring).asList()))

def FileParser(parser, filepath: str, verbose:bool = False):
    """Parse the whole file by given grammer

    verbose -> print the parsing info if True

    """
    from time import time
    start = time()
    with open(filepath, 'r') as f:
        rawS = f.readlines()
        line_number = len(rawS)
    tokens = parser.parseString("".join(rawS)).asList()
    interval = time() - start

    if verbose:
        import pprint
        pp = pprint.PrettyPrinter(indent = 4)
        print("Total processing time: {:.2f} seconds".format(interval) )
        print("Processing rate:       {:.2f} lines/sec".format(line_number/interval) )

""" 
Vector Indexing 
    Formal specification to transfer slicing in verilog to index in list
"""
def getVecRange(msb: int, lsb: int) -> list:
    """Get the list of [msb, msb-1, msb-2, ... lsb]"""
    if lsb > msb:
        return range(msb, lsb+1)
    return range(msb, lsb-1, -1)

def getVecIndex(msb: int, lsb: int, index: int) -> int:
    """Get the index in the list of [msb, ..., index, ... , lsb]
    
    index -> index in verilog slicing
    """
    if lsb > msb:
        return index - msb
    return msb - index

""" 
Base Number Parser 
    Parse the base numeber in verilog to formal binary string
"""
# Dictionary to map one octal char to binary
o2bDict = {
    "0" : "000", "1" : "001", "2" : "010",
    "3" : "011", "4" : "100", "5" : "101",
    "6" : "110", "7" : "111", "x" : "xxx",
    "z" : "zzz", "X" : "xxx", "Z" : "zzz",
    "_" : ""
}
o2b = lambda v: o2bDict[v]

# Dictionary to map one heximal char to binary
h2bDict = {
    "0" : "0000", "1" : "0001", "2" : "0010",
    "3" : "0011", "4" : "0100", "5" : "0101",
    "6" : "0110", "7" : "0111", "8" : "1000",
    "9" : "1001", "a" : "1010", "b" : "1011",
    "c" : "1100", "d" : "1101", "e" : "1110",
    "f" : "1111", "A" : "1010", "B" : "1011",
    "C" : "1100", "D" : "1101", "E" : "1110",
    "F" : "1111", "x" : "xxxx", "z" : "zzzz",
    "X" : "xxxx", "Z" : "zzzz", "_" : ""
}
h2b = lambda v: h2bDict[v]

def binExpend(bnum: str, width: int) -> str:
    """Expand binary value to specified size. """
    if not width: width = len(bnum)
    if bnum[0] == '1':
        return '0' * (width - len(bnum)) + bnum
    return bnum[0] * (width - len(bnum)) + bnum

def Bin2Bin(bnum: str, width: int = 0) -> str:
    return binExpend("".join(bnum.split("_")), width)
    
def Dic2Bin(bnum: str, width: int = 0) -> str:
    return binExpend(bin(int(bnum))[2:], width)

def Oct2Bin(bnum: str, width: int = 0) -> str:
    return binExpend("".join(map(o2b, bnum)), width)

def Hex2Bin(bnum: str, width: int = 0) -> str:
    return binExpend("".join(map(h2b, bnum)), width)

# Transform base number to regulated binary string with specified size
bnumParser = {
    "b": Bin2Bin, "B": Bin2Bin,
    "d": Dic2Bin, "D": Dic2Bin,
    "o": Oct2Bin, "O": Oct2Bin,
    "h": Hex2Bin, "H": Hex2Bin
}

""" 
Value Enconding 
    Standard of encoding 4-value to 2 bits
"""
value0 = 0 # 00
value1 = 1 # 01
valueX = 2 # 10
valueZ = 3 # 11

# 4-value encoder
"""
4-value encoding: 
    [Mbit][Lbit]
"""
vEncoder = {
    "1" : value1, "0" : value0,
    "x" : valueX, "X" : valueX, 
    "z" : valueZ, "Z" : valueZ,
}

# 4-value decoder
vDecoder = {
    value0: '0',
    value1: '1',
    valueX: 'x',
    valueZ: 'z'
}

