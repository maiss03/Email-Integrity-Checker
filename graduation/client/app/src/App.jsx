import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import React, { useEffect, useState } from "react";

import Register from "./pages/Register";
import Login from "./pages/login";
import Dashboard from "./pages/dashboard"; // استيراد الصفحة
import Inbox from "./pages/inbox";
import ComposeEmail from "./pages/ComposeEmail"; // ✅ استيراد صفحة الإرسال
import SentEmails from "./pages/SentEmails";
import ForgotPassword from "./pages/ForgotPassword";
import AllMails from "./pages/AllMails";
import ChangePassword from "./pages/ChangePassword";
import ChangeName from "./pages/ChangeName"; // ✅ استيراد الصفحة


//import Navbar from "./pages/Navbar"; // ✅ استيراد النافبار

// <Navbar />  {/* ✅ وضعه هنا ليظهر في كل الصفحات */}

import "../public/css/sb-admin-2.min.css";




function App() {
  
  useEffect(() => {
  const darkMode = localStorage.getItem("darkMode");
  if (darkMode === "true") {
    document.body.classList.add("dark-mode");
  }
}, []);

  return (

    <Router>
           
      <Routes>
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/inbox" element={<Inbox />} />
        <Route path="/ComposeEmail" element={<ComposeEmail />} />
        <Route path="/SentEmails" element={<SentEmails />} />
        <Route path="/ForgotPassword" element={<ForgotPassword />} />

        <Route path="/AllMails" element={<AllMails />} />
        <Route path="/ChangePassword" element={<ChangePassword />} />
        <Route path="/ChangeName" element={<ChangeName />} />

        

      </Routes>
    </Router>
  );
}

export default App;
