import React, { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "bootstrap/dist/css/bootstrap.min.css";
import Navbar from "./Navbar"; // ✅ استدعاء النافبار
import "../App.css";

const ChangePassword = () => {
  const navigate = useNavigate();
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
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

  const handleChangePassword = (e) => {
    e.preventDefault();

    // ✅ التأكد من أن جميع الحقول ممتلئة
    if (!oldPassword || !newPassword || !confirmPassword) {
      setError("❌ All fields are required!");
      return;
    }

    // ✅ التحقق من أن كلمة المرور الجديدة متطابقة
    if (newPassword !== confirmPassword) {
      setError("❌ New passwords do not match!");
      return;
    }

    // ✅ إرسال الطلب إلى `/change-password`
    axios
      .post(
        "http://localhost:5000/change-password",
        { old_password: oldPassword, new_password: newPassword, confirm_password: confirmPassword },
        { headers: { Authorization: localStorage.getItem("token") } }
      )
      .then((response) => {
        console.log("✅ Password Change Response:", response.data);
        setSuccessMessage("✅ Password changed successfully!");
        setError(""); 
        setTimeout(() => navigate("/dashboard"), 3000); // ✅ إعادة التوجيه بعد 3 ثواني
      })
      .catch((error) => {
        console.error("🚨 Error changing password:", error);
        setError(error.response?.data?.error || "❌ Failed to change password. Check your old password.");
      });
  };

  return (
    <div>
     <div>
    <Navbar userInfo={userInfo} />  {/* ✅ هنا نضع الـ Navbar */}
    <div className="container-fluid">
      <div className="row">
        {/* ✅ Sidebar */}
        <div className="sidebar">
          <h4 className="p-2">EMAIL SYSTEM</h4>
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
      <div className="container d-flex justify-content-center align-items-center" style={{ height: "100vh" }}>
        <div className="card p-4 shadow-lg" style={{ width: "400px" }}>
          <h3 className="text-center mb-3">🔒 Change Password</h3>
          
          {error && <div className="alert alert-danger">{error}</div>}
          {successMessage && <div className="alert alert-success">{successMessage}</div>}

          <form onSubmit={handleChangePassword}>
            <div className="mb-3">
              <label className="form-label">Old Password</label>
              <input
                type="password"
                className="form-control"
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
                required
              />
            </div>

            <div className="mb-3">
              <label className="form-label">New Password</label>
              <input
                type="password"
                className="form-control"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
              />
            </div>

            <div className="mb-3">
              <label className="form-label">Confirm New Password</label>
              <input
                type="password"
                className="form-control"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
            </div>

            <button type="submit" className="btn btn-primary w-100">🔄 Change Password</button>
          </form>
        </div>
      </div>
    </div>
    </div>
    </div>
    </div>
  );
};

export default ChangePassword;
