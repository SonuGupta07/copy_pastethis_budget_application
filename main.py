import api from "./axios";

export const getSavingsGoals = async () => {
  const response = await api.get("/savings/");
  return response.data;
};

export const createSavingsGoal = async (data) => {
  const response = await api.post("/savings/", data);
  return response.data;
};

export const updateSavingsGoal = async (goalId, data) => {
  const response = await api.put(`/savings/${goalId}`, data);
  return response.data;
};

export const deleteSavingsGoal = async (goalId) => {
  const response = await api.delete(`/savings/${goalId}`);
  return response.data;
};

export const getSavingsGoalProgress = async (goalId) => {
  const response = await api.get(`/savings/progress/${goalId}`);
  return response.data;
};
--------------------------------
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  createSavingsGoal,
  deleteSavingsGoal,
  getSavingsGoalProgress,
  getSavingsGoals,
  updateSavingsGoal,
} from "../api/savingsApi";
import { getUserIdFromToken } from "../utils/jwt";

const useSavings = () => {
  const [goals, setGoals] = useState([]);
  const [selectedProgress, setSelectedProgress] = useState(null);

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [progressLoading, setProgressLoading] = useState(false);

  const [error, setError] = useState("");

  const userId = useMemo(() => getUserIdFromToken(), []);

  const fetchGoals = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await getSavingsGoals();
      const list = Array.isArray(data) ? data : [];

      const userSpecificGoals = userId
        ? list.filter((goal) => Number(goal.user_id) === Number(userId))
        : list;

      setGoals(userSpecificGoals);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          "Failed to load savings goals"
      );
    } finally {
      setLoading(false);
    }
  }, [userId]);

  const addGoal = async (payload) => {
    setSaving(true);
    setError("");

    try {
      if (!userId) {
        throw new Error("User ID not found in token. Please login again.");
      }

      await createSavingsGoal({
        user_id: Number(userId),
        goal_name: payload.goal_name,
        target_amount: Number(payload.target_amount),
        current_amount: Number(payload.current_amount),
        target_date: payload.target_date,
      });

      await fetchGoals();
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "Failed to create savings goal";

      setError(message);
      throw new Error(message);
    } finally {
      setSaving(false);
    }
  };

  const editGoal = async (goalId, payload) => {
    setSaving(true);
    setError("");

    try {
      await updateSavingsGoal(goalId, {
        goal_name: payload.goal_name,
        target_amount: Number(payload.target_amount),
        current_amount: Number(payload.current_amount),
        target_date: payload.target_date,
      });

      await fetchGoals();
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        "Failed to update savings goal";

      setError(message);
      throw new Error(message);
    } finally {
      setSaving(false);
    }
  };

  const removeGoal = async (goalId) => {
    setDeleting(true);
    setError("");

    try {
      await deleteSavingsGoal(goalId);
      await fetchGoals();
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        "Failed to delete savings goal";

      setError(message);
      throw new Error(message);
    } finally {
      setDeleting(false);
    }
  };

  const fetchGoalProgress = async (goalId) => {
    setProgressLoading(true);
    setSelectedProgress(null);

    try {
      const data = await getSavingsGoalProgress(goalId);
      setSelectedProgress(data);
      return data;
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        "Failed to load goal progress";

      setError(message);
      throw new Error(message);
    } finally {
      setProgressLoading(false);
    }
  };

  useEffect(() => {
    fetchGoals();
  }, [fetchGoals]);

  return {
    goals,
    selectedProgress,
    loading,
    saving,
    deleting,
    progressLoading,
    error,
    userId,
    fetchGoals,
    addGoal,
    editGoal,
    removeGoal,
    fetchGoalProgress,
  };
};

export default useSavings;
---------------------------------------
import { useMemo, useState } from "react";
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
  InputAdornment,
  LinearProgress,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import SavingsIcon from "@mui/icons-material/Savings";
import AddIcon from "@mui/icons-material/Add";
import RefreshIcon from "@mui/icons-material/Refresh";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import FlagIcon from "@mui/icons-material/Flag";
import EventIcon from "@mui/icons-material/Event";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import PageHeader from "../../components/common/PageHeader";
import useSavings from "../../hooks/useSavings";

const getToday = () => new Date().toISOString().slice(0, 10);

const formatCurrency = (value) => {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(Number(value || 0));
};

const formatDate = (value) => {
  if (!value) return "-";

  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(value));
};

const getProgress = (currentAmount, targetAmount) => {
  if (!targetAmount || Number(targetAmount) <= 0) return 0;
  return (Number(currentAmount || 0) / Number(targetAmount)) * 100;
};

const getRemainingAmount = (currentAmount, targetAmount) => {
  return Math.max(Number(targetAmount || 0) - Number(currentAmount || 0), 0);
};

const getDaysRemaining = (targetDate) => {
  if (!targetDate) return null;

  const today = new Date();
  const target = new Date(targetDate);

  today.setHours(0, 0, 0, 0);
  target.setHours(0, 0, 0, 0);

  const difference = target.getTime() - today.getTime();
  return Math.ceil(difference / (1000 * 60 * 60 * 24));
};

const getGoalStatus = (goal) => {
  const progress = getProgress(goal.current_amount, goal.target_amount);
  const daysRemaining = getDaysRemaining(goal.target_date);

  if (progress >= 100 || goal.status === "COMPLETED") {
    return {
      label: "COMPLETED",
      color: "success",
    };
  }

  if (daysRemaining !== null && daysRemaining < 0) {
    return {
      label: "OVERDUE",
      color: "error",
    };
  }

  return {
    label: "IN PROGRESS",
    color: "primary",
  };
};

const SavingsPage = () => {
  const {
    goals,
    loading,
    saving,
    deleting,
    error,
    fetchGoals,
    addGoal,
    editGoal,
    removeGoal,
  } = useSavings();

  const [open, setOpen] = useState(false);
  const [editingGoal, setEditingGoal] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [formError, setFormError] = useState("");
  const [search, setSearch] = useState("");

  const [formData, setFormData] = useState({
    goal_name: "",
    target_amount: "",
    current_amount: "",
    target_date: getToday(),
  });

  const totalTargetAmount = useMemo(() => {
    return goals.reduce((sum, goal) => sum + Number(goal.target_amount || 0), 0);
  }, [goals]);

  const totalSavedAmount = useMemo(() => {
    return goals.reduce((sum, goal) => sum + Number(goal.current_amount || 0), 0);
  }, [goals]);

  const completedGoalsCount = useMemo(() => {
    return goals.filter(
      (goal) =>
        getProgress(goal.current_amount, goal.target_amount) >= 100 ||
        goal.status === "COMPLETED"
    ).length;
  }, [goals]);

  const overallProgress = useMemo(() => {
    if (totalTargetAmount <= 0) return 0;
    return (totalSavedAmount / totalTargetAmount) * 100;
  }, [totalSavedAmount, totalTargetAmount]);

  const filteredGoals = useMemo(() => {
    return goals.filter((goal) =>
      goal.goal_name?.toLowerCase().includes(search.toLowerCase())
    );
  }, [goals, search]);

  const handleOpenAdd = () => {
    setEditingGoal(null);
    setFormError("");
    setFormData({
      goal_name: "",
      target_amount: "",
      current_amount: "",
      target_date: getToday(),
    });
    setOpen(true);
  };

  const handleOpenEdit = (goal) => {
    setEditingGoal(goal);
    setFormError("");
    setFormData({
      goal_name: goal.goal_name || "",
      target_amount: goal.target_amount || "",
      current_amount: goal.current_amount || "",
      target_date: goal.target_date || getToday(),
    });
    setOpen(true);
  };

  const handleClose = () => {
    if (!saving) {
      setOpen(false);
      setEditingGoal(null);
    }
  };

  const handleChange = (event) => {
    setFormData({
      ...formData,
      [event.target.name]: event.target.value,
    });
  };

  const validateForm = () => {
    if (!formData.goal_name.trim()) {
      return "Goal name is required";
    }

    if (!formData.target_amount || Number(formData.target_amount) <= 0) {
      return "Target amount must be greater than zero";
    }

    if (formData.current_amount === "" || Number(formData.current_amount) < 0) {
      return "Current amount cannot be negative";
    }

    if (Number(formData.current_amount) > Number(formData.target_amount) * 2) {
      return "Current amount looks too high compared to target amount";
    }

    if (!formData.target_date) {
      return "Target date is required";
    }

    return "";
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setFormError("");

    const validationError = validateForm();

    if (validationError) {
      setFormError(validationError);
      return;
    }

    try {
      const payload = {
        goal_name: formData.goal_name.trim(),
        target_amount: formData.target_amount,
        current_amount: formData.current_amount,
        target_date: formData.target_date,
      };

      if (editingGoal) {
        await editGoal(editingGoal.goal_id, payload);
      } else {
        await addGoal(payload);
      }

      handleClose();
    } catch (err) {
      setFormError(err.message || "Something went wrong");
    }
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;

    try {
      await removeGoal(deleteTarget.goal_id);
      setDeleteTarget(null);
    } catch {
      // Hook handles error
    }
  };

  return (
    <Box>
      <PageHeader
        title="Savings Goals"
        subtitle="Plan, track and complete personal savings goals with clear progress insights."
        breadcrumbs={["Finance", "Savings Goals"]}
        actionText="Add Goal"
        onAction={handleOpenAdd}
      />

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={3}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Box
                  sx={{
                    width: 50,
                    height: 50,
                    borderRadius: 3,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "white",
                    background: "linear-gradient(135deg, #7c3aed, #2563eb)",
                  }}
                >
                  <SavingsIcon />
                </Box>

                <Box>
                  <Typography color="text.secondary" fontWeight={700}>
                    Total Target
                  </Typography>
                  <Typography variant="h5" fontWeight={900}>
                    {formatCurrency(totalTargetAmount)}
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Typography color="text.secondary" fontWeight={700}>
                Total Saved
              </Typography>
              <Typography variant="h5" fontWeight={900} color="success.main">
                {formatCurrency(totalSavedAmount)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Across all active goals.
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Typography color="text.secondary" fontWeight={700}>
                Overall Progress
              </Typography>
              <Typography variant="h5" fontWeight={900}>
                {overallProgress.toFixed(1)}%
              </Typography>
              <LinearProgress
                variant="determinate"
                value={Math.min(overallProgress, 100)}
                color={overallProgress >= 100 ? "success" : "primary"}
                sx={{ height: 8, borderRadius: 10, mt: 1.5 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Typography color="text.secondary" fontWeight={700}>
                Completed Goals
              </Typography>
              <Typography variant="h5" fontWeight={900} color="success.main">
                {completedGoalsCount}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Goals reached successfully.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
        <CardContent>
          <Stack
            direction={{ xs: "column", md: "row" }}
            justifyContent="space-between"
            spacing={2}
            mb={3}
          >
            <TextField
              label="Search goals"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              size="small"
              sx={{ minWidth: { xs: "100%", md: 320 } }}
            />

            <Stack direction="row" spacing={2}>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={fetchGoals}
              >
                Refresh
              </Button>

              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleOpenAdd}
              >
                Add Goal
              </Button>
            </Stack>
          </Stack>

          {loading ? (
            <Box display="flex" justifyContent="center" py={6}>
              <CircularProgress />
            </Box>
          ) : filteredGoals.length === 0 ? (
            <Box
              sx={{
                py: 8,
                textAlign: "center",
                border: "1px dashed",
                borderColor: "divider",
                borderRadius: 3,
              }}
            >
              <Typography variant="h6" fontWeight={900}>
                No savings goals found
              </Typography>

              <Typography color="text.secondary" mt={1}>
                Create your first goal to start tracking your savings journey.
              </Typography>

              <Button
                variant="contained"
                startIcon={<AddIcon />}
                sx={{ mt: 3 }}
                onClick={handleOpenAdd}
              >
                Add Savings Goal
              </Button>
            </Box>
          ) : (
            <Grid container spacing={3}>
              {filteredGoals.map((goal) => {
                const progress = getProgress(goal.current_amount, goal.target_amount);
                const remainingAmount = getRemainingAmount(
                  goal.current_amount,
                  goal.target_amount
                );
                const daysRemaining = getDaysRemaining(goal.target_date);
                const status = getGoalStatus(goal);

                return (
                  <Grid item xs={12} md={6} lg={4} key={goal.goal_id}>
                    <Card
                      elevation={0}
                      sx={{
                        height: "100%",
                        border: "1px solid",
                        borderColor: "divider",
                        transition: "0.2s ease",
                        "&:hover": {
                          boxShadow: "0 14px 36px rgba(15, 23, 42, 0.12)",
                          transform: "translateY(-3px)",
                        },
                      }}
                    >
                      <CardContent>
                        <Stack
                          direction="row"
                          justifyContent="space-between"
                          alignItems="flex-start"
                          mb={2}
                        >
                          <Box
                            sx={{
                              width: 48,
                              height: 48,
                              borderRadius: 3,
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              color: "white",
                              background:
                                status.label === "COMPLETED"
                                  ? "linear-gradient(135deg, #16a34a, #22c55e)"
                                  : "linear-gradient(135deg, #7c3aed, #2563eb)",
                            }}
                          >
                            {status.label === "COMPLETED" ? (
                              <CheckCircleIcon />
                            ) : (
                              <FlagIcon />
                            )}
                          </Box>

                          <Chip
                            label={status.label}
                            color={status.color}
                            size="small"
                            sx={{ fontWeight: 800 }}
                          />
                        </Stack>

                        <Typography variant="h6" fontWeight={900}>
                          {goal.goal_name}
                        </Typography>

                        <Stack spacing={1.2} mt={2}>
                          <Stack direction="row" justifyContent="space-between">
                            <Typography color="text.secondary">
                              Saved
                            </Typography>
                            <Typography fontWeight={900} color="success.main">
                              {formatCurrency(goal.current_amount)}
                            </Typography>
                          </Stack>

                          <Stack direction="row" justifyContent="space-between">
                            <Typography color="text.secondary">
                              Target
                            </Typography>
                            <Typography fontWeight={900}>
                              {formatCurrency(goal.target_amount)}
                            </Typography>
                          </Stack>

                          <Stack direction="row" justifyContent="space-between">
                            <Typography color="text.secondary">
                              Remaining
                            </Typography>
                            <Typography fontWeight={900}>
                              {formatCurrency(remainingAmount)}
                            </Typography>
                          </Stack>
                        </Stack>

                        <Box mt={2}>
                          <Stack direction="row" justifyContent="space-between" mb={0.8}>
                            <Typography variant="body2" fontWeight={800}>
                              Progress
                            </Typography>
                            <Typography variant="body2" fontWeight={900}>
                              {progress.toFixed(1)}%
                            </Typography>
                          </Stack>

                          <LinearProgress
                            variant="determinate"
                            value={Math.min(progress, 100)}
                            color={progress >= 100 ? "success" : "primary"}
                            sx={{ height: 10, borderRadius: 10 }}
                          />
                        </Box>

                        <Stack
                          direction="row"
                          alignItems="center"
                          spacing={1}
                          mt={2}
                          color="text.secondary"
                        >
                          <EventIcon fontSize="small" />
                          <Typography variant="body2">
                            Target: {formatDate(goal.target_date)}
                          </Typography>
                        </Stack>

                        {daysRemaining !== null && (
                          <Typography
                            variant="body2"
                            mt={1}
                            color={
                              status.label === "COMPLETED"
                                ? "success.main"
                                : daysRemaining < 0
                                ? "error.main"
                                : "text.secondary"
                            }
                          >
                            {status.label === "COMPLETED"
                              ? "Goal completed"
                              : daysRemaining < 0
                              ? `${Math.abs(daysRemaining)} day(s) overdue`
                              : `${daysRemaining} day(s) remaining`}
                          </Typography>
                        )}

                        <Stack direction="row" spacing={1} mt={3}>
                          <Tooltip title="Edit goal">
                            <IconButton onClick={() => handleOpenEdit(goal)}>
                              <EditIcon />
                            </IconButton>
                          </Tooltip>

                          <Tooltip title="Delete goal">
                            <IconButton
                              color="error"
                              onClick={() => setDeleteTarget(goal)}
                            >
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
                        </Stack>
                      </CardContent>
                    </Card>
                  </Grid>
                );
              })}
            </Grid>
          )}
        </CardContent>
      </Card>

      <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm">
        <DialogTitle fontWeight={900}>
          {editingGoal ? "Edit Savings Goal" : "Add Savings Goal"}
        </DialogTitle>

        <Box component="form" onSubmit={handleSubmit}>
          <DialogContent>
            {formError && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {formError}
              </Alert>
            )}

            <TextField
              label="Goal Name"
              name="goal_name"
              value={formData.goal_name}
              onChange={handleChange}
              fullWidth
              required
              margin="normal"
              placeholder="Example: Emergency Fund, Laptop, Vacation"
            />

            <TextField
              label="Target Amount"
              name="target_amount"
              type="number"
              value={formData.target_amount}
              onChange={handleChange}
              fullWidth
              required
              margin="normal"
              inputProps={{ min: 1, step: "0.01" }}
              InputProps={{
                startAdornment: <InputAdornment position="start">₹</InputAdornment>,
              }}
            />

            <TextField
              label="Current Saved Amount"
              name="current_amount"
              type="number"
              value={formData.current_amount}
              onChange={handleChange}
              fullWidth
              required
              margin="normal"
              inputProps={{ min: 0, step: "0.01" }}
              InputProps={{
                startAdornment: <InputAdornment position="start">₹</InputAdornment>,
              }}
            />

            <TextField
              label="Target Date"
              name="target_date"
              type="date"
              value={formData.target_date}
              onChange={handleChange}
              fullWidth
              required
              margin="normal"
              InputLabelProps={{ shrink: true }}
            />
          </DialogContent>

          <DialogActions sx={{ px: 3, pb: 3 }}>
            <Button onClick={handleClose} disabled={saving}>
              Cancel
            </Button>

            <Button type="submit" variant="contained" disabled={saving}>
              {saving
                ? "Saving..."
                : editingGoal
                ? "Update Goal"
                : "Create Goal"}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>

      <Dialog
        open={Boolean(deleteTarget)}
        onClose={() => !deleting && setDeleteTarget(null)}
        fullWidth
        maxWidth="xs"
      >
        <DialogTitle fontWeight={900}>Delete Savings Goal</DialogTitle>

        <DialogContent>
          <Typography>
            Are you sure you want to delete this savings goal?
          </Typography>

          {deleteTarget && (
            <Box
              sx={{
                mt: 2,
                p: 2,
                borderRadius: 3,
                backgroundColor: "action.hover",
              }}
            >
              <Typography fontWeight={900}>
                {deleteTarget.goal_name}
              </Typography>

              <Typography color="success.main" fontWeight={900}>
                {formatCurrency(deleteTarget.current_amount)} saved of{" "}
                {formatCurrency(deleteTarget.target_amount)}
              </Typography>
            </Box>
          )}
        </DialogContent>

        <DialogActions sx={{ px: 3, pb: 3 }}>
          <Button disabled={deleting} onClick={() => setDeleteTarget(null)}>
            Cancel
          </Button>

          <Button
            color="error"
            variant="contained"
            disabled={deleting}
            onClick={handleConfirmDelete}
          >
            {deleting ? "Deleting..." : "Delete"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SavingsPage;
------------------------------------
