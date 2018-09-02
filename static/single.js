$(document).ready(function(){
    var socket = io.connect();
    socket.on('connect', function() {
        console.log('connected');
    });
    var board = ['white man', 'white man', 'white man', 'white man','white man','white man','white man','white man','white man','white man','white man','white man', null, null, null, null, null, null, null, null, 'black man', 'black man', 'black man', 'black man', 'black man', 'black man', 'black man', 'black man', 'black man', 'black man', 'black man', 'black man'];
    var selected = null;
    var moves = [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []];
    var canvas = $('#game_board')[0];
    canvas.addEventListener('click', function(event){clicked(event)});
    var context = canvas.getContext('2d');
    function drawBoard(){
        var space = 0;
        // Draw board base
        for(var y = 0; y < 8; y++){
            for(var x = 0; x < 8; x++){
                if(x % 2 != y % 2){
                    context.fillStyle = 'white';
                }
                else {
                    context.fillStyle = 'darkgrey';
                }
                context.fillRect(x * 100, y * 100, 100, 100);
            }
        };
        for(var y = 0; y < 8; y++){
            for(var x = 0; x < 8; x++){
                if (x % 2 == y % 2) {
                    if (selected === null){
                        if (moves[space].length > 0){
                            if (board[space].split(' ')[0] == 'black'){
                                context.strokeStyle = '#007BFF';
                            }
                            else {
                                context.strokeStyle = 'red';
                            }
                            context.lineWidth = 3;
                            //This piece can be moved
                            context.strokeRect(x * 100, y * 100, 100, 100);
                            context.lineWidth = 1;
                        }
                    }
                    else {
                        if (space == selected){
                            context.strokeStyle = '#007BFF';
                            context.lineWidth = 3;
                            context.strokeRect(x * 100, y * 100, 100, 100);
                            context.lineWidth = 1;

                        }
                        else if( moves[selected].indexOf(space) >= 0){
                            // piece can move to here
                            context.fillStyle = '#007BFF';
                            context.fillRect(x * 100, y * 100, 100, 100);
                        }
                    }
                    if (board[space] != null){
                        context.strokeStyle = 'black';
                        if (board[space].split(' ')[0] == 'white'){
                            context.fillStyle = 'white';
                        }
                        else {
                            context.fillStyle = 'black';
                        }
                        context.beginPath();
                        context.arc(x * 100 + 50, y*  100 + 50, 45, 0, 2 * Math.PI);
                        context.fill();
                        context.stroke();
                        if (board[space].split(' ')[1] == 'king'){
                            context.font = "50px Times New Roman";
                            if (board[space].split(' ')[0] == 'black'){
                                context.fillStyle = 'white';
                            }
                            else{
                                context.fillStyle = 'black';
                            }
                            context.textAlign = 'center';
                            context.textBaseline = 'middle'; 
                            context.fillText('K', x*100+50, y*100+50);
                        }
                    }
                    space ++;
                }
            }
        }
    }
    socket.on('game end', function(data){
        var message;
        if (data.result=='black'){
            message = 'You win!';
        }
        else if (data.result=='white'){
            message = 'You lose :(';
        }
        else{
            message = 'It\'s a draw';
        }
        var display_message = '<div class="alert alert-success alert-dismissible fade show"><button type="button" class="close" data-dismiss="alert">&times;</button>'+message+'</div>';
        $('#info').append(display_message);
    });
    socket.on('move data', function(data){
        console.log('Received move data');
        moves = data.moves;
        drawBoard();
        console.log(moves);
        
    });
    socket.on('move response', function (data, from, to){
        console.log('callback')
        console.log(data.result);
        if (data.result){
            board = data.board;
            moves = data.moves;
        }
        drawBoard();
    });
    function clicked(event){
        var x = event.pageX - canvas.offsetLeft;
        var y = event.pageY - canvas.offsetTop;
        var pos = Math.floor(Math.floor(x / canvas.scrollWidth * 8) / 2) + Math.floor(y / canvas.scrollHeight * 8) * 4
        if (selected === null){
            if (board[pos] != null && board[pos].split(' ')[0] == 'black'){
                console.log('selected: '+pos)
                selected = pos;
                drawBoard();
            }

        }
        else {
            console.log('Making move from '+selected+ ' to '+pos);
            socket.emit('move request', {current_pos: selected, new_pos: pos});
            selected = null;
        }

    }
    
    drawBoard();

});