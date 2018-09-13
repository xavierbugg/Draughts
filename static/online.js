var color = null;
var started = false;
$(document).ready(function () {
    for (var i = 0; i < rooms.length; i++) {
        $("table").append(
            $('<tr></tr>').append(
                $('<td></td>').text(rooms[i]), $('<td></td').append(
                    $('<button/>', {
                        text: 'Join ',
                        class: "btn btn-primary",
                        id: rooms[i],
                        click: function () { socket.emit('join room', this.id) }
                    }
                    )
                )
            )
        )
    };
    socket.on('start game', function (data) {
        $('#findGame').toggleClass('hidden');
        $('.lead').toggleClass('hidden');
        $('#board_row').toggleClass('hidden');
        started = true
        moves = data.moves;
        if (data.black == id) {
            color = 'black';
        }
        else {
            color = 'white';
        }
        drawBoard();
    });
    socket.on('room close', function (room) {
        $('button#' + room).parent().parent().remove();
    });
    socket.on('add room', function (room) {
        console.log('New room ' + room.name);
        var element;
        if (room.creator == id) {
            element = $('<button/>', {
                text: 'Cancel',
                class: 'btn btn-primary',
                id: room.name,
                click: function () { socket.emit('cancel game', this.id) }
            });
        }
        else {
            element = $('<button/>', {
                text: 'Join ',
                class: "btn btn-primary",
                id: room.name,
                click: function () { socket.emit('join room', this.id) }
            });
        }
        $('table').append(
            $('<tr></tr>').append(
                $('<td></td>').text(room.name), $('<td></td').append(
                    element
                )
            )
        )
    });
    $(document).on('click', '#createGame', function () { socket.emit('create room', $('#nameInput').val()) });
});