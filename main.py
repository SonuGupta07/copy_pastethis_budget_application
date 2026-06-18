import api from "./axios";

export const getRecurringTransactions = async () => {
  const response = await api.get("/recurring/");
  return response.data;
};

export const createRecurringTransaction = async (data) => {
  const response = await api.post("/recurring/", data);
  return response.data;
};

export const updateRecurringTransaction = async (recurringId, data) => {
  const response = await api.put(`/recurring/${recurringId}`, data);
  return response.data;
};

export const deleteRecurringTransaction = async (recurringId) => {
  const response = await api.delete(`/recurring/${recurringId}`);
  return response.data;
};
------------------------------------------------
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  createRecurringTransaction,
  deleteRecurringTransaction,
  getRecurringTransactions,
  updateRecurringTransaction,
} from "../api/recurringApi";
import { getUserIdFromToken } from "../utils/jwt";

const useRecurring = () => {
  const [recurringList, setRecurringList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState("");

  const userId = useMemo(() => getUserIdFromToken(), []);

  const fetchRecurring = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await getRecurringTransactions();
      const list = Array.isArray(data) ? data : [];

      const userSpecificRecurring = userId
        ? list.filter((item) => Number(item.user_id) === Number(userId))
        : list;

      setRecurringList(userSpecificRecurring);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          "Failed to load recurring transactions"
      );
    } finally {
      setLoading(false);
    }
  }, [userId]);

  const addRecurring = async (payload) => {
    setSaving(true);
    setError("");

    try {
      if (!userId) {
        throw new Error("User ID not found in token. Please login again.");
      }

      await createRecurringTransaction({
        user_id: Number(userId),
        transaction_type: payload.transaction_type,
        category_id: Number(payload.category_id),
        amount: Number(payload.amount),
        frequency: payload.frequency,
        next_run_date: payload.next_run_date,
      });

      await fetchRecurring();
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "Failed to create recurring transaction";

      setError(message);
      throw new Error(message);
    } finally {
      setSaving(false);
    }
  };

  const editRecurring = async (recurringId, payload) => {
    setSaving(true);
    setError("");

    try {
      await updateRecurringTransaction(recurringId, {
        transaction_type: payload.transaction_type,
        category_id: Number(payload.category_id),
        amount: Number(payload.amount),
        frequency: payload.frequency,
        next_run_date: payload.next_run_date,
      });

      await fetchRecurring();
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        "Failed to update recurring transaction";

      setError(message);
      throw new Error(message);
    } finally {
      setSaving(false);
    }
  };

  const removeRecurring = async (recurringId) => {
    setDeleting(true);
    setError("");

    try {
      await deleteRecurringTransaction(recurringId);
      await fetchRecurring();
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        "Failed to delete recurring transaction";

      setError(message);
      throw new Error(message);
    } finally {
      setDeleting(false);
    }
  };

  useEffect(() => {
    fetchRecurring();
  }, [fetchRecurring]);

  return {
    recurringList,
    loading,
    saving,
    deleting,
    error,
    userId,
    fetchRecurring,
    addRecurring,
    editRecurring,
    removeRecurring,
  };
};

export default useRecurring;
-------------------------------------
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
  FormControl,
  Grid,
  IconButton,
  InputAdornment,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import RepeatIcon from "@mui/icons-material/Repeat";
import AddIcon from "@mui/icons-material/Add";
import RefreshIcon from "@mui/icons-material/Refresh";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import ReceiptLongIcon from "@mui/icons-material/ReceiptLong";
import EventRepeatIcon from "@mui/icons-material/EventRepeat";
import CalendarMonthIcon from "@mui/icons-material/CalendarMonth";
import PageHeader from "../../components/common/PageHeader";
import useRecurring from "../../hooks/useRecurring";
import useCategories from "../../hooks/useCategories";

const getToday = () => new Date().toISOString().slice(0, 10);

const frequencies = ["DAILY", "WEEKLY", "MONTHLY", "YEARLY"];

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

const getDaysUntilRun = (dateValue) => {
  if (!dateValue) return null;

  const today = new Date();
  const nextDate = new Date(dateValue);

  today.setHours(0, 0, 0, 0);
  nextDate.setHours(0, 0, 0, 0);

  const diff = nextDate.getTime() - today.getTime();
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
};

const getMonthlyEquivalent = (amount, frequency) => {
  const value = Number(amount || 0);

  switch (frequency) {
    case "DAILY":
      return value * 30;
    case "WEEKLY":
      return value * 4;
    case "MONTHLY":
      return value;
    case "YEARLY":
      return value / 12;
    default:
      return value;
  }
};

const RecurringPage = () => {
  const {
    recurringList,
    loading,
    saving,
    deleting,
    error,
    fetchRecurring,
    addRecurring,
    editRecurring,
    removeRecurring,
  } = useRecurring();

  const { categories, loading: categoryLoading } = useCategories();

  const [open, setOpen] = useState(false);
  const [editingRecurring, setEditingRecurring] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [formError, setFormError] = useState("");

  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [frequencyFilter, setFrequencyFilter] = useState("ALL");

  const [formData, setFormData] = useState({
    transaction_type: "EXPENSE",
    category_id: "",
    amount: "",
    frequency: "MONTHLY",
    next_run_date: getToday(),
  });

  const availableCategories = useMemo(() => {
    return categories.filter(
      (category) =>
        category.category_type?.toUpperCase().trim() ===
        formData.transaction_type
    );
  }, [categories, formData.transaction_type]);

  const incomeCategories = useMemo(() => {
    return categories.filter(
      (category) => category.category_type?.toUpperCase().trim() === "INCOME"
    );
  }, [categories]);

  const expenseCategories = useMemo(() => {
    return categories.filter(
      (category) => category.category_type?.toUpperCase().trim() === "EXPENSE"
    );
  }, [categories]);

  const getCategoryName = (categoryId) => {
    const category = categories.find(
      (item) => Number(item.category_id) === Number(categoryId)
    );

    return category?.category_name || "Unknown Category";
  };

  const totalRecurringIncome = useMemo(() => {
    return recurringList
      .filter((item) => item.transaction_type === "INCOME")
      .reduce(
        (sum, item) => sum + getMonthlyEquivalent(item.amount, item.frequency),
        0
      );
  }, [recurringList]);

  const totalRecurringExpense = useMemo(() => {
    return recurringList
      .filter((item) => item.transaction_type === "EXPENSE")
      .reduce(
        (sum, item) => sum + getMonthlyEquivalent(item.amount, item.frequency),
        0
      );
  }, [recurringList]);

  const upcomingCount = useMemo(() => {
    return recurringList.filter((item) => {
      const days = getDaysUntilRun(item.next_run_date);
      return days !== null && days >= 0 && days <= 7;
    }).length;
  }, [recurringList]);

  const filteredRecurring = useMemo(() => {
    return recurringList.filter((item) => {
      const categoryName = getCategoryName(item.category_id);

      const matchesSearch = `${categoryName} ${item.transaction_type} ${item.frequency}`
        .toLowerCase()
        .includes(search.toLowerCase());

      const matchesType =
        typeFilter === "ALL" || item.transaction_type === typeFilter;

      const matchesFrequency =
        frequencyFilter === "ALL" || item.frequency === frequencyFilter;

      return matchesSearch && matchesType && matchesFrequency;
    });
  }, [recurringList, search, typeFilter, frequencyFilter, categories]);

  const handleOpenAdd = () => {
    setEditingRecurring(null);
    setFormError("");
    setFormData({
      transaction_type: "EXPENSE",
      category_id: "",
      amount: "",
      frequency: "MONTHLY",
      next_run_date: getToday(),
    });
    setOpen(true);
  };

  const handleOpenEdit = (recurring) => {
    setEditingRecurring(recurring);
    setFormError("");
    setFormData({
      transaction_type: recurring.transaction_type || "EXPENSE",
      category_id: recurring.category_id || "",
      amount: recurring.amount || "",
      frequency: recurring.frequency || "MONTHLY",
      next_run_date: recurring.next_run_date || getToday(),
    });
    setOpen(true);
  };

  const handleClose = () => {
    if (!saving) {
      setOpen(false);
      setEditingRecurring(null);
    }
  };

  const handleChange = (event) => {
    const { name, value } = event.target;

    if (name === "transaction_type") {
      setFormData({
        ...formData,
        transaction_type: value,
        category_id: "",
      });
      return;
    }

    setFormData({
      ...formData,
      value,
    });
  };

  const validateForm = () => {
    if (!formData.transaction_type) {
      return "Please select transaction type";
    }

    if (!["INCOME", "EXPENSE"].includes(formData.transaction_type)) {
      return "Transaction type must be INCOME or EXPENSE";
    }

    if (!formData.category_id) {
      return "Please select a category";
    }

    if (!formData.amount || Number(formData.amount) <= 0) {
      return "Amount must be greater than zero";
    }

    if (!formData.frequency) {
      return "Please select frequency";
    }

    if (!frequencies.includes(formData.frequency)) {
      return "Invalid frequency selected";
    }

    if (!formData.next_run_date) {
      return "Next run date is required";
    }

    if (formData.next_run_date < getToday()) {
      return "Next run date cannot be in the past";
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
        transaction_type: formData.transaction_type,
        category_id: formData.category_id,
        amount: formData.amount,
        frequency: formData.frequency,
        next_run_date: formData.next_run_date,
      };

      if (editingRecurring) {
        await editRecurring(editingRecurring.recurring_id, payload);
      } else {
        await addRecurring(payload);
      }

      handleClose();
    } catch (err) {
      setFormError(err.message || "Something went wrong");
    }
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;

    try {
      await removeRecurring(deleteTarget.recurring_id);
      setDeleteTarget(null);
    } catch {
      // Hook already handles error
    }
  };

  return (
    <Box>
      <PageHeader
        title="Recurring Transactions"
        subtitle="Manage repeated income, rent, bills, subscriptions, EMI and other scheduled transactions."
        breadcrumbs={["Finance", "Recurring Transactions"]}
        actionText="Add Recurring"
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
              <Stack direction="row" spacing={2} alignItems="center">
                <Box
                  sx={{
                    width: 50,
                    height: 50,
                    borderRadius: 3,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    color: "white",
                    background: "linear-gradient(135deg, #2563eb, #7c3aed)",
                  }}
                >
                  <RepeatIcon />
                </Box>

                <Box>
                  <Typography color="text.secondary" fontWeight={700}>
                    Active Recurring
                  </Typography>
                  <Typography variant="h5" fontWeight={900}>
                    {recurringList.length}
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
                Monthly Income Estimate
              </Typography>
              <Typography variant="h5" fontWeight={900} color="success.main">
                {formatCurrency(totalRecurringIncome)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Converted from all recurring income.
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Typography color="text.secondary" fontWeight={700}>
                Monthly Expense Estimate
              </Typography>
              <Typography variant="h5" fontWeight={900} color="error.main">
                {formatCurrency(totalRecurringExpense)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Converted from all recurring expenses.
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Typography color="text.secondary" fontWeight={700}>
                Due in 7 Days
              </Typography>
              <Typography variant="h5" fontWeight={900} color="warning.main">
                {upcomingCount}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Upcoming scheduled transactions.
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
              label="Search recurring transactions"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              size="small"
              sx={{ minWidth: { xs: "100%", md: 320 } }}
            />

            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <FormControl size="small" sx={{ minWidth: 150 }}>
                <InputLabel>Type</InputLabel>
                <Select
                  label="Type"
                  value={typeFilter}
                  onChange={(event) => setTypeFilter(event.target.value)}
                >
                  <MenuItem value="ALL">All Types</MenuItem>
                  <MenuItem value="INCOME">Income</MenuItem>
                  <MenuItem value="EXPENSE">Expense</MenuItem>
                </Select>
              </FormControl>

              <FormControl size="small" sx={{ minWidth: 150 }}>
                <InputLabel>Frequency</InputLabel>
                <Select
                  label="Frequency"
                  value={frequencyFilter}
                  onChange={(event) => setFrequencyFilter(event.target.value)}
                >
                  <MenuItem value="ALL">All</MenuItem>
                  {frequencies.map((frequency) => (
                    <MenuItem key={frequency} value={frequency}>
                      {frequency}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={fetchRecurring}
              >
                Refresh
              </Button>

              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleOpenAdd}
              >
                Add
              </Button>
            </Stack>
          </Stack>

          {loading || categoryLoading ? (
            <Box display="flex" justifyContent="center" py={6}>
              <CircularProgress />
            </Box>
          ) : categories.length === 0 ? (
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
                No categories found
              </Typography>

              <Typography color="text.secondary" mt={1}>
                Please create income or expense categories before adding recurring transactions.
              </Typography>
            </Box>
          ) : filteredRecurring.length === 0 ? (
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
                No recurring transactions found
              </Typography>

              <Typography color="text.secondary" mt={1}>
                Add your first recurring income, rent, subscription or bill.
              </Typography>

              <Button
                variant="contained"
                startIcon={<AddIcon />}
                sx={{ mt: 3 }}
                onClick={handleOpenAdd}
              >
                Add Recurring Transaction
              </Button>
            </Box>
          ) : (
            <Grid container spacing={2}>
              {filteredRecurring.map((item) => {
                const isIncome = item.transaction_type === "INCOME";
                const daysUntilRun = getDaysUntilRun(item.next_run_date);

                return (
                  <Grid item xs={12} md={6} lg={4} key={item.recurring_id}>
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
                              background: isIncome
                                ? "linear-gradient(135deg, #16a34a, #22c55e)"
                                : "linear-gradient(135deg, #dc2626, #ef4444)",
                            }}
                          >
                            {isIncome ? <TrendingUpIcon /> : <ReceiptLongIcon />}
                          </Box>

                          <Chip
                            label={item.transaction_type}
                            color={isIncome ? "success" : "error"}
                            size="small"
                            sx={{ fontWeight: 800 }}
                          />
                        </Stack>

                        <Typography variant="h6" fontWeight={900}>
                          {getCategoryName(item.category_id)}
                        </Typography>

                        <Typography
                          variant="h5"
                          fontWeight={900}
                          color={isIncome ? "success.main" : "error.main"}
                          mt={1}
                        >
                          {formatCurrency(item.amount)}
                        </Typography>

                        <Stack direction="row" spacing={1} flexWrap="wrap" mt={2}>
                          <Chip
                            label={item.frequency}
                            color="primary"
                            size="small"
                            variant="outlined"
                          />

                          <Chip
                            label={`Monthly eq. ${formatCurrency(
                              getMonthlyEquivalent(item.amount, item.frequency)
                            )}`}
                            size="small"
                          />
                        </Stack>

                        <Stack direction="row" spacing={1} alignItems="center" mt={2}>
                          <CalendarMonthIcon fontSize="small" color="action" />
                          <Typography variant="body2" color="text.secondary">
                            Next run: {formatDate(item.next_run_date)}
                          </Typography>
                        </Stack>

                        {daysUntilRun !== null && (
                          <Typography
                            variant="body2"
                            mt={1}
                            color={
                              daysUntilRun < 0
                                ? "error.main"
                                : daysUntilRun <= 7
                                ? "warning.main"
                                : "text.secondary"
                            }
                          >
                            {daysUntilRun < 0
                              ? `${Math.abs(daysUntilRun)} day(s) overdue`
                              : daysUntilRun === 0
                              ? "Due today"
                              : `${daysUntilRun} day(s) remaining`}
                          </Typography>
                        )}

                        <Stack direction="row" spacing={1} mt={3}>
                          <Tooltip title="Edit recurring transaction">
                            <IconButton onClick={() => handleOpenEdit(item)}>
                              <EditIcon />
                            </IconButton>
                          </Tooltip>

                          <Tooltip title="Delete recurring transaction">
                            <IconButton
                              color="error"
                              onClick={() => setDeleteTarget(item)}
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
          {editingRecurring
            ? "Edit Recurring Transaction"
            : "Add Recurring Transaction"}
        </DialogTitle>

        <Box component="form" onSubmit={handleSubmit}>
          <DialogContent>
            {formError && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {formError}
              </Alert>
            )}

            <FormControl fullWidth margin="normal">
              <InputLabel>Transaction Type</InputLabel>
              <Select
                label="Transaction Type"
                name="transaction_type"
                value={formData.transaction_type}
                onChange={handleChange}
              >
                <MenuItem value="INCOME">Income</MenuItem>
                <MenuItem value="EXPENSE">Expense</MenuItem>
              </Select>
            </FormControl>

            <FormControl fullWidth margin="normal">
              <InputLabel>Category</InputLabel>
              <Select
                label="Category"
                name="category_id"
                value={formData.category_id}
                onChange={handleChange}
              >
                {availableCategories.map((category) => (
                  <MenuItem
                    key={category.category_id}
                    value={category.category_id}
                  >
                    {category.category_name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {formData.transaction_type === "INCOME" &&
              incomeCategories.length === 0 && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  Create at least one INCOME category before adding recurring income.
                </Alert>
              )}

            {formData.transaction_type === "EXPENSE" &&
              expenseCategories.length === 0 && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  Create at least one EXPENSE category before adding recurring expense.
                </Alert>
              )}

            <TextField
              label="Amount"
              name="amount"
              type="number"
              value={formData.amount}
              onChange={handleChange}
              fullWidth
              required
              margin="normal"
              inputProps={{ min: 1, step: "0.01" }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">₹</InputAdornment>
                ),
              }}
            />

            <FormControl fullWidth margin="normal">
              <InputLabel>Frequency</InputLabel>
              <Select
                label="Frequency"
                name="frequency"
                value={formData.frequency}
                onChange={handleChange}
              >
                {frequencies.map((frequency) => (
                  <MenuItem key={frequency} value={frequency}>
                    {frequency}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <TextField
              label="Next Run Date"
              name="next_run_date"
              type="date"
              value={formData.next_run_date}
              onChange={handleChange}
              fullWidth
              required
              margin="normal"
              inputProps={{ min: getToday() }}
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
                : editingRecurring
                ? "Update Recurring"
                : "Create Recurring"}
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
        <DialogTitle fontWeight={900}>
          Delete Recurring Transaction
        </DialogTitle>

        <DialogContent>
          <Typography>
            Are you sure you want to delete this recurring transaction?
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
                {getCategoryName(deleteTarget.category_id)}
              </Typography>

              <Typography
                fontWeight={900}
                color={
                  deleteTarget.transaction_type === "INCOME"
                    ? "success.main"
                    : "error.main"
                }
              >
                {formatCurrency(deleteTarget.amount)} /{" "}
                {deleteTarget.frequency}
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

export default RecurringPage;
-----------------------------------------
