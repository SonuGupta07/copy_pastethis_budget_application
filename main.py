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