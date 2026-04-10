function setText(id, value) {
    const node = document.getElementById(id);
    if (node) {
        node.textContent = value ?? "";
    }
}

function showMessage(id, message, type = "info") {
    const node = document.getElementById(id);
    if (!node) {
        return;
    }

    node.className = `message ${type}`;
    node.textContent = message;
}

function formatDateTime(date, time) {
    return `${date} ${time}`;
}

function persistJson(key, value) {
    localStorage.setItem(key, JSON.stringify(value));
}

function readJson(key) {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : null;
}

function clearKeys(keys) {
    keys.forEach((key) => localStorage.removeItem(key));
}
