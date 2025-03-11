import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";

const Login = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [twoFactorCode, setTwoFactorCode] = useState("");
  const [requires2FA, setRequires2FA] = useState(false);
  const [sessionToken, setSessionToken] = useState("");
  const [message, setMessage] = useState("");
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();

    try {
      const response = await axios.post("http://localhost:5000/login", {
        email,
        password,
      });

      console.log("Login Response:", response.data);

      if (response.data.requires_2fa) {
        setRequires2FA(true);
        setSessionToken(response.data.token);
        setMessage("Enter your 2FA code");
      } else if (response.data.token) {
        localStorage.setItem("token", response.data.token);
        window.location.href = "/dashboard";
      } else {
        setMessage("Invalid credentials or 2FA required.");
      }
    } catch (error) {
      setMessage(error.response?.data?.error || "Invalid email or password!");
    }
  };

  const handleVerify2FA = async (e) => {
    e.preventDefault();

    try {
      const response = await axios.post("http://localhost:5000/verify_2fa", {
        email,
        token: twoFactorCode,
      });

      console.log("2FA Verification Response:", response.data);

      if (response.data.token) {
        localStorage.setItem("token", response.data.token);
        navigate("/dashboard");
      } else {
        setMessage("Invalid 2FA code, please try again.");
      }
    } catch (error) {
      setMessage(error.response?.data?.error || "Failed to verify 2FA!");
    }
  };

  return (
    <div className="d-flex justify-content-center align-items-center vh-100">
      <div className="card shadow-lg p-5" style={{ width: "490px", marginRight: "0%" }}>  
        <div className="text-center mb-4">
          <h1 className="h4 text-gray-900">Login to your account</h1>
        </div>

        {!requires2FA ? (
          <form className="user" onSubmit={handleLogin}>
            <div className="form-group mb-3">
              <input
                type="email"
                className="form-control form-control-user"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                required
              />
            </div>
            <div className="form-group mb-3">
              <input
                type="password"
                className="form-control form-control-user"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
              />
            </div>
            <button type="submit" className="btn btn-primary btn-user btn-block">
              Login
            </button>

            {/* 🔹 Forgot Password Link */}
            <div className="text-center mt-3">
              <a href="/ForgotPassword" className="small text-primary">
                Forgot Password?
              </a>
            </div>

            {/* 🔹 Don't have an account? */}
            <div className="text-center mt-2">
              <span className="text-muted">Don't have an account? </span>
              <a href="/register" className="small text-primary">
                Sign up
              </a>
            </div>
          </form>
        ) : (
          <form className="user" onSubmit={handleVerify2FA}>
            <div className="form-group mb-3">
              <input
                type="text"
                className="form-control form-control-user"
                value={twoFactorCode}
                onChange={(e) => setTwoFactorCode(e.target.value)}
                placeholder="Enter your 2FA code"
                required
              />
            </div>
            <button type="submit" className="btn btn-success btn-user btn-block">
              Verify 2FA
            </button>
          </form>
        )}

        {message && <p className="mt-3 text-center">{message}</p>}
      </div>
    </div>
  );
};

export default Login;
