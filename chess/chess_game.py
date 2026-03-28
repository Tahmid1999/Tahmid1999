#!/usr/bin/env python3
"""
Community Chess Game for GitHub Profile README.
Anyone can play by clicking move links that create GitHub Issues.
A GitHub Action processes the move and updates the board.
"""

import chess
import chess.svg
import json
import os
import sys
import urllib.parse

# Configuration
REPO = "Tahmid1999/Tahmid1999"
STATE_FILE = "chess/game_state.json"
BOARD_SVG = "chess/board.svg"
README_FILE = "README.md"
START_MARKER = "<!-- CHESS:START -->"
END_MARKER = "<!-- CHESS:END -->"

PIECE_SYMBOLS = {
    chess.PAWN: "♟",
    chess.KNIGHT: "♞",
    chess.BISHOP: "♝",
    chess.ROOK: "♜",
    chess.QUEEN: "♛",
    chess.KING: "♚",
}

PIECE_NAMES = {
    chess.PAWN: "Pawn",
    chess.KNIGHT: "Knight",
    chess.BISHOP: "Bishop",
    chess.ROOK: "Rook",
    chess.QUEEN: "Queen",
    chess.KING: "King",
}


def load_state():
    """Load game state from JSON file."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return new_state()


def new_state():
    """Create a fresh game state."""
    return {
        "fen": chess.STARTING_FEN,
        "moves": [],
        "move_count": 0,
        "players": {},
        "game_over": False,
        "result": None
    }


def save_state(state):
    """Save game state to JSON file."""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def generate_board_svg(board, last_move=None):
    """Generate a beautiful SVG chess board."""
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
    """Create a clickable GitHub Issue link for a chess move."""
    title = urllib.parse.quote(f"chess|move|{uci}")
    body = urllib.parse.quote(
        f"I'm making a move: **{piece_name}** from `{from_sq}` to `{to_sq}`\n\n"
        f"*This issue will be automatically processed and closed by the Chess Bot.* ♟️"
    )
    return f"[`{to_sq}`](https://github.com/{REPO}/issues/new?title={title}&body={body})"


def generate_moves_markdown(board):
    """Generate organized, clickable move links."""
    if board.is_game_over():
        return ""

    # Group moves by piece type and from-square
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

    turn = "White" if board.turn == chess.WHITE else "Black"
    turn_icon = "⬜" if board.turn == chess.WHITE else "⬛"

    lines = []
    lines.append(f"> {turn_icon} **{turn}'s turn** — Click any move below to play!\n")
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
    """Generate status line for the game."""
    move_count = len(state.get("moves", []))
    total_players = len(state.get("players", {}))

    if board.is_game_over():
        if board.is_checkmate():
            winner = "Black" if board.turn == chess.WHITE else "White"
            return f"🏆 **Checkmate! {winner} wins!** ({move_count} moves, {total_players} players)"
        elif board.is_stalemate():
            return f"🤝 **Stalemate — Draw!** ({move_count} moves)"
        elif board.is_insufficient_material():
            return f"🤝 **Draw — Insufficient material!** ({move_count} moves)"
        else:
            return f"🤝 **Draw!** ({move_count} moves)"

    status_parts = [f"Move **#{move_count + 1}**"]
    if total_players > 0:
        status_parts.append(f"👥 {total_players} players")
    if board.is_check():
        status_parts.append("⚠️ **CHECK!**")

    return " · ".join(status_parts)


def generate_move_history(state):
    """Generate a compact move history."""
    moves = state.get("moves", [])
    if not moves:
        return ""

    # Show last 10 moves in algebraic-ish notation
    recent = moves[-10:]
    start_idx = len(moves) - len(recent)

    pairs = []
    for i in range(0, len(recent), 2):
        num = (start_idx + i) // 2 + 1
        if i + 1 < len(recent):
            pairs.append(f"{num}. `{recent[i]}` `{recent[i+1]}`")
        else:
            pairs.append(f"{num}. `{recent[i]}`")

    return "📜 **Recent:** " + " ".join(pairs)


def update_readme(board, state):
    """Update the chess section in README.md between markers."""
    status = generate_game_status(board, state)
    moves_md = generate_moves_markdown(board)
    history = generate_move_history(state)

    # New game link
    new_title = urllib.parse.quote("chess|new")
    new_body = urllib.parse.quote("Start a fresh chess game!\n\n*Processed automatically by Chess Bot.* ♟️")
    new_game_link = f"[🔄 New Game](https://github.com/{REPO}/issues/new?title={new_title}&body={new_body})"

    chess_md = f"""{status}

<div align="center">
  <img src="chess/board.svg" alt="♟️ Community Chess" width="420" />
</div>

{history}

{moves_md}

{new_game_link}"""

    # Read current README
    with open(README_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace between markers
    if START_MARKER in content and END_MARKER in content:
        before = content.split(START_MARKER)[0]
        after = content.split(END_MARKER)[1]
        content = f"{before}{START_MARKER}\n{chess_md}\n{END_MARKER}{after}"
    else:
        print("WARNING: Chess markers not found in README!")

    with open(README_FILE, 'w', encoding='utf-8') as f:
        f.write(content)


def handle_move(uci_str, player=None):
    """Process a chess move."""
    state = load_state()
    board = chess.Board(state["fen"])

    if board.is_game_over():
        return False, "Game is already over! Click 'New Game' to start fresh."

    try:
        move = chess.Move.from_uci(uci_str)
        if move not in board.legal_moves:
            return False, f"❌ Illegal move: `{uci_str}`"

        # Get piece info before pushing
        piece = board.piece_at(move.from_square)
        piece_name = PIECE_NAMES.get(piece.piece_type, "Piece")
        from_sq = chess.square_name(move.from_square)
        to_sq = chess.square_name(move.to_square)

        board.push(move)

        # Update state
        state["fen"] = board.fen()
        state["moves"].append(uci_str)
        state["move_count"] = len(state["moves"])
        if player:
            state["players"][player] = state["players"].get(player, 0) + 1
        state["game_over"] = board.is_game_over()
        if board.is_game_over():
            state["result"] = board.result()

        save_state(state)
        generate_board_svg(board, move)
        update_readme(board, state)

        result_msg = f"✅ **{piece_name}** moved from `{from_sq}` to `{to_sq}`"
        if player:
            result_msg += f" by @{player}"
        if board.is_check():
            result_msg += " — ⚠️ **Check!**"
        if board.is_checkmate():
            winner = "Black" if board.turn == chess.WHITE else "White"
            result_msg += f"\n\n🏆 **Checkmate! {winner} wins!**"

        return True, result_msg

    except ValueError as e:
        return False, f"❌ Invalid move format: `{e}`"


def handle_new_game():
    """Start a brand new game."""
    state = new_state()
    board = chess.Board()
    save_state(state)
    generate_board_svg(board)
    update_readme(board, state)
    return True, "🆕 New chess game started! Make your first move on my [profile](https://github.com/Tahmid1999)."


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: chess_game.py <command> [args]")
        print("  move <uci> [player]  - Make a move")
        print("  new                  - Start new game")
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
