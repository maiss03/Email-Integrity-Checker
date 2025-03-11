import React, { useEffect, useState } from "react";
import axios from "axios";
import "bootstrap/dist/css/bootstrap.min.css";
import "../App.css";
import Navbar from "./Navbar";


const SentEmails = () => {
  const [sentEmails, setSentEmails] = useState([]);
  const [selectedEmail, setSelectedEmail] = useState(null); // ✅ حالة لتحديد الإيميل المفتوح
  const [userInfo, setUserInfo] = useState(null);  // ✅ تعريف userInfo

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      window.location.href = "/login";
      return;
    }

    axios
      .get("http://localhost:5000/user_info", {
        headers: { Authorization: token },
      })
      .then((response) => {
        console.log("✅ User Info Response:", response.data); // طباعة البيانات للتأكد

        // التأكد من وجود البيانات قبل تعيينها
        if (response && response.data) {
          setRole(response.data.role);
          setUserInfo(response.data);  // ✅ حفظ بيانات المستخدم بشكل صحيح
        } else {
          console.error("🚨 Error: API response is missing user data", response);
        }
      })
      .catch((error) => console.error("🚨 Error fetching user info:", error));
  }, []);

  useEffect(() => {
    axios
      .get("http://localhost:5000/sent_emails", {
        headers: { Authorization: localStorage.getItem("token") },
      })
      .then((response) => {
        const sortedEmails = response.data.sent_emails.sort(
          (a, b) => new Date(b.created_at) - new Date(a.created_at)
        );
        setSentEmails(sortedEmails);
      })
      .catch((error) => console.error("Error fetching sent emails:", error));
  }, []);

  return (
    <div>
    <Navbar userInfo={userInfo} />  {/* ✅ هنا نضع الـ Navbar */}

    <div className="container-fluid">
      <div className="row">
        {/* ✅ Sidebar */}
        <div className="sidebar">
          <h4 className="p-3">EMAIL SYSTEM</h4>
          <ul className="list-group list-group-flush">
            <li className="list-group-item bg-primary text-white">
              <a href="/dashboard" className="text-white">📊 Dashboard</a>
            </li>
            <li className="list-group-item bg-primary text-white">
              <a href="/inbox" className="text-white">📥 Inbox</a>
            </li>
            <li className="list-group-item bg-primary text-white">
              <a href="/ComposeEmail" className="text-white">✉️ Compose Email</a>
            </li>
            <li className="list-group-item bg-primary text-white">
              <a href="/sent" className="text-white">📤 Sent Emails</a>
            </li>
            <li className="list-group-item bg-primary text-white">
              <a href="/AllMails" className="text-white">📬 All Mails</a>
            </li>
          </ul>
        </div>

        {/* ✅ Main Content */}
        <div className="container-fluid mt-4 d-flex flex-column align-items-center">
          <h2 className="text-center mb-3">📤 Sent Emails</h2>

          <div className="card shadow-sm w-75">
            <div className="card-header">
              <h5>Sent Emails 📤</h5>
            </div>
            <div className="card-body">
              {sentEmails.length > 0 ? (
                <table className="table">
                  <thead>
                    <tr>
                      <th>To</th>
                      <th>Subject</th>
                      <th>Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sentEmails.map((email, index) => (
                      <tr key={index} onClick={() => setSelectedEmail(email)} style={{ cursor: "pointer" }}>
                        <td>{email.receiver}</td>
                        <td>{email.subject}</td>
                        <td>{new Date(email.created_at).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="text-muted">No sent emails found.</p>
              )}
            </div>
          </div>

          {/* ✅ نافذة عرض تفاصيل الإيميل عند النقر */}
          {selectedEmail && (
            <div className="modal show d-block" tabIndex="-1">
              <div className="modal-dialog">
                <div className="modal-content">
                  <div className="modal-header">
                    <h5 className="modal-title">📨 Sent Email Details</h5>
                    <button type="button" className="btn-close" onClick={() => setSelectedEmail(null)}></button>
                  </div>
                  <div className="modal-body">
                    <p><strong>📧 To:</strong> {selectedEmail.receiver}</p>
                    <p><strong>📌 Subject:</strong> {selectedEmail.subject || "No Subject"}</p>
                    <p><strong>📝 Content:</strong> {selectedEmail.content}</p>
                    <p><strong>⏰ Date:</strong> {new Date(selectedEmail.created_at).toLocaleString()}</p>
                  </div>
                  <div className="modal-footer">
                    <button className="btn btn-secondary" onClick={() => setSelectedEmail(null)}>Close</button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
        </div>
      </div>
    </div>
  );
};

export default SentEmails;
