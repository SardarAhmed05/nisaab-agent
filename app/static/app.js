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



    addMessage(
        data.response,
        "bot"
    );

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


    div.innerText =
        text;


    box.appendChild(div);


    box.scrollTop =
        box.scrollHeight;

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


    document.getElementById("email")
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
    `₨ ${analytics.balance.toLocaleString()}`;


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
            "/api/transactions",
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