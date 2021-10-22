from flask import Flask, render_template, session, redirect, url_for
from flask_session import Session
from tempfile import mkdtemp
import copy

app = Flask(__name__)

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


def check_result(board):
    """ check and return result of the game """

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
            break
    if winner == "X":
        score = 1
    elif winner == "O":
        score = -1
    elif None not in board[0] and None not in board[1] and None not in board[2]:
        score = 0
    return score


def minimax(game, turn):
    """ help computer determine the best move """

    available_moves = []
    for i in range(3):
        for j in range(3):
            if game[i][j] == None:
                available_moves.append((i, j))

    max_hops = session['counter']

    score = check_result(game)
    if score in [-1, 0, 1]:
        # determine depth of recursion
        recursion_depth = max_hops - len(available_moves)
        return (score, recursion_depth)

    if turn == "X":
        value = -1000
        for move in available_moves:
            # update game with the next move
            game[move[0]][move[1]] = "X"
            score_depth = minimax(game, "O")
            # keep track of recursion depths for the corresponding scores (format: list of tuples)
            session["score_depth_track"].append(score_depth)
            value = max(value, score_depth[0])
            # determine the min recursion depth (hops) for the corresponding value
            # TODO original (3 lines below)
            # for score, depth in session["score_depth_track"]:
            #     if score == value:
            #         hops = depth if depth < max_hops else max_hops
            # TODO start test
            if value == -1:
                # determine longest way for loose
                hops = max(
                    depth for score, depth in session["score_depth_track"] if score == value)
            else:
                # determine shortest way for win
                hops = min(
                    depth for score, depth in session["score_depth_track"] if score == value)
            # TODO end test
            # restore game after analysis of the move
            game[move[0]][move[1]] = None

    else:
        value = 1000
        for move in available_moves:
            # update game with the next move
            game[move[0]][move[1]] = "O"
            score_depth = minimax(game, "X")
            # keep track of recursion depths for the corresponding scores (format: list of tuples)
            session["score_depth_track"].append(score_depth)
            value = min(value, score_depth[0])
            # determine the min recursion depth (hops) for the corresponding value
            # TODO original (3 lines below)
            # for score, depth in session["score_depth_track"]:
            #     if score == value:
            #         hops = depth if depth < max_hops else max_hops
            # TODO start test
            if value == 1:
                # determine longest way for loose
                hops = max(
                    depth for score, depth in session["score_depth_track"] if score == value)
            else:
                # determine shortest way for win
                hops = min(
                    depth for score, depth in session["score_depth_track"] if score == value)
            # TODO end test
            # restore game after analysis of the move
            game[move[0]][move[1]] = None

    return (value, hops)


@app.route("/")
def index():
    if "board" not in session:
        session["board"] = [[None, None, None], [
            None, None, None], [None, None, None]]
        session["turn"] = "X"
        session["moves"] = []
        session["gameover"] = False
        session["score_depth_track"] = []
    # update the player's turn
    elif session["turn"] == "X":
        session["turn"] = "O"
    else:
        session["turn"] = "X"
    # check the score to show result
    score = check_result(session["board"])
    result = ""
    if score != None:
        session["gameover"] = True
        if score == 1:
            result = "Winner is X!"
        elif score == -1:
            result = "Winner is O!"
        elif score == 0:
            result = "Tie game..."
    if session["moves"] == []:
        start = True
    else:
        start = False

    return render_template("game.html",
                           game=session["board"],
                           turn=session["turn"],
                           result=result,
                           gameover=session["gameover"],
                           start=start,
                           cthelp=len(session["moves"])
                           )


@app.route("/play/<int:row>/<int:col>")
def play(row, col):
    # update the board grid
    session["board"][row][col] = session["turn"]
    session["moves"].append((row, col))
    return redirect(url_for("index"))


@app.route("/restart")
def restart():
    if "board" in session:
        session["board"] = [[None, None, None], [
            None, None, None], [None, None, None]]
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
                available_next_moves.append((i, j))
    # set number of the moves left left to fill in the game board (used in minimax function to calculate depth of recurtion for each basecase)
    session['counter'] = len(available_next_moves)

    if len(available_next_moves) == 1:
        computer_move = available_next_moves[0]
    else:
        value_move_map = []
        value_hops = []
        for move in available_next_moves:
            # imitation of the test move
            game[move[0]][move[1]] = session["turn"]
            # value_hops tulpe: SCORE for the game presuming the test move is made and correspoding NUMBER OF HOPS(moves) to get ths score
            value_hop = minimax(game, next_turn)
            # compelete list of value_hops tuples for all available moves
            value_hops.append(value_hop)
            # compelete value_hops and move mapping list in format [((score, hops),(move tuple)), ] for all available moves
            value_move_map.append((value_hop, move))
            # cancelation of the test move
            game[move[0]][move[1]] = None

        # determine best move(s) by (1) best_value and (2) best_hops crireria
        if session["turn"] == "X":
            best_value, _ = max(value_hops, key=lambda item: item[0])
            if best_value == -1:
                # determine longest way for loose
                best_hops = max(
                    hops for value, hops in value_hops if value == best_value)
            else:
                # determine shortest way for win
                best_hops = min(
                    hops for value, hops in value_hops if value == best_value)
        else:
            best_value, _ = min(value_hops, key=lambda item: item[0])
            if best_value == 1:
                # determine longest way for loose
                best_hops = max(
                    hops for value, hops in value_hops if value == best_value)
            else:
                # determine shortest way for win
                best_hops = min(
                    hops for value, hops in value_hops if value == best_value)
        # compile and fill in "selected_moves" shortlist based on best_value/best_hops crireria
        selected_moves = []
        for item, move in value_move_map:
            if item[0] == best_value and item[1] == best_hops:
                selected_moves.append(move)

        # take the first element (presumably, "the best move") of the selected moves list
        computer_move = selected_moves[0]

    # do the computer_move on the original board
    session["board"][computer_move[0]][computer_move[1]] = session["turn"]
    # add the computer_move to history of moves
    session["moves"].append(computer_move)
    return redirect(url_for("index"))
