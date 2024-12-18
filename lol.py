from stockfish import Stockfish
import sys
import chess.pgn
import io
from pynput import keyboard
from pynput.keyboard import Key
import threading

move = -1
moves = 0
board = None
game = None
ss = None
fen = None
evaluations_cache = {}
best_moves_cache = {}

def prLightGray(skk): 
    print("\033[97m {}\033[00m" .format(skk))

def display_evaluation(eval):
    eval_type = eval["type"]
    value = int(eval["value"])
    if eval_type == "cp":
        print("Evaluation: ", value / 100)
    else:
        print("Evaluation: Mate in", value)

def display_best_moves(best_moves):
    print("Best Moves:")
    for top_move in best_moves:
        if top_move["Mate"] is None:
            print("Move: ", top_move["Move"], "Evaluation: ", int(top_move['Centipawn']) / 100)
        else:
            mate = int(top_move["Mate"])
            color = "white" if mate > 0 else "black"
            print("Move: ", top_move["Move"], "Mate in", abs(mate), "for", color)

def oldReadFunction():
    global ss,board,fen
    ss.set_fen_position(fen)
    print()
    print(board)
    print()
    eval = ss.get_evaluation()
    type = eval["type"]
    value = int(eval["value"])
    if(type == "cp"):
        print("Evaluation: ",value/100)
    else:
        print("Evaluation: ",end = '')
        if(value < 0):
            prLightGray(value)
        else:
            print(value)
    print("Best Moves:")
    best_moves = ss.get_top_moves(3)
    for top_move in best_moves:
        if(top_move["Mate"] == None):
            print("Move : ",top_move["Move"], "Evaluation: ",int(top_move['Centipawn'])/100)
        else:
            mate = int(top_move["Mate"])
            color = "white"
            if(mate < 0):
                color = "black"
            print("Move : ",top_move["Move"], "Mate in ",abs(mate)," for ",color)

def EngineRead():
    global ss, board, fen, evaluations_cache, best_moves_cache
    if fen in evaluations_cache:
        eval = evaluations_cache[fen]
        best_moves = best_moves_cache[fen]
        print()
        print(board)
        print()
        display_evaluation(eval)
        display_best_moves(best_moves)
    else:
        oldReadFunction()

def on_key_release(key):
    global move,moves,board,game,fen,ss
    if key == Key.right:
        if(move < moves-1):
            move += 1
            game = game.variations[0]
            curr = game.move
            color = "Black"
            if(move % 2 == 0):
                color = "White"
            print("\n",color, " has made the move: ",curr)
            board.push(curr)
            fen=board.fen()
            EngineRead()
        else:
            print("\n")

    elif key == Key.left:
        if(move > 0):
            move -= 1
            game = game.parent
            board.pop()
            fen = board.fen()
            EngineRead()
        else:
            print("\n")

def precompute_evaluations():
    global ss, game, evaluations_cache, best_moves_cache
    board_copy = game.board()
    for move in game.mainline_moves():
        board_copy.push(move)
        fen = board_copy.fen()
        if fen not in evaluations_cache:
            ss.set_fen_position(fen)
            eval = ss.get_evaluation()
            best_moves = ss.get_top_moves(3)
            evaluations_cache[fen] = eval
            best_moves_cache[fen] = best_moves

def main():
    global moves, board, game, ss, fen, evaluations_cache, best_moves_cache
    depth = int(input("Enter the depth of the engine: "))
    print("Enter the copied pgn:")
    str = sys.stdin.read()
    pgn = io.StringIO(str)
    game = chess.pgn.read_game(pgn)
    board = game.board()

    ss = Stockfish(path="./stockfish", depth=24, parameters={"Threads": 4, "Ponder": False, "Hash": 256})
    fen = board.fen()

    # Initialize caches
    evaluations_cache = {}
    best_moves_cache = {}

    # Start precomputing evaluations in a background thread
    precompute_thread = threading.Thread(target=precompute_evaluations)
    precompute_thread.daemon = True
    precompute_thread.start()

    print(board)
    print("Use arrow keys to navigate through the game")
    for _ in game.mainline_moves():
        moves += 1
    with keyboard.Listener(on_press=on_key_release) as listener:
        listener.join()

if __name__ == "__main__":
    main()
