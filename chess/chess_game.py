#!/usr/bin/env python3
"""
Community Chess Game with AI Opponent for GitHub Profile README.
Visitors play as White, AI plays as Black automatically.
Uses minimax with alpha-beta pruning for move selection.
"""

import chess
import chess.svg
import json
import os
import sys
import urllib.parse
import random

# Configuration
REPO = "Tahmid1999/Tahmid1999"
STATE_FILE = "chess/game_state.json"
BOARD_SVG = "chess/board.svg"
README_FILE = "README.md"
START_MARKER = "<!-- CHESS:START -->"
END_MARKER = "<!-- CHESS:END -->"
AI_DEPTH = 3  # Search depth for minimax

PIECE_SYMBOLS = {
    chess.PAWN: "♟", chess.KNIGHT: "♞", chess.BISHOP: "♝",
    chess.ROOK: "♜", chess.QUEEN: "♛", chess.KING: "♚",
}
PIECE_NAMES = {
    chess.PAWN: "Pawn", chess.KNIGHT: "Knight", chess.BISHOP: "Bishop",
    chess.ROOK: "Rook", chess.QUEEN: "Queen", chess.KING: "King",
}

# ============================================================
# CHESS AI ENGINE - Minimax with Alpha-Beta Pruning
# ============================================================

# Piece values
PIECE_VALUES = {
    chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
    chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 20000,
}

# Piece-square tables (from White's perspective, flipped for Black)
PAWN_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]

ROOK_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0,
]

QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]

KING_TABLE_MID = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20,
]

PST = {
    chess.PAWN: PAWN_TABLE,
    chess.KNIGHT: KNIGHT_TABLE,
    chess.BISHOP: BISHOP_TABLE,
    chess.ROOK: ROOK_TABLE,
    chess.QUEEN: QUEEN_TABLE,
    chess.KING: KING_TABLE_MID,
}


def evaluate_board(board):
    """Evaluate the board position. Positive = White advantage, Negative = Black advantage."""
    if board.is_checkmate():
        return -99999 if board.turn == chess.WHITE else 99999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is None:
            continue

        # Material value
        value = PIECE_VALUES[piece.piece_type]

        # Positional value from piece-square tables
        if piece.color == chess.WHITE:
            pst_index = chess.square_mirror(square)
            value += PST[piece.piece_type][pst_index]
            score += value
        else:
            value += PST[piece.piece_type][square]
            score -= value

    # Mobility bonus
    mobility = len(list(board.legal_moves))
    if board.turn == chess.WHITE:
        score += mobility * 2
    else:
        score -= mobility * 2

    return score


def order_moves(board):
    """Order moves for better alpha-beta pruning (captures first, then checks)."""
    moves = list(board.legal_moves)

    def move_score(move):
        score = 0
        # Prioritize captures (MVV-LVA: Most Valuable Victim - Least Valuable Attacker)
        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            if victim and attacker:
                score += PIECE_VALUES.get(victim.piece_type, 0) * 10 - PIECE_VALUES.get(attacker.piece_type, 0)
            else:
                score += 500
        # Prioritize promotions
        if move.promotion:
            score += 800
        # Prioritize checks
        board.push(move)
        if board.is_check():
            score += 300
        board.pop()
        return -score  # Negative for descending sort

    moves.sort(key=move_score)
    return moves


def minimax(board, depth, alpha, beta, maximizing):
    """Minimax algorithm with alpha-beta pruning."""
    if depth == 0 or board.is_game_over():
        return evaluate_board(board), None

    best_move = None

    if maximizing:  # White
        max_eval = float('-inf')
        for move in order_moves(board):
            board.push(move)
            eval_score, _ = minimax(board, depth - 1, alpha, beta, False)
            board.pop()
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:  # Black (AI)
        min_eval = float('inf')
        for move in order_moves(board):
            board.push(move)
            eval_score, _ = minimax(board, depth - 1, alpha, beta, True)
            board.pop()
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval, best_move


def get_ai_move(board):
    """Get the best move for the AI (Black) using minimax."""
    _, best_move = minimax(board, AI_DEPTH, float('-inf'), float('inf'), False)
    if best_move is None:
        # Fallback to random legal move
        legal_moves = list(board.legal_moves)
        if legal_moves:
            best_move = random.choice(legal_moves)
    return best_move


# ============================================================
# GAME STATE MANAGEMENT
# ============================================================

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return new_state()


def new_state():
    return {
        "fen": chess.STARTING_FEN,
        "moves": [],
        "move_count": 0,
        "players": {},
        "game_over": False,
        "result": None,
        "ai_enabled": True
    }


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


# ============================================================
# SVG & README GENERATION
# ============================================================

def generate_board_svg(board, last_move=None):
    kwargs = {
        "size": 420,
        "coordinates": True,
        "colors": {
            "square light": "#F0D9B5",
            "square dark": "#B58863",
            "square light lastmove": "#CDD16A",
            "square dark lastmove": "#AAA23A",
        },
    }
    if last_move:
        kwargs["lastmove"] = last_move
    if board.is_check():
        kwargs["check"] = board.king(board.turn)

    svg = chess.svg.board(board, **kwargs)
    os.makedirs(os.path.dirname(BOARD_SVG), exist_ok=True)
    with open(BOARD_SVG, 'w') as f:
        f.write(svg)


def make_move_link(uci, from_sq, to_sq, piece_name):
    title = urllib.parse.quote(f"chess|move|{uci}")
    body = urllib.parse.quote(
        f"I'm playing **{piece_name}** from `{from_sq}` → `{to_sq}`\n\n"
        f"*The AI will respond automatically!* 🤖♟️"
    )
    return f"[`{to_sq}`](https://github.com/{REPO}/issues/new?title={title}&body={body})"


def generate_moves_markdown(board):
    if board.is_game_over():
        return ""

    # Only show White's moves (human plays White)
    if board.turn != chess.WHITE:
        return ""

    moves_by_piece = {}
    for move in board.legal_moves:
        piece = board.piece_at(move.from_square)
        pt = piece.piece_type
        if pt not in moves_by_piece:
            moves_by_piece[pt] = {}
        from_sq = chess.square_name(move.from_square)
        if from_sq not in moves_by_piece[pt]:
            moves_by_piece[pt][from_sq] = []
        moves_by_piece[pt][from_sq].append(move)

    lines = []
    lines.append("> ⬜ **Your turn (White)** — Click any move, the AI will respond! 🤖\n")
    lines.append("<details open><summary>🎯 Available Moves</summary>\n")

    piece_order = [chess.KING, chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN]

    for pt in piece_order:
        if pt not in moves_by_piece:
            continue

        symbol = PIECE_SYMBOLS[pt]
        name = PIECE_NAMES[pt]
        lines.append(f"**{symbol} {name}**\n")
        lines.append("| From | Available Moves |")
        lines.append("|:----:|:----------------|")

        for from_sq in sorted(moves_by_piece[pt].keys()):
            sq_moves = moves_by_piece[pt][from_sq]
            move_links = []
            for move in sorted(sq_moves, key=lambda m: chess.square_name(m.to_square)):
                to_sq = chess.square_name(move.to_square)
                uci = move.uci()
                link = make_move_link(uci, from_sq, to_sq, name)
                move_links.append(link)
            lines.append(f"| **{from_sq}** | {' '.join(move_links)} |")

        lines.append("")

    lines.append("</details>\n")
    return "\n".join(lines)


def generate_game_status(board, state):
    move_count = len(state.get("moves", []))
    total_players = len(state.get("players", {}))

    if board.is_game_over():
        if board.is_checkmate():
            winner = "Black (🤖 AI)" if board.turn == chess.WHITE else "White (You!)"
            return f"🏆 **Checkmate! {winner} wins!** ({move_count} moves, {total_players} players)"
        elif board.is_stalemate():
            return f"🤝 **Stalemate — Draw!** ({move_count} moves)"
        elif board.is_insufficient_material():
            return f"🤝 **Draw — Insufficient material!** ({move_count} moves)"
        else:
            return f"🤝 **Draw!** ({move_count} moves)"

    status = f"⬜ You (White) vs 🤖 AI (Black) · Move **#{move_count + 1}**"
    if total_players > 0:
        status += f" · 👥 {total_players} players so far"
    if board.is_check():
        status += " · ⚠️ **CHECK!**"
    return status


def generate_move_history(state):
    moves = state.get("moves", [])
    if not moves:
        return ""

    recent = moves[-10:]
    start_idx = len(moves) - len(recent)

    pairs = []
    for i in range(0, len(recent), 2):
        num = (start_idx + i) // 2 + 1
        white_move = recent[i]
        if i + 1 < len(recent):
            black_move = recent[i + 1]
            pairs.append(f"{num}. `{white_move}` `{black_move}`🤖")
        else:
            pairs.append(f"{num}. `{white_move}`")

    return "📜 **Recent:** " + " ".join(pairs)


def update_readme(board, state):
    status = generate_game_status(board, state)
    moves_md = generate_moves_markdown(board)
    history = generate_move_history(state)

    new_title = urllib.parse.quote("chess|new")
    new_body = urllib.parse.quote("Start a fresh chess game vs AI!\n\n*Processed automatically.* ♟️")
    new_game_link = f"[🔄 New Game](https://github.com/{REPO}/issues/new?title={new_title}&body={new_body})"

    chess_md = f"""{status}

<div align="center">
  <img src="chess/board.svg" alt="♟️ Community Chess" width="420" />
</div>

{history}

{moves_md}

{new_game_link}"""

    with open(README_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    if START_MARKER in content and END_MARKER in content:
        before = content.split(START_MARKER)[0]
        after = content.split(END_MARKER)[1]
        content = f"{before}{START_MARKER}\n{chess_md}\n{END_MARKER}{after}"

    with open(README_FILE, 'w', encoding='utf-8') as f:
        f.write(content)


# ============================================================
# MOVE HANDLERS
# ============================================================

def handle_move(uci_str, player=None):
    """Process a human move (White) and then make AI move (Black)."""
    state = load_state()
    board = chess.Board(state["fen"])

    if board.is_game_over():
        return False, "Game is already over! Click 'New Game' to start fresh."

    if board.turn != chess.WHITE:
        return False, "❌ It's the AI's turn — this shouldn't happen!"

    try:
        move = chess.Move.from_uci(uci_str)
        if move not in board.legal_moves:
            return False, f"❌ Illegal move: `{uci_str}`"

        # --- HUMAN MOVE (WHITE) ---
        piece = board.piece_at(move.from_square)
        piece_name = PIECE_NAMES.get(piece.piece_type, "Piece")
        from_sq = chess.square_name(move.from_square)
        to_sq = chess.square_name(move.to_square)

        board.push(move)
        state["fen"] = board.fen()
        state["moves"].append(uci_str)
        if player:
            state["players"][player] = state["players"].get(player, 0) + 1

        result_msg = f"⬜ **You** moved **{piece_name}** `{from_sq}` → `{to_sq}`"

        if board.is_check():
            result_msg += " — ⚠️ Check!"
        if board.is_checkmate():
            result_msg += "\n\n🏆 **Checkmate! You win!** 🎉"

        # --- AI MOVE (BLACK) ---
        ai_msg = ""
        last_move = move

        if not board.is_game_over() and board.turn == chess.BLACK:
            ai_move = get_ai_move(board)
            if ai_move:
                ai_piece = board.piece_at(ai_move.from_square)
                ai_piece_name = PIECE_NAMES.get(ai_piece.piece_type, "Piece")
                ai_from = chess.square_name(ai_move.from_square)
                ai_to = chess.square_name(ai_move.to_square)

                board.push(ai_move)
                state["fen"] = board.fen()
                state["moves"].append(ai_move.uci())
                last_move = ai_move

                ai_msg = f"\n🤖 **AI** responded **{ai_piece_name}** `{ai_from}` → `{ai_to}`"

                if board.is_check():
                    ai_msg += " — ⚠️ Check!"
                if board.is_checkmate():
                    ai_msg += "\n\n🏆 **Checkmate! AI wins!** 🤖"

        # --- UPDATE STATE ---
        state["move_count"] = len(state["moves"])
        state["game_over"] = board.is_game_over()
        if board.is_game_over():
            state["result"] = board.result()

        save_state(state)
        generate_board_svg(board, last_move)
        update_readme(board, state)

        return True, result_msg + ai_msg

    except ValueError as e:
        return False, f"❌ Invalid move format: `{e}`"


def handle_new_game():
    """Start a new game."""
    state = new_state()
    board = chess.Board()
    save_state(state)
    generate_board_svg(board)
    update_readme(board, state)
    return True, "🆕 New game started! **You play White** vs 🤖 **AI (Black)**.\n\nMake your first move on my [profile](https://github.com/Tahmid1999)!"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: chess_game.py <command> [args]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "move" and len(sys.argv) >= 3:
        uci = sys.argv[2]
        player = sys.argv[3] if len(sys.argv) > 3 else None
        success, msg = handle_move(uci, player)
        print(msg)
        sys.exit(0 if success else 1)

    elif command in ("new", "init"):
        success, msg = handle_new_game()
        print(msg)
        sys.exit(0)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
