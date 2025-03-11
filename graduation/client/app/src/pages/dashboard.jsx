import axios from "axios";
import "bootstrap/dist/css/bootstrap.min.css";
import "../App.css";
import { useEffect, useState, useRef } from "react";
import Navbar from "./Navbar";

const Dashboard = () => {
  const [emails, setEmails] = useState([]);
  const [logs, setLogs] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const previousNotifications = useRef(new Set()); // ✅ استخدام useRef لحفظ الإشعارات السابقة
  const [searchQuery, setSearchQuery] = useState("");

  const [userInfo, setUserInfo] = useState(null);  // ✅ تعريف userInfo


  const [role, setRole] = useState("");
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [selectedLog, setSelectedLog] = useState(null);
  const [allUsersNotifications, setAllUsersNotifications] = useState([]); // ✅ إشعارات كل المستخدمين (للأدمن فقط)

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
        const fetchNotifications = async () => {
            try {
                const response = await axios.get("http://localhost:5000/notifications", {
                    headers: { Authorization: localStorage.getItem("token") },
                });

                const sortedNotifications = response.data.notifications.sort(
                    (a, b) => new Date(b.created_at) - new Date(a.created_at)
                );

                setNotifications(sortedNotifications);

                // ✅ التحقق من آخر إشعار ومنع إضافته إن كان مكررًا
                if (sortedNotifications.length > 0) {
                    const latestNotification = sortedNotifications[0].message;

                    if (!previousNotifications.current.has(latestNotification)) {
                        setNotifications(prev => [
                            { message: `📩 ${latestNotification}`, created_at: new Date() },
                            ...prev
                        ]);
                        
                        previousNotifications.current.add(latestNotification); // ✅ حفظ الإشعار لمنع التكرار
                    }
                }
            } catch (error) {
                console.error("Error fetching notifications:", error);
            }
        };

        fetchNotifications();

        // ✅ تحديث الإشعارات كل 10 ثواني
        const interval = setInterval(fetchNotifications, 10000);

        return () => clearInterval(interval);
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
  

  useEffect(() => {
    if (role === "admin") {
      axios
        .get("http://localhost:5000/logs", {
          headers: { Authorization: localStorage.getItem("token") },
        })
        .then((response) => {
            const sortedLogs = response.data.emails.sort(
              (a, b) => new Date(b.created_at) - new Date(a.created_at)
            );
            setLogs(sortedLogs);
          })
          .catch((error) => console.error("Error fetching logs:", error));
    
      axios
        .get("http://localhost:5000/all_notifications", {
          headers: { Authorization: localStorage.getItem("token") },
        })
        .then((response) => {
            const sortedUserNotifications = response.data.notifications.sort(
              (a, b) => new Date(b.created_at) - new Date(a.created_at)
            );
            setAllUsersNotifications(sortedUserNotifications);
          })
          .catch((error) => console.error("Error fetching all users' notifications:", error));
      }
  }, [role]);

  return (
    
    
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

        {/* ✅ Main Content */}
        <div className="main-content">
          <h2 className="mt-12">Dashboard</h2>

          <div className="row">
            {/* ✅ Notifications */}
            <div className="col-md-6">
              <div className="card shadow-sm mb-4 fixed-box">
                <div className="card-header">
                  <h5>Notifications 🔔</h5>
                </div>
                <div className="card-body scroll-box">
                  {notifications.length > 0 ? (
                    notifications.map((notif, index) => (
                      <div key={index} className="alert alert-info d-flex justify-content-between">
                        <span>
                          {notif.message} - <small>{new Date(notif.created_at).toLocaleString()}</small>
                        </span>
                        <button className="btn-close" onClick={() => setNotifications(notifications.filter((_, i) => i !== index))}></button>
                      </div>
                    ))
                  ) : (
                    <p className="text-muted">No notifications</p>
                  )}
                </div>
              </div>
            </div>

            {/* ✅ Inbox */}
            <div className="col-md-6">
              <div className="card shadow-sm mb-4 fixed-box">
                <div className="card-header">
                  <h5>Inbox 📩</h5>
                </div>
                <div className="card-body scroll-box">
                  {emails.length > 0 ? (
                    <table className="table">
                      <thead>
                        <tr>
                          <th>From</th>
                          <th>Subject</th>
                          <th>Date</th>
                        </tr>
                      </thead>
                      <tbody>
                        {emails.map((email, index) => (
                          <tr key={index} onClick={() => setSelectedEmail(email)} style={{ cursor: "pointer" }}>
                            <td>{email.sender}</td>
                            <td>{email.subject}</td>
                            <td>{new Date(email.created_at).toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <p className="text-muted">No emails received</p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* ✅ إشعارات جميع المستخدمين (Admin Only) */}
          {role === "admin" && (
            <div className="col-md-12">
              <div className="card shadow-sm mb-4 fixed-box">
                <div className="card-header">
                  <h5>Users Notifications 📢</h5>
                </div>
                <div className="card-body scroll-box">
                  {allUsersNotifications.length > 0 ? (
                    allUsersNotifications.map((notif, index) => (
                      <div key={index} className="alert alert-warning">
                        <strong>{notif.username}:</strong> {notif.message} -{" "}
                        <small>{new Date(notif.created_at).toLocaleString()}</small>
                      </div>
                    ))
                  ) : (
                    <p className="text-muted">No user notifications available</p>
                  )}
                </div>
              </div>
            </div>
          )}
          {/* ✅ Logs (Admin Only) */}
          {role === "admin" && (
            <div className="card shadow-sm">
              <div className="card-header">
                <h5>System Logs 🔍</h5>
              </div>
              <div className="card-body">
                {logs.length > 0 ? (
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Sender</th>
                        <th>Receiver</th>
                        <th>content</th>
                        <th>Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {logs.map((log, index) => (
                        <tr key={index} onClick={() => setSelectedLog(log)} style={{ cursor: "pointer" }}>
                          <td>{log.sender}</td>
                          <td>{log.receiver}</td>
                          <td>{log.content}</td>
                          <td>{new Date(log.created_at).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="text-muted">No logs available</p>
                )}
              </div>
            </div>
          )}

          {/* ✅ Email Modal */}
          {selectedEmail && (
            <div className="modal show d-block">
              <div className="modal-dialog">
                <div className="modal-content">
                  <div className="modal-header">
                    <h5 className="modal-title">Email Details</h5>
                    <button type="button" className="btn-close" onClick={() => setSelectedEmail(null)}></button>
                  </div>
                  <div className="modal-body">
                    <p><strong>📧From:</strong> {selectedEmail.sender}</p>
                    <p><strong>🔍Content:</strong> {selectedEmail.content}</p>
                    <p><strong>⏰Date:</strong> {new Date(selectedEmail.created_at).toLocaleString()}</p>
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
          {/* ✅ Log Modal */}
           {/* 📝 نافذة عرض تفاصيل اللوج */}
      {selectedLog && (
        <div className="modal show d-block" tabIndex="-1">
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">📝 Log Details</h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={() => setSelectedLog(null)} // ✅ إغلاق النافذة
                ></button>
              </div>
              <div className="modal-body">
                <p><strong>📧 Sender:</strong> {selectedLog.sender}</p>
                <p><strong>📩 Receiver:</strong> {selectedLog.receiver}</p>
                <p><strong>🔍 Content:</strong> {selectedLog.content}</p>
                <p><strong>⏰ Date:</strong> {new Date(selectedLog.created_at).toLocaleString()}</p>
              </div>
              <div className="modal-footer">
                <button
                  className="btn btn-secondary"
                  onClick={() => setSelectedLog(null)} // ✅ إغلاق النافذة عند النقر
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
    </div>
  );
};

export default Dashboard;



