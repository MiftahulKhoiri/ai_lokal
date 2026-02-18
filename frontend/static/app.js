const sendBtn = document.getElementById("sendBtn");
const messageInput = document.getElementById("message");
const chatContainer = document.getElementById("chat");
const homeScreen = document.getElementById("homeScreen");

let controller = null;
let isStreaming = false;

// ================= AUTO RESIZE =================
messageInput.addEventListener("input", () => {
    messageInput.style.height = "auto";
    messageInput.style.height = messageInput.scrollHeight + "px";
});

// ================= MOBILE KEYBOARD FIX =================
function adjustForKeyboard() {
    setTimeout(() => {
        scrollToBottom(true);
    }, 250);
}

messageInput.addEventListener("focus", adjustForKeyboard);

// ================= SEND BUTTON =================
sendBtn.addEventListener("click", () => {
    if (isStreaming && controller) {
        controller.abort();
        return;
    }
    sendMessage();
});

// ================= ENTER =================
messageInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendBtn.click();
    }
});

// ================= SCROLL =================
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

// ================= MARKDOWN RENDER =================
function renderMarkdown(text) {
    // Escape HTML
    text = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

    // Code block
    text = text.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
        return `
            <div class="code-block">
                <button class="copy-btn">Copy</button>
                <pre><code>${code.trim()}</code></pre>
            </div>
        `;
    });

    // Line break
    text = text.replace(/\n/g, "<br>");

    return text;
}

// ================= COPY (Delegated - No Rebinding) =================
chatContainer.addEventListener("click", function (e) {
    if (e.target.classList.contains("copy-btn")) {
        const code = e.target.parentElement.querySelector("code").innerText;
        navigator.clipboard.writeText(code);
        e.target.innerText = "Copied!";
        setTimeout(() => (e.target.innerText = "Copy"), 1200);
    }
});

// ================= SEND MESSAGE =================
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
    sendBtn.innerText = "STOP";

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
        botBubble.innerHTML = "";

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            fullText += chunk;

            botBubble.innerHTML = renderMarkdown(fullText);
            scrollToBottom();
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

// ================= ADD MESSAGE =================
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