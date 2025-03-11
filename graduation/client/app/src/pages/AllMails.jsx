import React, { useEffect, useState } from "react";
import axios from "axios";
import "bootstrap/dist/css/bootstrap.min.css";
import Navbar from "./Navbar";
import "../App.css";

const AllMails = () => {
  const [receivedEmails, setReceivedEmails] = useState([]);
  const [sentEmails, setSentEmails] = useState([]);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [userInfo, setUserInfo] = useState(null);
  const [activeTab, setActiveTab] = useState("received");

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      window.location.href = "/login";
      return;
    }

    // ✅ جلب بيانات المستخدم بدون setRole
    axios
      .get("http://localhost:5000/user_info", {
        headers: { Authorization: token },
      })
      .then((response) => {
        console.log("✅ User Info Response:", response.data);
        if (response && response.data) {
          setUserInfo(response.data);  // ✅ حفظ بيانات المستخدم
        } else {
          console.error("🚨 Error: Missing user data in API response", response);
        }
      })
      .catch((error) => console.error("🚨 Error fetching user info:", error));
  }, []);

  useEffect(() => {
    const token = localStorage.getItem("token");

    // ✅ جلب الإيميلات المستلمة مع `setReceivedEmails`
    axios
      .get("http://localhost:5000/inbox", {
        headers: { Authorization: token },
      })
      .then((response) => {
        console.log("📩 Received Emails Response:", response.data);
        const sortedEmails = response.data.emails.sort(
          (a, b) => new Date(b.created_at) - new Date(a.created_at)
        );
        setReceivedEmails(sortedEmails);
      })
      .catch((error) => console.error("🚨 Error fetching inbox:", error));

    // ✅ جلب الإيميلات المرسلة مع `setSentEmails`
    axios
      .get("http://localhost:5000/sent_emails", {
        headers: { Authorization: token },
      })
      .then((response) => {
        console.log("📤 Sent Emails Response:", response.data);
        const sortedEmails = response.data.sent_emails.sort(
          (a, b) => new Date(b.created_at) - new Date(a.created_at)
        );
        setSentEmails(sortedEmails);
      })
      .catch((error) => console.error("🚨 Error fetching sent emails:", error));
  }, []);

  return (
    <div>
      <Navbar userInfo={userInfo} />
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
                <a href="/SentEmails" className="text-white">📤 Sent Emails</a>
              </li>
              <li className="list-group-item bg-primary text-white">
              <a href="/AllMails" className="text-white">📬 All Mails</a>
            </li>
            </ul>
          </div>

          <div className="container mt-4">
            <h2 className="text-center">📬 All Mails</h2>

            {/* ✅ التبويبات */}
            <ul className="nav nav-tabs mb-3">
              <li className="nav-item">
                <button
                  className={`nav-link ${activeTab === "received" ? "active fw-bold" : ""}`}
                  onClick={() => setActiveTab("received")}
                >
                  📥 Received Emails
                </button>
              </li>
              <li className="nav-item">
                <button
                  className={`nav-link ${activeTab === "sent" ? "active fw-bold" : ""}`}
                  onClick={() => setActiveTab("sent")}
                >
                  📤 Sent Emails
                </button>
              </li>
            </ul>

            {/* ✅ عرض محتوى التبويبات */}
            <div className="card-body table-container">
            {activeTab === "received" && (
                  <ReceivedEmailsTable emails={receivedEmails} setSelectedEmail={setSelectedEmail} />
                )}
                {activeTab === "sent" && (
                  <SentEmailsTable emails={sentEmails} setSelectedEmail={setSelectedEmail} />
                )}
              </div>
          </div>

          {/* ✅ نافذة عرض تفاصيل الإيميل */}
          {selectedEmail && (
            <div className="modal show d-block" tabIndex="-1">
              <div className="modal-dialog">
                <div className="modal-content">
                  <div className="modal-header">
                    <h5 className="modal-title">📨 Email Details</h5>
                    <button
                      type="button"
                      className="btn-close"
                      onClick={() => setSelectedEmail(null)}
                    ></button>
                  </div>
                  <div className="modal-body">
                    <p><strong>📌 Subject:</strong> {selectedEmail.subject || "No Subject"}</p>
                    <p><strong>📝 Content:</strong> {selectedEmail.content}</p>
                    <p><strong>⏰ Date:</strong> {new Date(selectedEmail.created_at).toLocaleString()}</p>
                  </div>
                  <div className="modal-footer">
                <button
                  className="btn btn-secondary"
                  onClick={() => setSelectedEmail(null)} // ✅ إغلاق النافذة عند النقر
                >
                  Close
                </button>
              </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// ✅ جدول الإيميلات المستلمة (يُظهر فقط المرسل)
const ReceivedEmailsTable = ({ emails, setSelectedEmail }) => (
    <div className="table-responsive">
    <table className="table table-hover table-bordered">
      <thead className="table-primary">
        <tr>
          <th>Sender</th>
          <th>Subject</th>
          <th>Date</th>
        </tr>
      </thead>
      <tbody>
        {emails.length > 0 ? (
          emails.map((email, index) => (
            <tr key={index} onClick={() => setSelectedEmail(email)} style={{ cursor: "pointer" }}>
              <td>{email.sender}</td>
              <td>{email.subject || "No Subject"}</td>
              <td>{new Date(email.created_at).toLocaleString()}</td>
            </tr>
          ))
        ) : (
          <tr>
            <td colSpan="3" className="text-center text-muted">No received emails found</td>
          </tr>
        )}
      </tbody>
    </table>
  </div>
);

// ✅ جدول الإيميلات المرسلة (يُظهر فقط المستلم)
const SentEmailsTable = ({ emails, setSelectedEmail }) => (
    <div className="table-responsive">
    <table className="table table-hover table-bordered">
      <thead className="table-success">
        <tr>
          <th>Receiver</th>
          <th>Subject</th>
          <th>Date</th>
        </tr>
      </thead>
      <tbody>
        {emails.length > 0 ? (
          emails.map((email, index) => (
            <tr key={index} onClick={() => setSelectedEmail(email)} style={{ cursor: "pointer" }}>
              <td>{email.receiver}</td>
              <td>{email.subject || "No Subject"}</td>
              <td>{new Date(email.created_at).toLocaleString()}</td>
            </tr>
          ))
        ) : (
          <tr>
            <td colSpan="3" className="text-center text-muted">No sent emails found</td>
          </tr>
        )}
      </tbody>
    </table>
  </div>
);

export default AllMails;
