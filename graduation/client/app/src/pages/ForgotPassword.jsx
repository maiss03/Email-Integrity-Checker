import React, { useState } from "react";
import axios from "axios";

const ForgotPassword = () => {
  const [email, setEmail] = useState("");
  const [twoFACode, setTwoFACode] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [step, setStep] = useState(1);
  const [message, setMessage] = useState("");

  // ✅ إرسال البريد الإلكتروني للتحقق
  const handleRequestReset = async (e) => {
    e.preventDefault();

    try {
      const response = await axios.post("http://localhost:5000/request_password_reset", { email });

      setMessage(response.data.message);
      setStep(2); // الانتقال لخطوة إدخال كود 2FA
    } catch (error) {
      setMessage(error.response?.data?.error || "Something went wrong!");
    }
  };

  // ✅ التحقق من رمز 2FA والحصول على Reset Token
  const handleVerify2FA = async (e) => {
    e.preventDefault();

    try {
      const response = await axios.post("http://localhost:5000/verify_2fa_for_reset", {
        email,
        token: twoFACode,
      });

      setResetToken(response.data.reset_token);
      setMessage("2FA verified! Now, reset your password.");
      setStep(3); // الانتقال لخطوة إدخال كلمة المرور الجديدة
    } catch (error) {
      setMessage(error.response?.data?.error || "Invalid 2FA Code!");
    }
  };

  // ✅ إعادة تعيين كلمة المرور
  const handleResetPassword = async (e) => {
    e.preventDefault();

    try {
      const response = await axios.post(
        "http://localhost:5000/reset-password",
        {
          new_password: newPassword,
          confirm_password: confirmPassword,
        },
        {
          headers: { Authorization: resetToken }, // ✅ إرسال Reset Token في الهيدر
        }
      );

      setMessage(response.data.message);
      setStep(4); // انتهاء العملية بنجاح
    } catch (error) {
      setMessage(error.response?.data?.error || "Something went wrong!");
    }
  };

  return (
    <div className="d-flex justify-content-center align-items-center vh-100">
      <div className="card shadow-lg p-5" style={{ width: "490px", marginRight: "0%" }}> 
        <h2 className="text-center mb-4">🔑 Forgot Password</h2>

        {message && <p className="alert alert-info text-center">{message}</p>}

        {step === 1 && (
          <form onSubmit={handleRequestReset}>
            <p className="text-center text-muted">
              Enter your email to receive a 2FA verification request.
            </p>
            <div className="form-group mb-3">
              <input
                type="email"
                className="form-control"
                placeholder="📧 Enter Email Address..."
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn btn-primary btn-block">
              Request Reset
            </button>
          </form>
        )}

        {step === 2 && (
          <form onSubmit={handleVerify2FA}>
            <p className="text-center text-muted">Enter your 2FA Code.</p>
            <div className="form-group mb-3">
              <input
                type="text"
                className="form-control"
                placeholder="🔢 Enter 2FA Code..."
                value={twoFACode}
                onChange={(e) => setTwoFACode(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn btn-primary btn-block">
              Verify 2FA
            </button>
          </form>
        )}

        {step === 3 && (
          <form onSubmit={handleResetPassword}>
            <p className="text-center text-muted">Enter your new password.</p>
            <div className="form-group mb-3">
              <input
                type="password"
                className="form-control"
                placeholder="🔑 New Password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
              />
            </div>
            <div className="form-group mb-3">
              <input
                type="password"
                className="form-control"
                placeholder="🔄 Confirm Password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn btn-primary btn-block">
              Reset Password
            </button>
          </form>
        )}

        {step === 4 && (
          <div className="text-center">
            <p className="text-success">✅ Password reset successfully!</p>
            <a href="/login" className="btn btn-success btn-block">Go to Login</a>
          </div>
        )}
      </div>
    </div>
  );
};

export default ForgotPassword;
