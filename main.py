import api from "./axios";

export const getNotificationsByUser = async (userId) => {
  const response = await api.get(`/notifications/${userId}`);
  return response.data;
};

export const createNotification = async (data) => {
  const response = await api.post("/notifications/", data);
  return response.data;
};

export const markNotificationAsRead = async (notificationId) => {
  const response = await api.put(`/notifications/read/${notificationId}`);
  return response.data;
};

export const deleteNotification = async (notificationId) => {
  const response = await api.delete(`/notifications/${notificationId}`);
  return response.data;
};

export const getAllBudgets = async () => {
  const response = await api.get("/budget/");
  return response.data;
};

export const getAllExpenses = async () => {
  const response = await api.get("/expense/");
  return response.data;
};

export const getAllSavingsGoals = async () => {
  const response = await api.get("/savings/");
  return response.data;
};

export const getAllRecurringTransactions = async () => {
  const response = await api.get("/recurring/");
  return response.data;
};

export const getAllCategories = async () => {
  const response = await api.get("/categories/");
  return response.data;
};
---------------------------------
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  createNotification,
  deleteNotification,
  getAllBudgets,
  getAllCategories,
  getAllExpenses,
  getAllRecurringTransactions,
  getAllSavingsGoals,
  getNotificationsByUser,
  markNotificationAsRead,
} from "../api/notificationApi";
import { getUserIdFromToken } from "../utils/jwt";

const normalizeArray = (data) => {
  if (Array.isArray(data)) return data;
  if (!data) return [];
  return [data];
};

const getDaysRemaining = (dateValue) => {
  if (!dateValue) return null;

  const today = new Date();
  const target = new Date(dateValue);

  today.setHours(0, 0, 0, 0);
  target.setHours(0, 0, 0, 0);

  return Math.ceil((target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
};

const buildCategoryMap = (categories) => {
  const map = {};

  categories.forEach((category) => {
    map[Number(category.category_id)] = category.category_name;
  });

  return map;
};

const buildSmartAlerts = ({
  budgets,
  expenses,
  savingsGoals,
  recurringTransactions,
  categories,
  userId,
}) => {
  const alerts = [];
  const categoryMap = buildCategoryMap(categories);

  const userBudgets = budgets.filter(
    (item) => Number(item.user_id) === Number(userId)
  );

  const userExpenses = expenses.filter(
    (item) => Number(item.user_id) === Number(userId)
  );

  const userSavingsGoals = savingsGoals.filter(
    (item) => Number(item.user_id) === Number(userId)
  );

  const userRecurring = recurringTransactions.filter(
    (item) => Number(item.user_id) === Number(userId)
  );

  userBudgets.forEach((budget) => {
    const expenseForBudget = userExpenses
      .filter((expense) => {
        const expenseDate = new Date(expense.expense_date);

        return (
          Number(expense.category_id) === Number(budget.category_id) &&
          expenseDate.getMonth() + 1 === Number(budget.month) &&
          expenseDate.getFullYear() === Number(budget.year)
        );
      })
      .reduce((sum, expense) => sum + Number(expense.amount || 0), 0);

    const budgetAmount = Number(budget.budget_amount || 0);
    const usage = budgetAmount > 0 ? (expenseForBudget / budgetAmount) * 100 : 0;
    const categoryName = categoryMap[Number(budget.category_id)] || "Budget";

    if (usage >= 100) {
      alerts.push({
        type: "BUDGET_EXCEEDED",
        severity: "error",
        title: "Budget Exceeded",
        message: `${categoryName} budget exceeded. Usage is ${usage.toFixed(
          1
        )}% for ${budget.month}/${budget.year}.`,
      });
    } else if (usage >= 80) {
      alerts.push({
        type: "BUDGET_WARNING",
        severity: "warning",
        title: "Budget Warning",
        message: `${categoryName} budget reached ${usage.toFixed(
          1
        )}%. Monitor spending carefully.`,
      });
    }
  });

  userSavingsGoals.forEach((goal) => {
    const target = Number(goal.target_amount || 0);
    const current = Number(goal.current_amount || 0);
    const progress = target > 0 ? (current / target) * 100 : 0;
    const daysRemaining = getDaysRemaining(goal.target_date);

    if (progress >= 100) {
      alerts.push({
        type: "SAVINGS_COMPLETED",
        severity: "success",
        title: "Savings Goal Completed",
        message: `${goal.goal_name} has reached the target amount.`,
      });
    } else if (daysRemaining !== null && daysRemaining < 0) {
      alerts.push({
        type: "SAVINGS_OVERDUE",
        severity: "error",
        title: "Savings Goal Overdue",
        message: `${goal.goal_name} target date is overdue by ${Math.abs(
          daysRemaining
        )} day(s).`,
      });
    } else if (daysRemaining !== null && daysRemaining <= 7) {
      alerts.push({
        type: "SAVINGS_DUE_SOON",
        severity: "warning",
        title: "Savings Goal Due Soon",
        message: `${goal.goal_name} target date is due in ${daysRemaining} day(s).`,
      });
    }
  });

  userRecurring.forEach((item) => {
    const daysRemaining = getDaysRemaining(item.next_run_date);
    const categoryName = categoryMap[Number(item.category_id)] || "Recurring";

    if (daysRemaining !== null && daysRemaining < 0) {
      alerts.push({
        type: "RECURRING_OVERDUE",
        severity: "error",
        title: "Recurring Transaction Overdue",
        message: `${categoryName} recurring transaction is overdue by ${Math.abs(
          daysRemaining
        )} day(s).`,
      });
    } else if (daysRemaining !== null && daysRemaining <= 7) {
      alerts.push({
        type: "RECURRING_DUE_SOON",
        severity: "info",
        title: "Recurring Transaction Due Soon",
        message: `${categoryName} recurring transaction is due in ${daysRemaining} day(s).`,
      });
    }
  });

  const currentMonth = new Date().getMonth() + 1;
  const currentYear = new Date().getFullYear();

  const currentMonthExpenses = userExpenses.filter((expense) => {
    const date = new Date(expense.expense_date);

    return date.getMonth() + 1 === currentMonth && date.getFullYear() === currentYear;
  });

  const totalCurrentMonthExpense = currentMonthExpenses.reduce(
    (sum, expense) => sum + Number(expense.amount || 0),
    0
  );

  if (totalCurrentMonthExpense > 50000) {
    alerts.push({
      type: "HIGH_EXPENSE",
      severity: "warning",
      title: "High Monthly Expense",
      message: `Current month expense is ₹${totalCurrentMonthExpense.toLocaleString(
        "en-IN"
      )}. Review spending patterns.`,
    });
  }

  return alerts;
};

const useNotifications = () => {
  const userId = useMemo(() => getUserIdFromToken(), []);

  const [notifications, setNotifications] = useState([]);
  const [smartAlerts, setSmartAlerts] = useState([]);

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const [error, setError] = useState("");

  const fetchNotifications = useCallback(async () => {
    if (!userId) {
      setError("User ID not found in token. Please login again.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const results = await Promise.allSettled([
        getNotificationsByUser(userId),
        getAllBudgets(),
        getAllExpenses(),
        getAllSavingsGoals(),
        getAllRecurringTransactions(),
        getAllCategories(),
      ]);

      const userNotifications =
        results[0].status === "fulfilled" ? normalizeArray(results[0].value) : [];

      const budgets =
        results[1].status === "fulfilled" ? normalizeArray(results[1].value) : [];

      const expenses =
        results[2].status === "fulfilled" ? normalizeArray(results[2].value) : [];

      const savingsGoals =
        results[3].status === "fulfilled" ? normalizeArray(results[3].value) : [];

      const recurringTransactions =
        results[4].status === "fulfilled" ? normalizeArray(results[4].value) : [];

      const categories =
        results[5].status === "fulfilled" ? normalizeArray(results[5].value) : [];

      setNotifications(
        userNotifications.sort(
          (a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0)
        )
      );

      setSmartAlerts(
        buildSmartAlerts({
          budgets,
          expenses,
          savingsGoals,
          recurringTransactions,
          categories,
          userId,
        })
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          "Failed to load notifications"
      );
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const addNotification = async (payload) => {
    if (!userId) {
      throw new Error("User ID not found in token. Please login again.");
    }

    setSaving(true);
    setError("");

    try {
      await createNotification({
        user_id: Number(userId),
        title: payload.title,
        message: payload.message,
      });

      await fetchNotifications();
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        "Failed to create notification";

      setError(message);
      throw new Error(message);
    } finally {
      setSaving(false);
    }
  };

  const saveSmartAlertAsNotification = async (alert) => {
    await addNotification({
      title: alert.title,
      message: alert.message,
    });
  };

  const markAsRead = async (notificationId) => {
    setUpdating(true);
    setError("");

    try {
      await markNotificationAsRead(notificationId);
      await fetchNotifications();
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        "Failed to mark notification as read";

      setError(message);
      throw new Error(message);
    } finally {
      setUpdating(false);
    }
  };

  const markAllAsRead = async () => {
    const unread = notifications.filter((item) => item.is_read !== "Y");

    setUpdating(true);
    setError("");

    try {
      await Promise.all(
        unread.map((item) => markNotificationAsRead(item.notification_id))
      );

      await fetchNotifications();
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        "Failed to mark all notifications as read";

      setError(message);
      throw new Error(message);
    } finally {
      setUpdating(false);
    }
  };

  const removeNotification = async (notificationId) => {
    setDeleting(true);
    setError("");

    try {
      await deleteNotification(notificationId);
      await fetchNotifications();
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        "Failed to delete notification";

      setError(message);
      throw new Error(message);
    } finally {
      setDeleting(false);
    }
  };

  const unreadCount = useMemo(() => {
    return notifications.filter((item) => item.is_read !== "Y").length;
  }, [notifications]);

  const totalAlertCount = unreadCount + smartAlerts.length;

  return {
    userId,
    notifications,
    smartAlerts,
    unreadCount,
    totalAlertCount,
    loading,
    saving,
    updating,
    deleting,
    error,
    fetchNotifications,
    addNotification,
    saveSmartAlertAsNotification,
    markAsRead,
    markAllAsRead,
    removeNotification,
  };
};

export default useNotifications;
--------------------------------------------------
import { useState } from "react";
import {
  Badge,
  Box,
  Button,
  Divider,
  IconButton,
  Menu,
  MenuItem,
  Stack,
  Typography,
} from "@mui/material";
import NotificationsIcon from "@mui/icons-material/Notifications";
import DoneAllIcon from "@mui/icons-material/DoneAll";
import { useNavigate } from "react-router-dom";
import useNotifications from "../../hooks/useNotifications";

const NotificationBell = () => {
  const navigate = useNavigate();
  const {
    notifications,
    smartAlerts,
    totalAlertCount,
    markAsRead,
    markAllAsRead,
  } = useNotifications();

  const [anchorEl, setAnchorEl] = useState(null);

  const open = Boolean(anchorEl);

  const handleOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const latestNotifications = notifications.slice(0, 4);
  const latestSmartAlerts = smartAlerts.slice(0, 3);

  return (
    <>
      <IconButton color="inherit" onClick={handleOpen}>
        <Badge badgeContent={totalAlertCount} color="error">
          <NotificationsIcon />
        </Badge>
      </IconButton>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        PaperProps={{
          sx: {
            width: 380,
            maxWidth: "95vw",
            borderRadius: 3,
          },
        }}
      >
        <Box px={2} py={1.5}>
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Box>
              <Typography fontWeight={900}>Notifications</Typography>
              <Typography variant="body2" color="text.secondary">
                {totalAlertCount} active alert(s)
              </Typography>
            </Box>

            <IconButton size="small" onClick={markAllAsRead}>
              <DoneAllIcon fontSize="small" />
            </IconButton>
          </Stack>
        </Box>

        <Divider />

        {latestSmartAlerts.length > 0 && (
          <Box px={2} py={1}>
            <Typography variant="caption" color="text.secondary" fontWeight={800}>
              SMART FINANCE ALERTS
            </Typography>

            {latestSmartAlerts.map((alert) => (
              <MenuItem key={`${alert.type}-${alert.message}`} sx={{ whiteSpace: "normal" }}>
                <Box>
                  <Typography fontWeight={800}>{alert.title}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {alert.message}
                  </Typography>
                </Box>
              </MenuItem>
            ))}
          </Box>
        )}

        {latestNotifications.length > 0 && (
          <Box px={2} py={1}>
            <Typography variant="caption" color="text.secondary" fontWeight={800}>
              SYSTEM NOTIFICATIONS
            </Typography>

            {latestNotifications.map((notification) => (
              <MenuItem
                key={notification.notification_id}
                sx={{ whiteSpace: "normal" }}
                onClick={() => {
                  if (notification.is_read !== "Y") {
                    markAsRead(notification.notification_id);
                  }
                }}
              >
                <Box>
                  <Typography fontWeight={800}>{notification.title}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {notification.message}
                  </Typography>
                </Box>
              </MenuItem>
            ))}
          </Box>
        )}

        {latestNotifications.length === 0 && latestSmartAlerts.length === 0 && (
          <Box px={2} py={4} textAlign="center">
            <Typography color="text.secondary">No notifications found.</Typography>
          </Box>
        )}

        <Divider />

        <Box px={2} py={1.5}>
          <Button
            fullWidth
            variant="contained"
            onClick={() => {
              handleClose();
              navigate("/notifications");
            }}
          >
            View All Notifications
          </Button>
        </Box>
      </Menu>
    </>
  );
};

export default NotificationBell;
----------------------------------------
import { useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  IconButton,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import NotificationsActiveIcon from "@mui/icons-material/NotificationsActive";
import DoneIcon from "@mui/icons-material/Done";
import DeleteIcon from "@mui/icons-material/Delete";
import RefreshIcon from "@mui/icons-material/Refresh";
import AddIcon from "@mui/icons-material/Add";
import SaveIcon from "@mui/icons-material/Save";
import PageHeader from "../../components/common/PageHeader";
import useNotifications from "../../hooks/useNotifications";

const formatDate = (value) => {
  if (!value) return "-";

  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
};

const getAlertColor = (severity) => {
  if (severity === "error") return "error";
  if (severity === "warning") return "warning";
  if (severity === "success") return "success";
  return "info";
};

const NotificationsPage = () => {
  const {
    notifications,
    smartAlerts,
    unreadCount,
    loading,
    saving,
    updating,
    deleting,
    error,
    fetchNotifications,
    addNotification,
    saveSmartAlertAsNotification,
    markAsRead,
    markAllAsRead,
    removeNotification,
  } = useNotifications();

  const [open, setOpen] = useState(false);
  const [formError, setFormError] = useState("");
  const [formData, setFormData] = useState({
    title: "",
    message: "",
  });

  const handleOpen = () => {
    setFormError("");
    setFormData({
      title: "",
      message: "",
    });
    setOpen(true);
  };

  const handleClose = () => {
    if (!saving) {
      setOpen(false);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setFormError("");

    if (!formData.title.trim()) {
      setFormError("Title is required");
      return;
    }

    if (!formData.message.trim()) {
      setFormError("Message is required");
      return;
    }

    try {
      await addNotification({
        title: formData.title.trim(),
        message: formData.message.trim(),
      });

      handleClose();
    } catch (err) {
      setFormError(err.message || "Failed to create notification");
    }
  };

  return (
    <Box>
      <PageHeader
        title="Notifications & Alerts"
        subtitle="Track finance alerts, smart warnings, recurring reminders and system notifications."
        breadcrumbs={["Insights", "Notifications"]}
        actionText="Create Notification"
        onAction={handleOpen}
      />

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={4}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Typography color="text.secondary" fontWeight={800}>
                Total Notifications
              </Typography>
              <Typography variant="h4" fontWeight={900}>
                {notifications.length}
              </Typography>
              <Typography color="text.secondary">Stored in database</Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Typography color="text.secondary" fontWeight={800}>
                Unread Notifications
              </Typography>
              <Typography variant="h4" fontWeight={900} color="error.main">
                {unreadCount}
              </Typography>
              <Typography color="text.secondary">Need user attention</Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Typography color="text.secondary" fontWeight={800}>
                Smart Finance Alerts
              </Typography>
              <Typography variant="h4" fontWeight={900} color="warning.main">
                {smartAlerts.length}
              </Typography>
              <Typography color="text.secondary">Generated from finance data</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Stack
        direction={{ xs: "column", sm: "row" }}
        spacing={2}
        justifyContent="space-between"
        mb={3}
      >
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchNotifications}
          >
            Refresh
          </Button>

          <Button
            variant="outlined"
            startIcon={<DoneIcon />}
            disabled={updating || unreadCount === 0}
            onClick={markAllAsRead}
          >
            Mark All Read
          </Button>
        </Stack>

        <Button variant="contained" startIcon={<AddIcon />} onClick={handleOpen}>
          Create Notification
        </Button>
      </Stack>

      {loading ? (
        <Box display="flex" justifyContent="center" py={8}>
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={3}>
          <Grid item xs={12} lg={6}>
            <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
              <CardContent>
                <Typography variant="h6" fontWeight={900} mb={2}>
                  Smart Finance Alerts
                </Typography>

                {smartAlerts.length === 0 ? (
                  <Box
                    sx={{
                      py: 6,
                      border: "1px dashed",
                      borderColor: "divider",
                      borderRadius: 3,
                      textAlign: "center",
                    }}
                  >
                    <Typography color="text.secondary">
                      No smart alerts found. Your finance data looks stable.
                    </Typography>
                  </Box>
                ) : (
                  <Stack spacing={2}>
                    {smartAlerts.map((alert) => (
                      {<Tooltip title="Save as database notification">
                            <IconButton
                              color="inherit"
                              size="small"
                              onClick={() => saveSmartAlertAsNotification(alert)}
                            >
                              <SaveIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        }
                      >
                        <Typography fontWeight={900}>{alert.title}</Typography>
                        <Typography variant="body2">{alert.message}</Typography>
                      </Alert>
                    ))}
                  </Stack>
                )}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} lg={6}>
            <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
              <CardContent>
                <Typography variant="h6" fontWeight={900} mb={2}>
                  System Notifications
                </Typography>

                {notifications.length === 0 ? (
                  <Box
                    sx={{
                      py: 6,
                      border: "1px dashed",
                      borderColor: "divider",
                      borderRadius: 3,
                      textAlign: "center",
                    }}
                  >
                    <Typography color="text.secondary">
                      No database notifications found.
                    </Typography>
                  </Box>
                ) : (
                  <Stack spacing={2}>
                    {notifications.map((notification) => (
                      <Card
                        key={notification.notification_id}
                        elevation={0}
                        sx={{
                          border: "1px solid",
                          borderColor:
                            notification.is_read === "Y" ? "divider" : "primary.main",
                          backgroundColor:
                            notification.is_read === "Y"
                              ? "background.paper"
                              : "action.hover",
                        }}
                      >
                        <CardContent>
                          <Stack
                            direction="row"
                            justifyContent="space-between"
                            alignItems="flex-start"
                            spacing={2}
                          >
                            <Box>
                              <Stack direction="row" spacing={1} alignItems="center">
                                <NotificationsActiveIcon color="primary" />
                                <Typography fontWeight={900}>
                                  {notification.title}
                                </Typography>

                                <Chip
                                  label={
                                    notification.is_read === "Y" ? "Read" : "Unread"
                                  }
                                  color={
                                    notification.is_read === "Y" ? "default" : "primary"
                                  }
                                  size="small"
                                />
                              </Stack>

                              <Typography color="text.secondary" mt={1}>
                                {notification.message}
                              </Typography>

                              <Typography
                                variant="caption"
                                color="text.secondary"
                                display="block"
                                mt={1}
                              >
                                {formatDate(notification.created_at)}
                              </Typography>
                            </Box>

                            <Stack direction="row">
                              {notification.is_read !== "Y" && (
                                <Tooltip title="Mark as read">
                                  <IconButton
                                    color="success"
                                    disabled={updating}
                                    onClick={() =>
                                      markAsRead(notification.notification_id)
                                    }
                                  >
                                    <DoneIcon />
                                  </IconButton>
                                </Tooltip>
                              )}

                              <Tooltip title="Delete notification">
                                <IconButton
                                  color="error"
                                  disabled={deleting}
                                  onClick={() =>
                                    removeNotification(notification.notification_id)
                                  }
                                >
                                  <DeleteIcon />
                                </IconButton>
                              </Tooltip>
                            </Stack>
                          </Stack>
                        </CardContent>
                      </Card>
                    ))}
                  </Stack>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm">
        <DialogTitle fontWeight={900}>Create Notification</DialogTitle>

        <Box component="form" onSubmit={handleSubmit}>
          <DialogContent>
            {formError && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {formError}
              </Alert>
            )}

            <TextField
              label="Title"
              value={formData.title}
              onChange={(event) =>
                setFormData({ ...formData, title: event.target.value })
              }
              fullWidth
              required
              margin="normal"
              placeholder="Example: Budget Alert"
            />

            <TextField
              label="Message"
              value={formData.message}
              onChange={(event) =>
                setFormData({ ...formData, message: event.target.value })
              }
              fullWidth
              required
              multiline
              rows={4}
              margin="normal"
              placeholder="Example: Food budget crossed 80%."
            />
          </DialogContent>

          <DialogActions sx={{ px: 3, pb: 3 }}>
            <Button onClick={handleClose} disabled={saving}>
              Cancel
            </Button>

            <Button type="submit" variant="contained" disabled={saving}>
              {saving ? "Creating..." : "Create"}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>
    </Box>
  );
};

export default NotificationsPage;
----------------------------------------------