async function requireAuth() {

    const token = localStorage.getItem("token");

    if (!token) {
        window.location.href = "/";
        return;
    }

    try {

        const response = await fetch(
            "/api/me",
            {
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            }
        );

        if (!response.ok) {

            localStorage.removeItem("token");
            localStorage.removeItem("activeConversationId");
            window.location.href = "/";
            return;

        }

    } catch (error) {

        console.error("Authentication check failed:", error);

        localStorage.removeItem("token");
        localStorage.removeItem("activeConversationId");
        window.location.href = "/";

    }
}

async function login() {


    const identifier =
        document.getElementById("email").value;


    const password =
        document.getElementById("password").value;



    const response = await fetch(
        "/api/auth/login",
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                identifier,
                password
            })
        }
    );


    const data = await response.json();



    if(response.ok){

        localStorage.setItem(
            "token",
            data.access_token
        );
        localStorage.removeItem("activeConversationId");

        showToast("Login successful! Redirecting...", "success");

        setTimeout(() => {
            window.location.href="/dashboard";
        }, 600);

    }

    else {

        document.getElementById("error").innerText =
            data.detail;

    }

}

let googleClientId = "";

async function initGoogleAuth() {
    try {
        const res = await fetch("/api/auth/google/config");
        if (res.ok) {
            const data = await res.json();
            googleClientId = data.client_id || "";
            if (googleClientId && window.google && window.google.accounts && window.google.accounts.id) {
                google.accounts.id.initialize({
                    client_id: googleClientId,
                    callback: handleGoogleCallback,
                    auto_select: false
                });
            }
        }
    } catch (err) {
        console.error("Google Auth Config fetch error:", err);
    }
}

async function handleGoogleSignIn() {
    if (googleClientId && window.google && window.google.accounts && window.google.accounts.id) {
        google.accounts.id.prompt((notification) => {
            if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
                if (window.google.accounts.oauth2) {
                    const client = google.accounts.oauth2.initTokenClient({
                        client_id: googleClientId,
                        scope: "email profile openid",
                        callback: handleGoogleCallback
                    });
                    client.requestAccessToken();
                }
            }
        });
    } else {
        showToast("Please set GOOGLE_CLIENT_ID in your .env file to enable Google Sign-In", "info");
    }
}

async function handleGoogleCallback(response) {
    const credential = response.credential || response.access_token;
    if (!credential) return;

    try {
        showToast("Signing in with Google...", "info");
        const res = await fetch("/api/auth/google", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ credential })
        });

        const data = await res.json();
        if (res.ok) {
            localStorage.setItem("token", data.access_token);
            localStorage.removeItem("activeConversationId");
            showToast("Google Sign-In successful! Redirecting...", "success");
            setTimeout(() => {
                window.location.href = "/dashboard";
            }, 600);
        } else {
            showToast(data.detail || "Google authentication failed", "error");
        }
    } catch (err) {
        console.error("Google Auth error:", err);
        showToast("Error connecting to Google Auth", "error");
    }
}

window.addEventListener("DOMContentLoaded", initGoogleAuth);

const messageBox = document.getElementById("message");

if(messageBox){

    initializeChat();

    messageBox.addEventListener("input", () => {

        messageBox.style.height = "42px";

        messageBox.style.height =
            Math.min(messageBox.scrollHeight, 150) + "px";

    });

    messageBox.addEventListener("focus", () => {
        setTimeout(() => {
            const box = document.getElementById("messages");
            if (box) box.scrollTop = box.scrollHeight;
        }, 300);
    });

    messageBox.addEventListener("keydown", function(event){

        if(event.key === "Enter" && !event.shiftKey){

            event.preventDefault();

            sendMessage();

        }

    });

}

function initializeChatHistoryToggle() {

    const toggle =
        document.getElementById("chat-history-toggle");

    const openBtn =
        document.getElementById("chat-history-open");

    const sidebar =
        document.querySelector(".chat-sidebar");

    if (!sidebar)
        return;


    function updateToggleState() {

        const isOpen =
            sidebar.classList.contains("open");

        if (toggle) {
            toggle.setAttribute(
                "aria-expanded",
                String(isOpen)
            );
        }

        if (openBtn) {
            openBtn.setAttribute(
                "aria-expanded",
                String(isOpen)
            );
        }
    }


    function setInitialState() {

        if (window.innerWidth > 800) {

            sidebar.classList.add("open");

        } else {

            sidebar.classList.remove("open");

        }

        updateToggleState();
    }


    if (toggle) {
        toggle.addEventListener("click", () => {

            sidebar.classList.remove("open");

            updateToggleState();

        });
    }


    if (openBtn) {
        openBtn.addEventListener("click", () => {

            sidebar.classList.add("open");

            updateToggleState();

        });
    }


    const backdrop =
        document.getElementById("chat-sidebar-backdrop");

    if (backdrop) {
        backdrop.addEventListener("click", () => {
            sidebar.classList.remove("open");
            updateToggleState();
        });
    }

    setInitialState();


    window.addEventListener("resize", () => {

        if (window.innerWidth > 800) {

            sidebar.classList.add("open");

        } else {

            sidebar.classList.remove("open");

        }

        updateToggleState();

    });

}

if (window.location.pathname === "/chat") {
    initializeChatHistoryToggle();
}

async function sendMessage() {

    const input = document.getElementById("message");
    const sendBtn = document.getElementById("send-btn");

    const text = input.value.trim();

    if (!text)
        return;


    // Disable sending while AI responds
    if (sendBtn)
        sendBtn.disabled = true;


    addMessage(
        text,
        "user"
    );


    input.value = "";
    input.style.height = "auto";

    showTypingIndicator();


    const token =
        localStorage.getItem("token");


    try {

        const response = await fetch(
            "/api/chat",
            {

                method: "POST",

                headers: {

                    "Content-Type": "application/json",

                    "Authorization":
                        `Bearer ${token}`

                },


                body: JSON.stringify({

                    message: text,
                    conversation_id: Number(localStorage.getItem("activeConversationId"))

                })

            }
        );


        const data =
            await response.json();

        if (!response.ok)
            throw new Error(data.detail || "Could not send message");


        hideTypingIndicator();


        addMessage(
            data.response,
            "bot"
        );

        if (data.conversation_id)
            localStorage.setItem("activeConversationId", data.conversation_id);

        loadConversations().catch(console.error);


    } catch(error) {

        hideTypingIndicator();

        addMessage(
            "Sorry, something went wrong. Please try again.",
            "bot"
        );

        console.error(error);

    }


    // Enable sending again
    if (sendBtn)
        sendBtn.disabled = false;


    // Keep typing ready
    input.focus();

}

function showTypingIndicator(){

    const box =
        document.getElementById("messages");

    const div =
        document.createElement("div");

    div.className = "bot message typing-indicator";
    div.id = "typing-indicator";

    div.innerHTML = `
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
    `;

    box.appendChild(div);

    box.scrollTop = box.scrollHeight;

}


function hideTypingIndicator(){

    const indicator =
        document.getElementById("typing-indicator");

    if(indicator){
        indicator.remove();
    }

}


function addMessage(
    text,
    type
){
    const box =
        document.getElementById("messages");

    if (!box) return;

    const existingChips = box.querySelector(".prompt-chips-container");
    if (existingChips) {
        existingChips.remove();
    }

    if (type === "bot") {
        const wrapper = document.createElement("div");
        wrapper.className = "bot-message-wrapper";

        const div = document.createElement("div");
        div.className = "bot message";
        div.innerHTML = formatMessage(text);
        wrapper.appendChild(div);

        const copyBtn = document.createElement("button");
        copyBtn.type = "button";
        copyBtn.className = "msg-copy-btn";
        copyBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
            </svg>
            <span>Copy</span>
        `;

        copyBtn.onclick = () => {
            if (navigator.clipboard) {
                navigator.clipboard.writeText(text).then(() => {
                    const label = copyBtn.querySelector("span");
                    if (label) label.innerText = "✓ Copied";
                    setTimeout(() => {
                        if (label) label.innerText = "Copy";
                    }, 2000);
                }).catch(console.error);
            }
        };

        wrapper.appendChild(copyBtn);
        box.appendChild(wrapper);
    } else {
        const div = document.createElement("div");
        div.className = `${type} message`;
        div.innerHTML = formatMessage(text);
        box.appendChild(div);
    }

    box.scrollTop = box.scrollHeight;
}

function formatMessage(text) {
    // Escape HTML first to prevent injection
    let escaped = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");

    // Convert **bold** to <strong>
    escaped = escaped.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

    // Convert line breaks to <br>
    escaped = escaped.replace(/\n/g, "<br>");

    return escaped;
}

async function loadDashboard(){

    const token =
        localStorage.getItem("token");


    const userResponse =
        await fetch(
            "/api/me",
            {
                headers:{
                    "Authorization":
                    `Bearer ${token}`
                }
            }
        );


    const user =
        await userResponse.json();


    document.getElementById("welcome")
    .innerText =
    `Welcome, ${user.username}`;


    document.getElementById("user-email")
    .innerText =
    user.email;

    const analyticsResponse =
        await fetch(
            "/api/analytics/summary",
            {
                headers:{
                    "Authorization":
                    `Bearer ${token}`
                }
            }
        );


    const analytics =
        await analyticsResponse.json();


    document.getElementById("balance")
    .innerText =
    `₨ ${Math.max(0, analytics.balance).toLocaleString()}`;


    document.getElementById("income")
    .innerText =
    `₨ ${analytics.income.toLocaleString()}`;


    document.getElementById("expenses")
    .innerText =
    `₨ ${analytics.expenses.toLocaleString()}`;


    const categoryBox =
        document.getElementById("category-breakdown");


    categoryBox.innerHTML = "";


    const categories = Object.entries(analytics.category_breakdown);

    if(categories.length === 0){

        categoryBox.innerText = "No spending recorded yet";

    }

    else{

        const maxAmount = Math.max(...categories.map(([, amount]) => amount));
        const totalSpending = categories.reduce((sum, [, amt]) => sum + amt, 0);

        if (totalSpending > 0) {
            const chartColors = ["#f2a93b", "#3fbf8f", "#f0665b", "#8a968f", "#53645a"];
            const donutContainer = document.createElement("div");
            donutContainer.className = "category-analytics-container";

            let cumulativePercent = 0;
            const radius = 34;
            const circumference = 2 * Math.PI * radius;

            let circlesSvg = "";
            let legendHtml = "";

            categories.forEach(([cat, amt], idx) => {
                const color = chartColors[idx % chartColors.length];
                const pct = (amt / totalSpending);
                const dashArray = `${pct * circumference} ${circumference}`;
                const dashOffset = -cumulativePercent * circumference;
                cumulativePercent += pct;

                circlesSvg += `<circle cx="45" cy="45" r="${radius}" fill="transparent" stroke="${color}" stroke-width="12" stroke-dasharray="${dashArray}" stroke-dashoffset="${dashOffset}" />`;
                legendHtml += `<div class="legend-item"><span class="legend-dot" style="background:${color}"></span><span>${cat} (${Math.round(pct * 100)}%)</span></div>`;
            });

            donutContainer.innerHTML = `
                <svg class="donut-chart-svg" viewBox="0 0 90 90">
                    ${circlesSvg}
                </svg>
                <div class="category-legend">
                    ${legendHtml}
                </div>
            `;

            categoryBox.appendChild(donutContainer);
        }

        categories.forEach(([category, amount]) => {

            const row = document.createElement("div");
            row.className = "category-row";

            const percent = maxAmount > 0 ? (amount / maxAmount) * 100 : 0;

            row.innerHTML = `
                <div class="category-row-top">
                    <span class="cat-name">${category}</span>
                    <span class="cat-amount">₨ ${amount.toLocaleString()}</span>
                </div>
                <div class="category-bar-track">
                    <div class="category-bar-fill" style="width: ${percent}%"></div>
                </div>
            `;

            categoryBox.appendChild(row);

        });

    }


    const txnResponse =
        await fetch(
            "/api/transactions?limit=5",
            {
                headers:{
                    "Authorization":
                    `Bearer ${token}`
                }
            }
        );


    const transactions =
        await txnResponse.json();


    const box =
        document.getElementById("transactions");


    box.innerHTML="";


    if(transactions.length === 0){

        box.innerText = "No transactions yet";

    }

    else{

        transactions.forEach(txn=>{

            const row = document.createElement("div");
            row.className = "txn-row";

            const sign = txn.type === "income" ? "+" : "-";

            row.innerHTML = `
                <div class="txn-dot ${txn.type}"></div>
                <div class="txn-details">
                    <div class="txn-category">${txn.category}</div>
                    <div class="txn-meta">${txn.date} · ${txn.description}</div>
                </div>
                <div class="txn-amount ${txn.type}">${sign}₨ ${txn.amount.toLocaleString()}</div>
            `;

            box.appendChild(row);

        });

        const viewAllLink = document.createElement("a");
            viewAllLink.href = "/transactions";
            viewAllLink.className = "view-all-link";
            viewAllLink.innerText = "View all transactions →";
            box.appendChild(viewAllLink);

    }

}

function openChat(){

    window.location.href="/chat";

}

function logout(){

    localStorage.removeItem("token");
    localStorage.removeItem("activeConversationId");

    showToast("Logged out successfully", "info");

    setTimeout(() => {
        window.location.href="/";
    }, 600);

}

async function signup(){

    const username =
        document.getElementById("username").value;

    const email =
        document.getElementById("signup-email").value;

    const password =
        document.getElementById("signup-password").value;

    // Clear old errors before this attempt
    document.getElementById("username-error").innerText = "";
    document.getElementById("email-error").innerText = "";
    document.getElementById("password-error").innerText = "";
    document.getElementById("signup-error").innerText = "";


    const response = await fetch(
        "/api/auth/signup",
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                username,
                email,
                password
            })
        }
    );


    const data =
        await response.json();


    if(response.ok){

        showToast("Account created successfully!", "success");

        setTimeout(() => {
            window.location.href="/";
        }, 1000);

    }

    else{

        if(Array.isArray(data.detail)){

            const fieldErrorMap = {
                "username": "username-error",
                "email": "email-error",
                "password": "password-error"
            };

            data.detail.forEach(err => {
                const field = err.loc[err.loc.length - 1];
                const elementId = fieldErrorMap[field];

                if(elementId){
                    const cleanMsg = err.msg.replace(/^Value error,\s*/, "");
                    document.getElementById(elementId).innerText = cleanMsg;
                }
            });

        }

        else{

            document.getElementById("signup-error").innerText =
                data.detail;

        }

    }
}

function togglePassword(id, button) {

    const input = document.getElementById(id);

    if (input.type === "password") {

        input.type = "text";

        button.innerHTML = `
        <svg 
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round">
            <path d="M17.94 17.94A10.94 10.94 0 0 1 12 20c-7 0-10-8-10-8a18.45 18.45 0 0 1 5.06-5.94"/>
            <path d="M1 1l22 22"/>
            <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/>
        </svg>`;

    } else {

        input.type = "password";

        button.innerHTML = `
        <svg 
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round">
            <path d="M2.5 12s3.5-7 9.5-7 9.5 7 9.5 7-3.5 7-9.5 7-9.5-7-9.5-7z"/>
            <circle cx="12" cy="12" r="3"/>
        </svg>`;

    }

}

async function loadAllTransactions(){

    const token = localStorage.getItem("token");

    const box = document.getElementById("all-transactions");

    try {

        const txnResponse = await fetch(
            "/api/transactions?limit=1000",
            {
                headers:{
                    "Authorization": `Bearer ${token}`
                }
            }
        );

        const transactions = await txnResponse.json();

        box.innerHTML = "";

        let totalIncome = 0;
        let totalExpenses = 0;


        if(transactions.length === 0){

            box.innerHTML = `
                <div class="empty-state">
                    No transactions yet
                </div>
            `;

        }

        else{

            transactions.forEach(txn => {

                const amount = Number(txn.amount);

                if(txn.type === "income"){
                    totalIncome += amount;
                }
                else{
                    totalExpenses += amount;
                }


                const row = document.createElement("div");

                row.className = "txn-row";


                const sign = txn.type === "income" ? "+" : "-";


                row.innerHTML = `
                    <div class="txn-dot ${txn.type}"></div>

                    <div class="txn-details">
                        <div class="txn-category">
                            ${txn.category}
                        </div>

                        <div class="txn-meta">
                            ${txn.date} · ${txn.description}
                        </div>
                    </div>

                    <div class="txn-amount ${txn.type}">
                        ${sign}₨ ${amount.toLocaleString()}
                    </div>
                `;


                box.appendChild(row);

            });

        }


        // Update summary cards if they exist
        const incomeElement = document.getElementById("total-income");
        const expenseElement = document.getElementById("total-expenses");


        if(incomeElement){
            incomeElement.innerText =
                `₨ ${totalIncome.toLocaleString()}`;
        }


        if(expenseElement){
            expenseElement.innerText =
                `₨ ${totalExpenses.toLocaleString()}`;
        }


    } catch(error){

        console.error("Failed to load transactions:", error);

        box.innerText =
            "Unable to load transactions";

    }

}

if (
    window.location.pathname === "/dashboard" ||
    window.location.pathname === "/chat" ||
    window.location.pathname === "/transactions"
) {
    requireAuth();
}

const welcomeMessage = "Welcome back.\n\nI'm Nisaab, your personal finance assistant. You can ask me about your balance, expenses, transactions, or budgeting.";

async function initializeChat() {
    const token = localStorage.getItem("token");
    const sendBtn = document.getElementById("send-btn");
    if (!token)
        return;

    if (sendBtn)
        sendBtn.disabled = true;

    try {
        await loadConversations();
        const activeConversationId = localStorage.getItem("activeConversationId");

        if (activeConversationId) {
            await selectConversation(Number(activeConversationId));
        } else {
            await createNewChat();
        }
    } catch (error) {
        console.error(error);
        await renderChatHistory([]);
    } finally {
        if (sendBtn)
            sendBtn.disabled = false;
    }
}

async function loadConversations() {
    const list = document.getElementById("conversation-list");
    const token = localStorage.getItem("token");

    if (!list || !token)
        return;

    const response = await fetch("/api/chat/conversations", {
        headers: { "Authorization": `Bearer ${token}` }
    });

    if (!response.ok)
        throw new Error("Could not load conversations");

    const conversations = await response.json();
    const activeConversationId = Number(localStorage.getItem("activeConversationId"));
    list.replaceChildren();
    
    conversations.forEach(conversation => {
    const row = document.createElement("div");
    row.className = "conversation-row";

    const button = document.createElement("button");
    button.type = "button";
    button.className = "conversation-item";
    button.textContent = conversation.title;
    button.title = conversation.title;

    if (conversation.id === activeConversationId)
        button.classList.add("active");

    button.addEventListener(
        "click",
        () => selectConversation(conversation.id)
    );

    row.appendChild(button);

    const deleteButton = document.createElement("button");
    deleteButton.type = "button";
    deleteButton.className = "conversation-delete";
    deleteButton.setAttribute(
        "aria-label",
        `Delete ${conversation.title}`
    );
    deleteButton.textContent = "×";

    deleteButton.addEventListener(
        "click",
        () => deleteConversation(conversation)
    );

    row.appendChild(deleteButton);

    list.appendChild(row);
})};


function conversationDateGroup(updatedAt) {
    const date = new Date(updatedAt);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const weekAgo = new Date(today);
    weekAgo.setDate(weekAgo.getDate() - 7);

    if (date >= today)
        return "Today";
    if (date >= yesterday)
        return "Yesterday";
    if (date >= weekAgo)
        return "Previous 7 Days";
    return "Older";
}

async function createNewChat() {
    const token = localStorage.getItem("token");
    const sendBtn = document.getElementById("send-btn");
    if (!token)
        return;

    if (sendBtn)
        sendBtn.disabled = true;

    try {
        const response = await fetch("/api/chat/conversations", {
            method: "POST",
            headers: { "Authorization": `Bearer ${token}` }
        });
        if (!response.ok)
            throw new Error("Could not create conversation");

        if (window.innerWidth <= 800) {
            const sidebar = document.querySelector(".chat-sidebar");
            if (sidebar) sidebar.classList.remove("open");
        }

        const conversation = await response.json();
        localStorage.setItem("activeConversationId", conversation.id);
        await renderChatHistory([]);
        await loadConversations();
    } catch (error) {
        console.error(error);
    } finally {
        if (sendBtn)
            sendBtn.disabled = false;
    }
}

async function selectConversation(conversationId) {
    const token = localStorage.getItem("token");
    if (!token)
        return;

    if (window.innerWidth <= 800) {
        const sidebar = document.querySelector(".chat-sidebar");
        if (sidebar) sidebar.classList.remove("open");
    }

    const response = await fetch(
        `/api/chat/conversations/${conversationId}/messages`,
        { headers: { "Authorization": `Bearer ${token}` } }
    );

    if (!response.ok) {
        localStorage.removeItem("activeConversationId");
        await createNewChat();
        return;
    }

    localStorage.setItem("activeConversationId", conversationId);
    await renderChatHistory(await response.json());
    await loadConversations();
}

function showToast(message, type = "info") {
    let container = document.querySelector(".toast-container");
    if (!container) {
        container = document.createElement("div");
        container.className = "toast-container";
        document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    
    const iconMap = {
        success: "✓",
        error: "✕",
        info: "ℹ"
    };

    toast.innerHTML = `
        <span class="toast-icon">${iconMap[type] || "ℹ"}</span>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateY(-10px) scale(0.95)";
        setTimeout(() => toast.remove(), 200);
    }, 3200);
}

function showConfirmModal(title, message, confirmText = "Delete", cancelText = "Cancel") {
    return new Promise((resolve) => {
        let backdrop = document.querySelector(".confirm-modal-backdrop");
        if (!backdrop) {
            backdrop = document.createElement("div");
            backdrop.className = "confirm-modal-backdrop";
            backdrop.innerHTML = `
                <div class="confirm-modal">
                    <h3 id="modal-title"></h3>
                    <p id="modal-desc"></p>
                    <div class="confirm-actions">
                        <button type="button" class="btn-secondary" id="modal-cancel-btn"></button>
                        <button type="button" class="btn-danger" id="modal-confirm-btn"></button>
                    </div>
                </div>
            `;
            document.body.appendChild(backdrop);
        }

        document.getElementById("modal-title").innerText = title;
        document.getElementById("modal-desc").innerText = message;
        
        const cancelBtn = document.getElementById("modal-cancel-btn");
        const confirmBtn = document.getElementById("modal-confirm-btn");
        
        cancelBtn.innerText = cancelText;
        confirmBtn.innerText = confirmText;

        backdrop.classList.add("open");

        function cleanup(result) {
            backdrop.classList.remove("open");
            cancelBtn.onclick = null;
            confirmBtn.onclick = null;
            resolve(result);
        }

        cancelBtn.onclick = () => cleanup(false);
        confirmBtn.onclick = () => cleanup(true);
        backdrop.onclick = (e) => {
            if (e.target === backdrop) cleanup(false);
        };
    });
}

async function deleteConversation(conversation) {
    const confirmed = await showConfirmModal(
        "Delete Conversation",
        `Are you sure you want to delete “${conversation.title}”? This action cannot be undone.`,
        "Delete",
        "Cancel"
    );
    if (!confirmed) return;

    const token = localStorage.getItem("token");
    const response = await fetch(
        `/api/chat/conversations/${conversation.id}`,
        {
            method: "DELETE",
            headers: { "Authorization": `Bearer ${token}` }
        }
    );

    if (!response.ok) {
        showToast("Could not delete conversation", "error");
        return;
    }

    showToast("Conversation deleted", "info");

    if (Number(localStorage.getItem("activeConversationId")) === conversation.id) {
        localStorage.removeItem("activeConversationId");
        await createNewChat();
    } else {
        await loadConversations();
    }
}

async function renderChatHistory(history) {

    const box = document.getElementById("messages");
    if (!box)
        return;
    box.replaceChildren();

    if (!history.length) {
        addMessage(welcomeMessage, "bot");

        const chipsContainer = document.createElement("div");
        chipsContainer.className = "prompt-chips-container";

        const prompts = [
            "💡 Show my monthly spending summary",
            "📊 What is my highest expense category?",
            "💰 How can I save money this week?"
        ];

        prompts.forEach(promptText => {
            const chip = document.createElement("button");
            chip.type = "button";
            chip.className = "prompt-chip";
            chip.textContent = promptText;
            chip.onclick = () => {
                const input = document.getElementById("message");
                if (input) {
                    input.value = promptText.replace(/^[^\w\s]+\s*/, "");
                    sendMessage();
                }
            };
            chipsContainer.appendChild(chip);
        });

        box.appendChild(chipsContainer);
        return;
    }

    history.forEach(message => addMessage(
        message.content,
        message.role === "assistant" ? "bot" : "user"
    ));
}

// Global Keyboard Shortcuts
window.addEventListener("keydown", (e) => {
    // Ctrl+K or Cmd+K or '/' (when not typing in an input) to focus chat textarea
    if (((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") || (e.key === "/" && document.activeElement.tagName !== "INPUT" && document.activeElement.tagName !== "TEXTAREA")) {
        const chatInput = document.getElementById("message");
        if (chatInput) {
            e.preventDefault();
            chatInput.focus();
        }
    }

    // Escape to close chat sidebar
    if (e.key === "Escape") {
        const sidebar = document.querySelector(".chat-sidebar");
        if (sidebar && sidebar.classList.contains("open")) {
            sidebar.classList.remove("open");
            const toggle = document.getElementById("chat-history-toggle");
            if (toggle) toggle.setAttribute("aria-expanded", "false");
        }
    }
});
