const sendBtn = document.getElementById("sendBtn");
const messageInput = document.getElementById("message");
const chatContainer = document.getElementById("chat");
const hero = document.getElementById("hero");

let controller = null;
let isStreaming = false;

/* ================= AUTO RESIZE ================= */

messageInput.addEventListener("input", () => {
    messageInput.style.height = "auto";
    messageInput.style.height = messageInput.scrollHeight + "px";

    sendBtn.disabled = messageInput.value.trim().length === 0;
});

/* ================= ENTER SEND ================= */

messageInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        if (!sendBtn.disabled) sendBtn.click();
    }
});

/* ================= SCROLL ================= */

function scrollToBottom(force = false) {
    chatContainer.scrollTo({
        top: chatContainer.scrollHeight,
        behavior: "smooth"
    });
}

/* ================= MARKDOWN ================= */

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

/* ================= COPY BUTTON ================= */

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

    // Hero collapse
    if (hero) hero.classList.add("hide");

    addMessage(text, "user");

    messageInput.value = "";
    messageInput.style.height = "auto";
    sendBtn.disabled = true;

    // Micro animation
    sendBtn.classList.add("sending");
    setTimeout(() => sendBtn.classList.remove("sending"), 600);

    const botBubble = addMessage("", "bot");

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

                fullText += data;

                botBubble.innerHTML =
                    renderMarkdown(fullText) +
                    '<span class="cursor">|</span>';

                scrollToBottom();

                if (window.Prism) {
                    Prism.highlightAllUnder(botBubble);
                }
            }
        }

        // Remove cursor when done
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
    } else {
        msg.innerText = text;
    }

    chatContainer.appendChild(msg);
    scrollToBottom(true);
    return msg;
}