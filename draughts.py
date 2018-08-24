from flask import Flask, render_template, url_for, session
from flask_socketio import SocketIO, emit
import random
import time
BLACK = 0
WHITE = 1
BLACK_MAN = 0
WHITE_MAN = 1
BLACK_KING = 2
WHITE_KING = 3

def get_board(move_list):
    board = [WHITE_MAN, WHITE_MAN, WHITE_MAN, WHITE_MAN, WHITE_MAN, WHITE_MAN, WHITE_MAN, WHITE_MAN, WHITE_MAN, WHITE_MAN, WHITE_MAN, WHITE_MAN, None, None, None,
                        None, None, None,  None, None, BLACK_MAN, BLACK_MAN, BLACK_MAN, BLACK_MAN, BLACK_MAN, BLACK_MAN, BLACK_MAN, BLACK_MAN, BLACK_MAN, BLACK_MAN, BLACK_MAN, BLACK_MAN]
    for move in move_list:
        for i in range(len(move)-1):
            board = simulate_move(move[i], move[i+1], board)
    return board

def game_has_ended(board):
    if not can_move(board, WHITE):
        return True
    else:
        return not can_move(board, BLACK)


def is_double_jump(board, move_list, color):
    if len(move_list) and (color == BLACK and move_list[-1][-1] // 4 == 0 or color == WHITE and move_list[-1][-1] // 4 == 7):
        positions = [0]
        for move in move_list[::-1]:
            if move[-1] == positions[-1]:
                positions += move[:-1][::-1]
        if positions.count(0) == 1:
            return False
    return len(move_list) and not is_turn(color, move_list) and piece_can_jump(move_list[-1][-1], board, color) and abs(move_list[-1][0] - move_list[-1][1]) >= 7


def is_turn(color, move_list):
    return color == BLACK and len(move_list) % 2 == 0 or color == WHITE and len(move_list) % 2 == 1


def piece_can_jump(piece, board, color):
    moves=[7,9]
    if board[piece]//2:
        possible_moves = moves + [-move for move in moves]
    elif color == BLACK:
        possible_moves = [-move for move in moves]
    elif color == WHITE:
        possible_moves = moves
    for move in possible_moves:
        if valid_move(piece, piece+move, board, color):
            return True
    return False


def piece_can_move(piece, board, color, moves=[3, 4, 5, 7, 9]):
    if board[piece]//2:
        possible_moves = moves + [-move for move in moves]
    elif color == BLACK:
        possible_moves = [-move for move in moves]
    elif color == WHITE:
        possible_moves = moves
    for move in possible_moves:
        if valid_move(piece, piece+move, board, color):
            return True
    return False

def get_piece_moves(board, move_list, piece, display=False, moves=[3,4,5,7,9]):
    new_positions = []
    color = board[piece]%2
    if board[piece]//2:
        possible_moves = moves + [-move for move in moves]
    elif color == BLACK:
        possible_moves = [-move for move in moves]
    elif color == WHITE:
        possible_moves = moves
    for move in possible_moves:
        if correct_move(piece, piece+move, board, move_list, color, display=display):
            new_positions.append(piece+move)
    return new_positions

def get_possible_moves(board, move_list, color, display=False, moves=[3,4,5,7,9]):
    possible_moves = []
    for i in range(32):
        if board[i] is not None and board[i]%2 == color:
            for new_pos in get_piece_moves(board, move_list, i, display=display):
                possible_moves.append([i, new_pos])
    return possible_moves

def can_move(board, color, moves=[3, 4, 5, 7, 9]):
    for i in range(32):
        if board[i] is not None and board[i]%2 == color:
            if piece_can_move(i, board, color):
                return True
    return False


def can_jump(board, color):
    for i in range(32):
        if board[i] is not None and board[i]%2 == color:
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
        elif new - current == 9 and board[current+4] is not None and board[current+4]%2 != color:
            if current % 8 == 3:
                return False
            else:
                return True
        elif new - current == 7 and board[current+3] is not None and board[current+3]%2 != color:
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
        elif new - current == 9 and board[current+5] is not None and board[current+5]%2 != color:
            if current % 8 == 7:
                return False
            else:
                return True
        elif new - current == 7 and board[current+4] is not None and board[current+4]%2 != color:
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
        elif current - new == 9 and board[current-5] is not None and board[current-5]%2 != color:
            if current % 8 == 0:
                return False
            else:
                return True
        elif current - new == 7 and board[current-4] is not None and board[current-4]%2 != color:
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

        elif current - new == 9 and board[current-4] is not None and board[current-4]%2 != color:
            if current % 8 == 4:
                return False
            else:
                return True

        elif current - new == 7 and board[current-3] is not None and board[current-3]%2 != color:
            if current % 8 == 7:
                return False
            else:
                return True
        else:
            return False


    
def correct_move(current, new, board, move_list, color, display=False):
    if is_double_jump(board, move_list, color):
        if current != move_list[-1][-1] or not move_is_jump(current, new):
            if display:
                print('should double jump')
            return False
        else:
            # Skip other checks as this would not be considered as the players turn
            return valid_move(current, new, board, color)
    if not is_turn(color, move_list) or is_double_jump(board, move_list, int(not color)):
        if display:
            print('not turn')
            print(is_turn(color, move_list))
            print(is_double_jump(board, move_list, int(not color)))
        # Its not the players turn
        return False
    elif can_jump(board, color) and not move_is_jump(current, new):
        if display:
            print('should jump')
        return False
    else:
        if display:
            print('valid_move')
        return valid_move(current, new, board, color)


def valid_move(current, new, board, color):
    # New position is clear and on the board
    if 0 <= new < 32 and board[new] is None:
        color, _type = board[current]%2, board[current]//2
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
    return abs(current - new) in (7, 9)


app = Flask(__name__)
app.config['SECRET_KEY'] = 'klekjkefnklsdjklafjiejjkldmkvmda'
socketio = SocketIO(app)

def simulate_move(current, new, board):
    color = board[current]%2
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

def make_move(current, new, board):
    color = board[current]%2
    if is_double_jump(board, session['move_list'], color):
        session['move_list'][-1].append(new)
    else:
        session['move_list'].append([current, new])
    session['board'] = simulate_move(current, new, board)

def evaluate(board):
    scores = [3, 5]
    value = 0
    for number, space in enumerate(board):
        if space is not None:
            color, is_king = space%2, space//2
            piece_value = scores[is_king]
            if not is_king:
                if number % 8 in (0, 7):
                    piece_value += 1
                if color == WHITE:
                    piece_value += 0.05*(number//4)
                else:
                    piece_value += 0.05*(7-number//4)
            if color == BLACK:
                piece_value *= -1
            value += piece_value
            
    return int(round(value,2)*100)

def add_move(move_list, move):
    if move_list[-1][-1] == move[0]:
        move_list = [x[:] for x in move_list]
        move_list[-1]+=move[1:]
    else:
        move_list += [move]
    return move_list
        
def get_children(move_list, board, player):
    return [add_move(move_list[:], move) for move in get_possible_moves(board, move_list, player)]

def minimax(depth, move_list, alpha, beta, player):
    board = get_board(move_list)
    if game_has_ended(board):
        if can_move(board, BLACK):
            return -9999
        elif can_move(board, WHITE):
            return 9999
        else:
            return 0
    if not depth:
        return evaluate(board)
    if player:
        value = -99999
        for child in get_children(move_list, board, player):
            if is_double_jump(get_board(child), child, player):
                value = max(value, minimax(depth, child, alpha, beta, WHITE))

            else:
                if move_is_jump(child[-1][-2], child[-1][-1]):
                    value = max(value, minimax(depth, child, alpha, beta, BLACK))
                else:
                    value = max(value, minimax(depth-1, child, alpha, beta, BLACK))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        if not len(get_children(move_list, board, player)):
            print('No moves found on: {} white'.format(move_list))
            print(board)
            print(can_move(board, player))
            print(is_double_jump(board, move_list, player))
            print(is_double_jump(board, move_list, BLACK))
            print(is_turn(player, move_list))
            print('Testing moves')
            print(get_possible_moves(board, move_list, player, display=True))
            print('Done testing')
        return value
    else:
        value = 99999
        for child in get_children(move_list, board, player):
            if is_double_jump(get_board(child), child, player):
                value = min(value, minimax(depth, child, alpha, beta, BLACK))
            else:
                if move_is_jump(child[-1][-2], child[-1][-1]):
                    value = min(value, minimax(depth, child, alpha, beta, WHITE))
                else:
                    value = min(value, minimax(depth-1, child, alpha, beta, WHITE))
            beta = min(beta, value)
            if beta <= alpha:
                break
        if not len(get_children(move_list, board, player)):
            print('No moves found on: {} black'.format(move_list))
            print(board)
            print(can_move(board, player))
            print(is_double_jump(board, move_list, player))
            print(is_turn(player, move_list))
            print('Testing moves')
            print(get_possible_moves(board, move_list, player))
            print('Done testing')
        return value

def get_best_move(move_list, moves):
    depth = 3
    best_move = None
    best_value = 0
    print('Current score: ', evaluate(get_board(move_list)))
    for move in moves:
        if is_double_jump(get_board(add_move([x for x in move_list], move)), add_move([x for x in move_list], move), WHITE):
            value = minimax(depth, add_move([x for x in move_list], move), -99999, 99999, WHITE)
        else:
            value = minimax(depth, add_move([x for x in move_list], move), -99999, 99999, BLACK)
        print(move, value)
        if value >= best_value or best_move is None:
            best_move = move
            best_value = value
    print('Best move: ', best_move, '\nValue ', best_value)
    return best_move

def make_ai_move(board, move_list):
    moves = get_possible_moves(board, move_list, WHITE)
    if len(moves) == 1:
        move = moves[0]
    else:
        x = time.time()
        move = get_best_move(move_list, moves)
        print('time to find move: ', time.time()-x)
    make_move(move[0], move[1], board)
    emit('move response', {'result': True, 'board':[None if piece is None else ['black man', 'white man', 'black king', 'white king'][piece] for piece in board], 'type': 'ai'})
    if is_double_jump(board, move_list, WHITE):
        time.sleep(0.4)
        make_ai_move(board, move_list)

@app.route('/')
def index():
    # Render the start page
    return render_template('index.html')


@socketio.on('move request')
def user_move(data):
    current, new, board = int(data["current_pos"]), int(data["new_pos"]), session['board']
    color = board[current]%2
    if correct_move(current, new, board, session['move_list'], color) and not (session['version'] == 'single' and color == WHITE):
        make_move(current, new, board)
        emit('move response', {'result': True, 'board': [None if piece is None else ['black man', 'white man', 'black king', 'white king'][piece] for piece in board]})
        time.sleep(0.1)
        if session['version'] == 'single' and not game_has_ended(board) and not is_double_jump(board, session['move_list'], BLACK):
            make_ai_move(board, session['move_list'])
        if game_has_ended(board):
            if can_move(board, BLACK):
                emit('game end', {'result': 'black'})
            elif can_move(board, WHITE):
                emit('game end', {'result':'white'})
            else:
                emit('game end', {'result': 'draw'})
    else:
        emit('move response', {'result': False})


@app.route('/game/<version>')
def game(version):
    session['version'] = version
    session['move_list'] = []
    session['board'] = [WHITE_MAN, WHITE_MAN, WHITE_MAN, WHITE_MAN, WHITE_MAN, WHITE_MAN, WHITE_MAN, WHITE_MAN, WHITE_MAN, WHITE_MAN, WHITE_MAN, WHITE_MAN, None, None, None,
                        None, None, None,  None, None, BLACK_MAN, BLACK_MAN, BLACK_MAN, BLACK_MAN, BLACK_MAN, BLACK_MAN, BLACK_MAN, BLACK_MAN, BLACK_MAN, BLACK_MAN, BLACK_MAN, BLACK_MAN]
    return render_template('game.html', version=version)


if __name__ == '__main__':
    socketio.run(app, port=5000, debug=True)
