const sendBtn = document.getElementById("sendBtn");
const messageInput = document.getElementById("message");
const chatContainer = document.getElementById("chat");
const homeScreen = document.getElementById("homeScreen");

sendBtn.addEventListener("click", sendMessage);
messageInput.addEventListener("keypress", function(e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

function sendMessage() {
    const text = messageInput.value.trim();
    if (!text) return;

    // sembunyikan home screen
    homeScreen.style.display = "none";
    chatContainer.style.display = "block";

    addMessage(text, "user");

    // contoh balasan dummy
    setTimeout(() => {
        addMessage("Ini adalah respon dari AIRA 🤖", "bot");
    }, 800);

    messageInput.value = "";
}

function addMessage(text, sender) {
    const msg = document.createElement("div");
    msg.classList.add("message", sender);
    msg.innerText = text;
    chatContainer.appendChild(msg);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}