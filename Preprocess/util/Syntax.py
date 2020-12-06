if __name__ == "__main__":
    from  util import bnumParser, StringParser
else:
    from .util import bnumParser, StringParser

from pyparsing import \
    Literal, CaselessLiteral, Keyword, Word, OneOrMore, ZeroOrMore, \
    Forward, NotAny, delimitedList, Group, Optional, Combine, Suppress
from pyparsing import \
    alphas, nums, restOfLine, cppStyleComment, alphanums, printables, \
    dblQuotedString, empty, ParseException, ParseResults, MatchFirst,\
    oneOf, GoToColumn, ParseResults, StringEnd, FollowedBy, ParserElement,\
    And, Regex

# primitives
SEMI, COLON, LPAR, RPAR, LBRACE, RBRACE, LBRACK, RBRACK, DOT, COMMA, EQ, QUEST = map(
    Literal, ";:(){}[].,=?"
)

# keywords
WIRE   = Keyword("wire")
MODULE = Keyword("module")

""" Identifier """
identLead = alphas+"$_"
identBody = alphanums+"$_"

# Identifier which not allowed numeric value as first charcter
IDENTIFIER = Regex(
    r"[" +identLead + "][" +identBody+ "]*"
).setName("baseIDENTIFIER")

# Identifier which allowed any character after '\'
eIDENTIFIER = Regex(
    r"\\\S+"
).setName("escapedIDENTIFIER")

IDENTIFIER = (IDENTIFIER | eIDENTIFIER).setName("IDENTIFIER")
identifier = (
    IDENTIFIER + ZeroOrMore(
        Combine(DOT + IDENTIFIER)
    )
).setName("identifier")

""" number """
def parseBaseNumber(t) -> list:
    """ Parse the base number to a list of chars representing in the binary form """
    encoder = bnumParser[t[-2]]
    value = t[-1]
    # Specifed the width of base number
    width = int(t[0]) if len(t) > 2 else 0

    if width < 0: # Negative 
        absDic = int(encoder(value, -width), base = 2)
        return list(bin(absDic - (1 << -width))[3:])
    return list(encoder(value, width))

UnsignedNumber = OneOrMore(Word(nums + "_"))
hexnums = nums + "abcdefABCDEF_?xXzZ"
DecimalNumber  = Combine(Optional(
    Literal("+") | Literal("-")) + UnsignedNumber)
Base = Regex("'[bBoOdDhH]").setName("BASE").setParseAction(lambda t: t[0][1:])
BaseNumber = (
    Optional(DecimalNumber) + Base + Word(hexnums)
).setName("BASENUMBER").setParseAction(parseBaseNumber)

number = ( 
        BaseNumber
        | Regex(r"[+-]?[0-9_]+(\.[0-9_]*)?([Ee][+-]?[0-9_]+)?").setParseAction(lambda t: float(t[0]))
).setName("number")


""" expression and primary """
UNOP  = oneOf(
    "+  -  !  ~  &  ~&  |  ^|  ^  ~^" 
).setName("UNARY_OPERATOR")
BINOP = oneOf( 
    "+  -  *  /  %  ==  !=  ===  !==  &&  "
    "||  <  <=  >  >=  &  |  ^  ^~  >>  << ** <<< >>>" 
).setName("BINARY_OPERATOR")

expr = Forward().setName("expression")

concat = (
    LBRACE + delimitedList(expr) + RBRACE
).setName("concatenation").setParseAction(lambda t:t[1:-1])
# Replication Operator
multiconcat = (
    LBRACE + expr + Group(concat) + RBRACE
).setName("multiconcatenation").setParseAction(lambda t:int(t[1])*list(t[2]))
funcCall = Group(
    identifier + Group(LPAR + delimitedList(expr) + RPAR)
).setName("functionCall")

subscrRef = (
    LBRACK + expr + Optional((COLON + expr).setParseAction(lambda t:t[1])) + RBRACK
).setParseAction(lambda t:t[1:-1])

subscrIdentifier = (identifier + Optional(Group(subscrRef)))
mintypmaxExpr = Group(expr + COLON + expr + COLON + expr).setName("mintypmax")

primary = (
    number 
    | (LPAR + mintypmaxExpr + RPAR) 
    | (LPAR +  Group(expr)  + RPAR).setParseAction(lambda t: t[1])
    | multiconcat 
    | concat 
    | dblQuotedString 
    | funcCall
    | subscrIdentifier 
).setName("primary")

expr << (
    (UNOP + expr)
    | (primary + QUEST + expr + COLON + expr).setParseAction(lambda t: [t[0], t[2], t[4]])
    | (primary + Optional(BINOP + primary))
)

lvalue = (subscrIdentifier | concat)

if __name__ == "__main__":
    tstring = " \
{u_partition_o_ICCADs_n44319 [3], u_partition_o_ICCADs_n44319 [3]}\
"
    StringParser(concat, tstring)
    