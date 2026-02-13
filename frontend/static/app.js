let isStreaming = false;

const input = document.getElementById("message");
const button = document.getElementById("sendBtn");
const chat = document.getElementById("chat");

input.addEventListener("keydown", function(e) {
    if (e.key === "Enter" && !isStreaming) {
        sendMessage();
    }
});

button.addEventListener("click", function() {
    if (!isStreaming) {
        sendMessage();
    }
});

function sendMessage() {

    let message = input.value.trim();
    if (!message) return;

    addMessage(message, "user");
    input.value = "";

    isStreaming = true;
    input.disabled = true;
    button.disabled = true;

    let assistantBubble = addMessage("Mengetik...", "assistant");

    fetch("/stream", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message: message})
    })
    .then(response => {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        assistantBubble.innerText = "";

        function read() {
            reader.read().then(({done, value}) => {
                if (done) {
                    isStreaming = false;
                    input.disabled = false;
                    button.disabled = false;
                    input.focus();
                    return;
                }

                assistantBubble.innerText += decoder.decode(value);
                scrollToBottom();
                read();
            });
        }

        read();
    })
    .catch(error => {
        assistantBubble.innerText = "ERROR: Tidak dapat terhubung.";
        isStreaming = false;
        input.disabled = false;
        button.disabled = false;
    });
}

function addMessage(text, sender) {
    let bubble = document.createElement("div");
    bubble.className = "bubble " + sender;
    bubble.innerText = text;

    chat.appendChild(bubble);
    scrollToBottom();

    return bubble;
}

function scrollToBottom(){
    chat.scrollTop = chat.scrollHeight;
}