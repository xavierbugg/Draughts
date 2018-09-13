import json
import random
import time

from flask import Flask, render_template, request, session, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room

BLACK, WHITE = 0, 1
BLACK_MAN, WHITE_MAN, BLACK_KING, WHITE_KING = range(4)
BASE_DEPTH = 3
BASE_MOVES, JUMP_MOVES = [3, 4, 5, 7, 9], [7, 9]
rooms = []
start_board = [WHITE_MAN if i < 12 else
                BLACK_MAN if i > 19 else None for i in range(32)]


class Room():
    def __init__(self, name, black_id, white_id, board, move_list):
        self.name = name
        self.black_id = black_id
        self.white_id = white_id
        self.board = board
        self.move_list = move_list

    def is_full(self):
        return bool(self.black_id and self.white_id)


def get_board(move_list):
    board = start_board[:]
    for move in move_list:
        for i in range(len(move)-1):
            board = simulate_move(move[i], move[i+1], board)
    return board


def game_has_ended(board):
    return not (can_move(board, WHITE) and can_move(board, BLACK))


def is_double_jump(board, move_list, color):
    if len(move_list) and (color == BLACK and move_list[-1][-1] // 4 == 0 or color == WHITE and move_list[-1][-1] // 4 == 7):
        positions = [0]
        for move in move_list[::-1]:
            if move[-1] == positions[-1]:
                positions += move[:-1][::-1]
        if positions.count(0) == 1:
            return False
    return len(move_list) and not is_turn(color, move_list) and piece_can_jump(move_list[-1][-1], board, color) and abs(move_list[-1][0] - move_list[-1][1]) in JUMP_MOVES


def is_turn(color, move_list):
    return color == len(move_list) % 2


def piece_can_move(piece, board, color, moves=BASE_MOVES):
    if board[piece]//2:
        possible_moves = moves + [-move for move in moves]
    elif color == BLACK:
        possible_moves = [-move for move in moves]
    elif color == WHITE:
        possible_moves = moves
    for move in possible_moves:
        if valid_basic_move(piece, piece+move, board, color):
            return True
    return False


def piece_can_jump(piece, board, color):
    return piece_can_move(piece, board, color, moves=JUMP_MOVES)


def get_piece_moves(board, move_list, piece, moves=[3, 4, 5, 7, 9]):
    new_positions = []
    color = board[piece] % 2
    if board[piece]//2:
        possible_moves = moves + [-move for move in moves]
    elif color == BLACK:
        possible_moves = [-move for move in moves]
    elif color == WHITE:
        possible_moves = moves
    for move in possible_moves:
        if valid_move(piece, piece+move, board, move_list, color):
            new_positions.append(piece+move)
    return new_positions


def get_possible_moves(board, move_list, color, moves=BASE_MOVES):
    possible_moves = []
    for i in range(32):
        if board[i] is not None and board[i] % 2 == color:
            for new_pos in get_piece_moves(board, move_list, i):
                possible_moves.append([i, new_pos])
    return possible_moves


def can_move(board, color, moves=BASE_MOVES):
    for i in range(32):
        if board[i] is not None and board[i] % 2 == color:
            if piece_can_move(i, board, color):
                return True
    return False


def can_jump(board, color):
    for i in range(32):
        if board[i] is not None and board[i] % 2 == color and piece_can_jump(i, board, color):
            return True
    return False


def valid_backward_move(current, new, board, color):
    if current // 4 % 2 == 0:
        if new - current in (3, 4):
            if current % 8 == 0 and new - current == 3:
                return False
            else:
                return True
        elif new - current == 9 and board[current+4] is not None and board[current+4] % 2 != color:
            if current % 8 == 3:
                return False
            else:
                return True
        elif new - current == 7 and board[current+3] is not None and board[current+3] % 2 != color:
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
        elif new - current == 9 and board[current+5] is not None and board[current+5] % 2 != color:
            if current % 8 == 7:
                return False
            else:
                return True
        elif new - current == 7 and board[current+4] is not None and board[current+4] % 2 != color:
            if current % 8 == 4:
                return False

            else:
                return True


def valid_forward_move(current, new, board, color):
    if current // 4 % 2 == 0:
        if current - new in (4, 5):
            return not (current % 8 == 0 and current - new == 5)

        elif current - new == 9 and board[current-5] is not None and board[current-5] % 2 != color:
            return not current % 8 == 0

        elif current - new == 7 and board[current-4] is not None and board[current-4] % 2 != color:
            return not current % 8 == 3

        else:
            return False

    else:
        if current - new in (3, 4):
            return not (current % 8 == 7 and current - new == 3)

        elif current - new == 9 and board[current-4] is not None and board[current-4] % 2 != color:
            return not current % 8 == 4

        elif current - new == 7 and board[current-3] is not None and board[current-3] % 2 != color:
            return not current % 8 == 7

        else:
            return False


def valid_move(current, new, board, move_list, color):
    if is_double_jump(board, move_list, color):
        if current != move_list[-1][-1] or not move_is_jump(current, new):
            return False
        else:
            # Skip other checks as this would not be considered as the players turn
            return valid_basic_move(current, new, board, color)
    if not is_turn(color, move_list) or is_double_jump(board, move_list, int(not color)):
        # Its not the players turn
        return False
    elif can_jump(board, color) and not move_is_jump(current, new):
        return False
    else:
        return valid_basic_move(current, new, board, color)


def valid_basic_move(current, new, board, color):
    # Returns if a move is valid based on how a piece can jump and the piece in its way
    # New position is clear and on the board
    if 0 <= new < 32 and board[new] is None:
        color, _type = board[current] % 2, board[current]//2
        if color == BLACK:
            if valid_forward_move(current, new, board, color):
                return True
            else:
                if _type:
                    return valid_backward_move(current, new, board, color)
                else:
                    return False
        elif color == WHITE:
            if valid_backward_move(current, new, board, color):
                return True
            else:
                if _type:
                    return valid_forward_move(current, new, board, color)
                else:
                    return False
        else:
            return False
    else:
        return False


def move_is_jump(current, new):
    return abs(current - new) in JUMP_MOVES


app = Flask(__name__)
app.config['SECRET_KEY'] = 'klekjkefnklsdjklafjiejjkldmkvmda'
socketio = SocketIO(app)


def simulate_move(current, new, board):
    color = board[current] % 2
    # Move piece to new position and king it if necessary
    if board[current]//2 == 0 and (color == BLACK and new // 4 == 0 or color == WHITE and new // 4 == 7):
        board[new] = color + 2
    else:
        board[new] = board[current]
    board[current] = None

    if move_is_jump(current, new):  # Removes piece jumped over
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
            if current-new == 9:
                board[current-4] = None
            elif current-new == 7:
                board[current-3] = None
            elif current-new == -9:
                board[current+5] = None
            elif current - new == -7:
                board[current+4] = None
    return board


def make_move(current, new, board, move_list=None):
    if move_list is None:
        move_list = session['move_list']
    color = board[current] % 2
    if is_double_jump(board, move_list, color):
        move_list[-1].append(new)
    else:
        move_list.append([current, new])
    board = simulate_move(current, new, board)


def evaluate(board):
    scores = [3, 5]
    black_score, white_score = 0, 0
    for number, space in enumerate(board):
        if space is not None:
            color, is_king = space % 2, space//2
            piece_value = scores[is_king]
            if not is_king:
                if number % 8 in (0, 7):
                    piece_value += 1
                if color == WHITE:
                    piece_value += 0.05*(number//4)
                else:
                    piece_value += 0.05*(7-number//4)
            if color == BLACK:
                black_score += piece_value
            else:
                white_score += piece_value
    return int(white_score / black_score * 1000) + random.randint(-3, 3)


def add_move(move_list, move):
    if move_list[-1][-1] == move[0]:
        move_list = [x[:] for x in move_list]
        move_list[-1] += move[1:]
    else:
        move_list += [move]
    return move_list


def get_children(move_list, board, player):
    return [add_move(move_list[:], move) for move in get_possible_moves(board, move_list, player)]


def minimax(depth, move_list, alpha, beta, player):
    board = get_board(move_list)
    if game_has_ended(board):
        if can_move(board, BLACK):
            return -9999999
        elif can_move(board, WHITE):
            return 9999999
        else:
            return 0
    if not depth:
        return evaluate(board)
    if player:
        value = -9999999
        for child in get_children(move_list, board, player):
            if is_double_jump(get_board(child), child, player):
                value = max(value, minimax(depth, child, alpha, beta, WHITE))

            else:
                if move_is_jump(child[-1][-2], child[-1][-1]):
                    value = max(value, minimax(
                        depth, child, alpha, beta, BLACK))
                else:
                    value = max(value, minimax(
                        depth-1, child, alpha, beta, BLACK))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = 9999999
        for child in get_children(move_list, board, player):
            if is_double_jump(get_board(child), child, player):
                value = min(value, minimax(depth, child, alpha, beta, BLACK))
            else:
                if move_is_jump(child[-1][-2], child[-1][-1]):
                    value = min(value, minimax(
                        depth, child, alpha, beta, WHITE))
                else:
                    value = min(value, minimax(
                        depth-1, child, alpha, beta, WHITE))
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value


def get_best_move(move_list, moves):
    best_move, best_value = None, 0
    for move in moves:
        if is_double_jump(get_board(add_move([x for x in move_list], move)), add_move([x for x in move_list], move), WHITE):
            color = WHITE
        else:
            color = BLACK
        value = minimax(session['depth'], add_move(
            [x for x in move_list], move), -9999999, 9999999, color)
        print(value)
        if value >= best_value or best_move is None:
            best_move, best_value = move, value
    return best_move


def make_ai_move(board, move_list):
    moves = get_possible_moves(board, move_list, WHITE)
    if len(moves) == 1:
        move = moves[0]
    else:
        x = time.time()
        move = get_best_move(move_list, moves)
        t = time.time()-x
        print('Time to find move: ', t)
        print('Time per move: ', t/len(moves))
        if t / len(moves) < 0.3:
            session['depth'] += 1
            print('Depth increased to {}'.format(session['depth']))
    make_move(move[0], move[1], board)
    emit('move response', {'moves': move_data(board, move_list), 'result': True, 'board': [None if piece is None else [
         'black man', 'white man', 'black king', 'white king'][piece] for piece in board], 'type': 'ai'})
    if is_double_jump(board, move_list, WHITE):
        socketio.sleep(0.4)
        make_ai_move(board, move_list)


def move_data(board, move_list):
    if is_double_jump(board, move_list, (len(move_list)+1) % 2):
        _moves = get_possible_moves(
            board, move_list, (len(move_list)+1) % 2)
    else:
        _moves = get_possible_moves(
            board, move_list, len(move_list) % 2)
    moves = []
    for x in range(32):
        moves.append([])
        for move in _moves:
            if move[0] == x:
                moves[x].append(move[1])
    return moves


@socketio.on('cancel game')
def cancel_game(room):
    if type(room) == str:
        for _room in rooms:
            if _room.name == room:
                rooms.remove(_room)
                del _room
                emit('room close', room, broadcast=True)
    elif type(room) == Room:
        if room in rooms:
            rooms.remove(room)
            emit('room close', room.name, broadcast=True)
            del room
    session['room'] = None


@socketio.on('create room')
def create_game(name):
    if session['room'] is not None:
        return 0
    if name is None or name == '':
        room = 'Room{}'.format(len(rooms))
    else:
        room = str(name)
    join_room(room)
    room_strut = Room(room, session['id'], 0, list(start_board), [])
    rooms.append(room_strut)
    session['room'] = room_strut
    session['color'] = BLACK
    emit('add room', {'name': room, 'creator': [
         session['id']]}, broadcast=True)


@socketio.on('disconnect')
def disconnected():
    if session['version'] == 'online':
        cancel_game(session['room'])


@socketio.on('join room')
def join_game(name):
    for room in rooms:
        if room.name == name:
            if not room.is_full():
                room.white_id = session['id']
                join_room(name)
                session['color'] = WHITE
                session['room'] = room
                emit('start game', {'moves': move_data(room.board, room.move_list),
                                    'black': room.black_id, 'white': room.white_id}, room=room.name)


@app.route('/online_game')
def online_game():
    session['room'] = None
    session['version'] = 'online'
    session['id'] = random.randint(1, 1000)
    return render_template('base.html', version='online', rooms=json.dumps([room.name for room in rooms]), id=session['id'])


@app.route('/')
def index():
    # Render the start page
    return render_template('index.html')


@socketio.on('request move data')
def request_move_data():
    emit('move data', {'moves': move_data(
        session['board'], session['move_list'])})


@socketio.on('online move request')
def online_user_move(data):
    current, new, color, board, move_list = int(data['current_pos']), int(
        data["new_pos"]), session['color'], session['room'].board, session['room'].move_list
    if valid_move(current, new, board, move_list, color):
        make_move(current, new, board, move_list)
        emit('move response', {'moves': move_data(board, move_list), 'result': True, 'board': [None if piece is None else [
             'black man', 'white man', 'black king', 'white king'][piece] for piece in board]}, room=session['room'].name)
        if game_has_ended(board):
            result = 'black' if can_move(
                board, BLACK) else 'white' if can_move(board, WHITE) else 'draw'
            emit('game end', {'result': result}, room=session['room'])
    else:
        emit('move response', {'result': False}, room=session['room'])


@socketio.on('move request')
def user_move(data):
    current, new = int(data["current_pos"]), int(data["new_pos"])
    color = session['board'][current] % 2
    if valid_move(current, new, session['board'], session['move_list'], color) and not (session['version'] == 'single' and color == WHITE):
        make_move(current, new, session['board'])
        emit('move response', {'moves': move_data(session['board'], session['move_list']), 'result': True, 'board': [
             None if piece is None else ['black man', 'white man', 'black king', 'white king'][piece] for piece in session['board']]})
        socketio.sleep(1)
        if session['version'] == 'single' and not game_has_ended(session['board']) and not is_double_jump(session['board'], session['move_list'], BLACK):
            make_ai_move(session['board'], session['move_list'])
        if game_has_ended(session['board']):
            result = 'black' if can_move(session['board'], BLACK) else 'white' if can_move(session['board'], WHITE) else 'draw'
            emit('game end', {'result': result})
    else:
        emit('move response', {'result': False})


@app.route('/game/<version>')
def game(version):
    if version == 'single':
        session['depth'] = BASE_DEPTH
    session['version'] = version
    session['move_list'] = []
    session['board'] = list(start_board)
    return render_template('base.html', version=version, id=None, rooms=None)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
