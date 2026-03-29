function generateQR() {
    const roll = localStorage.getItem("studentRoll");

    const data = JSON.stringify({
        roll: roll,
        time: Date.now()
    });

    QRCode.toCanvas(document.getElementById("qr"), data);
}

// Auto refresh every 60 sec
generateQR();
setInterval(generateQR, 60000);