const username = "{{ request.user.username|escapejs }}";
// Set up WebSocket connection to the specific room
const roomName = "{{ room_name }}";
const chatSocket = new WebSocket(
    'wss://' + window.location.host + '/ws/chat/' + roomName + '/'
);

// Assume `chatSocket` is the WebSocket connection instance
const endChatButton = document.getElementById('endChatButton');
endChatButton.addEventListener('click', () => {
    // Close the WebSocket connection
    chatSocket.close();
    roomName = null;
    clearCookie("room_name");
    window.location.reload;
});

chatSocket.onmessage = function (e) {
    const data = JSON.parse(e.data);
    document.querySelector('#chat-log').innerHTML += '<b>' + data.username + ':</b> ' + data.message + '<br>';
};

document.querySelector('#chat-message-submit').onclick = function (e) {
    const messageInputDom = document.querySelector('#chat-message-input');
    const message = messageInputDom.value;
    chatSocket.send(JSON.stringify({ 'username': username, 'message': message }));
    messageInputDom.value = '';
};

function clearCookie(name) {
    document.cookie = name + "=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
}


