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

        assistantBubble.innerHTML = "";

        function read() {
            reader.read().then(({done, value}) => {
                if (done) {
                    addTimestamp(assistantBubble);
                    addCopyButton(assistantBubble);
                    isStreaming = false;
                    input.disabled = false;
                    button.disabled = false;
                    input.focus();
                    return;
                }

                assistantBubble.innerHTML += parseMarkdown(decoder.decode(value));
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
    bubble.innerHTML = parseMarkdown(text);

    chat.appendChild(bubble);
    addTimestamp(bubble);
    addCopyButton(bubble);

    scrollToBottom();
    return bubble;
}

function addTimestamp(bubble) {
    let time = document.createElement("span");
    time.className = "timestamp";

    let now = new Date();
    let formatted = now.getHours().toString().padStart(2, '0') + ":" +
                    now.getMinutes().toString().padStart(2, '0');

    time.innerText = formatted;
    bubble.appendChild(time);
}

function addCopyButton(bubble) {
    let btn = document.createElement("button");
    btn.className = "copy-btn";
    btn.innerText = "⧉";

    btn.onclick = function() {
        navigator.clipboard.writeText(bubble.innerText);
        btn.innerText = "✓";
        setTimeout(() => btn.innerText = "⧉", 1000);
    };

    bubble.appendChild(btn);
}

function parseMarkdown(text) {
    return text
        .replace(/```([\s\S]*?)```/g, "<pre><code>$1</code></pre>")
        .replace(/\*\*(.*?)\*\*/g, "<b>$1</b>")
        .replace(/\*(.*?)\*/g, "<i>$1</i>");
}

function scrollToBottom(){
    chat.scrollTop = chat.scrollHeight;
}