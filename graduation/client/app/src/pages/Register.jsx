import React, { useState } from 'react';
import axios from 'axios';

const Register = () => {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [repeatPassword, setRepeatPassword] = useState('');
  const [qrCode, setQrCode] = useState(null);
  const [message, setMessage] = useState('');

  const handleRegister = async (e) => {
    e.preventDefault();

    if (password !== repeatPassword) {
      setMessage("❌ Passwords do not match!");
      return;
    }

    try {
      const response = await axios.post("http://localhost:5000/register", {
        first_name: firstName,
        last_name: lastName,
        email,
        password
      });

      setMessage(response.data.message);
      setQrCode(response.data.qr_code);
    } catch (error) {
      setMessage(error.response?.data?.error || "An error occurred, please try again!");
    }
  };

  return (
    <div className="d-flex justify-content-center align-items-center vh-100">
      <div className="card shadow-lg p-5" style={{ width: "500px" }}>
        <div className="text-center mb-4">
          <h1 className="h4 text-gray-900">Create an Account!</h1>
        </div>
        <form className="user" onSubmit={handleRegister}>
          <div className="row">
            {/* First Name */}
            <div className="col-6 mb-3">
              <input type="text" className="form-control" 
                value={firstName} onChange={(e) => setFirstName(e.target.value)} 
                placeholder="First Name" required />
            </div>
            {/* Last Name */}
            <div className="col-6 mb-3">
              <input type="text" className="form-control" 
                value={lastName} onChange={(e) => setLastName(e.target.value)} 
                placeholder="Last Name" required />
            </div>
          </div>
          {/* Email */}
          <div className="form-group mb-3">
            <input type="email" className="form-control" 
              value={email} onChange={(e) => setEmail(e.target.value)} 
              placeholder="Email Address" required />
          </div>
          <div className="row">
            {/* Password */}
            <div className="col-6 mb-3">
              <input type="password" className="form-control" 
                value={password} onChange={(e) => setPassword(e.target.value)} 
                placeholder="Password" required />
            </div>
            {/* Repeat Password */}
            <div className="col-6 mb-3">
              <input type="password" className="form-control" 
                value={repeatPassword} onChange={(e) => setRepeatPassword(e.target.value)} 
                placeholder="Repeat Password" required />
            </div>
          </div>
          <button type="submit" className="btn btn-primary w-100">
            Register Account
          </button>
        </form>

        {/* رسالة النجاح أو الخطأ */}
        {message && <p className="mt-3 text-center">{message}</p>}

        {/* ✅ تحسين تصميم QR Code */}
        {qrCode && (
          <div className="text-center mt-4">
            <p>📲 Scan this QR Code to enable 2FA:</p>
            <div className="d-flex justify-content-center">
              <img src={qrCode} alt="QR Code" style={{ width: "140px", height: "140px", border: "2px solid #ddd", padding: "10px", borderRadius: "10px" }} />
            </div>
          </div>
        )}

        {/* ✅ زر تسجيل الدخول إذا كان لديه حساب بالفعل */}
        <div className="text-center mt-3">
          <p>Already have an account? <a href="/login" className="text-primary">Login</a></p>
        </div>
      </div>
    </div>
  );
};

export default Register;
