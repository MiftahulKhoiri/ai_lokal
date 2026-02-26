const sendBtn = document.getElementById("sendBtn");
const messageInput = document.getElementById("message");
const chatContainer = document.getElementById("chat");
const homeScreen = document.getElementById("homeScreen");

let controller = null;
let isStreaming = false;

/* ================= AUTO RESIZE ================= */

messageInput.addEventListener("input", () => {
    messageInput.style.height = "auto";
    messageInput.style.height = messageInput.scrollHeight + "px";
});

/* ================= ENTER ================= */

messageInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendBtn.click();
    }
});

/* ================= SMART SCROLL ================= */

function isNearBottom() {
    return (
        chatContainer.scrollHeight - chatContainer.scrollTop
        <= chatContainer.clientHeight + 100
    );
}

function scrollToBottom(force = false) {
    if (force || isNearBottom()) {
        chatContainer.scrollTo({
            top: chatContainer.scrollHeight,
            behavior: "smooth"
        });
    }
}

/* ================= MARKDOWN RENDER ================= */

function renderMarkdown(text) {
    text = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

    text = text.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
        const language = lang ? `language-${lang}` : "language-python";
        return `
            <div class="code-block">
                <button class="copy-btn">Copy</button>
                <pre><code class="${language}">${code.trim()}</code></pre>
            </div>
        `;
    });

    text = text.replace(/\n/g, "<br>");
    return text;
}

/* ================= COPY HANDLER ================= */

chatContainer.addEventListener("click", function (e) {
    if (e.target.classList.contains("copy-btn")) {
        const code = e.target.parentElement.querySelector("code").innerText;
        navigator.clipboard.writeText(code);
        e.target.innerText = "Copied";
        setTimeout(() => e.target.innerText = "Copy", 1200);
    }
});

/* ================= SEND BUTTON ================= */

sendBtn.addEventListener("click", () => {
    if (isStreaming && controller) {
        controller.abort();
        return;
    }
    sendMessage();
});

/* ================= SEND MESSAGE ================= */

async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text) return;

    homeScreen.style.display = "none";
    chatContainer.style.display = "block";

    addMessage(text, "user");

    messageInput.value = "";
    messageInput.style.height = "auto";

    const botBubble = addMessage("", "bot");

    botBubble.innerHTML = `
        <span class="typing">
            <span></span><span></span><span></span>
        </span>
    `;

    controller = new AbortController();
    isStreaming = true;
    sendBtn.innerText = "Stop";

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
        let lastRender = 0;

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            const parts = buffer.split("\n\n");
            buffer = parts.pop(); // sisa event yang belum lengkap

            for (const part of parts) {
                if (!part.startsWith("data: ")) continue;

                const data = part.replace("data: ", "").trim();

                if (data === "[DONE]") {
                    isStreaming = false;
                    break;
                }

                fullText += data;

                const now = Date.now();
                if (now - lastRender > 40) {
                    botBubble.innerHTML = renderMarkdown(fullText);

                    if (window.Prism) {
                        Prism.highlightAllUnder(botBubble);
                    }

                    scrollToBottom();
                    lastRender = now;
                }
            }
        }

        botBubble.innerHTML = renderMarkdown(fullText);

        if (window.Prism) {
            Prism.highlightAllUnder(botBubble);
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

/* ================= ADD MESSAGE ================= */

function addMessage(text, sender) {
    const msg = document.createElement("div");
    msg.classList.add("message", sender);

    if (sender === "bot") {
        msg.innerHTML = renderMarkdown(text);

        if (window.Prism) {
            Prism.highlightAllUnder(msg);
        }

    } else {
        msg.innerText = text;
    }

    chatContainer.appendChild(msg);
    scrollToBottom(true);
    return msg;
}