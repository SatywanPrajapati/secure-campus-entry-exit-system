const studentSession = readJson("studentSession");
let qrIntervalId = null;
let countdownId = null;

if (!studentSession) {
    window.location.href = "login.html";
}

function renderStudentProfile(student) {
    setText("studentNameHeading", `${student.name} QR Pass`);
    setText("studentName", student.name);
    setText("studentCollegeId", student.college_id);
    setText("studentRollNumber", student.roll_number);
    setText("studentCourse", student.course);
    setText("studentValidity", student.validity);
    setText("studentPhone", student.phone);
    setText("studentEmail", student.email);
    document.getElementById("studentPhoto").src = student.photo_url;
    document.getElementById("studentSignature").src = student.signature_url;
}

function startCountdown(expiresAt) {
    clearInterval(countdownId);
    const timerNode = document.getElementById("qrTimer");

    const updateTimer = () => {
        const remaining = Math.max(0, expiresAt - Math.floor(Date.now() / 1000));
        timerNode.textContent = `${remaining}s`;
    };

    updateTimer();
    countdownId = setInterval(updateTimer, 1000);
}

async function loadQrCode() {
    try {
        const response = await apiRequest(`/api/student/${studentSession.college_id}/qr`);
        await QRCode.toCanvas(document.getElementById("qrCanvas"), response.token, {
            width: 250,
            margin: 1
        });
        persistJson("latestQr", { token: response.token, expires_at: response.expires_at });
        startCountdown(response.expires_at);
        showMessage("qrMessage", "Dynamic QR generated successfully.", "success");
    } catch (error) {
        showMessage("qrMessage", error.message, "error");
    }
}

renderStudentProfile(studentSession);
loadQrCode();
qrIntervalId = setInterval(loadQrCode, window.APP_CONFIG.qrRefreshMs);

document.getElementById("refreshQrButton").addEventListener("click", loadQrCode);
document.getElementById("studentLogoutButton").addEventListener("click", () => {
    clearInterval(qrIntervalId);
    clearInterval(countdownId);
    clearKeys(["studentSession", "latestQr"]);
    window.location.href = "login.html";
});
