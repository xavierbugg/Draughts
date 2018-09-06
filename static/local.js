$(document).ready(function(){
    socket.on('connect', function() {
        console.log('connected');
        socket.emit('request move data');
    });
    drawBoard();
});
