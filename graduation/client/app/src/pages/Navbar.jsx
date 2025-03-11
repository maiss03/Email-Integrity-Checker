import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import "../App.css";

const Navbar = () => {
  const navigate = useNavigate();
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [showSettingsMenu, setShowSettingsMenu] = useState(false);
  const [userInfo, setUserInfo] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    axios.get("http://localhost:5000/user_info", {
      headers: { Authorization: localStorage.getItem("token") },
    })
    .then(response => {
      console.log("✅ Full API Response:", response.data); // طباعة البيانات المسترجعة
      
      // التأكد من أن الاستجابة تحتوي على البيانات المطلوبة قبل تعيينها
      if (response.data && response.data.email) {
        setUserInfo(response.data);
      } else {
        console.error("🚨 Error: Missing user data in API response", response.data);
      }
    })
    .catch(error => console.error("🚨 Error fetching user info:", error));
  }, []);
  
  

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/login");
  };

  const handleSearch = (e) => {
    e.preventDefault();
    console.log("🔍 Searching for:", searchQuery);
    // أضف كود البحث الفعلي هنا
  };

  return (
    <nav
      className="navbar navbar-light bg-light d-flex justify-content-between px-4 shadow-sm"
      style={{ position: "fixed", width: "calc(100% - 225px)",left: "225px", top: 0, zIndex: 1000 }}
    >
      {/* ✅ شريط البحث */}
      <form className="d-flex align-items-center" onSubmit={handleSearch}>
        <input
          type="text"
          className="form-control"
          placeholder="Search emails..."
          style={{ width: "300px" }}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <button type="submit" className="btn btn-primary ms-2">
          🔍
        </button>
      </form>

      <div className="d-flex align-items-center">
  {/* ✅ أيقونة الإعدادات */}
  <div className="position-relative me-3">
    <button
      className="btn btn-light"
      onClick={() => {
        setShowSettingsMenu(!showSettingsMenu);
        setShowProfileMenu(false); // ✅ إغلاق قائمة الملف الشخصي عند فتح الإعدادات
      }}
      style={{ cursor: "pointer" }}
    >
      ⚙️
    </button>
    {showSettingsMenu && (
      <div className="dropdown-menu show position-absolute start-100 mt-2 p-2 shadow"
        style={{
          transform: "translateX(-100%)",
          width: "200px",
          textAlign: "left",
          padding: "10px",
          top: "50px",
        }}
      >
        <button
          className="dropdown-item"
          onClick={() => navigate("/ChangePassword")}
          style={{ cursor: "pointer" }}
        >
          🔑 Reset Password
        </button>
        <button
  className="dropdown-item"
  onClick={() => {
    navigate("/ChangeName"); // ✅ الانتقال إلى صفحة تغيير الاسم
  }}
  style={{ cursor: "pointer" }}
>
  ✏️ Change Name
</button>



      </div>
    )}
  </div>

  {/* ✅ أيقونة الملف الشخصي */}
  <div className="position-relative">
    <button
      className="btn btn-light rounded-circle text-white"
      style={{
        backgroundColor: "#4285F4",
        width: "40px",
        height: "40px",
        fontSize: "18px",
        fontWeight: "bold",
        cursor: "pointer",
      }}
      onClick={() => {
        setShowProfileMenu(!showProfileMenu);
        setShowSettingsMenu(false); // ✅ إغلاق قائمة الإعدادات عند فتح الملف الشخصي
      }}
    >
      {userInfo?.email ? userInfo.email.charAt(0).toUpperCase() : "U"}
    </button>

    {showProfileMenu && (
      <div className="dropdown-menu show position-absolute start-100 mt-2 p-2 shadow"
        style={{
          transform: "translateX(-100%)",
          width: "200px",
          textAlign: "left",
          padding: "10px",
          top: "50px",
        }}
      >
        <p className="dropdown-item-text">
          <strong>
            {userInfo?.first_name && userInfo?.last_name
              ? `${userInfo.first_name} ${userInfo.last_name}`
              : "Unknown User"}
          </strong>
        </p>
        <p className="dropdown-item-text text-muted">
          {userInfo?.email || "No Email"}
        </p>
        <hr />
        <button
          className="dropdown-item text-danger"
          onClick={handleLogout}
          style={{ cursor: "pointer" }}
        >
          🚪 Sign Out
        </button>
      </div>
    )}
  </div>
</div>

    </nav>
  );
};

export default Navbar;