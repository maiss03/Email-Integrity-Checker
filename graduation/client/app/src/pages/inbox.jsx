import React, { useEffect, useState } from "react";
import axios from "axios";
import "bootstrap/dist/css/bootstrap.min.css";
import "../App.css";
import Navbar from "./Navbar";

const Inbox = () => {
  const [emails, setEmails] = useState([]); // جميع الإيميلات
  const [searchQuery, setSearchQuery] = useState(""); // 🔍 قيمة البحث
  const [selectedEmail, setSelectedEmail] = useState(null); // ✅ تخزين الإيميل عند النقر عليه
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
      .get("http://localhost:5000/inbox", {
        headers: { Authorization: localStorage.getItem("token") },
      })
      .then((response) => {
        const sortedEmails = response.data.emails.sort(
          (a, b) => new Date(b.created_at) - new Date(a.created_at)
        );
        setEmails(sortedEmails);
      })
      .catch((error) => console.error("Error fetching inbox:", error));
  }, []);

  // ✅ تصفية الإيميلات بناءً على قيمة البحث
  const filteredEmails = emails.filter((email) =>
    email.sender.toLowerCase().includes(searchQuery.toLowerCase()) ||
    email.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
    email.created_at.toLowerCase().includes(searchQuery.toLowerCase()) 
  );

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
              <a href="/SentEmails" className="text-white">📤 Sent Emails</a>
            </li>
            <li className="list-group-item bg-primary text-white">
              <a href="/AllMails" className="text-white">📬 All Mails</a>
            </li>
          </ul>
        </div>

        {/* 📥 عنوان الصفحة */}
        <div className="container-fluid mt-4 d-flex flex-column align-items-center">
          <h2 className="text-center mb-2">📥 Inbox</h2>

          {/* 🔍 البحث */}
          <input
            type="text"
            className="form-control w-50 mb-4"
            placeholder="🔎 Search emails..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />

          {/* 📩 جدول الإيميلات */}
          <div className="card shadow-sm w-75">
            <div className="card-header">
              <h5>Emails 📩</h5>
            </div>
            <div className="card-body">
              {filteredEmails.length > 0 ? (
                <table className="table">
                  <thead>
                    <tr>
                      <th>From</th>
                      <th>Subject</th>
                      <th>Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredEmails.map((email, index) => (
                      <tr key={index} 
                          onClick={() => setSelectedEmail(email)} // ✅ فتح تفاصيل الإيميل عند النقر
                          style={{ cursor: "pointer" }}> 
                        <td>{email.sender}</td>
                        <td>{email.subject || "No Subject"}</td>
                        <td>{new Date(email.created_at).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="text-muted">No matching emails found.</p>
              )}
            </div>
            </div>
          </div>
        </div>
      </div>

      {/* 📨 نافذة عرض تفاصيل الإيميل */}
      {selectedEmail && (
        <div className="modal show d-block" tabIndex="-1">
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">📨 Email Details</h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={() => setSelectedEmail(null)} // ✅ إغلاق النافذة
                ></button>
              </div>
              <div className="modal-body">
                <p><strong>📧 From:</strong> {selectedEmail.sender}</p>
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
  );
};

export default Inbox;
