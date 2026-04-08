# Generated from /Users/ruicorreia/Projects/21018-Compilacao/MOCP.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .MOCPParser import MOCPParser
else:
    from MOCPParser import MOCPParser

# This class defines a complete listener for a parse tree produced by MOCPParser.
class MOCPListener(ParseTreeListener):

    # Enter a parse tree produced by MOCPParser#program.
    def enterProgram(self, ctx:MOCPParser.ProgramContext):
        pass

    # Exit a parse tree produced by MOCPParser#program.
    def exitProgram(self, ctx:MOCPParser.ProgramContext):
        pass


    # Enter a parse tree produced by MOCPParser#prototypes.
    def enterPrototypes(self, ctx:MOCPParser.PrototypesContext):
        pass

    # Exit a parse tree produced by MOCPParser#prototypes.
    def exitPrototypes(self, ctx:MOCPParser.PrototypesContext):
        pass


    # Enter a parse tree produced by MOCPParser#body.
    def enterBody(self, ctx:MOCPParser.BodyContext):
        pass

    # Exit a parse tree produced by MOCPParser#body.
    def exitBody(self, ctx:MOCPParser.BodyContext):
        pass


    # Enter a parse tree produced by MOCPParser#unit.
    def enterUnit(self, ctx:MOCPParser.UnitContext):
        pass

    # Exit a parse tree produced by MOCPParser#unit.
    def exitUnit(self, ctx:MOCPParser.UnitContext):
        pass


    # Enter a parse tree produced by MOCPParser#prototype.
    def enterPrototype(self, ctx:MOCPParser.PrototypeContext):
        pass

    # Exit a parse tree produced by MOCPParser#prototype.
    def exitPrototype(self, ctx:MOCPParser.PrototypeContext):
        pass


    # Enter a parse tree produced by MOCPParser#mainPrototype.
    def enterMainPrototype(self, ctx:MOCPParser.MainPrototypeContext):
        pass

    # Exit a parse tree produced by MOCPParser#mainPrototype.
    def exitMainPrototype(self, ctx:MOCPParser.MainPrototypeContext):
        pass


    # Enter a parse tree produced by MOCPParser#mainFunction.
    def enterMainFunction(self, ctx:MOCPParser.MainFunctionContext):
        pass

    # Exit a parse tree produced by MOCPParser#mainFunction.
    def exitMainFunction(self, ctx:MOCPParser.MainFunctionContext):
        pass


    # Enter a parse tree produced by MOCPParser#functionDef.
    def enterFunctionDef(self, ctx:MOCPParser.FunctionDefContext):
        pass

    # Exit a parse tree produced by MOCPParser#functionDef.
    def exitFunctionDef(self, ctx:MOCPParser.FunctionDefContext):
        pass


    # Enter a parse tree produced by MOCPParser#parameters.
    def enterParameters(self, ctx:MOCPParser.ParametersContext):
        pass

    # Exit a parse tree produced by MOCPParser#parameters.
    def exitParameters(self, ctx:MOCPParser.ParametersContext):
        pass


    # Enter a parse tree produced by MOCPParser#parameter.
    def enterParameter(self, ctx:MOCPParser.ParameterContext):
        pass

    # Exit a parse tree produced by MOCPParser#parameter.
    def exitParameter(self, ctx:MOCPParser.ParameterContext):
        pass


    # Enter a parse tree produced by MOCPParser#type.
    def enterType(self, ctx:MOCPParser.TypeContext):
        pass

    # Exit a parse tree produced by MOCPParser#type.
    def exitType(self, ctx:MOCPParser.TypeContext):
        pass


    # Enter a parse tree produced by MOCPParser#returnType.
    def enterReturnType(self, ctx:MOCPParser.ReturnTypeContext):
        pass

    # Exit a parse tree produced by MOCPParser#returnType.
    def exitReturnType(self, ctx:MOCPParser.ReturnTypeContext):
        pass


    # Enter a parse tree produced by MOCPParser#declaration.
    def enterDeclaration(self, ctx:MOCPParser.DeclarationContext):
        pass

    # Exit a parse tree produced by MOCPParser#declaration.
    def exitDeclaration(self, ctx:MOCPParser.DeclarationContext):
        pass


    # Enter a parse tree produced by MOCPParser#variableList.
    def enterVariableList(self, ctx:MOCPParser.VariableListContext):
        pass

    # Exit a parse tree produced by MOCPParser#variableList.
    def exitVariableList(self, ctx:MOCPParser.VariableListContext):
        pass


    # Enter a parse tree produced by MOCPParser#variable.
    def enterVariable(self, ctx:MOCPParser.VariableContext):
        pass

    # Exit a parse tree produced by MOCPParser#variable.
    def exitVariable(self, ctx:MOCPParser.VariableContext):
        pass


    # Enter a parse tree produced by MOCPParser#arrayBlock.
    def enterArrayBlock(self, ctx:MOCPParser.ArrayBlockContext):
        pass

    # Exit a parse tree produced by MOCPParser#arrayBlock.
    def exitArrayBlock(self, ctx:MOCPParser.ArrayBlockContext):
        pass


    # Enter a parse tree produced by MOCPParser#valueList.
    def enterValueList(self, ctx:MOCPParser.ValueListContext):
        pass

    # Exit a parse tree produced by MOCPParser#valueList.
    def exitValueList(self, ctx:MOCPParser.ValueListContext):
        pass


    # Enter a parse tree produced by MOCPParser#expression.
    def enterExpression(self, ctx:MOCPParser.ExpressionContext):
        pass

    # Exit a parse tree produced by MOCPParser#expression.
    def exitExpression(self, ctx:MOCPParser.ExpressionContext):
        pass


    # Enter a parse tree produced by MOCPParser#expressionOr.
    def enterExpressionOr(self, ctx:MOCPParser.ExpressionOrContext):
        pass

    # Exit a parse tree produced by MOCPParser#expressionOr.
    def exitExpressionOr(self, ctx:MOCPParser.ExpressionOrContext):
        pass


    # Enter a parse tree produced by MOCPParser#expressionAnd.
    def enterExpressionAnd(self, ctx:MOCPParser.ExpressionAndContext):
        pass

    # Exit a parse tree produced by MOCPParser#expressionAnd.
    def exitExpressionAnd(self, ctx:MOCPParser.ExpressionAndContext):
        pass


    # Enter a parse tree produced by MOCPParser#expressionEquality.
    def enterExpressionEquality(self, ctx:MOCPParser.ExpressionEqualityContext):
        pass

    # Exit a parse tree produced by MOCPParser#expressionEquality.
    def exitExpressionEquality(self, ctx:MOCPParser.ExpressionEqualityContext):
        pass


    # Enter a parse tree produced by MOCPParser#equalityOp.
    def enterEqualityOp(self, ctx:MOCPParser.EqualityOpContext):
        pass

    # Exit a parse tree produced by MOCPParser#equalityOp.
    def exitEqualityOp(self, ctx:MOCPParser.EqualityOpContext):
        pass


    # Enter a parse tree produced by MOCPParser#expressionRelational.
    def enterExpressionRelational(self, ctx:MOCPParser.ExpressionRelationalContext):
        pass

    # Exit a parse tree produced by MOCPParser#expressionRelational.
    def exitExpressionRelational(self, ctx:MOCPParser.ExpressionRelationalContext):
        pass


    # Enter a parse tree produced by MOCPParser#relationalOp.
    def enterRelationalOp(self, ctx:MOCPParser.RelationalOpContext):
        pass

    # Exit a parse tree produced by MOCPParser#relationalOp.
    def exitRelationalOp(self, ctx:MOCPParser.RelationalOpContext):
        pass


    # Enter a parse tree produced by MOCPParser#expressionAdd.
    def enterExpressionAdd(self, ctx:MOCPParser.ExpressionAddContext):
        pass

    # Exit a parse tree produced by MOCPParser#expressionAdd.
    def exitExpressionAdd(self, ctx:MOCPParser.ExpressionAddContext):
        pass


    # Enter a parse tree produced by MOCPParser#expressionMul.
    def enterExpressionMul(self, ctx:MOCPParser.ExpressionMulContext):
        pass

    # Exit a parse tree produced by MOCPParser#expressionMul.
    def exitExpressionMul(self, ctx:MOCPParser.ExpressionMulContext):
        pass


    # Enter a parse tree produced by MOCPParser#expressionUnary.
    def enterExpressionUnary(self, ctx:MOCPParser.ExpressionUnaryContext):
        pass

    # Exit a parse tree produced by MOCPParser#expressionUnary.
    def exitExpressionUnary(self, ctx:MOCPParser.ExpressionUnaryContext):
        pass


    # Enter a parse tree produced by MOCPParser#castExpr.
    def enterCastExpr(self, ctx:MOCPParser.CastExprContext):
        pass

    # Exit a parse tree produced by MOCPParser#castExpr.
    def exitCastExpr(self, ctx:MOCPParser.CastExprContext):
        pass


    # Enter a parse tree produced by MOCPParser#primary.
    def enterPrimary(self, ctx:MOCPParser.PrimaryContext):
        pass

    # Exit a parse tree produced by MOCPParser#primary.
    def exitPrimary(self, ctx:MOCPParser.PrimaryContext):
        pass


    # Enter a parse tree produced by MOCPParser#functionCall.
    def enterFunctionCall(self, ctx:MOCPParser.FunctionCallContext):
        pass

    # Exit a parse tree produced by MOCPParser#functionCall.
    def exitFunctionCall(self, ctx:MOCPParser.FunctionCallContext):
        pass


    # Enter a parse tree produced by MOCPParser#arguments.
    def enterArguments(self, ctx:MOCPParser.ArgumentsContext):
        pass

    # Exit a parse tree produced by MOCPParser#arguments.
    def exitArguments(self, ctx:MOCPParser.ArgumentsContext):
        pass


    # Enter a parse tree produced by MOCPParser#block.
    def enterBlock(self, ctx:MOCPParser.BlockContext):
        pass

    # Exit a parse tree produced by MOCPParser#block.
    def exitBlock(self, ctx:MOCPParser.BlockContext):
        pass


    # Enter a parse tree produced by MOCPParser#statement.
    def enterStatement(self, ctx:MOCPParser.StatementContext):
        pass

    # Exit a parse tree produced by MOCPParser#statement.
    def exitStatement(self, ctx:MOCPParser.StatementContext):
        pass


    # Enter a parse tree produced by MOCPParser#whileStatement.
    def enterWhileStatement(self, ctx:MOCPParser.WhileStatementContext):
        pass

    # Exit a parse tree produced by MOCPParser#whileStatement.
    def exitWhileStatement(self, ctx:MOCPParser.WhileStatementContext):
        pass


    # Enter a parse tree produced by MOCPParser#forStatement.
    def enterForStatement(self, ctx:MOCPParser.ForStatementContext):
        pass

    # Exit a parse tree produced by MOCPParser#forStatement.
    def exitForStatement(self, ctx:MOCPParser.ForStatementContext):
        pass


    # Enter a parse tree produced by MOCPParser#expressionOrAssign.
    def enterExpressionOrAssign(self, ctx:MOCPParser.ExpressionOrAssignContext):
        pass

    # Exit a parse tree produced by MOCPParser#expressionOrAssign.
    def exitExpressionOrAssign(self, ctx:MOCPParser.ExpressionOrAssignContext):
        pass


    # Enter a parse tree produced by MOCPParser#writeStatement.
    def enterWriteStatement(self, ctx:MOCPParser.WriteStatementContext):
        pass

    # Exit a parse tree produced by MOCPParser#writeStatement.
    def exitWriteStatement(self, ctx:MOCPParser.WriteStatementContext):
        pass


    # Enter a parse tree produced by MOCPParser#returnStatement.
    def enterReturnStatement(self, ctx:MOCPParser.ReturnStatementContext):
        pass

    # Exit a parse tree produced by MOCPParser#returnStatement.
    def exitReturnStatement(self, ctx:MOCPParser.ReturnStatementContext):
        pass


    # Enter a parse tree produced by MOCPParser#assignStatement.
    def enterAssignStatement(self, ctx:MOCPParser.AssignStatementContext):
        pass

    # Exit a parse tree produced by MOCPParser#assignStatement.
    def exitAssignStatement(self, ctx:MOCPParser.AssignStatementContext):
        pass


    # Enter a parse tree produced by MOCPParser#expressionStatement.
    def enterExpressionStatement(self, ctx:MOCPParser.ExpressionStatementContext):
        pass

    # Exit a parse tree produced by MOCPParser#expressionStatement.
    def exitExpressionStatement(self, ctx:MOCPParser.ExpressionStatementContext):
        pass


    # Enter a parse tree produced by MOCPParser#stringArgument.
    def enterStringArgument(self, ctx:MOCPParser.StringArgumentContext):
        pass

    # Exit a parse tree produced by MOCPParser#stringArgument.
    def exitStringArgument(self, ctx:MOCPParser.StringArgumentContext):
        pass



del MOCPParser