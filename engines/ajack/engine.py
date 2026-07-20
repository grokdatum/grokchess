"""Three L1 engines for the ajack collaboration.

They share one hand-written board evaluator, then choose moves in different
ways:

* ``AjackBerserker`` attacks first and accepts tactical risk.
* ``AjackLongbow`` builds pressure with bishops, rooks, and queens.
* ``AjackCounter`` predicts the opponent's best reply and favors moves that
  leave a strong answer to that reply.
"""

import random

import chess

from grokchess.engine_base import Engine


PIECE_VALUE = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

CENTER = [0] * 64
for _sq in range(64):
    _file, _rank = chess.square_file(_sq), chess.square_rank(_sq)
    _dist = abs(_file - 3.5) + abs(_rank - 3.5)
    CENTER[_sq] = int((6 - _dist) * 3)

INF = 10**9


def evaluate(board: chess.Board) -> int:
    """Static score from White's point of view."""
    if board.is_checkmate():
        return -INF if board.turn == chess.WHITE else INF
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    score = 0
    bishops = {chess.WHITE: 0, chess.BLACK: 0}
    for square, piece in board.piece_map().items():
        value = PIECE_VALUE[piece.piece_type]
        if piece.color == chess.WHITE:
            score += value + CENTER[square]
            if piece.piece_type == chess.BISHOP:
                bishops[chess.WHITE] += 1
            if piece.piece_type == chess.PAWN:
                score += chess.square_rank(square) * 2
        else:
            score -= value + CENTER[chess.square_mirror(square)]
            if piece.piece_type == chess.BISHOP:
                bishops[chess.BLACK] += 1
            if piece.piece_type == chess.PAWN:
                score -= (7 - chess.square_rank(square)) * 2

    if bishops[chess.WHITE] >= 2:
        score += 30
    if bishops[chess.BLACK] >= 2:
        score -= 30
    return score


def _score_for(board: chess.Board, color: chess.Color) -> int:
    score = evaluate(board)
    return score if color == chess.WHITE else -score


def _move_bonus(board: chess.Board, move: chess.Move) -> int:
    bonus = 0
    moving_piece = board.piece_at(move.from_square)
    captured_type = board.piece_type_at(move.to_square)
    if captured_type is None and board.is_en_passant(move):
        captured_type = chess.PAWN
    if captured_type is not None:
        moving_value = PIECE_VALUE[moving_piece.piece_type] if moving_piece else 0
        bonus += PIECE_VALUE[captured_type] - moving_value // 12
    if move.promotion is not None:
        bonus += PIECE_VALUE[move.promotion]
    if board.gives_check(move):
        bonus += 35
    if board.is_castling(move):
        bonus += 25
    return bonus


def _ordered_moves(board: chess.Board) -> list[chess.Move]:
    moves = list(board.legal_moves)
    random.shuffle(moves)
    moves.sort(key=lambda move: _move_bonus(board, move), reverse=True)
    return moves


def _top_ordered_moves(board: chess.Board, limit: int) -> list[chess.Move]:
    return _ordered_moves(board)[:limit]


def _choose_highest_scoring_move(board: chess.Board, score_move) -> chess.Move:
    best_score = -INF
    best_moves: list[chess.Move] = []
    for move in _ordered_moves(board):
        score = score_move(move)
        if score > best_score:
            best_score = score
            best_moves = [move]
        elif score == best_score:
            best_moves.append(move)
    return random.choice(best_moves)


def _king_zone(board: chess.Board, color: chess.Color) -> chess.SquareSet:
    king = board.king(color)
    if king is None:
        return chess.SquareSet()
    zone = chess.SquareSet(chess.BB_KING_ATTACKS[king])
    zone.add(king)
    return zone


def _attack_pressure(board: chess.Board, color: chess.Color) -> int:
    score = 0
    enemy = not color
    enemy_zone = _king_zone(board, enemy)
    for square, piece in board.piece_map().items():
        if piece.color != color:
            continue
        attacks = board.attacks(square)
        score += len(attacks & enemy_zone) * 28
        for target in attacks:
            victim = board.piece_at(target)
            if victim is not None and victim.color == enemy:
                score += PIECE_VALUE[victim.piece_type] // 10
    return score


def _has_pawn_on_file(board: chess.Board, color: chess.Color, file_index: int) -> bool:
    for square in board.pieces(chess.PAWN, color):
        if chess.square_file(square) == file_index:
            return True
    return False


def _long_range_pressure(board: chess.Board, color: chess.Color) -> int:
    score = 0
    enemy = not color
    enemy_home_ranks = {5, 6, 7} if color == chess.WHITE else {0, 1, 2}
    for square, piece in board.piece_map().items():
        if piece.color != color or piece.piece_type not in {
            chess.BISHOP,
            chess.ROOK,
            chess.QUEEN,
        }:
            continue
        attacks = board.attacks(square)
        score += len(attacks) * 5
        if piece.piece_type in {chess.ROOK, chess.QUEEN}:
            file_index = chess.square_file(square)
            if not _has_pawn_on_file(board, color, file_index):
                score += 20
            if not _has_pawn_on_file(board, enemy, file_index):
                score += 20
        for target in attacks:
            victim = board.piece_at(target)
            distance = chess.square_distance(square, target)
            if distance >= 3:
                score += 7
            if chess.square_rank(target) in enemy_home_ranks:
                score += 4
            if victim is not None and victim.color == enemy:
                score += PIECE_VALUE[victim.piece_type] // 8 + distance * 3
                if board.is_pinned(enemy, target):
                    score += 45
    return score


class AjackBerserker(Engine):
    name = "ajack-berserker"
    author = "ajack"
    league = "L1"

    def choose_move(self, board: chess.Board) -> chess.Move:
        us = board.turn

        def score_move(move: chess.Move) -> int:
            bonus = self._aggression_bonus(board, move)
            board.push(move)
            score = _score_for(board, us) + bonus + _attack_pressure(board, us)
            board.pop()
            return score

        return _choose_highest_scoring_move(board, score_move)

    def _aggression_bonus(self, board: chess.Board, move: chess.Move) -> int:
        bonus = _move_bonus(board, move) * 2
        moving_piece = board.piece_at(move.from_square)
        if board.gives_check(move):
            bonus += 120
        if moving_piece is not None:
            enemy_king = board.king(not board.turn)
            if enemy_king is not None:
                old_distance = chess.square_distance(move.from_square, enemy_king)
                new_distance = chess.square_distance(move.to_square, enemy_king)
                bonus += (old_distance - new_distance) * 18
            if moving_piece.piece_type in {chess.KNIGHT, chess.BISHOP}:
                home_rank = 0 if moving_piece.color == chess.WHITE else 7
                if chess.square_rank(move.from_square) == home_rank:
                    bonus += 35
        return bonus


class AjackLongbow(Engine):
    name = "ajack-longbow"
    author = "ajack"
    league = "L1"

    def choose_move(self, board: chess.Board) -> chess.Move:
        us = board.turn

        def score_move(move: chess.Move) -> int:
            bonus = self._line_bonus(board, move)
            board.push(move)
            score = (
                _score_for(board, us)
                + bonus
                + _long_range_pressure(board, us)
                - _long_range_pressure(board, not us) // 2
            )
            board.pop()
            return score

        return _choose_highest_scoring_move(board, score_move)

    def _line_bonus(self, board: chess.Board, move: chess.Move) -> int:
        bonus = _move_bonus(board, move)
        piece = board.piece_at(move.from_square)
        if piece is None:
            return bonus
        if piece.piece_type in {chess.BISHOP, chess.ROOK, chess.QUEEN}:
            bonus += 50
            if chess.square_distance(move.from_square, move.to_square) >= 3:
                bonus += 25
        if piece.piece_type == chess.PAWN and chess.square_file(move.from_square) in {3, 4}:
            bonus += 15
        return bonus


class AjackCounter(Engine):
    name = "ajack-counter"
    author = "ajack"
    league = "L1"
    move_limit = 10
    reply_limit = 8
    counter_limit = 8

    def choose_move(self, board: chess.Board) -> chess.Move:
        us = board.turn
        moves = _top_ordered_moves(board, self.move_limit)

        def score_move(move: chess.Move) -> int:
            bonus = _move_bonus(board, move)
            board.push(move)
            score = self._score_after_expected_reply(board, us) + bonus
            board.pop()
            return score

        return self._choose_from_moves(moves, score_move)

    def _choose_from_moves(self, moves: list[chess.Move], score_move) -> chess.Move:
        best_score = -INF
        best_moves: list[chess.Move] = []
        for move in moves:
            score = score_move(move)
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif score == best_score:
                best_moves.append(move)
        return random.choice(best_moves)

    def _score_after_expected_reply(self, board: chess.Board, us: chess.Color) -> int:
        if board.is_game_over():
            return _score_for(board, us)

        best_score = INF
        for reply in _top_ordered_moves(board, self.reply_limit):
            bonus = _move_bonus(board, reply)
            board.push(reply)
            score = self._best_counter_score(board, us) - bonus
            board.pop()
            if score < best_score:
                best_score = score
        return best_score

    def _best_counter_score(self, board: chess.Board, us: chess.Color) -> int:
        if board.is_game_over():
            return _score_for(board, us)

        best_score = -INF
        for counter in _top_ordered_moves(board, self.counter_limit):
            bonus = _move_bonus(board, counter)
            board.push(counter)
            score = _score_for(board, us) + bonus
            board.pop()
            best_score = max(best_score, score)
        return best_score
