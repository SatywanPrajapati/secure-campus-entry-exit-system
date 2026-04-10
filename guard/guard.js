const guardSession = readJson("guardSession");
let scannedToken = "";
let previewData = null;

if (!guardSession) {
    window.location.href = "login.html";
}

document.getElementById("guardWelcome").textContent = `Welcome, ${guardSession.name}`;
document.getElementById("guardPhoto").src = guardSession.photo_url;
setText("guardName", guardSession.name);
setText("guardIdValue", guardSession.guard_id);
setText("guardEmail", guardSession.email);
setText("guardPhone", guardSession.phone);
document.getElementById("previewPhoto").src = "https://placehold.co/240x300/png?text=No+Scan";
document.getElementById("previewSignature").src = "https://placehold.co/240x80/png?text=No+Signature";

function updateApprovalButton() {
    const accepted = document.getElementById("termsAccepted").checked;
    document.getElementById("approveButton").disabled = !(accepted && previewData && scannedToken);
}

function renderPreview(student, nextAction) {
    previewData = student;
    setText("previewName", student.name);
    setText("previewCollegeId", student.college_id);
    setText("previewRoll", student.roll_number);
    setText("previewCourse", student.course);
    setText("previewValidity", student.validity);
    setText("previewPhone", student.phone);
    setText("previewNextAction", nextAction);
    document.getElementById("previewPhoto").src = student.photo_url;
    document.getElementById("previewSignature").src = student.signature_url;
    document.getElementById("attendanceAction").value = nextAction;
    Array.from(document.getElementById("attendanceAction").options).forEach((option) => {
        option.disabled = option.value !== nextAction;
    });
    updateApprovalButton();
}

async function previewToken(token) {
    if (!token) {
        showMessage("scanMessage", "QR token missing.", "error");
        return;
    }

    try {
        const response = await apiRequest("/api/scan/preview", {
            method: "POST",
            body: JSON.stringify({ token })
        });
        scannedToken = token;
        renderPreview(response.student, response.next_action);
        showMessage("scanMessage", response.message, "success");
        showMessage("approvalMessage", "Student details loaded. Guard can now approve attendance.", "info");
    } catch (error) {
        previewData = null;
        scannedToken = "";
        updateApprovalButton();
        showMessage("scanMessage", error.message, "error");
    }
}

function onScanSuccess(decodedText) {
    document.getElementById("manualToken").value = decodedText;
    previewToken(decodedText);
}

if (window.Html5QrcodeScanner) {
    const scanner = new Html5QrcodeScanner("reader", { fps: 10, qrbox: 220 }, false);
    scanner.render(onScanSuccess, () => {});
}

document.getElementById("manualPreviewButton").addEventListener("click", () => {
    previewToken(document.getElementById("manualToken").value.trim());
});

document.getElementById("termsAccepted").addEventListener("change", updateApprovalButton);

document.getElementById("approveButton").addEventListener("click", async () => {
    const action = document.getElementById("attendanceAction").value;
    const note = document.getElementById("attendanceNote").value.trim();
    const accepted = document.getElementById("termsAccepted").checked;

    try {
        const response = await apiRequest("/api/attendance", {
            method: "POST",
            body: JSON.stringify({
                token: scannedToken,
                guard_id: guardSession.guard_id,
                action,
                note,
                accepted
            })
        });
        showMessage("approvalMessage", response.message, "success");
        showMessage("scanMessage", `Next allowed action: ${response.next_action}`, "info");
        document.getElementById("termsAccepted").checked = false;
        updateApprovalButton();
    } catch (error) {
        showMessage("approvalMessage", error.message, "error");
    }
});

document.getElementById("guardLogoutButton").addEventListener("click", () => {
    clearKeys(["guardSession"]);
    window.location.href = "login.html";
});
