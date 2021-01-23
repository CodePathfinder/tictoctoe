from flask import Flask, render_template, session, redirect, url_for
from flask_session import Session
from tempfile import mkdtemp
import math
import copy

app = Flask(__name__)

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# this function checks and returns result of the game 
def check_result(board):
    players = ["X", "O"]
    winner = ""
    score = None
    for player in players:
        if board[0][0] == player and board[0][1] == player and board[0][2] == player or \
            board[1][0] == player and board[1][1] == player and board[1][2] == player or \
            board[2][0] == player and board[2][1] == player and board[2][2] == player or \
            board[0][0] == player and board[1][0] == player and board[2][0] == player or \
            board[0][1] == player and board[1][1] == player and board[2][1] == player or \
            board[0][2] == player and board[1][2] == player and board[2][2] == player or \
            board[0][0] == player and board[1][1] == player and board[2][2] == player or \
            board[2][0] == player and board[1][1] == player and board[0][2] == player:
            
            winner = player
   
    if winner == "X":
        score = 1
    elif winner == "O":
        score = -1
    elif None not in board[0] and None not in board[1] and None not in board[2] and not winner:
        score = 0
    return score


# this function helps the computer determin the best move (brute force algorthm)
def minimax(game, turn):
    score = check_result(game)
    if score in [-1, 0, 1]:
        print("THIS IS A BASE CASE! SCORE = ", score)
        return score

    available_moves = []
    for i in range(3):
        for j in range(3):
            if game[i][j] == None:
                available_moves.append((i ,j))

    print("Available_moves: ", available_moves)

    if turn == "X":
        value = -1000
        for move in available_moves:
            # update game with the next move
            game[move[0]][move[1]] = "X"
            value = max(value, minimax(game, "O"))
            # restore game after analysis of the next move
            game[move[0]][move[1]] = None

    else:
        value = 1000
        for move in available_moves:
            # update game with the next move
            game[move[0]][move[1]] = "O"
            value = min(value, minimax(game, "X"))
            # restore game after analysis of the next move
            game[move[0]][move[1]] = None

    return value


@app.route("/")
def index():
    if "board" not in session:
        session["board"] = [[None, None, None], [None, None, None], [None, None, None]]
        session["turn"] = "X"
        session["moves"] = []
        session["gameover"] = False
    # update the player's turn
    elif  session["turn"] == "X":
        session["turn"] = "O"
    else:
        session["turn"] = "X"
    # check of the score for show result
    score = check_result(session["board"])
    if score != None:
        session["gameover"] = True
    result = ""
    if session["moves"] == []:
        start = True
    else:
        start = False
    if score == 1:
        result = "Winner is X!"
    elif score == -1:
        result = "Winner is O!"
    elif score == 0:  
        result = "Tie game..."
    return render_template("game.html", game=session["board"], turn=session["turn"], result=result, gameover=session["gameover"], start=start)


@app.route("/play/<int:row>/<int:col>")
def play(row, col):
    # update the board grid
    session["board"][row][col] = session["turn"]
    session["moves"].append((row, col))
    return redirect(url_for("index"))


@app.route("/restart")
def restart():
    session["board"] = [[None, None, None], [None, None, None], [None, None, None]]
    session["turn"] = "O"
    session["moves"].clear()
    session["gameover"] = False
    return redirect(url_for("index"))


@app.route("/undo")
def undo():
    if len(session["moves"]) > 0:
        move = session["moves"].pop()
        session["board"][move[0]][move[1]] = None
        session["gameover"] = False
    return redirect(url_for("index"))


@app.route("/computermove")
def computermove():
    # create game matrix (argument in MINIMAX) as deep copy of session["board"]  
    game = copy.deepcopy(session["board"])
    if session["turn"] == "X":
        next_turn = "O"
    else:
        next_turn = "X"
    available_next_moves = []
    for i in range(3):
        for j in range(3):
            if game[i][j] == None:
                available_next_moves.append((i ,j))
    
    print(f"List of moves available for {session['turn']} player: {available_next_moves}")

    if len(available_next_moves) == 1:
        computer_move = available_next_moves[0]
    else:    
        values = []
        value_move_map = []
        for move in available_next_moves:
            # imitation of the test move
            game[move[0]][move[1]] = session["turn"]
            # value: score for the game presuming the test move is made 
            value = minimax(game, next_turn)
            # list of scores for the games for each of available moves
            values.append(value)
            # score - move mapping list
            value_move_map.append((value, move))
            # cancelation of the test move
            game[move[0]][move[1]] = None
        print("Values List:", values) 
        print("Value_Move_Map:", value_move_map) 

        selected_moves = []
        if session["turn"] == "X":
            best_value = max(values)
        else:
            best_value = min(values)
        print("Best Value:", best_value) 
        for item in value_move_map:
            if item[0] == best_value:
                selected_moves.append(item[1])
        print("SELECTED MOVES LIST: ", selected_moves)
        
        # if one or more elements in selected moves list, the first element is selected
        computer_move = selected_moves[0]

    session["board"][computer_move[0]][computer_move[1]] = session["turn"]
    session["moves"].append(computer_move)
    return redirect(url_for("index"))
