let currentData = null;

function onScanSuccess(decodedText) {
    const obj = JSON.parse(decodedText);

    const currentTime = Date.now();

    // 60 sec validation
    if (currentTime - obj.time > 60000) {
        alert("QR Expired ❌");
        return;
    }

    currentData = obj;

    document.getElementById("result").innerHTML = `
    <h3>Roll: ${obj.roll}</h3>
  `;
}

new Html5QrcodeScanner("reader", { fps: 10 }).render(onScanSuccess);

function entry() {
    sendData("Entry");
}

function exit() {
    sendData("Exit");
}

function sendData(type) {
    fetch("YOUR_SCRIPT_URL", {
        method: "POST",
        body: JSON.stringify({
            roll: currentData.roll,
            type: type,
            guard: localStorage.getItem("guardName")
        })
    });

    alert(type + " Logged ✅");
}