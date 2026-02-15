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

async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text) return;

    homeScreen.style.display = "none";
    chatContainer.style.display = "block";

    addMessage(text, "user");
    messageInput.value = "";

    // buat bubble kosong untuk bot
    const botBubble = addMessage("", "bot");

    try {
        const response = await fetch("/stream", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message: text })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            botBubble.innerText += chunk;
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

    } catch (err) {
        botBubble.innerText = "Koneksi gagal ke server.";
        console.error(err);
    }
}

function addMessage(text, sender) {
    const msg = document.createElement("div");
    msg.classList.add("message", sender);
    msg.innerText = text;
    chatContainer.appendChild(msg);
    return msg;
}