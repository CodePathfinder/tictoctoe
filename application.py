from flask import Flask, render_template, session, redirect, url_for
from flask_session import Session
from tempfile import mkdtemp
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
def minimax(game, turn, arr):
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

    # minimax algorithm for "X" player
    if turn == "X":
        value = -1000
        for move in available_moves:
            # update map with each available move
            print(f"X-move: {move}]")
            # update game with the currect move
            game[move[0]][move[1]] = "X"
            value = max(value, minimax(game, "O", arr))
            # recover game grid after analysis of the move
            game[move[0]][move[1]] = None
            # update map when value is compared with minimax result
        print()

    # minimax algorithm for "O" player
    else:
        value = 1000
        for move in available_moves:
            print(f"O-move: {move}]")
            # update game with the currect move
            game[move[0]][move[1]] = "O"
            value = min(value, minimax(game, "X", arr))
            # recover game grid after analysis of the move
            game[move[0]][move[1]] = None
            # update map when value is compared with minimax result
        print()

    if (8 - len(session["moves"])) == len(available_moves):
        print("APPENDED VALUE: ", value)
        arr.append(value)

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
    if score == 1:
        result = "Winner is X!"
    elif score == -1:
        result = "Winner is O!"
    elif score == 0:  
        result = "Tie game..."
    return render_template("game.html", game=session["board"], turn=session["turn"], result=result, gameover=session["gameover"])


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
    # available next moves - list of all moves available for the moving player
    available_next_moves = []
    for i in range(3):
        for j in range(3):
            if game[i][j] == None:
                available_next_moves.append((i ,j))
    
    # minimax shall not be called if only one move left on the board
    if len(available_next_moves) == 1:
        computer_move = available_next_moves[0]
    else:
        # create array of scores for available next moves to be filled in by minimax
        values_arr = []

        # board_value: current game/board "best scenario score" (-1, 0, or 1) for the moving player (return of minimax()) 
        board_value = minimax(game, session["turn"], values_arr)
        
        # results of minimax function
        print(f"GAME/BOARD STATUS = {board_value} for {session['turn']} player")
        print("list of game/board scores avaliable for next moves", values_arr)
        print(f"List of moves available for {session['turn']} player: {available_next_moves}")

        # select move(s) based on "best scenario score" and correspondance of indexes in arr and available moves lists
        selected_moves = []
        for i in range(len(values_arr)):
            if values_arr[i] == board_value:
                selected_moves.append(available_next_moves[i])
        print("SELECTED MOVES LIST: ", selected_moves)

        # if more than one elements in selected moves list, the first element is selected
        try:
            computer_move = selected_moves[0]
        except IndexError:
            print("Sorry, no selected moves in the list")

    # update the board with computer selected move
    session["board"][computer_move[0]][computer_move[1]] = session["turn"]
    session["moves"].append(computer_move)
    return redirect(url_for("index"))
