$(document).ready(function(){
    socket.on('connect', function() {
        socket.emit('request move data');
    });
    drawBoard();
});
