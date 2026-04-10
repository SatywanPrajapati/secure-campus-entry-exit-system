from __future__ import annotations

import base64
import csv
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from flask import Flask, jsonify, request, send_file, send_from_directory


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
STUDENTS_FILE = DATA_DIR / "students.csv"
GUARDS_FILE = DATA_DIR / "guards.csv"
ATTENDANCE_FILE = DATA_DIR / "attendance.csv"
SECRET_KEY = "iit-patna-main-gate-secret"
QR_VALIDITY_SECONDS = 60
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"

app = Flask(__name__, static_folder=str(BASE_DIR), static_url_path="")

STUDENT_HEADERS = [
    "college_id",
    "roll_number",
    "name",
    "course",
    "validity",
    "phone",
    "email",
    "photo_url",
    "signature_url",
]
GUARD_HEADERS = ["guard_id", "name", "email", "phone", "photo_url"]
ATTENDANCE_HEADERS = [
    "attendance_id",
    "student_college_id",
    "student_name",
    "roll_number",
    "course",
    "phone",
    "action",
    "note",
    "guard_id",
    "guard_name",
    "guard_phone",
    "date",
    "time",
    "timestamp",
]


@dataclass
class ScanState:
    allowed_actions: List[str]
    next_action: str
    message: str


def read_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_csv(path: Path, headers: List[str], rows: List[Dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def append_csv(path: Path, headers: List[str], row: Dict[str, str]) -> None:
    with path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        writer.writerow(row)


def ensure_data_files() -> None:
    DATA_DIR.mkdir(exist_ok=True)

    if not STUDENTS_FILE.exists():
        write_csv(
            STUDENTS_FILE,
            STUDENT_HEADERS,
            [
                {
                    "college_id": "IITP2024001",
                    "roll_number": "2401CS01",
                    "name": "Aarav Kumar",
                    "course": "B.Tech CSE",
                    "validity": "2028-05-31",
                    "phone": "9876543210",
                    "email": "aarav.kumar@iitp.ac.in",
                    "photo_url": "https://placehold.co/240x300/png?text=Aarav",
                    "signature_url": "https://placehold.co/240x80/png?text=Signature",
                },
                {
                    "college_id": "IITP2024002",
                    "roll_number": "2401EE08",
                    "name": "Sneha Singh",
                    "course": "B.Tech EEE",
                    "validity": "2028-05-31",
                    "phone": "9123456780",
                    "email": "sneha.singh@iitp.ac.in",
                    "photo_url": "https://placehold.co/240x300/png?text=Sneha",
                    "signature_url": "https://placehold.co/240x80/png?text=Signature",
                },
                {
                    "college_id": "IITP2024003",
                    "roll_number": "2401ME05",
                    "name": "Rohit Raj",
                    "course": "B.Tech Mechanical",
                    "validity": "2028-05-31",
                    "phone": "9988776655",
                    "email": "rohit.raj@iitp.ac.in",
                    "photo_url": "https://placehold.co/240x300/png?text=Rohit",
                    "signature_url": "https://placehold.co/240x80/png?text=Signature",
                },
            ],
        )

    if not GUARDS_FILE.exists():
        write_csv(
            GUARDS_FILE,
            GUARD_HEADERS,
            [
                {
                    "guard_id": "GRD-101",
                    "name": "Manoj Kumar",
                    "email": "manoj.guard@iitp.ac.in",
                    "phone": "9000000001",
                    "photo_url": "https://placehold.co/200x220/png?text=Guard+1",
                },
                {
                    "guard_id": "GRD-102",
                    "name": "Rakesh Yadav",
                    "email": "rakesh.guard@iitp.ac.in",
                    "phone": "9000000002",
                    "photo_url": "https://placehold.co/200x220/png?text=Guard+2",
                },
            ],
        )

    if not ATTENDANCE_FILE.exists():
        write_csv(ATTENDANCE_FILE, ATTENDANCE_HEADERS, [])


def sign_value(value: str) -> str:
    return hmac.new(SECRET_KEY.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def encode_qr_payload(payload: Dict[str, str]) -> str:
    json_payload = json.dumps(payload, separators=(",", ":"))
    return base64.urlsafe_b64encode(json_payload.encode("utf-8")).decode("utf-8")


def decode_qr_payload(token: str) -> Dict[str, str]:
    decoded = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
    return json.loads(decoded)


def get_student_by_college_id(college_id: str) -> Optional[Dict[str, str]]:
    for student in read_csv(STUDENTS_FILE):
        if student["college_id"].lower() == college_id.lower():
            return student
    return None


def get_guard_by_id(guard_id: str) -> Optional[Dict[str, str]]:
    for guard in read_csv(GUARDS_FILE):
        if guard["guard_id"].lower() == guard_id.lower():
            return guard
    return None


def get_attendance_logs() -> List[Dict[str, str]]:
    return sorted(read_csv(ATTENDANCE_FILE), key=lambda item: item["timestamp"], reverse=True)


def get_last_student_action(student_college_id: str) -> Optional[str]:
    for log in get_attendance_logs():
        if log["student_college_id"] == student_college_id:
            return log["action"]
    return None


def build_scan_state(student_college_id: str) -> ScanState:
    last_action = get_last_student_action(student_college_id)
    if last_action == "IN":
        return ScanState(["OUT"], "OUT", "Student is already inside campus. Only OUT can be approved now.")
    return ScanState(["IN"], "IN", "Student can be marked IN for a fresh entry.")


def verify_qr_token(token: str) -> Dict[str, str]:
    try:
        payload = decode_qr_payload(token)
    except Exception as exc:  # noqa: BLE001
        raise ValueError("Invalid QR format.") from exc

    signature = payload.get("signature", "")
    college_id = payload.get("college_id", "")
    expires_at = payload.get("expires_at", "")
    issued_at = payload.get("issued_at", "")
    expected = sign_value(f"{college_id}|{issued_at}|{expires_at}")

    if not college_id or not expires_at or not issued_at or not signature:
        raise ValueError("QR payload is incomplete.")
    if not hmac.compare_digest(signature, expected):
        raise ValueError("QR signature verification failed.")
    if int(expires_at) < int(datetime.now().timestamp()):
        raise ValueError("QR expired. Ask the student to refresh the QR.")

    student = get_student_by_college_id(college_id)
    if not student:
        raise ValueError("Student not found for scanned QR.")
    return student


def student_public_data(student: Dict[str, str]) -> Dict[str, str]:
    return {
        "college_id": student["college_id"],
        "roll_number": student["roll_number"],
        "name": student["name"],
        "course": student["course"],
        "validity": student["validity"],
        "phone": student["phone"],
        "email": student["email"],
        "photo_url": student["photo_url"],
        "signature_url": student["signature_url"],
    }


@app.get("/")
def index() -> object:
    return send_from_directory(BASE_DIR, "index.html")


@app.post("/api/student/login")
def student_login() -> object:
    payload = request.get_json(silent=True) or {}
    college_id = (payload.get("college_id") or "").strip()
    student = get_student_by_college_id(college_id)
    if not student:
        return jsonify({"ok": False, "message": "College ID not found."}), 404
    return jsonify({"ok": True, "student": student_public_data(student)})


@app.get("/api/student/<college_id>/qr")
def student_qr(college_id: str) -> object:
    student = get_student_by_college_id(college_id)
    if not student:
        return jsonify({"ok": False, "message": "Student not found."}), 404

    issued_at = int(datetime.now().timestamp())
    expires_at = issued_at + QR_VALIDITY_SECONDS
    signature = sign_value(f"{student['college_id']}|{issued_at}|{expires_at}")
    token = encode_qr_payload(
        {
            "college_id": student["college_id"],
            "issued_at": str(issued_at),
            "expires_at": str(expires_at),
            "signature": signature,
        }
    )
    return jsonify(
        {
            "ok": True,
            "token": token,
            "expires_at": expires_at,
            "validity_seconds": QR_VALIDITY_SECONDS,
            "student": student_public_data(student),
        }
    )


@app.post("/api/guard/login")
def guard_login() -> object:
    payload = request.get_json(silent=True) or {}
    guard_id = (payload.get("guard_id") or "").strip()
    guard = get_guard_by_id(guard_id)
    if not guard:
        return jsonify({"ok": False, "message": "Guard ID not found."}), 404
    return jsonify({"ok": True, "guard": guard})


@app.post("/api/scan/preview")
def scan_preview() -> object:
    payload = request.get_json(silent=True) or {}
    token = payload.get("token") or ""
    try:
        student = verify_qr_token(token)
    except ValueError as error:
        return jsonify({"ok": False, "message": str(error)}), 400

    state = build_scan_state(student["college_id"])
    return jsonify(
        {
            "ok": True,
            "student": student_public_data(student),
            "allowed_actions": state.allowed_actions,
            "next_action": state.next_action,
            "message": state.message,
        }
    )


@app.post("/api/attendance")
def attendance() -> object:
    payload = request.get_json(silent=True) or {}
    token = payload.get("token") or ""
    guard_id = (payload.get("guard_id") or "").strip()
    action = (payload.get("action") or "").strip().upper()
    note = (payload.get("note") or "").strip()
    accepted = bool(payload.get("accepted"))

    if not accepted:
        return jsonify({"ok": False, "message": "Terms must be accepted by guard."}), 400

    guard = get_guard_by_id(guard_id)
    if not guard:
        return jsonify({"ok": False, "message": "Guard not found."}), 404

    try:
        student = verify_qr_token(token)
    except ValueError as error:
        return jsonify({"ok": False, "message": str(error)}), 400

    state = build_scan_state(student["college_id"])
    if action not in state.allowed_actions:
        return jsonify({"ok": False, "message": f"{action} is not allowed right now. {state.message}"}), 400

    now = datetime.now()
    entry = {
        "attendance_id": f"ATD-{int(now.timestamp())}",
        "student_college_id": student["college_id"],
        "student_name": student["name"],
        "roll_number": student["roll_number"],
        "course": student["course"],
        "phone": student["phone"],
        "action": action,
        "note": note,
        "guard_id": guard["guard_id"],
        "guard_name": guard["name"],
        "guard_phone": guard["phone"],
        "date": now.strftime(DATE_FORMAT),
        "time": now.strftime(TIME_FORMAT),
        "timestamp": now.isoformat(),
    }
    append_csv(ATTENDANCE_FILE, ATTENDANCE_HEADERS, entry)
    updated_state = build_scan_state(student["college_id"])
    return jsonify(
        {"ok": True, "message": f"{student['name']} marked {action} successfully.", "record": entry, "next_action": updated_state.next_action}
    )


@app.post("/api/admin/login")
def admin_login() -> object:
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = (payload.get("password") or "").strip()
    if username != "admin" or password != "admin123":
        return jsonify({"ok": False, "message": "Invalid admin credentials."}), 401
    return jsonify({"ok": True, "admin": {"name": "IIT Patna Control Room Admin"}})


@app.get("/api/admin/dashboard")
def admin_dashboard() -> object:
    students = read_csv(STUDENTS_FILE)
    guards = read_csv(GUARDS_FILE)
    logs = get_attendance_logs()
    today = datetime.now().strftime(DATE_FORMAT)
    todays_logs = [log for log in logs if log["date"] == today]
    return jsonify(
        {
            "ok": True,
            "data": {
                "summary": {
                    "students": len(students),
                    "guards": len(guards),
                    "today_entries": sum(1 for log in todays_logs if log["action"] == "IN"),
                    "today_exits": sum(1 for log in todays_logs if log["action"] == "OUT"),
                    "today_total": len(todays_logs),
                },
                "students": students,
                "guards": guards,
                "attendance": logs,
            },
        }
    )


@app.get("/api/admin/export/attendance")
def export_attendance() -> object:
    return send_file(ATTENDANCE_FILE, as_attachment=True, download_name="attendance.csv")


@app.get("/api/admin/export/students")
def export_students() -> object:
    return send_file(STUDENTS_FILE, as_attachment=True, download_name="students.csv")


@app.get("/api/admin/export/guards")
def export_guards() -> object:
    return send_file(GUARDS_FILE, as_attachment=True, download_name="guards.csv")


if __name__ == "__main__":
    ensure_data_files()
    app.run(debug=True, port=5000)
else:
    ensure_data_files()
