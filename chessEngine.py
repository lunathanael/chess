"""
This class is responsible for storing all the information about the current state of a chess. It will also be
responsible for determining the valid moves at the current state and keep a move log.
"""
import numpy as np

class GameState:
    def __init__(self):
        self.board = np.array([["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
                               ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
                               ["--", "--", "--", "--", "--", "--", "--", "--"],
                               ["--", "--", "--", "--", "--", "--", "--", "--"],
                               ["--", "--", "--", "--", "--", "--", "--", "--"],
                               ["--", "--", "--", "--", "--", "--", "--", "--"],
                               ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
                               ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]])

        self.moveFunctions = {"p": self.getPawnMoves, "B": self.getBishopMoves, "N": self.getKnightMoves,
                              "R": self.getRookMoves, "Q": self.getQueenMoves, "K": self.getKingMoves}

        self.whiteToMove = True
        self.moveLog = []

        self.whiteKingLocation = (7, 4)
        self.blackKingLocation = (0, 4)
        self.checkMate = False
        self.staleMate = False
        self.draw = False
        self.check = False
        self.enpassantPossible = ()  # Coordinates for the square at which enpassant is possible
        self.enpassantPossibleLog = [self.enpassantPossible]
        self.currentCastlingRights = CastleRights(True, True, True, True)
        self.castleRightsLog = [CastleRights(self.currentCastlingRights.wks, self.currentCastlingRights.bks,
                                             self.currentCastlingRights.wqs, self.currentCastlingRights.bqs)]
        self.boardLog = np.zeros((1, 2))

        self.trying = False
        self.castled = [False, False]

    def initMove(self, move, aiThinking=False, isAIMove=False):
        self.board[move.startRow][move.startCol] = "--"
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.moveLog.append(move)
        # Refresh king location
        if move.pieceMoved == "wK":
            self.whiteKingLocation = (move.endRow, move.endCol)
        if move.pieceMoved == "bK":
            self.blackKingLocation = (move.endRow, move.endCol)

        # Pawn Promotion
        if move.isPawnPromotion:
            if self.trying or aiThinking or isAIMove:
                promotedPiece = move.promotionPiece
            else:
                promotedPiece = input("Promote to Q, R, B, or N:")
            self.board[move.endRow][move.endCol] = move.pieceMoved[0] + promotedPiece

        # En passant Move
        if move.isEnpassantMove:
            self.board[move.startRow][move.endCol] = "--"

        # Update enpassantpossible variable
        if move.pieceMoved[1] == "p" and abs(move.startRow - move.endRow) == 2:  # Only 2 square pawn advances
            self.enpassantPossible = ((move.startRow + move.endRow) // 2, move.startCol)
        else:
            self.enpassantPossible = ()

        # Castle move
        if move.isCastleMove:
            if self.whiteToMove:
                self.castled[0] = True
            else:
                self.castled[1] = True
            if move.endCol - move.startCol == 2:  # Kingside Castle
                self.board[move.endRow][move.endCol - 1] = self.board[move.endRow][move.endCol + 1]  # Add Rook
                self.board[move.endRow][move.endCol + 1] = "--"  # Erase old rook
            else:  # Queenside Castle
                self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][move.endCol - 2]  # Add Rook
                self.board[move.endRow][move.endCol - 2] = "--"  # Erase old rook


        self.whiteToMove = not self.whiteToMove

        if not self.trying:
            hashOf = hash(getFen(self.board, self.enpassantPossible, self.whiteToMove, self.currentCastlingRights))
            indexx = ind(self.boardLog, hashOf)
            if indexx == None:
                self.boardLog = np.vstack((self.boardLog, [hashOf, 1]))
            else:
                self.boardLog[list(indexx)[0], 1] += 1
                if self.boardLog[list(indexx)[0], 1] >= 3:
                    self.draw = True
            self.enpassantPossibleLog.append(self.enpassantPossible)
            # Update Castling Rights
            self.updateCastleRights(move)
            self.castleRightsLog.append(CastleRights(self.currentCastlingRights.wks, self.currentCastlingRights.bks,
                                                 self.currentCastlingRights.wqs, self.currentCastlingRights.bqs))


    def undoMove(self):
        if len(self.moveLog) != 0:
            if self.check:
                self.check = not self.check
            if not self.trying:
                hashOf = hash(getFen(self.board, self.enpassantPossible, self.whiteToMove, self.currentCastlingRights))
                indexx = ind(self.boardLog, hashOf)
                if indexx != None:
                    if self.boardLog[list(indexx)[0], 1] == 1:
                        self.boardLog = self.boardLog[:-1]
                    elif self.boardLog[list(indexx)[0], 1] == 2:
                        self.boardLog[list(indexx)[0], 1] -= 1
                    elif self.boardLog[list(indexx)[0], 1] == 3:
                        self.boardLog[list(indexx)[0], 1] -= 1

            move = self.moveLog.pop()
            #print(str(move))
            self.board[move.startRow][move.startCol] = move.pieceMoved
            self.board[move.endRow][move.endCol] = move.pieceCaptured

            # Refresh king location
            if move.pieceMoved == "wK":
                self.whiteKingLocation = (move.startRow, move.startCol)
            if move.pieceMoved == "bK":
                self.blackKingLocation = (move.startRow, move.startCol)

            # Enpassant Move
            if move.isEnpassantMove:
                self.board[move.endRow][move.endCol] = "--"  # Leave landing square blank
                self.board[move.startRow][move.endCol] = move.pieceCaptured


            if not self.trying:
                self.enpassantPossibleLog.pop()
                self.enpassantPossible = self.enpassantPossibleLog[-1]
                # Undo Castling Rights
                self.castleRightsLog.pop()  # Get rid of new castle rights from move undone
                self.currentCastlingRights = self.castleRightsLog[-1]  # Set current castle rights to last in list\

            if move.isCastleMove:
                if move.endCol - move.startCol == 2:
                    self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][move.endCol - 1]
                    self.board[move.endRow][move.endCol - 1] = "--"
                else:
                    self.board[move.endRow][move.endCol - 2] = self.board[move.endRow][move.endCol + 1]
                    self.board[move.endRow][move.endCol + 1] = "--"

            self.draw = False
            self.checkMate = False
            self.staleMate = False
            self.whiteToMove = not self.whiteToMove

    def updateCastleRights(self, move):
        if move.pieceMoved == "wK":
            self.currentCastlingRights.wks = False
            self.currentCastlingRights.wqs = False
        elif move.pieceMoved == "bK":
            self.currentCastlingRights.bks = False
            self.currentCastlingRights.bqs = False
        elif move.pieceMoved == "wR":
            if move.startRow == 7:
                if move.startCol == 0:
                    self.currentCastlingRights.wqs = False
                if move.startCol == 7:
                    self.currentCastlingRights.wks = False
        elif move.pieceMoved == "bR":
            if move.startRow == 0:
                if move.startCol == 0:
                    self.currentCastlingRights.bqs = False
                if move.startCol == 7:
                    self.currentCastlingRights.bks = False

        # Rook Captured
        elif move.pieceCaptured == "wR":
            if move.endRow == 7:
                if move.endCol == 0:
                    self.currentCastlingRights.wqs = False
                if move.endCol == 7:
                    self.currentCastlingRights.wks = False
        elif move.pieceCaptured == "bR":
            if move.endRow == 0:
                if move.endCol == 0:
                    self.currentCastlingRights.bqs = False
                if move.endCol == 7:
                    self.currentCastlingRights.bks = False

    # Checks are considered
    def getValidMoves(self):
        self.trying = True
        moves = self.getAllPossibleMoves()
        opp = "b" if self.whiteToMove else "w"
        for i in range(len(moves) - 1, -1, -1):
            self.initMove(moves[i])
            if self.inCheck(opp):
                moves.remove(moves[i])
            self.undoMove()

        if self.whiteToMove:
            self.getCastleMoves(self.whiteKingLocation[0], self.whiteKingLocation[1], moves, "b")
        else:
            self.getCastleMoves(self.blackKingLocation[0], self.blackKingLocation[1], moves, "w")

        if len(moves) == 0:
            if self.inCheck(opp):
                self.check = True
                self.checkMate = True
            else:
                self.check = False
                self.staleMate = True

        else:
            self.checkMate = False
            self.staleMate = False
        self.trying = False

        return moves

    def inCheck(self, opp):
        if opp == "w":
            return self.isUnderAttack("w", self.blackKingLocation[0], self.blackKingLocation[1])

        else:
            return self.isUnderAttack("b", self.whiteKingLocation[0], self.whiteKingLocation[1])

    def isUnderAttack(self, targetTurn, r, c):
        # Check Knight Squares
        knightMoves = ((1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1))  # 4 Directions
        for m in knightMoves:
            endRow = r + m[0]
            endCol = c + m[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece == (targetTurn + "N"):  # Valid target
                    return True

        # Check Diagonals
        directions = ((1, 1), (1, -1), (-1, 1), (-1, -1))
        for d in directions:
            for i in range(1, 8):  # Maximum of 7 squares
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    endPiece = self.board[endRow][endCol]
                    if endPiece == "--":
                        continue
                    if endPiece[0] != targetTurn:
                        break
                    if endPiece[1] == "Q" or endPiece[1] == "B":  # Valid target
                        return True
                    if i == 1:
                        if endPiece[1] == "K":
                            return True
                        if d[0] == 1 and endPiece == "wp":
                            return True
                        if d[0] == -1 and endPiece == "bp":
                            return True
                    break
                else:  # Move is off board
                    break
        # Check Horizontal
        directions = ((-1, 0), (1, 0), (0, -1), (0, 1))  # 4 Directions
        for d in directions:
            for i in range(1, 8):  # Maximum of 7 squares
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    endPiece = self.board[endRow][endCol]
                    if endPiece == "--":
                        continue
                    if endPiece[0] != targetTurn:
                        break
                    if endPiece[1] == "Q" or endPiece[1] == "R":
                        # Valid target
                        return True
                    if i == 1 and endPiece[1] == "K":
                        return True
                    break
                else:  # Move is off board
                    break

        return False

    def getValidCaptures(self):
        self.trying = True
        moves = self.getCapturesOnly()
        opp = "b" if self.whiteToMove else "w"
        if moves == None:
            return moves
        for i in range(len(moves) - 1, -1, -1):
            self.initMove(moves[i])
            if self.inCheck(opp):
                moves.remove(moves[i])
            self.undoMove()

        if len(moves) == 0:
            if self.inCheck(opp):
                self.check = True
                self.checkMate = True
            else:
                self.check = False
                self.staleMate = True

        else:
            self.checkMate = False
            self.staleMate = False

        self.trying = False

        return moves


    def getCapturesOnly(self):
        moves = []
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                turn = self.board[r][c][0]
                if (turn == "w" and self.whiteToMove) or (turn == "b" and not self.whiteToMove):
                    piece = self.board[r][c][1]
                    targetTurn = "b" if self.whiteToMove else "w"
                    # Captures and promotions first
                    if self.whiteToMove:
                        moveAmount = -1
                        startRow = 6
                        backRow = 0
                    else:
                        moveAmount = 1
                        startRow = 1
                        backRow = 7
                    match piece:
                        case "p":
                            if c - 1 >= 0:
                                if self.board[r + moveAmount][c - 1][0] == targetTurn:
                                    if r == backRow:
                                        moves.insert(
                                            0, makeMove((r, c), (r + moveAmount, c - 1), self.board, promotionPiece="Q"))
                                        moves.insert(
                                            0, makeMove((r, c), (r + moveAmount, c - 1), self.board, promotionPiece="N"))
                                        moves.insert(
                                            0, makeMove((r, c), (r + moveAmount, c - 1), self.board, promotionPiece="B"))
                                        moves.insert(
                                            0, makeMove((r, c), (r + moveAmount, c - 1), self.board, promotionPiece="R"))
                                    else:
                                        moves.insert(0, makeMove((r, c), (r + moveAmount, c - 1), self.board))
                                elif (r + moveAmount, c - 1) == self.enpassantPossible:
                                    moves.insert(
                                        0, makeMove((r, c), (r + moveAmount, c - 1), self.board, isEnpassantMove=True))
                            if c + 1 <= 7:
                                if self.board[r + moveAmount][c + 1][0] == targetTurn:
                                    if r == backRow:
                                        moves.insert(0, makeMove((r, c), (r + moveAmount, c + 1), self.board, "Q"))
                                        moves.insert(0, makeMove((r, c), (r + moveAmount, c + 1), self.board, "N"))
                                        moves.insert(0, makeMove((r, c), (r + moveAmount, c + 1), self.board, "B"))
                                        moves.insert(0, makeMove((r, c), (r + moveAmount, c + 1), self.board, "R"))
                                    else:
                                        moves.insert(0, makeMove((r, c), (r + moveAmount, c + 1), self.board))
                                elif (r + moveAmount, c + 1) == self.enpassantPossible:
                                    moves.insert(
                                        0, makeMove((r, c), (r + moveAmount, c + 1), self.board, isEnpassantMove=True))
                        case "B":
                            directions = ((-1, -1), (1, 1), (1, -1), (-1, 1))  # 4 Directions
                            for d in directions:
                                for i in range(1, 8):  # Maximum of 7 squares
                                    endRow = r + d[0] * i
                                    endCol = c + d[1] * i
                                    if 0 <= endRow < 8 and 0 <= endCol < 8:
                                        endPiece = self.board[endRow][endCol]
                                        if endPiece[0] == targetTurn:  # Valid target
                                            moves.append(makeMove((r, c), (endRow, endCol), self.board))
                                            break
                                        elif endPiece[0] != "-":  # Same turn target
                                            break
                                    else:  # Move is off board
                                        break
                        case "N":
                            knightMoves = (
                            (1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1))  # 4 Directions
                            for m in knightMoves:
                                endRow = r + m[0]
                                endCol = c + m[1]
                                if 0 <= endRow < 8 and 0 <= endCol < 8:
                                    endPiece = self.board[endRow][endCol]
                                    if endPiece[0] == targetTurn:  # Valid target
                                        moves.append(makeMove((r, c), (endRow, endCol), self.board))
                        case "R":
                            directions = ((-1, 0), (1, 0), (0, -1), (0, 1))  # 4 Directions
                            for d in directions:
                                for i in range(1, 8):  # Maximum of 7 squares
                                    endRow = r + d[0] * i
                                    endCol = c + d[1] * i
                                    if 0 <= endRow < 8 and 0 <= endCol < 8:
                                        endPiece = self.board[endRow][endCol]
                                        if endPiece[0] == targetTurn:  # Valid target
                                            moves.append(makeMove((r, c), (endRow, endCol), self.board))
                                            break
                                        elif endPiece != "--":  # Same turn target
                                            break
                                    else:  # Move is off board
                                        break
                        case "Q":
                            directions = (
                            (-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (1, -1), (-1, 1))  # 8 Directions
                            for d in directions:
                                for i in range(1, 8):  # Maximum of 7 squares
                                    endRow = r + d[0] * i
                                    endCol = c + d[1] * i
                                    if 0 <= endRow < 8 and 0 <= endCol < 8:
                                        endPiece = self.board[endRow][endCol]
                                        if endPiece[0] == targetTurn:  # Valid target
                                            moves.append(makeMove((r, c), (endRow, endCol), self.board))
                                            break
                                        elif endPiece != "--":  # Same turn target
                                            break
                                    else:  # Move is off board
                                        break
                        case "K":
                            directions = (
                            (-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (1, -1), (-1, 1))  # 8 Directions
                            for i in range(8):
                                endRow = r + directions[i][0]
                                endCol = c + directions[i][1]
                                if 0 <= endRow < 8 and 0 <= endCol < 8:
                                    endPiece = self.board[endRow][endCol]
                                    if endPiece[0] == targetTurn:  # Valid target
                                        moves.append(makeMove((r, c), (endRow, endCol), self.board))
                    # Captures over.

    def getAllPossibleMoves(self):
        moves = []
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                turn = self.board[r][c][0]
                if (turn == "w" and self.whiteToMove) or (turn == "b" and not self.whiteToMove):
                    piece = self.board[r][c][1]
                    self.moveFunctions[piece](r, c, moves)  # Call the appropriate move function based off of piece type
        return moves

    def getPawnMoves(self, r, c, moves): # Add promotion choices
        if self.whiteToMove:
            moveAmount = -1
            startRow = 6
            backRow = 0
            targetColor = "b"
        else:
            moveAmount = 1
            startRow = 1
            backRow = 7
            targetColor = "w"
        if c - 1 >= 0:
            if self.board[r + moveAmount][c - 1][0] == targetColor:
                if r == backRow:
                    moves.insert(0, makeMove((r, c), (r + moveAmount, c - 1), self.board, promotionPiece="Q"))
                    moves.insert(0, makeMove((r, c), (r + moveAmount, c - 1), self.board, promotionPiece="N"))
                    moves.insert(0, makeMove((r, c), (r + moveAmount, c - 1), self.board, promotionPiece="B"))
                    moves.insert(0, makeMove((r, c), (r + moveAmount, c - 1), self.board, promotionPiece="R"))
                else:
                    moves.append(makeMove((r, c), (r + moveAmount, c - 1), self.board))
            elif (r + moveAmount, c - 1) == self.enpassantPossible:
                moves.insert(0, makeMove((r, c), (r + moveAmount, c - 1), self.board, isEnpassantMove=True))
        if c + 1 <= 7:
            if self.board[r + moveAmount][c + 1][0] == targetColor:
                if r == backRow:
                    moves.insert(0, makeMove((r, c), (r + moveAmount, c + 1), self.board, "Q"))
                    moves.insert(0, makeMove((r, c), (r + moveAmount, c + 1), self.board, "N"))
                    moves.insert(0, makeMove((r, c), (r + moveAmount, c + 1), self.board, "B"))
                    moves.insert(0, makeMove((r, c), (r + moveAmount, c + 1), self.board, "R"))
                else:
                    moves.insert(0, makeMove((r, c), (r + moveAmount, c + 1), self.board))
            elif (r + moveAmount, c + 1) == self.enpassantPossible:
                moves.insert(0, makeMove((r, c), (r + moveAmount, c + 1), self.board, isEnpassantMove=True))


        if self.board[r + moveAmount][c] == "--":
            if r == startRow and self.board[r + (2 * moveAmount)][c] == "--":
                moves.append(makeMove((r, c), (r + (2 * moveAmount), c), self.board))
            if r == backRow:
                moves.insert(0, makeMove((r, c), (r + moveAmount, c), self.board, promotionPiece="Q"))
                moves.insert(0, makeMove((r, c), (r + moveAmount, c), self.board, promotionPiece="N"))
                moves.insert(0, makeMove((r, c), (r + moveAmount, c), self.board, promotionPiece="B"))
                moves.insert(0, makeMove((r, c), (r + moveAmount, c), self.board, promotionPiece="R"))
            else:
                moves.append(makeMove((r, c), (r + moveAmount, c), self.board))

    def getBishopMoves(self, r, c, moves):
        directions = ((-1, -1), (1, 1), (1, -1), (-1, 1))  # 4 Directions
        allyTurn = "w" if self.whiteToMove else "b"
        for d in directions:
            for i in range(1, 8):  # Maximum of 7 squares
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] == allyTurn:
                        break
                    elif endPiece == "--":
                        moves.append(makeMove((r, c), (endRow, endCol), self.board))
                    else:
                        moves.insert(0, makeMove((r, c), (endRow, endCol), self.board))
                        break
                else:  # Move is off board
                    break

    def getKnightMoves(self, r, c, moves):
        knightMoves = ((1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1))  # 4 Directions
        allyTurn = "w" if self.whiteToMove else "b"
        for m in knightMoves:
            endRow = r + m[0]
            endCol = c + m[1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] != allyTurn:  # Valid target
                    if endPiece == "--":
                        moves.append(makeMove((r, c), (endRow, endCol), self.board))
                    else:
                        moves.insert(0, makeMove((r, c), (endRow, endCol), self.board))

    def getRookMoves(self, r, c, moves):
        directions = ((-1, 0), (1, 0), (0, -1), (0, 1))  # 4 Directions
        allyTurn = "w" if self.whiteToMove else "b"
        for d in directions:
            for i in range(1, 8):  # Maximum of 7 squares
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    endPiece = self.board[endRow][endCol]
                    if endPiece[0] != allyTurn:  # Valid target
                        if endPiece == "--":
                            moves.append(makeMove((r, c), (endRow, endCol), self.board))
                        else:
                            moves.insert(0, makeMove((r, c), (endRow, endCol), self.board))
                            break
                    else:  # Same turn target
                        break
                else:  # Move is off board
                    break

    def getQueenMoves(self, r, c, moves):
        directions = ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (1, -1), (-1, 1))  # 8 Directions
        targetTurn = "b" if self.whiteToMove else "w"
        for d in directions:
            for i in range(1, 8):  # Maximum of 7 squares
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:
                    endPiece = self.board[endRow][endCol]
                    if endPiece == "--":  # Valid empty space
                        moves.append(makeMove((r, c), (endRow, endCol), self.board))
                    elif endPiece[0] == targetTurn:  # Valid target
                        moves.insert(0, makeMove((r, c), (endRow, endCol), self.board))
                        break
                    else:  # Same turn target
                        break
                else:  # Move is off board
                    break

    def getKingMoves(self, r, c, moves):
        directions = ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (1, -1), (-1, 1))  # 8 Directions
        allyTurn = "w" if self.whiteToMove else "b"
        for i in range(8):
            endRow = r + directions[i][0]
            endCol = c + directions[i][1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece == "--":  # Valid empty space
                    moves.append(makeMove((r, c), (endRow, endCol), self.board))
                elif endPiece[0] != allyTurn:  # Valid target
                    moves.insert(0, makeMove((r, c), (endRow, endCol), self.board))

    # Get all valid castle moves for the king at (r, c) and add to list of moves
    def getCastleMoves(self, r, c, moves, allyTurn):
        if self.inCheck(allyTurn):
            self.check = True
            return
        else:
            self.check = False
        if not ((r == 0 and c == 4) or (r == 7 and c == 4)):
            return
        if (self.whiteToMove and self.currentCastlingRights.wks) or (
                not self.whiteToMove and self.currentCastlingRights.bks):
            self.getKingsideCastleMoves(r, c, moves, allyTurn)
        if (self.whiteToMove and self.currentCastlingRights.wqs) or (
                not self.whiteToMove and self.currentCastlingRights.bqs):
            self.getQueensideCastleMoves(r, c, moves, allyTurn)

    def getKingsideCastleMoves(self, r, c, moves, allyTurn):
        if self.board[r][c + 1] == "--" and self.board[r][c + 2] == "--":
            if (not self.isUnderAttack(allyTurn, r, c + 1)) and (not self.isUnderAttack(allyTurn, r, c + 2)):
                moves.insert(0, makeMove((r, c), (r, c + 2), self.board, isCastleMove=True))

    def getQueensideCastleMoves(self, r, c, moves, allyTurn):
        if self.board[r][c - 1] == "--" and self.board[r][c - 2] == "--" and self.board[r][c - 3] == "--":
            if not self.isUnderAttack(allyTurn, r, c - 1) and not self.isUnderAttack(allyTurn, r, c - 2):
                moves.insert(0, makeMove((r, c), (r, c - 2), self.board, isCastleMove=True))


class CastleRights():
    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs


class makeMove:
    ranksToRows = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
    rowsToRanks = {v: k for k, v in ranksToRows.items()}
    filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
    colsToFiles = {v: k for k, v in filesToCols.items()}

    def __init__(self, startSq, endSq, board, promotionPiece="Q", isEnpassantMove=False, isCastleMove=False):
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]

        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]

        # Pawn promotion
        self.isPawnPromotion = (
                    (self.pieceMoved == "wp" and self.endRow == 0) or (self.pieceMoved == "bp" and self.endRow == 7))
        self.promotionPiece = promotionPiece

        # Enpassant
        self.isEnpassantMove = isEnpassantMove
        if self.isEnpassantMove:
            self.pieceCaptured = "wp" if self.pieceMoved == "bp" else "bp"

        self.isCapture = self.pieceCaptured != "--"

        # Castle move
        self.isCastleMove = isCastleMove

        # Assigning an identity for each move
        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol

    """
    Override The equals method
    """

    def __eq__(self, other):
        if isinstance(other, makeMove):
            return self.moveID == other.moveID
        return False

    def getChessNotation(self):
        # Can add to make real chess notation
        return self.getRankFile(self.startRow, self.startCol) + self.getRankFile(self.endRow, self.endCol)

    def getRankFile(self, r, c):
        return self.colsToFiles[c] + self.rowsToRanks[r]

    def __str__(self):  # Overriding string function
        # Castle Move
        if self.isCastleMove:
            return "O-O" if self.endCol == 6 else "O-O-O"
        endSquare = self.getRankFile(self.endRow, self.endCol)
        # Pawn Moves
        if self.pieceMoved[1] == "p":
            if self.isCapture:
                return self.colsToFiles[self.startCol] + "x" + endSquare
            if self.isPawnPromotion:
                return endSquare + "=" + self.promotionPiece
            else:
                return endSquare

            # Pawn Promotions
        #Two of same type of piece moving to a square,
        # Adding + for check and # for Checkmate

        # piece moves
        moveString = self.pieceMoved[1]
        if self.isCapture:
            moveString += "x"
        return moveString + endSquare


def getFen(board, enp, turn, castle):
    spaces = 0
    FEN = ""
    for row in range(len(board)):
        for col in range(len(board[row])):
            square = board[row][col]
            if square == "--":
                spaces += 1
                continue
            else:
                if spaces != 0:
                    FEN += str(spaces)
                    spaces = 0
                piece = square[1]
                if square == "wp":
                    piece = piece.capitalize()
                if square[0] == "b":
                    piece = piece.lower()
                FEN += piece
        if spaces != 0:
            FEN += str(spaces)
            spaces = 0
        if row != 7:
            FEN += "/"
    if turn:
        FEN += " w "
    else:
        FEN += " b "

    if castle.wks:
        FEN += "K"
    if castle.wqs:
        FEN += "Q"
    if castle.bks:
        FEN += "k"
    if castle.bqs:
        FEN += "q"

    if enp != ():
        FEN += " " + getRankFile(list(enp)[0], list(enp)[1])
    return FEN

ranksToRows = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
rowsToRanks = {v: k for k, v in ranksToRows.items()}
filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
colsToFiles = {v: k for k, v in filesToCols.items()}


def getRankFile(r, c):
    return colsToFiles[c] + rowsToRanks[r]


def ind(array, item):
    for idx, val in np.ndenumerate(array):
        if val == item:
            return idx