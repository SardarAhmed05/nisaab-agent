function requireAuth(){

    const token = localStorage.getItem("token");

    if(!token){
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