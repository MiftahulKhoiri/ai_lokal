const sendBtn = document.getElementById("sendBtn");
const messageInput = document.getElementById("message");
const chatContainer = document.getElementById("chat");
const homeScreen = document.getElementById("homeScreen");

sendBtn.addEventListener("click", sendMessage);

messageInput.addEventListener("keypress", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

function scrollToBottom() {
    chatContainer.scrollTo({
        top: chatContainer.scrollHeight,
        behavior: "smooth"
    });
}

async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text) return;

    homeScreen.style.display = "none";
    chatContainer.style.display = "block";

    addMessage(text, "user");
    messageInput.value = "";

    const botBubble = addMessage("", "bot");

    sendBtn.disabled = true; // cegah spam klik

    try {
        const response = await fetch("/stream", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message: text })
        });

        if (!response.ok) {
            throw new Error("Server error");
        }

        if (!response.body) {
            throw new Error("ReadableStream not supported");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            botBubble.innerText += chunk;

            scrollToBottom();
        }

    } catch (err) {
        botBubble.innerText = "Koneksi gagal ke server.";
        console.error(err);
    } finally {
        sendBtn.disabled = false;
        scrollToBottom();
    }
}

function addMessage(text, sender) {
    const msg = document.createElement("div");
    msg.classList.add("message", sender);
    msg.innerText = text;
    chatContainer.appendChild(msg);

    scrollToBottom();
    return msg;
}