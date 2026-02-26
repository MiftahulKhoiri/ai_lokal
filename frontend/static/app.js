const sendBtn = document.getElementById("sendBtn");
const messageInput = document.getElementById("message");
const chatContainer = document.getElementById("chat");
const hero = document.getElementById("hero");
const aiStatus = document.getElementById("aiStatus");
const topProgress = document.getElementById("topProgress");

let controller = null;
let isStreaming = false;

/* ================= STATE MANAGEMENT ================= */

function setState(state) {
    if (state === "idle") {
        aiStatus.innerText = "Idle";
        topProgress.style.width = "0%";
    }

    if (state === "thinking") {
        aiStatus.innerText = "Thinking...";
        topProgress.style.width = "60%";
    }

    if (state === "responding") {
        aiStatus.innerText = "Responding...";
        topProgress.style.width = "90%";
    }
}

/* ================= AUTO RESIZE ================= */

messageInput.addEventListener("input", () => {
    messageInput.style.height = "auto";
    messageInput.style.height = messageInput.scrollHeight + "px";
    sendBtn.disabled = messageInput.value.trim().length === 0;
});

/* ================= SEND ================= */

sendBtn.addEventListener("click", () => {
    if (isStreaming && controller) {
        controller.abort();
        return;
    }
    sendMessage();
});

async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text) return;

    if (hero) hero.classList.add("hide");

    addMessage(text, "user");

    messageInput.value = "";
    messageInput.style.height = "auto";
    sendBtn.disabled = true;

    sendBtn.classList.add("sending");
    setTimeout(() => sendBtn.classList.remove("sending"), 600);

    const botBubble = addMessage("", "bot");

    botBubble.innerHTML = `
        <div class="thinking">
            <div class="thinking-ring"></div>
            AIRA sedang berpikir
        </div>
    `;

    setState("thinking");

    controller = new AbortController();
    isStreaming = true;

    try {
        const response = await fetch("/stream", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text }),
            signal: controller.signal
        });

        if (!response.ok) throw new Error("Server error");

        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");

        let fullText = "";
        let buffer = "";
        let firstToken = false;

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            const events = buffer.split("\n\n");
            buffer = events.pop();

            for (const event of events) {
                if (!event.startsWith("data: ")) continue;

                const data = event.replace("data: ", "");

                if (data === "[DONE]") {
                    isStreaming = false;
                    break;
                }

                if (!firstToken) {
                    firstToken = true;
                    setState("responding");
                }

                fullText += data;

                botBubble.innerHTML =
                    renderMarkdown(fullText) +
                    '<span class="cursor">|</span>';

                scrollToBottom();
            }
        }

        botBubble.innerHTML = renderMarkdown(fullText);
        setState("idle");

    } catch (err) {
        botBubble.innerText = "⚠ Koneksi gagal.";
        setState("idle");
    } finally {
        isStreaming = false;
        controller = null;
        topProgress.style.width = "100%";
        setTimeout(() => setState("idle"), 400);
    }
}

/* ================= RENDER ================= */

function renderMarkdown(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\n/g, "<br>");
}

function scrollToBottom() {
    chatContainer.scrollTo({
        top: chatContainer.scrollHeight,
        behavior: "smooth"
    });
}

function addMessage(text, sender) {
    const msg = document.createElement("div");
    msg.classList.add("message", sender);
    msg.innerHTML = text;
    chatContainer.appendChild(msg);
    scrollToBottom();
    return msg;
}