from flask import Flask, render_template, redirect, url_for, request, make_response, jsonify
import records

def can_move(board, color, moves = [3, 4, 5, 7, 9]):
    for i in range(32):
        if board[i] is not None and board[i].split(' ')[0] == color:
            if board[i].split(' ')[1] == 'king':
                possible_moves = moves + [-move for move in moves]
            elif color == 'black':
                possible_moves = [-move for move in moves]
            elif color == 'white':
                possible_moves = moves
            for move in possible_moves:
                if _valid_move(i, i+move, board, color):
                    return True
    return False

def can_jump(board, color):
    return can_move(board, color, moves=[7, 9])

def valid_backward_move(current, new, board, color):
    if current // 4 % 2 == 0:
        if new - current in (3, 4):
            if current % 8 == 0 and new - current == 3:
                return False
            else:
                return True
        elif new - current == 9 and board[current+4] is not None and board[current+4].split(' ')[0] != color:
            if current % 8 == 6:
                return False
            else:
                return True
        elif new - current == 7 and board[current+3] is not None and board[current+3].split(' ')[0] != color:
            if current % 8 == 0:
                return False
            else:
                return True

        else:
            return False
    else:
        if new - current in (4, 5):
            if current % 8 == 7 and new - current == 5:
                return False
            else:
                return True
        elif new - current == 9 and board[current+5] is not None and board[current+5].split(' ')[0] != color:
            if current % 8 == 7:
                return False
            else:
                return True
        elif new - current == 7 and board[current+4] is not None and board[current+4].split(' ')[0] != color:
            if current % 8 == 1:
                return False

            else:
                return True


def valid_forward_move(current, new, board, color):
    # If the piece is moving from a row that starts with a black square
    if current // 4 % 2 == 0:
        if current - new in (4, 5):
            if current % 8 == 0 and current - new == 5:
                return False
            else:
                return True

        # Check if the move is a valid jump move
        elif current - new == 9 and board[current-5] is not None and board[current-5].split(' ')[0] != color:
            if current % 8 == 0:
                return False
            else:
                return True
        elif current - new == 7 and board[current-4] is not None and board[current-4].split(' ')[0] != color:
            if current % 8 == 6:
                return False
            else:
                return True

        else:
            return False

    else:
        if current - new in (3, 4):
            if current % 8 == 7 and current - new == 3:
                return False

            else:
                return True

        elif current - new == 9 and board[current-4] is not None and board[current-4].split(' ')[0] != color:
            if current % 8 == 1:
                return False
            else:
                return True

        elif current - new == 7 and board[current-3] is not None and board[current-3].split(' ')[0] != color:
            if current % 8 == 7:
                return False
            else:
                return True
        else:
            return False

def valid_move(current, new, board, color):
    if can_jump(board, color) and not abs(current - new) in (9, 7):
        return False
    else:
        return _valid_move(current, new, board, color)

def _valid_move(current, new, board, color):
    if 0 <= new < 32 and board[new] is None:
        color, _type = board[current].split(' ')
        if color == 'black':
            result = valid_forward_move(current, new, board, color)
            if result:
                return True
            else:
                if _type == 'king':
                    if valid_backward_move(current, new, board, color):
                        return True
                    else:
                        return False
                else:
                    return False
        elif color == 'white':
            if valid_backward_move(current, new, board, color):
                return True
            else:
                if _type == 'king':
                    if valid_forward_move(current, new, board, color):
                        return True
                    else:
                        return False
                else:
                    return False
        else:
            return False
    else:
        return False


app = Flask(__name__)


@app.route('/')
def index():
    # Render the start page
    return render_template('index.html')


@app.route('/make_move', methods=['POST'])
def make_move():
    current, new, board = int(request.form["current_pos"]), int(request.form["new_pos"]), request.form.getlist("board[]")
    board = [None if x == '' else x for x in board]
    color = board[current].split(' ')[0]
    if valid_move(current, new, board, color):
        board[new] = board[current]
        board[current] = None
        if abs(current - new) in (7, 9):
            # Remove piece jumped over

            # For jump moves starting on a even indexed rows
            if current // 4 % 2 == 0:
                if current - new == 9:
                    board[current-5] = None
                elif current - new == 7:
                    board[current-4] = None
                elif current - new == -9:
                    board[current+4] = None
                elif current - new == -7:
                    board[current+3] = None
                else:
                    return jsonify(result='Error')
            else:
                if current-new == 9:
                    board[current-4] = None
                elif current-new == 7:
                    board[current-3] = None
                elif current-new == -9:
                    board[current+5] = None
                elif current - new == -7:
                    board[current+4] = None
                else:
                    return jsonify(result='Error')
        return jsonify(result=True, board=board)

    else:
        return jsonify(result=False)


@app.route('/single_player')
def single_player_game():
    return render_template('single.html')


@app.route('/online')
def online_game():
    return render_template('online.html')


@app.route('/local')
def local_game():
    return render_template('local.html')


if __name__ == '__main__':
    app.run(debug=True)
