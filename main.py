import DashboardIcon from "@mui/icons-material/Dashboard";
import AccountBalanceWalletIcon from "@mui/icons-material/AccountBalanceWallet";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import ReceiptLongIcon from "@mui/icons-material/ReceiptLong";
import SavingsIcon from "@mui/icons-material/Savings";
import RepeatIcon from "@mui/icons-material/Repeat";
import CategoryIcon from "@mui/icons-material/Category";
import AnalyticsIcon from "@mui/icons-material/Analytics";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import NotificationsIcon from "@mui/icons-material/Notifications";
import AdminPanelSettingsIcon from "@mui/icons-material/AdminPanelSettings";
import ManageAccountsIcon from "@mui/icons-material/ManageAccounts";
import SecurityIcon from "@mui/icons-material/Security";
import HistoryIcon from "@mui/icons-material/History";

export const navigationItems = [
  {
    section: "Overview",
    items: [
      {
        label: "Dashboard",
        path: "/dashboard",
        icon: <DashboardIcon />,
        roles: ["USER", "ADMIN", "MANAGER"],
      },
    ],
  },
  {
    section: "Finance",
    items: [
      {
        label: "Income",
        path: "/income",
        icon: <TrendingUpIcon />,
        roles: ["USER", "ADMIN", "MANAGER"],
      },
      {
        label: "Expenses",
        path: "/expenses",
        icon: <ReceiptLongIcon />,
        roles: ["USER", "ADMIN", "MANAGER"],
      },
      {
        label: "Budgets",
        path: "/budgets",
        icon: <AccountBalanceWalletIcon />,
        roles: ["USER", "ADMIN", "MANAGER"],
      },
      {
        label: "Savings Goals",
        path: "/savings",
        icon: <SavingsIcon />,
        roles: ["USER", "ADMIN", "MANAGER"],
      },
      {
        label: "Recurring",
        path: "/recurring",
        icon: <RepeatIcon />,
        roles: ["USER", "ADMIN", "MANAGER"],
      },
      {
        label: "Categories",
        path: "/categories",
        icon: <CategoryIcon />,
        roles: ["USER", "ADMIN", "MANAGER"],
      },
    ],
  },
  {
    section: "Insights",
    items: [
      {
        label: "Analytics",
        path: "/analytics",
        icon: <AnalyticsIcon />,
        roles: ["USER", "ADMIN", "MANAGER"],
      },
      {
        label: "AI Assistant",
        path: "/ai/budget-advisor",
        icon: <SmartToyIcon />,
        roles: ["USER", "ADMIN", "MANAGER"],
      },
      {
        label: "Notifications",
        path: "/notifications",
        icon: <NotificationsIcon />,
        roles: ["USER", "ADMIN", "MANAGER"],
      },
    ],
  },
  {
    section: "Administration",
    items: [
      {
        label: "User Management",
        path: "/admin/users",
        icon: <ManageAccountsIcon />,
        roles: ["ADMIN"],
      },
      {
        label: "Role Management",
        path: "/admin/roles",
        icon: <SecurityIcon />,
        roles: ["ADMIN"],
      },
      {
        label: "Audit Logs",
        path: "/admin/audit-logs",
        icon: <HistoryIcon />,
        roles: ["ADMIN"],
      },
      {
        label: "Admin Panel",
        path: "/admin",
        icon: <AdminPanelSettingsIcon />,
        roles: ["ADMIN"],
      },
    ],
  },
];
----------------------------------------------------
import { Link, useLocation } from "react-router-dom";
import {
  Box,
  Chip,
  Divider,
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  useTheme,
} from "@mui/material";
import AccountBalanceWalletIcon from "@mui/icons-material/AccountBalanceWallet";
import { navigationItems } from "../../app/navigation";

const drawerWidth = 280;

const Sidebar = ({ mobileOpen, onClose, currentRole = "USER" }) => {
  const location = useLocation();
  const theme = useTheme();

  const drawerContent = (
    <Box
      sx={{
        height: "100%",
        background:
          theme.palette.mode === "dark"
            ? "linear-gradient(180deg, #0f172a 0%, #111827 100%)"
            : "linear-gradient(180deg, #ffffff 0%, #f8fafc 100%)",
        borderRight: `1px solid ${theme.palette.divider}`,
      }}
    >
      <Toolbar sx={{ px: 3, py: 2 }}>
        <Box display="flex" alignItems="center" gap={1.5}>
          <Box
            sx={{
              width: 44,
              height: 44,
              borderRadius: 3,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: "linear-gradient(135deg, #2563eb, #7c3aed)",
              color: "white",
            }}
          >
            <AccountBalanceWalletIcon />
          </Box>

          <Box>
            <Typography variant="h6" fontWeight={800} lineHeight={1.1}>
              BudgetPro
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Finance Manager
            </Typography>
          </Box>
        </Box>
      </Toolbar>

      <Box px={3} pb={2}>
        <Chip
          label={`${currentRole} Workspace`}
          color={currentRole === "ADMIN" ? "error" : "primary"}
          size="small"
          sx={{ fontWeight: 700 }}
        />
      </Box>

      <Divider />

      <Box sx={{ overflowY: "auto", height: "calc(100% - 140px)", px: 1.5 }}>
        {navigationItems.map((section) => {
          const visibleItems = section.items.filter((item) =>
            item.roles.includes(currentRole)
          );

          if (visibleItems.length === 0) return null;

          return (
            <Box key={section.section} mt={2}>
              <Typography
                variant="caption"
                color="text.secondary"
                fontWeight={800}
                sx={{ px: 2, textTransform: "uppercase", letterSpacing: 0.8 }}
              >
                {section.section}
              </Typography>

              <List dense>
                {visibleItems.map((item) => {
                  const active =
                    location.pathname === item.path ||
                    location.pathname.startsWith(`${item.path}/`);

                  return (
                    <ListItemButton
                      key={item.path}
                      component={Link}
                      to={item.path}
                      onClick={onClose}
                      sx={{
                        my: 0.5,
                        borderRadius: 3,
                        color: active ? "primary.main" : "text.primary",
                        backgroundColor: active
                          ? theme.palette.mode === "dark"
                            ? "rgba(59,130,246,0.16)"
                            : "rgba(37,99,235,0.10)"
                          : "transparent",
                        "&:hover": {
                          backgroundColor:
                            theme.palette.mode === "dark"
                              ? "rgba(255,255,255,0.06)"
                              : "rgba(15,23,42,0.06)",
                        },
                      }}
                    >
                      <ListItemIcon
                        sx={{
                          color: active ? "primary.main" : "text.secondary",
                          minWidth: 42,
                        }}
                      >
                        {item.icon}
                      </ListItemIcon>

                      <ListItemText
                        primary={item.label}
                        primaryTypographyProps={{
                          fontWeight: active ? 800 : 600,
                          fontSize: 14,
                        }}
                      />
                    </ListItemButton>
                  );
                })}
              </List>
            </Box>
          );
        })}
      </Box>
    </Box>
  );

  return (
    <>
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={onClose}
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: "block", lg: "none" },
          "& .MuiDrawer-paper": {
            width: drawerWidth,
            border: "none",
          },
        }}
      >
        {drawerContent}
      </Drawer>

      <Drawer
        variant="permanent"
        sx={{
          display: { xs: "none", lg: "block" },
          width: drawerWidth,
          flexShrink: 0,
          "& .MuiDrawer-paper": {
            width: drawerWidth,
            border: "none",
          },
        }}
        open
      >
        {drawerContent}
      </Drawer>
    </>
  );
};

export default Sidebar;
--------------------------------------------------------
import {
  AppBar,
  Avatar,
  Badge,
  Box,
  IconButton,
  InputBase,
  Menu,
  MenuItem,
  Toolbar,
  Tooltip,
  Typography,
  alpha,
  useTheme,
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import SearchIcon from "@mui/icons-material/Search";
import NotificationsNoneIcon from "@mui/icons-material/NotificationsNone";
import DarkModeIcon from "@mui/icons-material/DarkMode";
import LightModeIcon from "@mui/icons-material/LightMode";
import LogoutIcon from "@mui/icons-material/Logout";
import PersonIcon from "@mui/icons-material/Person";
import { useState } from "react";
import useAuth from "../../hooks/useAuth";

const drawerWidth = 280;

const Navbar = ({ onMenuClick, onThemeToggle, mode = "light" }) => {
  const theme = useTheme();
  const { user, logout } = useAuth();

  const [anchorEl, setAnchorEl] = useState(null);

  const userEmail = user?.email || "user@example.com";
  const initials = userEmail?.charAt(0)?.toUpperCase() || "U";

  return (
    <AppBar
      position="fixed"
      elevation={0}
      sx={{
        width: { lg: `calc(100% - ${drawerWidth}px)` },
        ml: { lg: `${drawerWidth}px` },
        backdropFilter: "blur(20px)",
        background:
          theme.palette.mode === "dark"
            ? "rgba(15,23,42,0.78)"
            : "rgba(255,255,255,0.82)",
        color: "text.primary",
        borderBottom: `1px solid ${theme.palette.divider}`,
      }}
    >
      <Toolbar sx={{ gap: 2 }}>
        <IconButton
          color="inherit"
          edge="start"
          onClick={onMenuClick}
          sx={{ display: { lg: "none" } }}
        >
          <MenuIcon />
        </IconButton>

        <Box>
          <Typography variant="h6" fontWeight={800}>
            Dashboard
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Track, plan and improve your financial health
          </Typography>
        </Box>

        <Box sx={{ flexGrow: 1 }} />

        <Box
          sx={{
            display: { xs: "none", md: "flex" },
            alignItems: "center",
            px: 2,
            py: 0.8,
            width: 320,
            borderRadius: 4,
            backgroundColor: alpha(theme.palette.text.primary, 0.06),
          }}
        >
          <SearchIcon fontSize="small" sx={{ mr: 1, color: "text.secondary" }} />
          <InputBase placeholder="Search transactions, budgets..." fullWidth />
        </Box>

        <Tooltip title="Notifications">
          <IconButton>
            <Badge badgeContent={3} color="error">
              <NotificationsNoneIcon />
            </Badge>
          </IconButton>
        </Tooltip>

        <Tooltip title="Toggle theme">
          <IconButton onClick={onThemeToggle}>
            {mode === "dark" ? <LightModeIcon /> : <DarkModeIcon />}
          </IconButton>
        </Tooltip>

        <Tooltip title="Account">
          <IconButton onClick={(event) => setAnchorEl(event.currentTarget)}>
            <Avatar
              sx={{
                width: 38,
                height: 38,
                fontWeight: 800,
                background: "linear-gradient(135deg, #2563eb, #7c3aed)",
              }}
            >
              {initials}
            </Avatar>
          </IconButton>
        </Tooltip>

        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={() => setAnchorEl(null)}
          PaperProps={{
            sx: {
              mt: 1.5,
              minWidth: 230,
              borderRadius: 3,
            },
          }}
        >
          <Box px={2} py={1.5}>
            <Typography fontWeight={800}>Signed in as</Typography>
            <Typography variant="body2" color="text.secondary">
              {userEmail}
            </Typography>
          </Box>

          <MenuItem onClick={() => setAnchorEl(null)}>
            <PersonIcon fontSize="small" sx={{ mr: 1 }} />
            Profile
          </MenuItem>

          <MenuItem onClick={logout}>
            <LogoutIcon fontSize="small" sx={{ mr: 1 }} />
            Logout
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;
--------------------------------------------
import { Box, Toolbar } from "@mui/material";
import { Outlet } from "react-router-dom";
import { useMemo, useState } from "react";
import { createTheme, ThemeProvider, CssBaseline } from "@mui/material";

import Sidebar from "../components/sidebar/Sidebar";
import Navbar from "../components/navbar/Navbar";
import useAuth from "../hooks/useAuth";

const DashboardLayout = () => {
  const { user } = useAuth();

  const [mobileOpen, setMobileOpen] = useState(false);
  const [mode, setMode] = useState(localStorage.getItem("themeMode") || "light");

  const currentRole = user?.role || "USER";

  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode,
          primary: {
            main: "#2563eb",
          },
          secondary: {
            main: "#7c3aed",
          },
          background: {
            default: mode === "dark" ? "#020617" : "#f8fafc",
            paper: mode === "dark" ? "#0f172a" : "#ffffff",
          },
        },
        shape: {
          borderRadius: 14,
        },
        typography: {
          fontFamily: "Inter, Arial, sans-serif",
          h4: {
            fontWeight: 800,
          },
          h5: {
            fontWeight: 800,
          },
          h6: {
            fontWeight: 800,
          },
        },
        components: {
          MuiCard: {
            styleOverrides: {
              root: {
                borderRadius: 22,
              },
            },
          },
          MuiButton: {
            styleOverrides: {
              root: {
                textTransform: "none",
                fontWeight: 700,
                borderRadius: 12,
              },
            },
          },
        },
      }),
    [mode]
  );

  const handleThemeToggle = () => {
    const nextMode = mode === "light" ? "dark" : "light";
    setMode(nextMode);
    localStorage.setItem("themeMode", nextMode);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />

      <Box sx={{ display: "flex", minHeight: "100vh" }}>
        <Navbar
          onMenuClick={() => setMobileOpen(true)}
          onThemeToggle={handleThemeToggle}
          mode={mode}
        />

        <Sidebar
          mobileOpen={mobileOpen}
          onClose={() => setMobileOpen(false)}
          currentRole={currentRole}
        />

        <Box
          component="main"
          sx={{
            flexGrow: 1,
            width: { lg: "calc(100% - 280px)" },
            minHeight: "100vh",
            background:
              mode === "dark"
                ? "radial-gradient(circle at top right, rgba(37,99,235,0.16), transparent 30%), #020617"
                : "radial-gradient(circle at top right, rgba(37,99,235,0.10), transparent 30%), #f8fafc",
          }}
        >
          <Toolbar />

          <Box sx={{ p: { xs: 2, md: 3 } }}>
            <Outlet />
          </Box>
        </Box>
      </Box>
    </ThemeProvider>
  );
};

export default DashboardLayout;
---------------------------------------------
import { Box, Breadcrumbs, Button, Typography } from "@mui/material";
import AddIcon from "@mui/icons-material/Add";
import NavigateNextIcon from "@mui/icons-material/NavigateNext";

const PageHeader = ({
  title,
  subtitle,
  actionText,
  onAction,
  breadcrumbs = [],
}) => {
  return (
    <Box
      sx={{
        mb: 3,
        display: "flex",
        justifyContent: "space-between",
        gap: 2,
        flexDirection: { xs: "column", md: "row" },
        alignItems: { xs: "flex-start", md: "center" },
      }}
    >
      <Box>
        {breadcrumbs.length > 0 && (
          <Breadcrumbs
            separator={<NavigateNextIcon fontSize="small" />}
            sx={{ mb: 1 }}
          >
            {breadcrumbs.map((item) => (
              <Typography key={item} variant="body2" color="text.secondary">
                {item}
              </Typography>
            ))}
          </Breadcrumbs>
        )}

        <Typography variant="h4" fontWeight={900}>
          {title}
        </Typography>

        {subtitle && (
          <Typography color="text.secondary" mt={0.5}>
            {subtitle}
          </Typography>
        )}
      </Box>

      {actionText && (
        <Button variant="contained" startIcon={<AddIcon />} onClick={onAction}>
          {actionText}
        </Button>
      )}
    </Box>
  );
};

export default PageHeader;
-------------------------------------------------
import {
  Box,
  Card,
  CardContent,
  Chip,
  Grid,
  LinearProgress,
  Stack,
  Typography,
} from "@mui/material";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import ReceiptLongIcon from "@mui/icons-material/ReceiptLong";
import AccountBalanceWalletIcon from "@mui/icons-material/AccountBalanceWallet";
import SavingsIcon from "@mui/icons-material/Savings";
import PageHeader from "../../components/common/PageHeader";

const statCards = [
  {
    title: "Total Income",
    value: "Connect API",
    icon: <TrendingUpIcon />,
    color: "#16a34a",
  },
  {
    title: "Total Expenses",
    value: "Connect API",
    icon: <ReceiptLongIcon />,
    color: "#dc2626",
  },
  {
    title: "Monthly Budget",
    value: "Connect API",
    icon: <AccountBalanceWalletIcon />,
    color: "#2563eb",
  },
  {
    title: "Savings Goals",
    value: "Connect API",
    icon: <SavingsIcon />,
    color: "#7c3aed",
  },
];

const Dashboard = () => {
  return (
    <Box>
      <PageHeader
        title="Financial Dashboard"
        subtitle="A complete overview of your income, expenses, budgets and savings."
        breadcrumbs={["Overview", "Dashboard"]}
      />

      <Grid container spacing={3}>
        {statCards.map((card) => (
          <Grid item xs={12} sm={6} lg={3} key={card.title}>
            <Card
              elevation={0}
              sx={{
                border: "1px solid",
                borderColor: "divider",
                height: "100%",
              }}
            >
              <CardContent>
                <Stack direction="row" justifyContent="space-between">
                  <Box>
                    <Typography color="text.secondary" fontWeight={700}>
                      {card.title}
                    </Typography>
                    <Typography variant="h5" mt={1}>
                      {card.value}
                    </Typography>
                  </Box>

                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: 3,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      color: "white",
                      background: card.color,
                    }}
                  >
                    {card.icon}
                  </Box>
                </Stack>

                <Chip
                  label="Waiting for backend data"
                  size="small"
                  sx={{ mt: 2 }}
                />
              </CardContent>
            </Card>
          </Grid>
        ))}

        <Grid item xs={12} lg={8}>
          <Card
            elevation={0}
            sx={{
              border: "1px solid",
              borderColor: "divider",
              minHeight: 350,
            }}
          >
            <CardContent>
              <Typography variant="h6">Spending Trend</Typography>
              <Typography color="text.secondary" mb={3}>
                Chart will be connected with analytics API.
              </Typography>

              <Stack spacing={2}>
                <Box>
                  <Typography variant="body2" fontWeight={700}>
                    Income vs Expense API
                  </Typography>
                  <LinearProgress variant="determinate" value={65} sx={{ mt: 1 }} />
                </Box>

                <Box>
                  <Typography variant="body2" fontWeight={700}>
                    Budget Usage API
                  </Typography>
                  <LinearProgress
                    color="secondary"
                    variant="determinate"
                    value={42}
                    sx={{ mt: 1 }}
                  />
                </Box>

                <Box>
                  <Typography variant="body2" fontWeight={700}>
                    Savings Goal API
                  </Typography>
                  <LinearProgress
                    color="success"
                    variant="determinate"
                    value={78}
                    sx={{ mt: 1 }}
                  />
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} lg={4}>
          <Card
            elevation={0}
            sx={{
              border: "1px solid",
              borderColor: "divider",
              minHeight: 350,
            }}
          >
            <CardContent>
              <Typography variant="h6">AI Financial Advisor</Typography>
              <Typography color="text.secondary" mt={1}>
                AI recommendations will appear here after connecting GenAI APIs.
              </Typography>

              <Box
                sx={{
                  mt: 3,
                  p: 2,
                  borderRadius: 3,
                  backgroundColor: "action.hover",
                }}
              >
                <Typography fontWeight={800}>Next Step</Typography>
                <Typography variant="body2" color="text.secondary">
                  Connect `/dashboard/{user_id}` and `/financial-health/{user_id}`
                  APIs.
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
----------------------------------------------------
import { Box, Card, CardContent, Chip, Typography } from "@mui/material";
import PageHeader from "../../components/common/PageHeader";

const ComingSoonPage = ({ title, subtitle }) => {
  return (
    <Box>
      <PageHeader
        title={title}
        subtitle={subtitle}
        breadcrumbs={["Budget Management", title]}
      />

      <Card
        elevation={0}
        sx={{
          border: "1px solid",
          borderColor: "divider",
          minHeight: 300,
        }}
      >
        <CardContent>
          <Chip label="UI module ready for development" color="primary" />

          <Typography variant="h5" mt={3} fontWeight={900}>
            {title}
          </Typography>

          <Typography color="text.secondary" mt={1}>
            This module will be connected with backend APIs in the next steps.
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default ComingSoonPage;
----------------------------------------------
import { Navigate } from "react-router-dom";

import Login from "../pages/auth/Login";
import Register from "../pages/auth/Register";
import VerifyOtp from "../pages/auth/VerifyOtp";
import ForgotPassword from "../pages/auth/ForgotPassword";
import ResetPassword from "../pages/auth/ResetPassword";

import DashboardLayout from "../layouts/DashboardLayout";
import Dashboard from "../pages/dashboard/Dashboard";
import ComingSoonPage from "../pages/common/ComingSoonPage";

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
    path: "/",
    element: (
      <ProtectedRoute>
        <DashboardLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        path: "dashboard",
        element: <Dashboard />,
      },
      {
        path: "income",
        element: (
          <ComingSoonPage
            title="Income Tracking"
            subtitle="Manage salary, business income, passive income and other sources."
          />
        ),
      },
      {
        path: "expenses",
        element: (
          <ComingSoonPage
            title="Expense Tracking"
            subtitle="Track daily spending, categories and monthly expense patterns."
          />
        ),
      },
      {
        path: "budgets",
        element: (
          <ComingSoonPage
            title="Budget Planning"
            subtitle="Create monthly budgets and monitor category-wise usage."
          />
        ),
      },
      {
        path: "savings",
        element: (
          <ComingSoonPage
            title="Savings Goals"
            subtitle="Plan goals, track progress and stay financially disciplined."
          />
        ),
      },
      {
        path: "recurring",
        element: (
          <ComingSoonPage
            title="Recurring Transactions"
            subtitle="Manage repeated income, EMI, rent and subscription transactions."
          />
        ),
      },
      {
        path: "categories",
        element: (
          <ComingSoonPage
            title="Category Management"
            subtitle="Organize income and expense categories."
          />
        ),
      },
      {
        path: "analytics",
        element: (
          <ComingSoonPage
            title="Analytics"
            subtitle="View pie charts, bar charts, trends and financial health score."
          />
        ),
      },
      {
        path: "notifications",
        element: (
          <ComingSoonPage
            title="Notifications"
            subtitle="View budget alerts, reminders and system notifications."
          />
        ),
      },
      {
        path: "ai/budget-advisor",
        element: (
          <ComingSoonPage
            title="AI Budget Advisor"
            subtitle="Get AI-powered budget advice and savings recommendations."
          />
        ),
      },
      {
        path: "admin/users",
        element: (
          <ComingSoonPage
            title="User Management"
            subtitle="Admin module for managing users."
          />
        ),
      },
      {
        path: "admin/roles",
        element: (
          <ComingSoonPage
            title="Role Management"
            subtitle="Admin module for roles and permissions."
          />
        ),
      },
      {
        path: "admin/audit-logs",
        element: (
          <ComingSoonPage
            title="Audit Logs"
            subtitle="Track user actions and security activities."
          />
        ),
      },
      {
        path: "admin",
        element: (
          <ComingSoonPage
            title="Admin Panel"
            subtitle="Central admin area for system configuration."
          />
        ),
      },
    ],
  },

  {
    path: "*",
    element: <Navigate to="/dashboard" replace />,
  },
];

export default routes;
-----------------------------------------
import { useRoutes } from "react-router-dom";
import routes from "./routes";

const App = () => {
  return useRoutes(routes);
};

export default App;
----------------------------------
const userData = {
  email: loginData.email,
  role: response?.role || response?.user?.role || "USER",
};





