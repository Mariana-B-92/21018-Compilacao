# Generated from /Users/ruicorreia/Projects/21018-Compilacao/MOCP.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .MOCPParser import MOCPParser
else:
    from MOCPParser import MOCPParser

# This class defines a complete generic visitor for a parse tree produced by MOCPParser.

class MOCPVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by MOCPParser#program.
    def visitProgram(self, ctx:MOCPParser.ProgramContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#prototypes.
    def visitPrototypes(self, ctx:MOCPParser.PrototypesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#body.
    def visitBody(self, ctx:MOCPParser.BodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#unit.
    def visitUnit(self, ctx:MOCPParser.UnitContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#prototype.
    def visitPrototype(self, ctx:MOCPParser.PrototypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#mainPrototype.
    def visitMainPrototype(self, ctx:MOCPParser.MainPrototypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#mainFunction.
    def visitMainFunction(self, ctx:MOCPParser.MainFunctionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#functionDef.
    def visitFunctionDef(self, ctx:MOCPParser.FunctionDefContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#parameters.
    def visitParameters(self, ctx:MOCPParser.ParametersContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#parameter.
    def visitParameter(self, ctx:MOCPParser.ParameterContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#type.
    def visitType(self, ctx:MOCPParser.TypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#returnType.
    def visitReturnType(self, ctx:MOCPParser.ReturnTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#declaration.
    def visitDeclaration(self, ctx:MOCPParser.DeclarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#variableList.
    def visitVariableList(self, ctx:MOCPParser.VariableListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#variable.
    def visitVariable(self, ctx:MOCPParser.VariableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#arrayBlock.
    def visitArrayBlock(self, ctx:MOCPParser.ArrayBlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#valueList.
    def visitValueList(self, ctx:MOCPParser.ValueListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#expression.
    def visitExpression(self, ctx:MOCPParser.ExpressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#expressionOr.
    def visitExpressionOr(self, ctx:MOCPParser.ExpressionOrContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#expressionAnd.
    def visitExpressionAnd(self, ctx:MOCPParser.ExpressionAndContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#expressionEquality.
    def visitExpressionEquality(self, ctx:MOCPParser.ExpressionEqualityContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#equalityOp.
    def visitEqualityOp(self, ctx:MOCPParser.EqualityOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#expressionRelational.
    def visitExpressionRelational(self, ctx:MOCPParser.ExpressionRelationalContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#relationalOp.
    def visitRelationalOp(self, ctx:MOCPParser.RelationalOpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#expressionAdd.
    def visitExpressionAdd(self, ctx:MOCPParser.ExpressionAddContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#expressionMul.
    def visitExpressionMul(self, ctx:MOCPParser.ExpressionMulContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#expressionUnary.
    def visitExpressionUnary(self, ctx:MOCPParser.ExpressionUnaryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#castExpr.
    def visitCastExpr(self, ctx:MOCPParser.CastExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#primary.
    def visitPrimary(self, ctx:MOCPParser.PrimaryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#functionCall.
    def visitFunctionCall(self, ctx:MOCPParser.FunctionCallContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#arguments.
    def visitArguments(self, ctx:MOCPParser.ArgumentsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#block.
    def visitBlock(self, ctx:MOCPParser.BlockContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#statement.
    def visitStatement(self, ctx:MOCPParser.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#whileStatement.
    def visitWhileStatement(self, ctx:MOCPParser.WhileStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#forStatement.
    def visitForStatement(self, ctx:MOCPParser.ForStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#expressionOrAssign.
    def visitExpressionOrAssign(self, ctx:MOCPParser.ExpressionOrAssignContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#writeStatement.
    def visitWriteStatement(self, ctx:MOCPParser.WriteStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#returnStatement.
    def visitReturnStatement(self, ctx:MOCPParser.ReturnStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#assignStatement.
    def visitAssignStatement(self, ctx:MOCPParser.AssignStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#expressionStatement.
    def visitExpressionStatement(self, ctx:MOCPParser.ExpressionStatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by MOCPParser#stringArgument.
    def visitStringArgument(self, ctx:MOCPParser.StringArgumentContext):
        return self.visitChildren(ctx)



del MOCPParser