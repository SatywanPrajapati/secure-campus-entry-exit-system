const API_BASE_URL = window.APP_CONFIG?.apiBaseUrl || "";

async function apiRequest(path, options = {}) {
    const config = {
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {})
        },
        ...options
    };

    const response = await fetch(`${API_BASE_URL}${path}`, config);
    const data = await response.json().catch(() => ({}));

    if (!response.ok || data.ok === false) {
        throw new Error(data.message || "Request failed.");
    }

    return data;
}
