import React, { useEffect, useState } from "react";
import axios from "axios";
import "bootstrap/dist/css/bootstrap.min.css";
import Navbar from "./Navbar";

const ComposeEmail = () => {
  const [receiverEmail, setReceiverEmail] = useState("");
  const [subject, setSubject] = useState("");
  const [content, setContent] = useState("");
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);
  const [userInfo, setUserInfo] = useState(null);  // ✅ تعريف userInfo

  const handleSendEmail = async (e) => {
    e.preventDefault();

    if (!receiverEmail || !subject || !content) {
      setError("All fields are required!");
      return;
    }

    try {
      const token = localStorage.getItem("token");
      const response = await axios.post(
        "http://localhost:5000/send_email",
        {
          receiver_email: receiverEmail,
          subject: subject, // ✅ إضافة العنوان
          content: content,
        },
        {
          headers: { Authorization: token },
        }
      );

      setMessage(response.data.message);
      setError(null);
      setReceiverEmail("");
      setSubject("");
      setContent("");
    } catch (err) {
      setError(err.response?.data?.error || "Failed to send email.");
      setMessage(null);
    }
  };

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
    <div className="compose-container">
      <h2 className="compose-title">
        <span role="img" aria-label="email">📩</span> Compose Email
      </h2>

      <form className="compose-form" onSubmit={handleSendEmail}>
        <div className="form-group">
          <label>Receiver Email:</label>
          <input
            type="email"
            className="form-control"
            placeholder="Enter recipient email..."
            value={receiverEmail}
            onChange={(e) => setReceiverEmail(e.target.value)}
            required
          />
        </div>


        <div className="form-group">
          <label>Subject:</label>
          <input
            type="text"
            className="form-control"
            placeholder="Enter email subject..."
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label>Content:</label>
          <textarea
            className="form-control textarea"
            rows="6"
            placeholder="Write your message here..."
            value={content}
            onChange={(e) => setContent(e.target.value)}
            required
          ></textarea>
        </div>

        <button type="submit" className="send-btn">
          Send Email <span role="img" aria-label="send">🚀</span>
        </button>
      </form>

      {message && <p className="message">{message}</p>}
    </div>
    </div>
    </div>
    </div>
  );
};

export default ComposeEmail;
