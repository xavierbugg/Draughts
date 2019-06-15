import json
import random
import time

from flask import Flask, render_template, request, session, url_for
from flask_socketio import Namespace, SocketIO, emit, join_room, leave_room

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

class Draughts():
    BLACK, WHITE = 0, 1
    BLACK_MAN, WHITE_MAN, BLACK_KING, WHITE_KING = range(4)
    BASE_MOVES, JUMP_MOVES = [3, 4, 5, 7, 9], [7, 9]
    START_BOARD = [WHITE_MAN if i < 12 else
                   BLACK_MAN if i > 19 else None for i in range(32)]

    def is_king(self, piece):
        return piece // 2

    def get_color(self, piece):
        return piece % 2

    def get_board(self, move_list):
        # Generates board from move list
        board = self.START_BOARD[:]
        for move in move_list:
            for i in range(len(move)-1):
                board = self.simulate_move(move[i], move[i+1], board)
        return board

    def game_has_ended(self, board):# What about draws?
        return not (self.can_move(board, self.WHITE) and self.can_move(board, self.BLACK))


    def is_double_jump(self, board, move_list, color):
        if not len(move_list):
            return False
        # Bool for if the player can make a double jump
        if color == self.BLACK and move_list[-1][-1] // 4 == 0 or color == WHITE and move_list[-1][-1] // 4 == 7:
            # The last piece to move moved to its back rows
            # If it has just been kinged it can't make a double jump
            positions = [0]
            for move in move_list[::-1]:
                if move[-1] == positions[-1]:
                    positions += move[:-1][::-1]
            if positions.count(0) == 1:
                # The piece was just kinged so can't double jump
                return False
        return not self.is_turn(color, move_list) and self.piece_can_jump(move_list[-1][-1], board, color) and abs(move_list[-1][0] - move_list[-1][1]) in JUMP_MOVES

    def is_turn(self, color, move_list):
        # Returns if it is the colors turn not considering double jumps on this turn
        return color == len(move_list) % 2

    def piece_can_move(self, piece, board, color, moves=BASE_MOVES):
        # Get the moves the piece can make
        if self.is_king(board[piece]):
            possible_moves = moves + [-move for move in moves]
        elif color == BLACK:
            possible_moves = [-move for move in moves]
        elif color == WHITE:
            possible_moves = moves

        for move in possible_moves:
            if self.valid_basic_move(piece, piece+move, board, color):
                return True
        return False

    def piece_can_jump(self, piece, board, color):
        return self.piece_can_move(piece, board, color, moves=JUMP_MOVES)

    def get_piece_moves(self, board, move_list, piece, moves=[3, 4, 5, 7, 9]):
        new_positions = []
        color = self.get_color(board[piece])
        if self.is_king(board[piece]):
            possible_moves = moves + [-move for move in moves]
        elif color == BLACK:
            possible_moves = [-move for move in moves]
        elif color == WHITE:
            possible_moves = moves
        for move in possible_moves:
            if self.valid_move(piece, piece+move, board, move_list, color):
                new_positions.append(piece+move)
        return new_positions


    def get_possible_moves(self, board, move_list, color, moves=BASE_MOVES):
        possible_moves = []
        for i in range(32):
            if board[i] is not None and board[i] % 2 == color:
                for new_pos in self.get_piece_moves(board, move_list, i):
                    possible_moves.append([i, new_pos])
        return possible_moves

    def get_jumped_pos(self, current, new):
        # Gets the position the piece jumped over
        if  current// 4 % 2 == 0:
            if current - new == 9:
                return current-5
            elif current - new == 7:
                return current-4
            elif current - new == -9:
                return current+4
            elif current - new == -7:
                return current+3
            else:
                return None
        else:
            if current-new == 9:
                return current-4
            elif current-new == 7:
                return current-3
            elif current-new == -9:
                return current+5
            elif current - new == -7:
                return current+4
            else:
                return None

    def can_move(self, board, color, moves=BASE_MOVES):
        for i in range(32):
            if board[i] is not None and board[i] % 2 == color:
                if self.piece_can_move(i, board, color, moves=moves):
                    return True
        return False


    def can_jump(self, board, color):
        return self.can_move(board, color, moves=self.JUMP_MOVES)


    def valid_backward_move(self, current, new, board, color):
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


    def valid_forward_move(self, current, new, board, color):
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


    def valid_move(self, current, new, board, move_list, color):
        # Returns if a move is valid based on double jumps, turns and must jump rules
        if self.is_double_jump(board, move_list, color):
            if current != move_list[-1][-1] or not self.move_is_jump(current, new):
                # Player needs to make double jump but is moving another piece or no making a jump move
                return False
            else:
                # Skip other checks as this would not be considered as the players turn
                return self.valid_basic_move(current, new, board, color)
        if not self.is_turn(color, move_list) or self.is_double_jump(board, move_list, int(not color)):
            # Its not the players turn
            return False
        elif self.can_jump(board, color) and not self.move_is_jump(current, new):
            return False
        else:
            return self.valid_basic_move(current, new, board, color)


    def valid_basic_move(self, current, new, board, color):
        # Returns if a move is valid based on how a piece can jump and the piece in its way
        if 0 <= new < 32 and board[new] is None:# New position is clear and on the board
            color, piece_is_king = self.get_color(board[current]), self.is_king(board[current])
            if color == BLACK:
                if self.valid_forward_move(current, new, board, color):
                    return True
                else:
                    if piece_is_king:
                        return self.valid_backward_move(current, new, board, color)
                    else:
                        return False
            elif color == WHITE:
                if self.valid_backward_move(current, new, board, color):
                    return True
                else:
                    if piece_is_king:
                        return self.valid_forward_move(current, new, board, color)
                    else:
                        return False
            else:
                return False
        else:
            return False

    def move_is_jump(self, current, new):
        return abs(current - new) in JUMP_MOVES

    def simulate_move(self, current, new, board):# Move piece to new position and king it if necessary
        color = self.get_color(board[current])
        if not self.is_king(board[current]) and (color == self.BLACK and new // 4 == 0 or color == self.WHITE and new // 4 == 7):
            # Make the piece a king
            board[new] = color + 2
        else:
            board[new] = board[current]
        board[current] = None

        if self.move_is_jump(current, new):  # Removes piece jumped over
            board[self.get_jumped_pos(current, new)] = None
        return board


app = Flask(__name__)
app.config['SECRET_KEY'] = 'klekjkefnklsdjklafjiejjkldmkvmda'
socketio = SocketIO(app)
class BaseDraughtsApp(Draughts):
    def make_move(self, current, new, board, move_list):
        color = self.get_color(board[current])
        if self.is_double_jump(board, move_list, color):
            move_list[-1].append(new)
        else:
            move_list.append([current, new])
        board = self.simulate_move(current, new, board)
        return board, move_list

    def move_data(self, board, move_list):
        if self.is_double_jump(board, move_list, self.get_color(len(move_list)+1)):
            _moves = self.get_possible_moves(
                board, move_list, (len(move_list)+1) % 2)
        else:
            _moves = self.get_possible_moves(
                board, move_list, len(move_list) % 2)
        moves = []
        for x in range(32):
            moves.append([])
            for move in _moves:
                if move[0] == x:
                    moves[x].append(move[1])
        return moves

class DraughtsApp(BaseDraughtsApp):
    def evaluate(self, board):
        scores = [3, 5]
        black_score, white_score = 0, 0
        for number, space in enumerate(board):
            if space is not None:
                color, is_king = self.get_color(space), self.is_king(space)
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
        return int(white_score / black_score * 1000)


    def add_move(self, move_list, move):
        if move_list[-1][-1] == move[0]:
            move_list = [x[:] for x in move_list]
            move_list[-1] += move[1:]
        else:
            move_list += [move]
        return move_list


    def get_children(self, move_list, board, player):
        children = []
        for move in self.get_possible_moves(board, move_list, player):
            children.append(self.add_move(move_list[:], move))
        return children


    def minimax(self, depth, move_list, alpha, beta, player):
        board = self.get_board(move_list)
        if self.game_has_ended(board):
            if self.can_move(board, BLACK):
                return -9999999
            elif self.can_move(board, WHITE):
                return 9999999
            else:
                return 0
        if not depth:
            return self.evaluate(board)
        if player:
            value = -9999999
            for child in self.get_children(move_list, board, player):
                if self.is_double_jump(self.get_board(child), child, player):
                    value = max(value, self.minimax(depth, child, alpha, beta, WHITE))

                else:
                    if self.move_is_jump(child[-1][-2], child[-1][-1]):
                        value = max(value, self.minimax(
                            depth, child, alpha, beta, BLACK))
                    else:
                        value = max(value, self.minimax(
                            depth-1, child, alpha, beta, BLACK))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value
        else:
            value = 9999999
            for child in self.get_children(move_list, board, player):
                if self.is_double_jump(self.get_board(child), child, player):
                    value = min(value, self.minimax(depth, child, alpha, beta, BLACK))
                else:
                    if self.move_is_jump(child[-1][-2], child[-1][-1]):
                        value = min(value, self.minimax(
                            depth, child, alpha, beta, WHITE))
                    else:
                        value = min(value, self.minimax(
                            depth-1, child, alpha, beta, WHITE))
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return value


    def get_best_move(self, move_list, moves, depth):
        best_move, best_value = None, 0
        values = []
        for move in moves:
            if self.is_double_jump(self.get_board(self.add_move([x for x in move_list], move)), self.add_move([x for x in move_list], move), self.WHITE):
                color = self.WHITE
            else:
                color = self.BLACK
            value = self.minimax(depth, self.add_move(
                [x for x in move_list], move), -9999999, 9999999, color)
            print(value)
            values.append(value)
        best_value = max(values)
        return moves[moves.index(best_value)]

    def make_ai_move(self, board, move_list, depth):
        moves = self.get_possible_moves(board, move_list, self.WHITE)
        if len(moves) == 1:
            move = moves[0]
        else:
            x = time.time()
            move = self.get_best_move(move_list, moves, depth)
            t = time.time()-x
            print('Time to find move: ', t)
            print('Time per move: ', t/len(moves))
            if t / len(moves) < 0.1:
                depth += 1
                print('Depth increased to {}'.format(session['depth']))
        board, move_list = self.make_move(move[0], move[1], board, move_list)
        emit('move_response', {'jumped': self.get_jumped_pos(move[0], move[1]),'to': move[1], 'from': move[0],'moves': self.move_data(board, move_list), 'result': True, 'board': [None if piece is None else [{'color': 'black', 'type': 'man'}, {'color': 'white', 'type': 'man'}, {'color': 'black', 'type': 'king'}, {'color': 'white', 'type': 'king'}][piece] for piece in board], 'type': 'ai'})
        if self.is_double_jump(board, move_list, WHITE):
            depth = self.make_ai_move(board, move_list, depth)
        return depth





class baseGameNamespace(Namespace, DraughtsApp):
    def on_request_move_data(self):
        emit('move_data', {'moves': self.move_data(
            session['board'], session['move_list'])})

    def on_move_request(self, data):
        current, new = int(data["current_pos"]), int(data["new_pos"])
        color = session['board'][current] % 2
        if self.valid_move(current, new, session['board'], session['move_list'], color) and not (session['version'] == 'single' and color == self.WHITE):
            self.make_move(current, new, session['board'], session['move_list'])
            emit('move_response', {'jumped': self.get_jumped_pos(current, new), 'to': new, 'from': current, 'moves': self.move_data(session['board'], session['move_list']), 'result': True, 'board': [
                None if piece is None else [{'color': 'black', 'type': 'man'}, {'color': 'white', 'type': 'man'}, {'color': 'black', 'type': 'king'}, {'color': 'white', 'type': 'king'}][piece] for piece in session['board']]})
            socketio.sleep(1)
            if session['version'] == 'single' and not self.game_has_ended(session['board']) and not self.is_double_jump(session['board'], session['move_list'], self.BLACK):
                session['depth'] = self.make_ai_move(session['board'], session['move_list'], session['depth'])
            if self.game_has_ended(session['board']):
                result = 'black' if self.can_move(session['board'], self.BLACK) else 'white' if self.can_move(
                    session['board'], self.WHITE) else 'draw'
                print('game ended')
                emit('game_end', {'result': result})
        else:
            emit('move_response', {'result': False})


class onlineGameNamespace(baseGameNamespace):
    def on_cancel_game(self, room):
        if type(room) == str:
            for _room in rooms:
                if _room.name == room:
                    rooms.remove(_room)
                    del _room
                    emit('room_close', room, broadcast=True, namespace='/online')
        elif type(room) == Room:
            if room in rooms:
                rooms.remove(room)
                emit('room_close', room.name, broadcast=True, namespace='/online')
                del room
        session['room'] = None

    def on_create_game(self, name):
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
        session['color'] = self.BLACK
        emit('add_room', {
             'name': room, 'creator': session['id']}, broadcast=True, namespace='/online')

    def on_join_game(self, name):
        for room in rooms:
            if room.name == name:
                if not room.is_full():
                    room.white_id = session['id']
                    join_room(name)
                    session['color'] = self.WHITE
                    session['room'] = room
                    emit('start_game', {'moves': self.move_data(room.board, room.move_list),
                                        'black': room.black_id, 'white': room.white_id}, room=room.name)
                    break

    def on_disconnect(self):
        self.on_cancel_game(session['room'])

    def on_move_request(self, data):
        current, new, color, board, move_list = int(data['current_pos']), int(
            data["new_pos"]), session['color'], session['room'].board, session['room'].move_list
        if self.valid_move(current, new, board, move_list, color):
            board, move_list = self.make_move(current, new, board, move_list)
            emit('move_response', {'jumped': self.get_jumped_pos(current, new),'to': new, 'from': current, 'moves': self.move_data(board, move_list), 'result': True, 'board': [None if piece is None else [{'color': 'black', 'type': 'man'}, {'color': 'white', 'type': 'man'}, {'color': 'black', 'type': 'king'}, {'color': 'white', 'type': 'king'}][piece] for piece in board]}, room=session['room'].name)
            if self.game_has_ended(board):
                result = 'black' if self.can_move(
                    board, self.BLACK) else 'white' if self.can_move(board, self.WHITE) else 'draw'
                emit('game_end', {'result': result}, room=session['room'].name)
        else:
            emit('move_response', {'result': False}, room=session['room'].name)

    def on_message(self, message):
        emit('message', message, room=session['room'].name, include_self=False)


socketio.on_namespace(baseGameNamespace('/'))
socketio.on_namespace(onlineGameNamespace('/online'))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/game/<version>')
def game(version):
    if version == 'single':
        session['depth'] = BASE_DEPTH

    if version == 'online':
        session['room'] = None
        _id = session['id'] = random.randint(1, 1000)
    else:
        _id = None
        session['move_list'] = []
        session['board'] = list(start_board)
    session['version'] = version
    return render_template('game.html', version=version, id=_id, rooms=json.dumps([room.name for room in rooms]))


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
