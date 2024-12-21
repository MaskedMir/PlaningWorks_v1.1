document.getElementById("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    const response = await fetch("http://localhost:8000/auth/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
    });

    const errorMessage = document.getElementById("errorMessage");
    if (response.ok) {
        alert("Login successful!");
    } else {
        const errorData = await response.json();
        errorMessage.innerText = errorData.detail;
    }
});
