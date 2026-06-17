import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("accessToken");

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("accessToken");
      localStorage.removeItem("tokenType");
      localStorage.removeItem("user");
    }

    return Promise.reject(error);
  }
);

export default api;
---------------------------------------
import api from "./axios";

export const registerUser = async (data) => {
  const response = await api.post("/auth/register", data);
  return response.data;
};

export const sendOtp = async (data) => {
  const response = await api.post("/auth/send-otp", data);
  return response.data;
};

export const verifyOtp = async (data) => {
  const response = await api.post("/auth/verify-otp", data);
  return response.data;
};

export const loginUser = async (data) => {
  const response = await api.post("/auth/login", data);
  return response.data;
};

export const forgotPassword = async (data) => {
  const response = await api.post("/auth/forgot-password", data);
  return response.data;
};

export const resetPassword = async (data) => {
  const response = await api.post("/auth/reset-password", data);
  return response.data;
};
-------------------------------------------
export const setToken = (token) => {
  localStorage.setItem("accessToken", token);
};

export const getToken = () => {
  return localStorage.getItem("accessToken");
};

export const removeToken = () => {
  localStorage.removeItem("accessToken");
};

export const setTokenType = (tokenType) => {
  localStorage.setItem("tokenType", tokenType);
};

export const getTokenType = () => {
  return localStorage.getItem("tokenType");
};

export const setUser = (user) => {
  localStorage.setItem("user", JSON.stringify(user));
};

export const getUser = () => {
  const user = localStorage.getItem("user");
  return user ? JSON.parse(user) : null;
};

export const clearAuthStorage = () => {
  localStorage.removeItem("accessToken");
  localStorage.removeItem("tokenType");
  localStorage.removeItem("user");
};
-----------------------
import { createContext, useState } from "react";
import { loginUser } from "../api/authApi";
import {
  setToken,
  setTokenType,
  getToken,
  setUser,
  getUser,
  clearAuthStorage,
} from "../utils/storage";

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setAuthUser] = useState(getUser());
  const [isAuthenticated, setIsAuthenticated] = useState(Boolean(getToken()));
  const [loading, setLoading] = useState(false);

  const login = async (loginData) => {
    setLoading(true);

    try {
      const response = await loginUser(loginData);

      if (!response.access_token) {
        throw new Error("Access token not received from backend");
      }

      setToken(response.access_token);
      setTokenType(response.token_type || "bearer");

      const userData = {
        email: loginData.email,
      };

      setUser(userData);
      setAuthUser(userData);
      setIsAuthenticated(true);

      return response;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    clearAuthStorage();
    setAuthUser(null);
    setIsAuthenticated(false);
    window.location.href = "/login";
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
--------------------------------
import { useContext } from "react";
import { AuthContext } from "../context/AuthContext";

const useAuth = () => {
  return useContext(AuthContext);
};

export default useAuth;
---------------------------------
import {
  Box,
  Card,
  CardContent,
  Container,
  Typography,
  useTheme,
} from "@mui/material";

const AuthLayout = ({ title, subtitle, children }) => {
  const theme = useTheme();

  return (
    <Box
      sx={{
        minHeight: "100vh",
        background:
          theme.palette.mode === "dark"
            ? "linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #111827 100%)"
            : "linear-gradient(135deg, #2563eb 0%, #7c3aed 50%, #ec4899 100%)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        px: 2,
        py: 4,
      }}
    >
      <Container maxWidth="lg">
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: { xs: "1fr", md: "1fr 450px" },
            gap: 4,
            alignItems: "center",
          }}
        >
          <Box sx={{ color: "white", display: { xs: "none", md: "block" } }}>
            <Typography variant="h3" fontWeight={800} mb={2}>
              Budget Management System
            </Typography>

            <Typography variant="h6" sx={{ maxWidth: 560, opacity: 0.9 }}>
              Manage income, expenses, savings, budgets, analytics and AI-based
              financial insights from one secure platform.
            </Typography>

            <Box sx={{ mt: 4 }}>
              <Typography>✓ Secure Authentication</Typography>
              <Typography>✓ OTP Verification</Typography>
              <Typography>✓ Finance Dashboard</Typography>
              <Typography>✓ AI Budget Advisor</Typography>
            </Box>
          </Box>

          <Card
            sx={{
              width: "100%",
              borderRadius: 5,
              boxShadow: "0 30px 80px rgba(0,0,0,0.25)",
            }}
          >
            <CardContent sx={{ p: { xs: 3, sm: 4 } }}>
              <Typography variant="h4" fontWeight={800} textAlign="center">
                {title}
              </Typography>

              <Typography
                variant="body2"
                color="text.secondary"
                textAlign="center"
                mt={1}
                mb={3}
              >
                {subtitle}
              </Typography>

              {children}
            </CardContent>
          </Card>
        </Box>
      </Container>
    </Box>
  );
};

export default AuthLayout;
-------------------------------
import { Navigate } from "react-router-dom";
import useAuth from "../hooks/useAuth";

const PublicRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

export default PublicRoute;
----------------------------------
import { Navigate } from "react-router-dom";
import useAuth from "../hooks/useAuth";

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

export default ProtectedRoute;
-------------------------------------
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  TextField,
  Typography,
} from "@mui/material";
import AuthLayout from "../../layouts/AuthLayout";
import { registerUser, sendOtp } from "../../api/authApi";

const Register = () => {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    password: "",
  });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (event) => {
    setFormData({
      ...formData,
      [event.target.name]: event.target.value,
    });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const registerResponse = await registerUser(formData);

      await sendOtp({
        email: formData.email,
      });

      navigate("/verify-otp", {
        state: {
          user_id: registerResponse.user_id,
          email: formData.email,
        },
      });
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          "Registration failed"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Create Account"
      subtitle="Register and verify your email to continue"
    >
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box component="form" onSubmit={handleSubmit}>
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: { xs: "1fr", sm: "1fr 1fr" },
            gap: 2,
          }}
        >
          <TextField
            label="First Name"
            name="first_name"
            value={formData.first_name}
            onChange={handleChange}
            required
            fullWidth
          />

          <TextField
            label="Last Name"
            name="last_name"
            value={formData.last_name}
            onChange={handleChange}
            required
            fullWidth
          />
        </Box>

        <TextField
          label="Email Address"
          name="email"
          type="email"
          value={formData.email}
          onChange={handleChange}
          margin="normal"
          required
          fullWidth
        />

        <TextField
          label="Phone Number"
          name="phone"
          value={formData.phone}
          onChange={handleChange}
          margin="normal"
          required
          fullWidth
        />

        <TextField
          label="Password"
          name="password"
          type="password"
          value={formData.password}
          onChange={handleChange}
          margin="normal"
          required
          fullWidth
        />

        <Button
          type="submit"
          variant="contained"
          fullWidth
          size="large"
          disabled={loading}
          sx={{ mt: 3, py: 1.4, borderRadius: 2 }}
        >
          {loading ? <CircularProgress size={24} color="inherit" /> : "Register"}
        </Button>
      </Box>

      <Typography textAlign="center" mt={3}>
        Already have an account? <Link to="/login">Login</Link>
      </Typography>
    </AuthLayout>
  );
};

export default Register;
--------------------------------
import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  TextField,
  Typography,
} from "@mui/material";
import AuthLayout from "../../layouts/AuthLayout";
import { sendOtp, verifyOtp } from "../../api/authApi";

const VerifyOtp = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const [userId] = useState(location.state?.user_id || "");
  const [email] = useState(location.state?.email || "");
  const [otpCode, setOtpCode] = useState("");

  const [success, setSuccess] = useState(
    "OTP has been sent to your registered email."
  );
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);

  const handleVerifyOtp = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (!userId) {
      setError("User ID missing. Please register again.");
      return;
    }

    setLoading(true);

    try {
      await verifyOtp({
        user_id: Number(userId),
        otp_code: otpCode,
      });

      setSuccess("OTP verified successfully. Redirecting to login...");

      setTimeout(() => {
        navigate("/login");
      }, 1200);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          "OTP verification failed"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleResendOtp = async () => {
    setError("");
    setSuccess("");

    if (!email) {
      setError("Email missing. Please register again.");
      return;
    }

    setResendLoading(true);

    try {
      await sendOtp({ email });
      setSuccess("OTP resent successfully.");
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          "Failed to resend OTP"
      );
    } finally {
      setResendLoading(false);
    }
  };

  return (
    <AuthLayout title="Verify OTP" subtitle="Enter the OTP sent to your email">
      {email && (
        <Typography textAlign="center" color="text.secondary" mb={2}>
          Email: {email}
        </Typography>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box component="form" onSubmit={handleVerifyOtp}>
        <TextField
          label="OTP Code"
          value={otpCode}
          onChange={(e) => setOtpCode(e.target.value)}
          required
          fullWidth
        />

        <Button
          type="submit"
          variant="contained"
          fullWidth
          size="large"
          disabled={loading}
          sx={{ mt: 3, py: 1.4, borderRadius: 2 }}
        >
          {loading ? <CircularProgress size={24} color="inherit" /> : "Verify OTP"}
        </Button>
      </Box>

      <Button
        variant="text"
        fullWidth
        disabled={resendLoading}
        onClick={handleResendOtp}
        sx={{ mt: 2 }}
      >
        {resendLoading ? "Sending OTP..." : "Resend OTP"}
      </Button>

      <Typography textAlign="center" mt={2}>
        Wrong email? <Link to="/register">Register again</Link>
      </Typography>
    </AuthLayout>
  );
};

export default VerifyOtp;
-------------------------------
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  TextField,
  Typography,
} from "@mui/material";
import AuthLayout from "../../layouts/AuthLayout";
import useAuth from "../../hooks/useAuth";

const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (event) => {
    setFormData({
      ...formData,
      [event.target.name]: event.target.value,
    });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login({
        email: formData.email,
        password: formData.password,
      });

      navigate("/dashboard");
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          err.message ||
          "Login failed"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Welcome Back" subtitle="Login to continue to dashboard">
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box component="form" onSubmit={handleSubmit}>
        <TextField
          label="Email Address"
          name="email"
          type="email"
          value={formData.email}
          onChange={handleChange}
          required
          fullWidth
          margin="normal"
        />

        <TextField
          label="Password"
          name="password"
          type="password"
          value={formData.password}
          onChange={handleChange}
          required
          fullWidth
          margin="normal"
        />

        <Box textAlign="right" mt={1}>
          <Link to="/forgot-password">Forgot Password?</Link>
        </Box>

        <Button
          type="submit"
          variant="contained"
          fullWidth
          size="large"
          disabled={loading}
          sx={{ mt: 3, py: 1.4, borderRadius: 2 }}
        >
          {loading ? <CircularProgress size={24} color="inherit" /> : "Login"}
        </Button>
      </Box>

      <Typography textAlign="center" mt={3}>
        Don&apos;t have an account? <Link to="/register">Register</Link>
      </Typography>
    </AuthLayout>
  );
};

export default Login;
--------------------------------
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  TextField,
  Typography,
} from "@mui/material";
import AuthLayout from "../../layouts/AuthLayout";
import { forgotPassword } from "../../api/authApi";

const ForgotPassword = () => {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleForgotPassword = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    try {
      const response = await forgotPassword({ email });

      setSuccess("Password reset request created successfully.");

      setTimeout(() => {
        navigate("/reset-password", {
          state: {
            email,
            token: response?.token || "",
          },
        });
      }, 1000);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          "Forgot password request failed"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Forgot Password"
      subtitle="Enter your email to receive reset token"
    >
      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box component="form" onSubmit={handleForgotPassword}>
        <TextField
          label="Email Address"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          fullWidth
          margin="normal"
        />

        <Button
          type="submit"
          variant="contained"
          fullWidth
          size="large"
          disabled={loading}
          sx={{ mt: 3, py: 1.4, borderRadius: 2 }}
        >
          {loading ? <CircularProgress size={24} color="inherit" /> : "Continue"}
        </Button>
      </Box>

      <Typography textAlign="center" mt={3}>
        Remember password? <Link to="/login">Login</Link>
      </Typography>
    </AuthLayout>
  );
};

export default ForgotPassword;
------------------------------------
import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  TextField,
  Typography,
} from "@mui/material";
import AuthLayout from "../../layouts/AuthLayout";
import { resetPassword } from "../../api/authApi";

const ResetPassword = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const [token, setToken] = useState(location.state?.token || "");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleResetPassword = async (event) => {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (!token) {
      setError("Reset token is required.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("New password and confirm password do not match.");
      return;
    }

    setLoading(true);

    try {
      await resetPassword({
        token,
        new_password: newPassword,
      });

      setSuccess("Password reset successful. Redirecting to login...");

      setTimeout(() => {
        navigate("/login");
      }, 1200);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          "Password reset failed"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout
      title="Reset Password"
      subtitle="Enter your reset token and new password"
    >
      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box component="form" onSubmit={handleResetPassword}>
        <TextField
          label="Reset Token"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          required
          fullWidth
          margin="normal"
        />

        <TextField
          label="New Password"
          type="password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          required
          fullWidth
          margin="normal"
        />

        <TextField
          label="Confirm Password"
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
          fullWidth
          margin="normal"
        />

        <Button
          type="submit"
          variant="contained"
          fullWidth
          size="large"
          disabled={loading}
          sx={{ mt: 3, py: 1.4, borderRadius: 2 }}
        >
          {loading ? (
            <CircularProgress size={24} color="inherit" />
          ) : (
            "Reset Password"
          )}
        </Button>
      </Box>

      <Typography textAlign="center" mt={3}>
        Back to <Link to="/login">Login</Link>
      </Typography>
    </AuthLayout>
  );
};

export default ResetPassword;
------------------------------------
import { Box, Button, Typography } from "@mui/material";
import useAuth from "../../hooks/useAuth";

const Dashboard = () => {
  const { logout, user } = useAuth();

  return (
    <Box sx={{ p: 4 }}>
      <Typography variant="h4" fontWeight={800}>
        Budget Management Dashboard
      </Typography>

      <Typography mt={2}>
        Login successful. Welcome {user?.email || "User"}.
      </Typography>

      <Button variant="contained" color="error" sx={{ mt: 3 }} onClick={logout}>
        Logout
      </Button>
    </Box>
  );
};

export default Dashboard;
--------------------------------
import { Navigate } from "react-router-dom";

import Login from "../pages/auth/Login";
import Register from "../pages/auth/Register";
import VerifyOtp from "../pages/auth/VerifyOtp";
import ForgotPassword from "../pages/auth/ForgotPassword";
import ResetPassword from "../pages/auth/ResetPassword";

import Dashboard from "../pages/dashboard/Dashboard";

import PublicRoute from "../routes/PublicRoute";
import ProtectedRoute from "../routes/ProtectedRoute";

const routes = [
  {
    path: "/",
    element: <Navigate to="/dashboard" replace />,
  },
  {
    path: "/login",
    element: (
      <PublicRoute>
        <Login />
      </PublicRoute>
    ),
  },
  {
    path: "/register",
    element: (
      <PublicRoute>
        <Register />
      </PublicRoute>
    ),
  },
  {
    path: "/verify-otp",
    element: (
      <PublicRoute>
        <VerifyOtp />
      </PublicRoute>
    ),
  },
  {
    path: "/forgot-password",
    element: (
      <PublicRoute>
        <ForgotPassword />
      </PublicRoute>
    ),
  },
  {
    path: "/reset-password",
    element: (
      <PublicRoute>
        <ResetPassword />
      </PublicRoute>
    ),
  },
  {
    path: "/dashboard",
    element: (
      <ProtectedRoute>
        <Dashboard />
      </ProtectedRoute>
    ),
  },
  {
    path: "*",
    element: <Navigate to="/login" replace />,
  },
];

export default routes;
-------------------------------
import { useRoutes } from "react-router-dom";
import routes from "./routes";

const App = () => {
  const element = useRoutes(routes);
  return element;
};

export default App;
-------------------------------
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { CssBaseline } from "@mui/material";

import App from "./app/App";
import { AuthProvider } from "./context/AuthContext";

import "./styles/global.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <CssBaseline />
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
-----------------------
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { CssBaseline } from "@mui/material";

import App from "./app/App";
import { AuthProvider } from "./context/AuthContext";

import "./styles/global.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <CssBaseline />
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
---------------------
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: Arial, Helvetica, sans-serif;
}

a {
  color: #2563eb;
  text-decoration: none;
  font-weight: 600;
}

a:hover {
  text-decoration: underline;
}