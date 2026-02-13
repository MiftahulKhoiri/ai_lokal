let controller = null;
let isStreaming = false;

const input = document.getElementById("message");
const button = document.getElementById("sendBtn");
const stopBtn = document.getElementById("stopBtn");
const chat = document.getElementById("chat");
const themeToggle = document.getElementById("themeToggle");

themeToggle.onclick = () => {
    document.body.classList.toggle("dark");
};

input.addEventListener("input", () => {
    input.style.height = "auto";
    input.style.height = input.scrollHeight + "px";
});

input.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey && !isStreaming) {
        e.preventDefault();
        sendMessage();
    }
});

stopBtn.onclick = () => {
    if (controller) controller.abort();
    isStreaming = false;
};

function sendMessage() {

    let message = input.value.trim();
    if (!message) return;

    addMessage(message, "user");
    input.value = "";
    input.style.height = "auto";

    isStreaming = true;
    controller = new AbortController();

    let assistantBubble = addMessage("", "assistant");

    fetch("/stream", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message: message}),
        signal: controller.signal
    })
    .then(response => {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        function read() {
            reader.read().then(({done, value}) => {
                if (done) {
                    addTimestamp(assistantBubble);
                    isStreaming = false;
                    return;
                }

                assistantBubble.innerHTML += parseMarkdown(decoder.decode(value));
                scrollToBottom();
                read();
            });
        }
        read();
    })
    .catch(() => {
        assistantBubble.innerText = "[Dihentikan]";
        isStreaming = false;
    });
}

function addMessage(text, sender) {
    let bubble = document.createElement("div");
    bubble.className = "bubble " + sender;
    bubble.innerHTML = parseMarkdown(text);
    chat.appendChild(bubble);
    scrollToBottom();
    return bubble;
}

function addTimestamp(bubble) {
    let span = document.createElement("span");
    span.className = "timestamp";
    let now = new Date();
    span.innerText =
        now.getHours().toString().padStart(2, '0') + ":" +
        now.getMinutes().toString().padStart(2, '0');
    bubble.appendChild(span);
}

function parseMarkdown(text) {
    return text
        .replace(/```([\s\S]*?)```/g, "<pre>$1</pre>")
        .replace(/\*\*(.*?)\*\*/g, "<b>$1</b>")
        .replace(/\*(.*?)\*/g, "<i>$1</i>");
}

function scrollToBottom() {
    chat.scrollTop = chat.scrollHeight;
}