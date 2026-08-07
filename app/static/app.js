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


        window.location.href="/dashboard";

    }

    else {

        document.getElementById("error").innerText =
            data.detail;

    }

}

async function sendMessage(){


    const input =
        document.getElementById("message");


    const text = input.value;


    if(!text)
        return;



    addMessage(
        text,
        "user"
    );


    input.value="";


    showTypingIndicator();


    const token =
        localStorage.getItem("token");



    const response = await fetch(
        "/api/chat",
        {

            method:"POST",

            headers:{

                "Content-Type":"application/json",

                "Authorization":
                    `Bearer ${token}`

            },


            body:JSON.stringify({

                message:text

            })

        }
    );



    const data =
        await response.json();


    hideTypingIndicator();


    addMessage(
        data.response,
        "bot"
    );

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


    const div =
        document.createElement("div");


    div.className =
        `${type} message`;


    div.innerHTML =
        formatMessage(text);


    box.appendChild(div);


    box.scrollTop =
        box.scrollHeight;

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

    window.location.href="/";

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

        alert("Account created successfully!");

        window.location.href="/";

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

function togglePassword(inputId, button){

    const input =
        document.getElementById(inputId);

    if(input.type === "password"){
        input.type = "text";
        button.innerText = "🙈";
    }
    else{
        input.type = "password";
        button.innerText = "👁";
    }

}

async function loadAllTransactions(){

    const token =
        localStorage.getItem("token");

    const txnResponse =
        await fetch(
            "/api/transactions?limit=1000",
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
        document.getElementById("all-transactions");

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

    }

}