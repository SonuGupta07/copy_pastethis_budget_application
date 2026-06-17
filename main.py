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

export const ROLES = {
  ADMIN: "ROLE_ADMIN",
  USER: "ROLE_USER",
};

export const navigationItems = [
  {
    section: "Overview",
    items: [
      {
        label: "Dashboard",
        path: "/dashboard",
        icon: <DashboardIcon />,
        roles: [ROLES.USER, ROLES.ADMIN],
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
        roles: [ROLES.USER, ROLES.ADMIN],
      },
      {
        label: "Expenses",
        path: "/expenses",
        icon: <ReceiptLongIcon />,
        roles: [ROLES.USER, ROLES.ADMIN],
      },
      {
        label: "Budgets",
        path: "/budgets",
        icon: <AccountBalanceWalletIcon />,
        roles: [ROLES.USER, ROLES.ADMIN],
      },
      {
        label: "Savings Goals",
        path: "/savings",
        icon: <SavingsIcon />,
        roles: [ROLES.USER, ROLES.ADMIN],
      },
      {
        label: "Recurring",
        path: "/recurring",
        icon: <RepeatIcon />,
        roles: [ROLES.USER, ROLES.ADMIN],
      },
      {
        label: "Categories",
        path: "/categories",
        icon: <CategoryIcon />,
        roles: [ROLES.USER, ROLES.ADMIN],
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
        roles: [ROLES.USER, ROLES.ADMIN],
      },
      {
        label: "AI Assistant",
        path: "/ai/budget-advisor",
        icon: <SmartToyIcon />,
        roles: [ROLES.USER, ROLES.ADMIN],
      },
      {
        label: "Notifications",
        path: "/notifications",
        icon: <NotificationsIcon />,
        roles: [ROLES.USER, ROLES.ADMIN],
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
        roles: [ROLES.ADMIN],
      },
      {
        label: "Role Management",
        path: "/admin/roles",
        icon: <SecurityIcon />,
        roles: [ROLES.ADMIN],
      },
      {
        label: "Audit Logs",
        path: "/admin/audit-logs",
        icon: <HistoryIcon />,
        roles: [ROLES.ADMIN],
      },
      {
        label: "Admin Panel",
        path: "/admin",
        icon: <AdminPanelSettingsIcon />,
        roles: [ROLES.ADMIN],
      },
    ],
  },
];
----------------------------
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
    Connect {`/dashboard/{user_id}`} and {`/financial-health/{user_id}`} APIs.
  </Typography>
</Box>