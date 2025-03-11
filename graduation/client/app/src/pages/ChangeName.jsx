import React, { useState, useEffect } from "react";
import axios from "axios";
import Navbar from "./Navbar";
import "bootstrap/dist/css/bootstrap.min.css";
import "../App.css";

const ChangeName = () => {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [message, setMessage] = useState("");
  const [userInfo, setUserInfo] = useState(null);

  useEffect(() => {
    axios
      .get("http://localhost:5000/user_info", {
        headers: { Authorization: localStorage.getItem("token") },
      })
      .then((response) => {
        setUserInfo(response.data);
        setFirstName(response.data.first_name || "");
        setLastName(response.data.last_name || "");
      })
      .catch((error) => console.error("🚨 Error fetching user info:", error));
  }, []);

  const handleUpdateName = (e) => {
    e.preventDefault();
    axios
      .put(
        "http://localhost:5000/update_name",
        { first_name: firstName, last_name: lastName },
        { headers: { Authorization: localStorage.getItem("token") } }
      )
      .then((response) => {
        setMessage(response.data.message);
      })
      .catch((error) =>
        setMessage(error.response?.data?.error || "An error occurred")
      );
  };

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

      <div className="container mt-5">
        <h2 className="text-center">✏️ Change Your Name</h2>
        <div className="card shadow-lg p-4 mx-auto" style={{ maxWidth: "500px" }}>
          <form onSubmit={handleUpdateName}>
            <div className="mb-3">
              <label className="form-label">First Name</label>
              <input
                type="text"
                className="form-control"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                required
              />
            </div>
            <div className="mb-3">
              <label className="form-label">Last Name</label>
              <input
                type="text"
                className="form-control"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn btn-primary w-100">
              Save Changes
            </button>
          </form>
          {message && <p className="mt-3 text-center">{message}</p>}
        </div>
      </div>
      </div>
      </div>
    </div>
  );
};

export default ChangeName;
