const adminSession = readJson("adminSession");

if (!adminSession) {
    window.location.href = "login.html";
}

function metricCard(label, value, hint) {
    return `
        <article class="metric">
            <span class="muted">${label}</span>
            <strong>${value}</strong>
            <div class="muted">${hint}</div>
        </article>
    `;
}

function renderTableRows(targetId, rows) {
    document.getElementById(targetId).innerHTML = rows.join("");
}

async function loadDashboard() {
    const response = await apiRequest("/api/admin/dashboard");
    const { summary, students, guards, attendance } = response.data;

    document.getElementById("metrics").innerHTML = [
        metricCard("Total Students", summary.students, "Registered in student master data"),
        metricCard("Total Guards", summary.guards, "Main gate guard profiles"),
        metricCard("Today's Entries", summary.today_entries, "Students marked IN today"),
        metricCard("Today's Exits", summary.today_exits, "Students marked OUT today"),
        metricCard("Today's Total Logs", summary.today_total, "Combined gate movement records")
    ].join("");

    renderTableRows("attendanceTableBody", attendance.map((item) => `
        <tr>
            <td>${item.student_name}<br><span class="muted">${item.student_college_id}</span></td>
            <td>${item.roll_number}</td>
            <td><span class="status-pill ${item.action.toLowerCase()}">${item.action}</span></td>
            <td>${formatDateTime(item.date, item.time)}</td>
            <td>${item.phone}</td>
            <td>${item.guard_name}<br><span class="muted">${item.guard_id}</span></td>
            <td>${item.guard_phone}</td>
            <td>${item.note || "-"}</td>
        </tr>
    `));

    renderTableRows("studentsTableBody", students.map((item) => `
        <tr>
            <td>${item.name}</td>
            <td>${item.college_id}</td>
            <td>${item.roll_number}</td>
            <td>${item.course}</td>
            <td>${item.validity}</td>
            <td>${item.phone}</td>
        </tr>
    `));

    renderTableRows("guardsTableBody", guards.map((item) => `
        <tr>
            <td>${item.guard_id}</td>
            <td>${item.name}</td>
            <td>${item.email}</td>
            <td>${item.phone}</td>
        </tr>
    `));
}

loadDashboard().catch((error) => {
    alert(error.message);
});

document.getElementById("adminLogoutButton").addEventListener("click", () => {
    clearKeys(["adminSession"]);
    window.location.href = "login.html";
});
