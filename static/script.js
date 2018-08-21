$(document).ready(function(){
    var socket = io.connect();
    socket.on('connect', function() {
        console.log('connected');
    });
    var board = ['white man', 'white man', 'white man', 'white man','white man','white man','white man','white man','white man','white man','white man','white man', null, null, null, null, null, null, null, null, 'black man', 'black man', 'black man', 'black man', 'black man', 'black man', 'black man', 'black man', 'black man', 'black man', 'black man', 'black man'];
    var selected = null;
    var canvas = $('#game_board')[0];
    canvas.addEventListener('click', function(event){clicked(event)});
    var context = canvas.getContext('2d');
    socket.on('game end', function(data){
        var message;
        if (data.result=='black'){
            message = 'Black Wins!';
        }
        else if (data.result=='white'){
            message = 'White Wins!';
        }
        else{
            message = 'It\'s a draw';
        }
        var display_message = '<div class="alert alert-success alert-dismissible fade show"><button type="button" class="close" data-dismiss="alert">&times;</button>'+message+'</div>';
        $('#info').append(display_message);
    })
    socket.on('move response', function (data, from, to){
        console.log('callback')
        console.log(data.result);
        if (data.result === true){
            for (var i = 0; i < 32; i++){
                if (data.board[i] != board[i]){
                    var row = Math.floor(i / 4);
                    var col = i%4 * 2 + Math.floor((i%8)/4);
                    if (data.board[i] === null){
                        console.log(row, col, 0)
                        context.fillStyle = 'darkgrey';
                        context.fillRect(col*100, 100 * row, 100, 100);
                    }
                    else{
                        console.log(row, col)
                        context.fillStyle = data.board[i].split(' ')[0];
                        context.beginPath();
                        context.arc(col * 100 + 50, row*  100 + 50, 45, 0, 2 * Math.PI);
                        context.fill();
                        context.stroke();
                        if (data.board[i].split(' ')[1] == 'king'){
                            context.font = "50px Times New Roman";
                            if (data.board[i].split(' ')[0] == 'black'){
                                context.fillStyle = 'white';
                            }
                            else{
                                context.fillStyle = 'black';
                            }
                            context.textAlign = 'center';
                            context.textBaseline = 'middle'; 
                            context.fillText('K', col*100+50, row*100+50);
                        }
                    }
                }
            }
            board = data.board;
        }
        else{
            //? do something
        }
    });
    function clicked(event){
        var x = event.pageX - canvas.offsetLeft;
        var y = event.pageY - canvas.offsetTop;
        var pos = Math.floor(Math.floor(x / canvas.scrollWidth * 8) / 2) + Math.floor(y / canvas.scrollHeight * 8) * 4
        if (selected === null){
            if (board[pos] != null){
                console.log('selected: '+pos)
                selected = pos;
            }

        }
        else {
            //check if move is valid
            console.log('Making move from '+selected+ ' to '+pos);
            socket.emit('move request', {current_pos: selected, new_pos: pos});
            selected = null;
        }

    }
    function drawBoard(){
        for(var x = 0; x < 8; x++){
            for(var y = 0; y < 8; y++){
                if(x % 2 == y % 2){
                    context.fillStyle = 'darkgrey';
                }
                else {
                    context.fillStyle = 'white';
                }
                context.fillRect(x * 100, y * 100, 100, 100);
                if (x%2 == y%2 && y < 3){
                    context.fillStyle = 'white';
                    context.beginPath();
                    context.arc(x * 100 + 50, y*  100 + 50, 45, 0, 2 * Math.PI);
                    context.fill();
                    context.stroke();
                }
                else if (x%2 == y%2 && y >4){
                    context.fillStyle = 'black';
                    context.beginPath();
                    context.arc(x*100+50, y*100+50, 45, 0, 2*Math.PI);
                    context.fill();
                    context.stroke();

                }
            }
        }
    }
    drawBoard();

});


