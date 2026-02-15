const sendBtn = document.getElementById("sendBtn");
const messageInput = document.getElementById("message");
const chatContainer = document.getElementById("chat");
const homeScreen = document.getElementById("homeScreen");

// Buat tombol scroll ke bawah
const scrollBtn = document.createElement("button");
scrollBtn.innerText = "⬇";
scrollBtn.className = "scroll-bottom-btn";
scrollBtn.style.display = "none";
document.body.appendChild(scrollBtn);

let controller = null;

sendBtn.addEventListener("click", sendMessage);

messageInput.addEventListener("keypress", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// AUTO RESIZE TEXTAREA
messageInput.addEventListener("input", () => {
    messageInput.style.height = "auto";
    messageInput.style.height = messageInput.scrollHeight + "px";
});

// SCROLL DETECTION
chatContainer.addEventListener("scroll", () => {
    const nearBottom =
        chatContainer.scrollHeight - chatContainer.scrollTop <=
        chatContainer.clientHeight + 50;

    scrollBtn.style.display = nearBottom ? "none" : "block";
});

scrollBtn.addEventListener("click", () => {
    scrollToBottom(true);
});

function scrollToBottom(smooth = false) {
    chatContainer.scrollTo({
        top: chatContainer.scrollHeight,
        behavior: smooth ? "smooth" : "auto"
    });
}

async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text) return;

    homeScreen.style.display = "none";
    chatContainer.style.display = "block";

    addMessage(text, "user");
    messageInput.value = "";
    messageInput.style.height = "auto";

    const botBubble = addMessage("", "bot");
    const typingIndicator = document.createElement("span");
    typingIndicator.innerText = "...";
    botBubble.appendChild(typingIndicator);

    controller = new AbortController();

    sendBtn.innerText = "STOP";

    try {
        const response = await fetch("/stream", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message: text }),
            signal: controller.signal
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");

        botBubble.innerText = "";

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            botBubble.innerText += chunk;

            scrollToBottom();
        }

    } catch (err) {
        if (err.name !== "AbortError") {
            botBubble.innerText = "Koneksi gagal.";
        }
    } finally {
        sendBtn.innerText = "⬤";
        controller = null;
        scrollToBottom();
    }
}

// STOP STREAMING
sendBtn.addEventListener("dblclick", () => {
    if (controller) {
        controller.abort();
        sendBtn.innerText = "⬤";
    }
});

function addMessage(text, sender) {
    const msg = document.createElement("div");
    msg.classList.add("message", sender);
    msg.innerText = text;
    chatContainer.appendChild(msg);
    scrollToBottom();
    return msg;
}