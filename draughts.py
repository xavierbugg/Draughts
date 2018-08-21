from flask import Flask, render_template, url_for, session
import records
from flask_socketio import SocketIO, emit

def has_ended(board):
    if not can_move(board, 'white'):
        return True
    else:
        return not can_move(board, 'black')

def is_double_jump(board, move_list, color):
    if len(move_list) and (color == 'black' and move_list[-1][-1] // 4 == 0 or color == 'white' and move_list[-1][-1] // 4 == 7):
        positions = [0]
        for move in move_list[::-1]:
            if move[-1] == positions[-1]:
                positions += move[:-1][::-1]
        if positions.count(0) == 1:
            return False
    return len(move_list) and not is_turn(color, move_list) and piece_can_jump(move_list[-1][-1], board, color) and abs(move_list[-1][0] - move_list[-1][1]) in (7, 9)
def is_turn(color, move_list):
    return color == 'black' and len(move_list)%2 == 0 or color == 'white' and len(move_list)%2 == 1

def piece_can_jump(piece, board, color):
    return piece_can_move(piece, board, color, moves = [7, 9])

def piece_can_move(piece, board, color, moves = [3, 4, 5, 7, 9]):
    if board[piece].split(' ')[1] == 'king':
        possible_moves = moves + [-move for move in moves]
    elif color == 'black':
        possible_moves = [-move for move in moves]
    elif color == 'white':
        possible_moves = moves
    for move in possible_moves:
        if _valid_move(piece, piece+move, board, color):
            return True
    return False

def can_move(board, color, moves = [3, 4, 5, 7, 9]):
    for i in range(32):
        if board[i] is not None and board[i].split(' ')[0] == color:
            if piece_can_move(i, board, color):
                return True
    return False

def can_jump(board, color):
    for i in range(32):
        if board[i] is not None and board[i].split(' ')[0] == color:
            if piece_can_jump(i, board, color):
                return True
    return False

def valid_backward_move(current, new, board, color):
    if current // 4 % 2 == 0:
        if new - current in (3, 4):
            if current % 8 == 0 and new - current == 3:
                return False
            else:
                return True
        elif new - current == 9 and board[current+4] is not None and board[current+4].split(' ')[0] != color:
            if current % 8 == 3:
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
            if current % 8 == 4:
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
            if current % 8 == 3:
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
            if current % 8 == 4:
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
    if is_double_jump(board, session['move_list'], color):
        if current != session['move_list'][-1][-1] or not move_is_jump(current, new):
            print('should be double jumping')
            return False
        else:
            # Skip other checks as this would not be considered as the players turn
            return _valid_move(current, new, board, color)
    if not is_turn(color, session['move_list']) or is_double_jump(board, session['move_list'], [x for x in ['black', 'white'] if x != color][0]):
        # Its not the players turn
        print('not players turn')
        return False
    elif can_jump(board, color) and not move_is_jump(current, new):
        print('must jump if can')
        return False
    else:
        return _valid_move(current, new, board, color)

def _valid_move(current, new, board, color):
    if 0 <= new < 32 and board[new] is None: # New position is clear and on the board
        color, _type = board[current].split(' ')
        if color == 'black':
            if valid_forward_move(current, new, board, color):
                return True
            else:
                if _type == 'king':
                    return valid_backward_move(current, new, board, color)
                else:
                    return False
        elif color == 'white':
            if valid_backward_move(current, new, board, color):
                return True
            else:
                if _type == 'king':
                    return valid_forward_move(current, new, board, color)
                else:
                    return False
        else:
            return False
    else:
        return False

def move_is_jump(current, new):
    return abs(current - new) in (7, 9)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'klekjkefnklsdjklafjiejjkldmkvmda'
socketio = SocketIO(app)


@app.route('/')
def index():
    # Render the start page
    return render_template('index.html')

@socketio.on('move request')
def make_move(data):
    print('request recieved')
    current, new, board = int(data["current_pos"]), int(data["new_pos"]), session['board']
    color = board[current].split(' ')[0]
    if valid_move(current, new, board, color):
        if is_double_jump(board, session['move_list'], color):
            session['move_list'][-1].append(new)
        else:
            session['move_list'].append([current, new])

        # Move piece to new position and king it if necessary
        if board[current].split(' ')[-1] == 'man' and (color == 'black' and new // 4 == 0 or color == 'white' and new // 4 == 7):
            print('kinged')
            board[new] = color + ' ' + 'king'
        else:
            board[new] = board[current]
        board[current] = None

        if move_is_jump(current, new): # Removes piece jumped over
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
                    emit('move response', {'result': 'Error'})
                    return
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
                    emit('move response', {'result': 'Error'})
                    return
        session['board'] = board
        print('response sent')
        emit('move response', {'result': True, 'board': board})
        if has_ended(board):
            if can_move(board, 'black'):
                emit('game end', {'result': 'black'})
            elif can_move(board, 'white'):
                emit('game end', {'result': 'white'})
            else:
                emit('game end', {'result': 'draw'})

    else:
        emit('move response', {'result': False})


@app.route('/single_player')
def single_player_game():
    return render_template('single.html')

@app.route('/online')
def online_game():
    return render_template('online.html')

@app.route('/local')
def local_game():
    session['move_list'] = []
    session['board'] = ['white man', 'white man', 'white man', 'white man', 'white man', 'white man', 'white man', 'white man', 'white man', 'white man', 'white man', 'white man', None, None, None, None, None, None,  None, None,'black man', 'black man', 'black man', 'black man', 'black man', 'black man', 'black man', 'black man', 'black man', 'black man', 'black man', 'black man']
    return render_template('local.html')


if __name__ == '__main__':
    socketio.run(app, port=5000, debug=True)
