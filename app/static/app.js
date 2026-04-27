const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const assignRoleForm = document.getElementById("assign-role-form");
const messageBox = document.getElementById("message");
const tabs = document.querySelectorAll(".tab");
const forms = document.querySelectorAll(".auth-form");
const profileCard = document.getElementById("profile-card");
const profileName = document.getElementById("profile-name");
const profileEmail = document.getElementById("profile-email");
const roleBadge = document.getElementById("role-badge");
const roleDescription = document.getElementById("role-description");
const logoutButton = document.getElementById("logout-button");
const adminPanel = document.getElementById("admin-panel");

const TOKEN_KEY = "trading_app_token";

function showMessage(text, type = "") {
    messageBox.textContent = text;
    messageBox.className = `message ${type}`.trim();
}

function setActiveTab(tabName) {
    tabs.forEach((tab) => {
        tab.classList.toggle("active", tab.dataset.tab === tabName);
    });

    forms.forEach((form) => {
        if (form.id === "assign-role-form") {
            return;
        }
        form.classList.toggle("active", form.id === `${tabName}-form`);
    });

    showMessage("");
}

function saveToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
}

function readToken() {
    return localStorage.getItem(TOKEN_KEY);
}

function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
}

function roleText(role) {
    if (role === "admin") {
        return "Administrator access: you can grant moderator roles.";
    }
    if (role === "moderator") {
        return "Moderator access: you can remove fake cards.";
    }
    return "User access: you can create cards and trade them.";
}

function protectAdminRoute(user) {
    if (window.location.pathname !== "/admin") {
        return;
    }

    if (!user || user.role !== "admin") {
        window.location.replace("/");
    }
}

function renderProfile(user) {
    protectAdminRoute(user);
    profileName.textContent = user.username;
    profileEmail.textContent = user.email;
    roleBadge.textContent = user.role;
    roleBadge.className = `badge ${user.role}`;
    roleDescription.textContent = roleText(user.role);
    profileCard.classList.remove("hidden");
    adminPanel.classList.toggle("hidden", user.role !== "admin");
    showMessage(`Signed in as ${user.role}.`, "success");
}

function resetProfile() {
    profileCard.classList.add("hidden");
    adminPanel.classList.add("hidden");
}

async function fetchCurrentUser() {
    const token = readToken();
    if (!token) {
        resetProfile();
        protectAdminRoute(null);
        return null;
    }

    const response = await fetch("/auth/me", {
        headers: {
            Authorization: `Bearer ${token}`
        }
    });

    if (!response.ok) {
        clearToken();
        resetProfile();
        protectAdminRoute(null);
        return null;
    }

    const user = await response.json();
    renderProfile(user);
    return user;
}

tabs.forEach((tab) => {
    tab.addEventListener("click", () => setActiveTab(tab.dataset.tab));
});

loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(loginForm).entries());

    const response = await fetch("/auth/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    });

    const data = await response.json();
    if (!response.ok) {
        showMessage(data.detail || "Unable to sign in.", "error");
        return;
    }

    saveToken(data.access_token);
    const user = await fetchCurrentUser();
    if (user && user.role === "admin" && window.location.pathname === "/") {
        window.location.replace("/admin");
    }
});

registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(registerForm).entries());

    const response = await fetch("/auth/register", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    });

    const data = await response.json();
    if (!response.ok) {
        showMessage(data.detail || "Unable to create account.", "error");
        return;
    }

    showMessage(`Account ${data.username} was created with the user role. Now sign in.`, "success");
    registerForm.reset();
    setActiveTab("login");
});

logoutButton.addEventListener("click", () => {
    clearToken();
    resetProfile();
    showMessage("Signed out.");
    if (window.location.pathname === "/admin") {
        window.location.replace("/");
    }
});

assignRoleForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const token = readToken();
    if (!token) {
        showMessage("Sign in as administrator first.", "error");
        return;
    }

    const payload = {
        email: new FormData(assignRoleForm).get("email"),
        role: "moderator"
    };

    const response = await fetch("/api/admin/assign-role", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(payload)
    });

    const data = await response.json();
    if (!response.ok) {
        showMessage(data.detail || "Unable to grant moderator access.", "error");
        return;
    }

    showMessage(`User ${data.username} is now a moderator.`, "success");
    assignRoleForm.reset();
});

fetchCurrentUser();
