import api from "./axios";

export const getExpenses = async () => {
  const response = await api.get("/expense/");
  return response.data;
};

export const createExpense = async (data) => {
  const response = await api.post("/expense/", data);
  return response.data;
};

export const updateExpense = async (expenseId, data) => {
  const response = await api.put(`/expense/${expenseId}`, data);
  return response.data;
};

export const deleteExpense = async (expenseId) => {
  const response = await api.delete(`/expense/${expenseId}`);
  return response.data;
};
--------------------------------------------
export const decodeJwtPayload = (token) => {
  try {
    if (!token) return null;

    const base64Url = token.split(".")[1];
    if (!base64Url) return null;

    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");

    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((char) => `%${`00${char.charCodeAt(0).toString(16)}`.slice(-2)}`)
        .join("")
    );

    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
};

export const getUserIdFromToken = () => {
  const token = localStorage.getItem("accessToken");
  const payload = decodeJwtPayload(token);

  return payload?.user_id || null;
};


-------------------------------------------
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  createExpense,
  deleteExpense,
  getExpenses,
  updateExpense,
} from "../api/expenseApi";
import { getUserIdFromToken } from "../utils/jwt";

const useExpense = () => {
  const [expenseList, setExpenseList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState("");

  const userId = useMemo(() => getUserIdFromToken(), []);

  const fetchExpenses = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await getExpenses();
      const list = Array.isArray(data) ? data : [];

      const userSpecificExpenses = userId
        ? list.filter((item) => Number(item.user_id) === Number(userId))
        : list;

      setExpenseList(userSpecificExpenses);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          "Failed to load expense records"
      );
    } finally {
      setLoading(false);
    }
  }, [userId]);

  const addExpense = async (payload) => {
    setSaving(true);
    setError("");

    try {
      if (!userId) {
        throw new Error("User ID not found in token. Please login again.");
      }

      await createExpense({
        user_id: Number(userId),
        category_id: Number(payload.category_id),
        amount: Number(payload.amount),
        description: payload.description,
        expense_date: payload.expense_date,
      });

      await fetchExpenses();
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "Failed to create expense";

      setError(message);
      throw new Error(message);
    } finally {
      setSaving(false);
    }
  };

  const editExpense = async (expenseId, payload) => {
    setSaving(true);
    setError("");

    try {
      await updateExpense(expenseId, {
        category_id: Number(payload.category_id),
        amount: Number(payload.amount),
        description: payload.description,
        expense_date: payload.expense_date,
      });

      await fetchExpenses();
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        "Failed to update expense";

      setError(message);
      throw new Error(message);
    } finally {
      setSaving(false);
    }
  };

  const removeExpense = async (expenseId) => {
    setDeleting(true);
    setError("");

    try {
      await deleteExpense(expenseId);
      await fetchExpenses();
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        "Failed to delete expense";

      setError(message);
      throw new Error(message);
    } finally {
      setDeleting(false);
    }
  };

  useEffect(() => {
    fetchExpenses();
  }, [fetchExpenses]);

  return {
    expenseList,
    loading,
    saving,
    deleting,
    error,
    userId,
    fetchExpenses,
    addExpense,
    editExpense,
    removeExpense,
  };
};

export default useExpense;
--------------------------------------------
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
  LinearProgress,
  MenuItem,
  Select,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import ReceiptLongIcon from "@mui/icons-material/ReceiptLong";
import AddIcon from "@mui/icons-material/Add";
import RefreshIcon from "@mui/icons-material/Refresh";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import CurrencyRupeeIcon from "@mui/icons-material/CurrencyRupee";
import CategoryIcon from "@mui/icons-material/Category";
import PageHeader from "../../components/common/PageHeader";
import useExpense from "../../hooks/useExpense";
import useCategories from "../../hooks/useCategories";

const getToday = () => new Date().toISOString().slice(0, 10);

const getCurrentMonthValue = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
};

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

const ExpensePage = () => {
  const {
    expenseList,
    loading,
    saving,
    deleting,
    error,
    fetchExpenses,
    addExpense,
    editExpense,
    removeExpense,
  } = useExpense();

  const { categories, loading: categoryLoading } = useCategories();

  const expenseCategories = useMemo(() => {
    return categories.filter(
      (category) => category.category_type?.toUpperCase().trim() === "EXPENSE"
    );
  }, [categories]);

  const [open, setOpen] = useState(false);
  const [editingExpense, setEditingExpense] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [formError, setFormError] = useState("");

  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("ALL");
  const [monthFilter, setMonthFilter] = useState("ALL");

  const [formData, setFormData] = useState({
    category_id: "",
    amount: "",
    description: "",
    expense_date: getToday(),
  });

  const totalExpense = useMemo(() => {
    return expenseList.reduce((sum, item) => sum + Number(item.amount || 0), 0);
  }, [expenseList]);

  const currentMonthExpense = useMemo(() => {
    const now = new Date();
    const currentMonth = now.getMonth();
    const currentYear = now.getFullYear();

    return expenseList.reduce((sum, item) => {
      const date = new Date(item.expense_date);

      if (
        date.getMonth() === currentMonth &&
        date.getFullYear() === currentYear
      ) {
        return sum + Number(item.amount || 0);
      }

      return sum;
    }, 0);
  }, [expenseList]);

  const highestExpense = useMemo(() => {
    if (expenseList.length === 0) return 0;
    return Math.max(...expenseList.map((item) => Number(item.amount || 0)));
  }, [expenseList]);

  const categorySpend = useMemo(() => {
    const totals = {};

    expenseList.forEach((expense) => {
      const key = expense.category_id;
      totals[key] = (totals[key] || 0) + Number(expense.amount || 0);
    });

    return Object.entries(totals)
      .map(([categoryId, amount]) => ({
        category_id: Number(categoryId),
        category_name:
          expenseCategories.find(
            (category) => Number(category.category_id) === Number(categoryId)
          )?.category_name || "Unknown Category",
        amount,
      }))
      .sort((a, b) => b.amount - a.amount)
      .slice(0, 5);
  }, [expenseList, expenseCategories]);

  const filteredExpenses = useMemo(() => {
    return expenseList.filter((expense) => {
      const category = expenseCategories.find(
        (item) => Number(item.category_id) === Number(expense.category_id)
      );

      const searchableText = `${expense.description || ""} ${
        category?.category_name || ""
      }`.toLowerCase();

      const matchesSearch = searchableText.includes(search.toLowerCase());

      const matchesCategory =
        categoryFilter === "ALL" ||
        Number(expense.category_id) === Number(categoryFilter);

      const matchesMonth =
        monthFilter === "ALL" ||
        String(expense.expense_date || "").startsWith(monthFilter);

      return matchesSearch && matchesCategory && matchesMonth;
    });
  }, [expenseList, expenseCategories, search, categoryFilter, monthFilter]);

  const getCategoryName = (categoryId) => {
    const category = expenseCategories.find(
      (item) => Number(item.category_id) === Number(categoryId)
    );

    return category?.category_name || "Unknown Category";
  };

  const handleOpenAdd = () => {
    setEditingExpense(null);
    setFormError("");
    setFormData({
      category_id: "",
      amount: "",
      description: "",
      expense_date: getToday(),
    });
    setOpen(true);
  };

  const handleOpenEdit = (expense) => {
    setEditingExpense(expense);
    setFormError("");
    setFormData({
      category_id: expense.category_id || "",
      amount: expense.amount || "",
      description: expense.description || "",
      expense_date: expense.expense_date || getToday(),
    });
    setOpen(true);
  };

  const handleClose = () => {
    if (!saving) {
      setOpen(false);
      setEditingExpense(null);
    }
  };

  const handleChange = (event) => {
    setFormData({
      ...formData,
      [event.target.name]: event.target.value,
    });
  };

  const validateForm = () => {
    if (!formData.category_id) {
      return "Please select an expense category";
    }

    if (!formData.amount || Number(formData.amount) <= 0) {
      return "Amount must be greater than zero";
    }

    if (!formData.description.trim()) {
      return "Description is required";
    }

    if (!formData.expense_date) {
      return "Expense date is required";
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
        category_id: formData.category_id,
        amount: formData.amount,
        description: formData.description.trim(),
        expense_date: formData.expense_date,
      };

      if (editingExpense) {
        await editExpense(editingExpense.expense_id, payload);
      } else {
        await addExpense(payload);
      }

      handleClose();
    } catch (err) {
      setFormError(err.message || "Something went wrong");
    }
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;

    try {
      await removeExpense(deleteTarget.expense_id);
      setDeleteTarget(null);
    } catch {
      // Hook already handles error
    }
  };

  return (
    <Box>
      <PageHeader
        title="Expense Tracking"
        subtitle="Track daily spending, category-wise expenses and monthly outflow."
        breadcrumbs={["Finance", "Expenses"]}
        actionText="Add Expense"
        onAction={handleOpenAdd}
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
                    background: "linear-gradient(135deg, #dc2626, #ef4444)",
                  }}
                >
                  <ReceiptLongIcon />
                </Box>

                <Box>
                  <Typography color="text.secondary" fontWeight={700}>
                    Total Expense
                  </Typography>
                  <Typography variant="h5" fontWeight={900}>
                    {formatCurrency(totalExpense)}
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Typography color="text.secondary" fontWeight={700}>
                Current Month Expense
              </Typography>
              <Typography variant="h5" fontWeight={900} color="error.main">
                {formatCurrency(currentMonthExpense)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Expenses recorded for this month.
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Typography color="text.secondary" fontWeight={700}>
                Highest Expense Entry
              </Typography>
              <Typography variant="h5" fontWeight={900}>
                {formatCurrency(highestExpense)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Highest single expense transaction.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} lg={8}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Stack
                direction={{ xs: "column", md: "row" }}
                justifyContent="space-between"
                spacing={2}
                mb={3}
              >
                <TextField
                  label="Search expenses"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  size="small"
                  sx={{ minWidth: { xs: "100%", md: 280 } }}
                />

                <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                  <FormControl size="small" sx={{ minWidth: 180 }}>
                    <InputLabel>Category</InputLabel>
                    <Select
                      label="Category"
                      value={categoryFilter}
                      onChange={(event) => setCategoryFilter(event.target.value)}
                    >
                      <MenuItem value="ALL">All Categories</MenuItem>
                      {expenseCategories.map((category) => (
                        <MenuItem
                          key={category.category_id}
                          value={category.category_id}
                        >
                          {category.category_name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <TextField
                    label="Month"
                    type="month"
                    size="small"
                    value={monthFilter === "ALL" ? "" : monthFilter}
                    onChange={(event) =>
                      setMonthFilter(event.target.value || "ALL")
                    }
                    InputLabelProps={{ shrink: true }}
                  />

                  <Button
                    variant="outlined"
                    startIcon={<RefreshIcon />}
                    onClick={fetchExpenses}
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
              ) : expenseCategories.length === 0 ? (
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
                    No expense category found
                  </Typography>
                  <Typography color="text.secondary" mt={1}>
                    Please create at least one category with type EXPENSE before
                    adding expenses.
                  </Typography>
                </Box>
              ) : filteredExpenses.length === 0 ? (
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
                    No expense records found
                  </Typography>
                  <Typography color="text.secondary" mt={1}>
                    Add your first expense to start tracking spending.
                  </Typography>

                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    sx={{ mt: 3 }}
                    onClick={handleOpenAdd}
                  >
                    Add Expense
                  </Button>
                </Box>
              ) : (
                <Stack spacing={2}>
                  {filteredExpenses.map((expense) => (
                    <Card
                      key={expense.expense_id}
                      elevation={0}
                      sx={{
                        border: "1px solid",
                        borderColor: "divider",
                        transition: "0.2s ease",
                        "&:hover": {
                          boxShadow: "0 14px 36px rgba(15, 23, 42, 0.12)",
                          transform: "translateY(-2px)",
                        },
                      }}
                    >
                      <CardContent>
                        <Stack
                          direction={{ xs: "column", md: "row" }}
                          justifyContent="space-between"
                          alignItems={{ xs: "flex-start", md: "center" }}
                          spacing={2}
                        >
                          <Stack direction="row" spacing={2} alignItems="center">
                            <Box
                              sx={{
                                width: 46,
                                height: 46,
                                borderRadius: 3,
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                backgroundColor: "error.light",
                                color: "error.contrastText",
                              }}
                            >
                              <CurrencyRupeeIcon />
                            </Box>

                            <Box>
                              <Typography variant="h6" fontWeight={900}>
                                {expense.description}
                              </Typography>

                              <Stack
                                direction="row"
                                spacing={1}
                                alignItems="center"
                                flexWrap="wrap"
                                mt={0.5}
                              >
                                <Chip
                                  label={getCategoryName(expense.category_id)}
                                  color="error"
                                  size="small"
                                />

                                <Typography
                                  variant="body2"
                                  color="text.secondary"
                                >
                                  {formatDate(expense.expense_date)}
                                </Typography>
                              </Stack>
                            </Box>
                          </Stack>

                          <Stack direction="row" spacing={2} alignItems="center">
                            <Typography
                              variant="h6"
                              fontWeight={900}
                              color="error.main"
                              sx={{ minWidth: 130 }}
                            >
                              {formatCurrency(expense.amount)}
                            </Typography>

                            <Tooltip title="Edit expense">
                              <IconButton onClick={() => handleOpenEdit(expense)}>
                                <EditIcon />
                              </IconButton>
                            </Tooltip>

                            <Tooltip title="Delete expense">
                              <IconButton
                                color="error"
                                onClick={() => setDeleteTarget(expense)}
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

        <Grid item xs={12} lg={4}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Stack direction="row" spacing={1} alignItems="center" mb={2}>
                <CategoryIcon color="primary" />
                <Typography variant="h6" fontWeight={900}>
                  Top Spending Categories
                </Typography>
              </Stack>

              {categorySpend.length === 0 ? (
                <Typography color="text.secondary">
                  Category insights will appear after adding expenses.
                </Typography>
              ) : (
                <Stack spacing={2}>
                  {categorySpend.map((item) => {
                    const percentage =
                      totalExpense > 0 ? (item.amount / totalExpense) * 100 : 0;

                    return (
                      <Box key={item.category_id}>
                        <Stack
                          direction="row"
                          justifyContent="space-between"
                          mb={0.8}
                        >
                          <Typography fontWeight={800}>
                            {item.category_name}
                          </Typography>
                          <Typography color="error.main" fontWeight={900}>
                            {formatCurrency(item.amount)}
                          </Typography>
                        </Stack>

                        <LinearProgress
                          variant="determinate"
                          value={percentage}
                          color="error"
                          sx={{ height: 8, borderRadius: 10 }}
                        />

                        <Typography
                          variant="caption"
                          color="text.secondary"
                          display="block"
                          mt={0.5}
                        >
                          {percentage.toFixed(1)}% of total expense
                        </Typography>
                      </Box>
                    );
                  })}
                </Stack>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm">
        <DialogTitle fontWeight={900}>
          {editingExpense ? "Edit Expense" : "Add Expense"}
        </DialogTitle>

        <Box component="form" onSubmit={handleSubmit}>
          <DialogContent>
            {formError && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {formError}
              </Alert>
            )}

            <FormControl fullWidth margin="normal">
              <InputLabel>Expense Category</InputLabel>
              <Select
                label="Expense Category"
                name="category_id"
                value={formData.category_id}
                onChange={handleChange}
              >
                {expenseCategories.map((category) => (
                  <MenuItem
                    key={category.category_id}
                    value={category.category_id}
                  >
                    {category.category_name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

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

            <TextField
              label="Description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              fullWidth
              required
              margin="normal"
              placeholder="Example: Grocery shopping, Rent payment, Cab fare"
            />

            <TextField
              label="Expense Date"
              name="expense_date"
              type="date"
              value={formData.expense_date}
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
                : editingExpense
                ? "Update Expense"
                : "Create Expense"}
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
        <DialogTitle fontWeight={900}>Delete Expense</DialogTitle>

        <DialogContent>
          <Typography>
            Are you sure you want to delete this expense record?
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
              <Typography fontWeight={800}>
                {deleteTarget.description}
              </Typography>
              <Typography color="error.main" fontWeight={900}>
                {formatCurrency(deleteTarget.amount)}
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

export default ExpensePage;
------------------------------------
