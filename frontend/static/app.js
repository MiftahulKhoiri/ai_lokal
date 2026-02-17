const sendBtn = document.getElementById("sendBtn");
const messageInput = document.getElementById("message");
const chatContainer = document.getElementById("chat");
const homeScreen = document.getElementById("homeScreen");

let controller = null;
let isStreaming = false;

// ===== AUTO RESIZE =====
messageInput.addEventListener("input", () => {
    messageInput.style.height = "auto";
    messageInput.style.height = messageInput.scrollHeight + "px";
});

// ===== SEND BUTTON =====
sendBtn.addEventListener("click", () => {
    if (isStreaming && controller) {
        controller.abort();
        return;
    }
    sendMessage();
});

// ===== ENTER =====
messageInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendBtn.click();
    }
});

function scrollToBottom(force = false) {
    const nearBottom =
        chatContainer.scrollHeight - chatContainer.scrollTop <=
        chatContainer.clientHeight + 80;

    if (nearBottom || force) {
        chatContainer.scrollTo({
            top: chatContainer.scrollHeight,
            behavior: "smooth"
        });
    }
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

    // typing animation
    botBubble.innerHTML = `<span class="typing">
        <span></span><span></span><span></span>
    </span>`;

    controller = new AbortController();
    isStreaming = true;
    sendBtn.innerText = "STOP";

    try {
        const response = await fetch("/stream", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: text
            }),
            signal: controller.signal
        });

        if (!response.ok) {
            throw new Error("Server error");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");

        let buffer = "";
        let renderScheduled = false;

        function scheduleRender() {
            if (!renderScheduled) {
                renderScheduled = true;
                setTimeout(() => {
                    botBubble.innerText += buffer;
                    buffer = "";
                    renderScheduled = false;
                    scrollToBottom();
                }, 25);
            }
        }

        botBubble.innerText = "";

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            buffer += chunk;
            scheduleRender();
        }

    } catch (err) {
        if (err.name !== "AbortError") {
            botBubble.innerText = "⚠ Koneksi ke model gagal.";
        }
    } finally {
        isStreaming = false;
        sendBtn.innerText = "⬤";
        controller = null;
        scrollToBottom(true);
    }
}

function addMessage(text, sender) {
    const msg = document.createElement("div");
    msg.classList.add("message", sender);
    msg.innerText = text;
    chatContainer.appendChild(msg);
    scrollToBottom(true);
    return msg;
}