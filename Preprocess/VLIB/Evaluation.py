from functools import reduce

class Bit(object):
    """Manage bitwise operation."""
    def __init__(self, bit: str) -> None:
        self.bit = bit
    
    def __add__(self, other):
        if isinstance(other, Bit):
            other = other.bit
        return Bit(f"({self.bit}|{other})")
    
    def __mul__(self, other):
        if isinstance(other, Bit):
            other = other.bit
        return Bit(f"({self.bit}&{other})")
    
    def __pow__(self, other):
        if isinstance(other, Bit):
            other = other.bit
        return Bit(f"({self.bit}^{other})")
    
    def __invert__(self):
        return Bit(f"({self.bit}^1)")

class EvalFunc: 
    """Generating a single line string of evaluation formula."""
    TransGate = ["buf", "not"]
    PrimiGate = ["and", "or", "xor"]
    InvGate   = ["nand", "nor", "xnor"]
    SeqUDP = ["udp_tlat", "udp_dff"]
    CmbUdp = ["udp_xbuf", "udp_mux2"]
    # Gate mapper and evaluation function generator
    @staticmethod
    def NOT_gate(a: tuple):
        aM, aL = a
        return aM, ~(aM + aL)

    @staticmethod
    def BUF_gate(a: tuple):
        aM, aL = a
        return aM, ~aM * aL

    @staticmethod
    def AND_gate(a: tuple, b: tuple):
        aM, aL = a
        bM, bL = b
        nM = (aM + aL) * (bM + bL) * (aM + bM)
        return nM, ~nM * (aL * bL)

    @staticmethod
    def OR_gate(a: tuple, b: tuple):
        aM, aL = a
        bM, bL = b
        nM = (aM + ~aL) * (bM + ~bL) * (aM + bM)
        return nM, ~nM * (aL + bL)

    @staticmethod
    def XOR_gate(a: tuple, b: tuple):
        aM, aL = a
        bM, bL = b
        nM = aM + bM
        return nM, ~nM * (aL ** bL)

    @staticmethod
    def udp_xbuf_gate(a: tuple, b: tuple):
        aM, aL = a
        bM, bL = b
        nM = bM + ~bL
        return nM, ~nM * (aM + aL)

    @staticmethod
    def udp_mux2_gate(a: tuple, b: tuple, s: tuple):
        aM, aL = a
        bM, bL = b
        sM, sL = s
        Mselector = sL * bM + ~sL * aM
        Lselector = sL * bL + ~sL * aL
        equal = aM ** bM + aL ** bL
        nM = sM * (aM + bM  + equal) + (~sM * Mselector)
        nL = ~nM * (sM*aL  + ~sM*Lselector)
        return nM, nL

    gateDict = {
        "xnor": XOR_gate.__func__,
        "nand": AND_gate.__func__,
        "and" : AND_gate.__func__,
        "or"  : OR_gate.__func__,
        "nor" : OR_gate.__func__,
        "xor" : XOR_gate.__func__,
        "not" : NOT_gate.__func__,
        "buf" : BUF_gate.__func__,
        "udp_xbuf" : udp_xbuf_gate.__func__,
        "udp_mux2" : udp_mux2_gate.__func__
    }

    @staticmethod
    def generate(Gname: str, inList: list) -> str:
        """Generate the evaluation formula string."""
        def seperator(a):
            if isinstance(a, Bit):
                a = a.bit
            return Bit(f"({a}>>1)"), Bit(f"({a}&1)")

        def combine(a: tuple):
            return f"(({a[1].bit}) + ({a[0].bit} << 1))"

        inList = map(seperator, inList)
        if Gname in EvalFunc.CmbUdp or Gname in EvalFunc.TransGate:
            return combine(EvalFunc.gateDict[Gname](*inList))
        if Gname in EvalFunc.InvGate:
            return combine(EvalFunc.NOT_gate(reduce(EvalFunc.gateDict[Gname], inList)))
        return combine(reduce(EvalFunc.gateDict[Gname], inList))

""" Toolkit """
def decoder(pattern: int, length: int) -> list:
    for bitIdx in range(length-1, -1, -1):
        yield (pattern >> (bitIdx << 1))&3

def encoder(pattern: list) -> list:
    """Encode list of input value into integer pattern.
    (-1 if the corresponding input port is not specified)"""
    clner, cmper = 0, 0
    for p in pattern:
        clner, cmper = clner << 2, cmper << 2
        if p != -1:
            clner, cmper = clner|3, cmper|p

    return filter(lambda x: not (x&clner)^cmper, 
            range(4**(len(pattern))))