import chess
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000
}

KNIGHT_TABLE = [
    -10,-5,-5,-5,-5,-5,-5,-10,
     -5, 0, 0, 0, 0, 0, 0, -5,
     -5, 0, 5, 5, 5, 5, 0, -5,
     -5, 0, 5, 10,10, 5, 0, -5,
     -5, 0, 5, 10,10, 5, 0, -5,
     -5, 0, 5, 5, 5, 5, 0, -5,
     -5, 0, 0, 0, 0, 0, 0, -5,
    -10,-5,-5,-5,-5,-5,-5,-10
]

def evaluate_board(board):
    if board.is_checkmate():
        return -99999 if board.turn else 99999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    total_evaluation = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is not None:
            val = PIECE_VALUES[piece.piece_type]
            if piece.piece_type == chess.KNIGHT:
                val += KNIGHT_TABLE[square if piece.color == chess.WHITE else 63 - square]
            if piece.color == chess.WHITE:
                total_evaluation += val
            else:
                total_evaluation -= val

    if board.has_kingside_castling_rights(chess.BLACK) or board.has_queenside_castling_rights(chess.BLACK):
        total_evaluation += 15
    if board.has_kingside_castling_rights(chess.WHITE) or board.has_queenside_castling_rights(chess.WHITE):
        total_evaluation -= 15

    return total_evaluation if board.turn == chess.WHITE else -total_evaluation

def alpha_beta(board, depth, alpha, beta, maximizing_player):
    if depth == 0 or board.is_game_over():
        return evaluate_board(board), None

    best_move = None
    legal_moves = list(board.legal_moves)
    legal_moves.sort(key=lambda m: board.is_capture(m), reverse=True)

    if maximizing_player:
        max_eval = -float('inf')
        for move in legal_moves:
            board.push(move)
            eval, _ = alpha_beta(board, depth - 1, alpha, beta, False)
            board.pop()
            if eval > max_eval:
                max_eval = eval
                best_move = move
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in legal_moves:
            board.push(move)
            eval, _ = alpha_beta(board, depth - 1, alpha, beta, True)
            board.pop()
            if eval < min_eval:
                min_eval = eval
                best_move = move
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval, best_move

@app.route('/move', methods=['POST'])
def make_move():
    data = request.json
    fen = data.get('fen')
    board = chess.Board(fen)
    
    if board.is_game_over():
        return jsonify({'error': 'Game over'})

    _, best_move = alpha_beta(board, depth=3, alpha=-float('inf'), beta=float('inf'), maximizing_player=True)
    
    if best_move:
        board.push(best_move)
        return jsonify({'best_move': best_move.uci(), 'fen': board.fen()})
    
    return jsonify({'error': 'No legal moves found'})

if __name__ == '__main__':
    app.run(port=5000)
