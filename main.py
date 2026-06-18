import api from "./axios";

export const getBudgets = async () => {
  const response = await api.get("/budget/");
  return response.data;
};

export const createBudget = async (data) => {
  const response = await api.post("/budget/", data);
  return response.data;
};

export const updateBudget = async (budgetId, data) => {
  const response = await api.put(`/budget/${budgetId}`, data);
  return response.data;
};

export const deleteBudget = async (budgetId) => {
  const response = await api.delete(`/budget/${budgetId}`);
  return response.data;
};

export const getBudgetSummary = async (userId) => {
  const response = await api.get(`/budget/summary/${userId}`);
  return response.data;
};

export const getBudgetCategorySummary = async (userId) => {
  const response = await api.get(`/budget/category-summary/${userId}`);
  return response.data;
};
-------------------------------------------
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  createBudget,
  deleteBudget,
  getBudgetCategorySummary,
  getBudgets,
  getBudgetSummary,
  updateBudget,
} from "../api/budgetApi";
import { getUserIdFromToken } from "../utils/jwt";

const useBudget = () => {
  const [budgets, setBudgets] = useState([]);
  const [summary, setSummary] = useState(null);
  const [categorySummary, setCategorySummary] = useState([]);

  const [loading, setLoading] = useState(false);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const [error, setError] = useState("");

  const userId = useMemo(() => getUserIdFromToken(), []);

  const fetchBudgets = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await getBudgets();
      const list = Array.isArray(data) ? data : [];

      const userSpecificBudgets = userId
        ? list.filter((item) => Number(item.user_id) === Number(userId))
        : list;

      setBudgets(userSpecificBudgets);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          "Failed to load budget records"
      );
    } finally {
      setLoading(false);
    }
  }, [userId]);

  const fetchBudgetInsights = useCallback(async () => {
    if (!userId) return;

    setSummaryLoading(true);

    try {
      const [summaryData, categorySummaryData] = await Promise.all([
        getBudgetSummary(userId),
        getBudgetCategorySummary(userId),
      ]);

      setSummary(summaryData);
      setCategorySummary(
        Array.isArray(categorySummaryData) ? categorySummaryData : []
      );
    } catch {
      setSummary(null);
      setCategorySummary([]);
    } finally {
      setSummaryLoading(false);
    }
  }, [userId]);

  const refreshBudgetData = useCallback(async () => {
    await fetchBudgets();
    await fetchBudgetInsights();
  }, [fetchBudgets, fetchBudgetInsights]);

  const addBudget = async (payload) => {
    setSaving(true);
    setError("");

    try {
      if (!userId) {
        throw new Error("User ID not found in token. Please login again.");
      }

      await createBudget({
        user_id: Number(userId),
        category_id: Number(payload.category_id),
        month: Number(payload.month),
        year: Number(payload.year),
        budget_amount: Number(payload.budget_amount),
      });

      await refreshBudgetData();
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "Failed to create budget";

      setError(message);
      throw new Error(message);
    } finally {
      setSaving(false);
    }
  };

  const editBudget = async (budgetId, payload) => {
    setSaving(true);
    setError("");

    try {
      await updateBudget(budgetId, {
        category_id: Number(payload.category_id),
        month: Number(payload.month),
        year: Number(payload.year),
        budget_amount: Number(payload.budget_amount),
      });

      await refreshBudgetData();
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        "Failed to update budget";

      setError(message);
      throw new Error(message);
    } finally {
      setSaving(false);
    }
  };

  const removeBudget = async (budgetId) => {
    setDeleting(true);
    setError("");

    try {
      await deleteBudget(budgetId);
      await refreshBudgetData();
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        "Failed to delete budget";

      setError(message);
      throw new Error(message);
    } finally {
      setDeleting(false);
    }
  };

  useEffect(() => {
    refreshBudgetData();
  }, [refreshBudgetData]);

  return {
    budgets,
    summary,
    categorySummary,
    loading,
    summaryLoading,
    saving,
    deleting,
    error,
    userId,
    refreshBudgetData,
    addBudget,
    editBudget,
    removeBudget,
  };
};

export default useBudget;
-----------------------------------------
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
import AccountBalanceWalletIcon from "@mui/icons-material/AccountBalanceWallet";
import AddIcon from "@mui/icons-material/Add";
import RefreshIcon from "@mui/icons-material/Refresh";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import SavingsIcon from "@mui/icons-material/Savings";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import PageHeader from "../../components/common/PageHeader";
import useBudget from "../../hooks/useBudget";
import useCategories from "../../hooks/useCategories";

const monthNames = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

const getCurrentMonth = () => new Date().getMonth() + 1;
const getCurrentYear = () => new Date().getFullYear();

const formatCurrency = (value) => {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(Number(value || 0));
};

const BudgetPage = () => {
  const {
    budgets,
    summary,
    categorySummary,
    loading,
    summaryLoading,
    saving,
    deleting,
    error,
    refreshBudgetData,
    addBudget,
    editBudget,
    removeBudget,
  } = useBudget();

  const { categories, loading: categoryLoading } = useCategories();

  const expenseCategories = useMemo(() => {
    return categories.filter(
      (category) => category.category_type?.toUpperCase().trim() === "EXPENSE"
    );
  }, [categories]);

  const [open, setOpen] = useState(false);
  const [editingBudget, setEditingBudget] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [formError, setFormError] = useState("");

  const [search, setSearch] = useState("");
  const [monthFilter, setMonthFilter] = useState("ALL");
  const [yearFilter, setYearFilter] = useState(String(getCurrentYear()));

  const [formData, setFormData] = useState({
    category_id: "",
    month: getCurrentMonth(),
    year: getCurrentYear(),
    budget_amount: "",
  });

  const totalBudget = useMemo(() => {
    return budgets.reduce(
      (sum, budget) => sum + Number(budget.budget_amount || 0),
      0
    );
  }, [budgets]);

  const currentMonthBudget = useMemo(() => {
    return budgets.reduce((sum, budget) => {
      if (
        Number(budget.month) === getCurrentMonth() &&
        Number(budget.year) === getCurrentYear()
      ) {
        return sum + Number(budget.budget_amount || 0);
      }

      return sum;
    }, 0);
  }, [budgets]);

  const filteredBudgets = useMemo(() => {
    return budgets.filter((budget) => {
      const category = expenseCategories.find(
        (item) => Number(item.category_id) === Number(budget.category_id)
      );

      const categoryName = category?.category_name || "";

      const matchesSearch = categoryName
        .toLowerCase()
        .includes(search.toLowerCase());

      const matchesMonth =
        monthFilter === "ALL" || Number(budget.month) === Number(monthFilter);

      const matchesYear =
        yearFilter === "ALL" || Number(budget.year) === Number(yearFilter);

      return matchesSearch && matchesMonth && matchesYear;
    });
  }, [budgets, expenseCategories, search, monthFilter, yearFilter]);

  const getCategoryName = (categoryId) => {
    const category = expenseCategories.find(
      (item) => Number(item.category_id) === Number(categoryId)
    );

    return category?.category_name || "Unknown Category";
  };

  const getUsageColor = (percentage) => {
    if (percentage >= 90) return "error";
    if (percentage >= 70) return "warning";
    return "success";
  };

  const handleOpenAdd = () => {
    setEditingBudget(null);
    setFormError("");
    setFormData({
      category_id: "",
      month: getCurrentMonth(),
      year: getCurrentYear(),
      budget_amount: "",
    });
    setOpen(true);
  };

  const handleOpenEdit = (budget) => {
    setEditingBudget(budget);
    setFormError("");
    setFormData({
      category_id: budget.category_id || "",
      month: budget.month || getCurrentMonth(),
      year: budget.year || getCurrentYear(),
      budget_amount: budget.budget_amount || "",
    });
    setOpen(true);
  };

  const handleClose = () => {
    if (!saving) {
      setOpen(false);
      setEditingBudget(null);
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

    if (!formData.month || Number(formData.month) < 1 || Number(formData.month) > 12) {
      return "Please select a valid month";
    }

    if (!formData.year || Number(formData.year) < 2024) {
      return "Please enter a valid year";
    }

    if (!formData.budget_amount || Number(formData.budget_amount) <= 0) {
      return "Budget amount must be greater than zero";
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
        month: formData.month,
        year: formData.year,
        budget_amount: formData.budget_amount,
      };

      if (editingBudget) {
        await editBudget(editingBudget.budget_id, payload);
      } else {
        await addBudget(payload);
      }

      handleClose();
    } catch (err) {
      setFormError(err.message || "Something went wrong");
    }
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;

    try {
      await removeBudget(deleteTarget.budget_id);
      setDeleteTarget(null);
    } catch {
      // Hook already handles error
    }
  };

  const utilization = Number(summary?.utilization_percentage || 0);
  const remainingBudget = Number(summary?.remaining_budget || 0);

  return (
    <Box>
      <PageHeader
        title="Budget Planning"
        subtitle="Create monthly category-wise budgets and monitor spending utilization."
        breadcrumbs={["Finance", "Budgets"]}
        actionText="Add Budget"
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
                    color: "white",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    background: "linear-gradient(135deg, #2563eb, #7c3aed)",
                  }}
                >
                  <AccountBalanceWalletIcon />
                </Box>

                <Box>
                  <Typography color="text.secondary" fontWeight={700}>
                    Total Budget
                  </Typography>
                  <Typography variant="h5" fontWeight={900}>
                    {formatCurrency(summary?.total_budget ?? totalBudget)}
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
                Total Expense
              </Typography>
              <Typography variant="h5" fontWeight={900} color="error.main">
                {formatCurrency(summary?.total_expense || 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Based on recorded expenses.
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Typography color="text.secondary" fontWeight={700}>
                Remaining Budget
              </Typography>
              <Typography
                variant="h5"
                fontWeight={900}
                color={remainingBudget < 0 ? "error.main" : "success.main"}
              >
                {formatCurrency(remainingBudget)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Available budget balance.
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Typography color="text.secondary" fontWeight={700}>
                Current Month Budget
              </Typography>
              <Typography variant="h5" fontWeight={900}>
                {formatCurrency(currentMonthBudget)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Budget planned for this month.
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
                  label="Search budget category"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  size="small"
                  sx={{ minWidth: { xs: "100%", md: 280 } }}
                />

                <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                  <FormControl size="small" sx={{ minWidth: 150 }}>
                    <InputLabel>Month</InputLabel>
                    <Select
                      label="Month"
                      value={monthFilter}
                      onChange={(event) => setMonthFilter(event.target.value)}
                    >
                      <MenuItem value="ALL">All Months</MenuItem>
                      {monthNames.map((month, index) => (
                        <MenuItem key={month} value={index + 1}>
                          {month}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <TextField
                    label="Year"
                    size="small"
                    value={yearFilter}
                    onChange={(event) => setYearFilter(event.target.value || "ALL")}
                    sx={{ width: 120 }}
                  />

                  <Button
                    variant="outlined"
                    startIcon={<RefreshIcon />}
                    onClick={refreshBudgetData}
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
                    Please create at least one EXPENSE category before creating budgets.
                  </Typography>
                </Box>
              ) : filteredBudgets.length === 0 ? (
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
                    No budgets found
                  </Typography>
                  <Typography color="text.secondary" mt={1}>
                    Create your first monthly category budget.
                  </Typography>

                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    sx={{ mt: 3 }}
                    onClick={handleOpenAdd}
                  >
                    Add Budget
                  </Button>
                </Box>
              ) : (
                <Stack spacing={2}>
                  {filteredBudgets.map((budget) => (
                    <Card
                      key={budget.budget_id}
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
                                backgroundColor: "primary.light",
                                color: "primary.contrastText",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                              }}
                            >
                              <SavingsIcon />
                            </Box>

                            <Box>
                              <Typography variant="h6" fontWeight={900}>
                                {getCategoryName(budget.category_id)}
                              </Typography>

                              <Stack direction="row" spacing={1} flexWrap="wrap" mt={0.5}>
                                <Chip
                                  label={`${monthNames[Number(budget.month) - 1]} ${budget.year}`}
                                  color="primary"
                                  size="small"
                                />

                                <Chip
                                  label="Expense Budget"
                                  color="error"
                                  size="small"
                                  variant="outlined"
                                />
                              </Stack>
                            </Box>
                          </Stack>

                          <Stack direction="row" spacing={2} alignItems="center">
                            <Typography variant="h6" fontWeight={900}>
                              {formatCurrency(budget.budget_amount)}
                            </Typography>

                            <Tooltip title="Edit budget">
                              <IconButton onClick={() => handleOpenEdit(budget)}>
                                <EditIcon />
                              </IconButton>
                            </Tooltip>

                            <Tooltip title="Delete budget">
                              <IconButton
                                color="error"
                                onClick={() => setDeleteTarget(budget)}
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
          <Stack spacing={3}>
            <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
              <CardContent>
                <Stack direction="row" spacing={1} alignItems="center" mb={2}>
                  <WarningAmberIcon color={getUsageColor(utilization)} />
                  <Typography variant="h6" fontWeight={900}>
                    Budget Utilization
                  </Typography>
                </Stack>

                {summaryLoading ? (
                  <Box display="flex" justifyContent="center" py={4}>
                    <CircularProgress size={28} />
                  </Box>
                ) : (
                  <>
                    <Typography variant="h4" fontWeight={900}>
                      {utilization.toFixed(2)}%
                    </Typography>

                    <LinearProgress
                      variant="determinate"
                      value={Math.min(utilization, 100)}
                      color={getUsageColor(utilization)}
                      sx={{ height: 10, borderRadius: 10, mt: 2 }}
                    />

                    <Typography variant="body2" color="text.secondary" mt={1.5}>
                      {utilization >= 100
                        ? "You have crossed your planned budget."
                        : utilization >= 70
                        ? "You are close to your budget limit."
                        : "Your spending is within a healthy range."}
                    </Typography>
                  </>
                )}
              </CardContent>
            </Card>

            <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
              <CardContent>
                <Typography variant="h6" fontWeight={900} mb={2}>
                  Category Budget Summary
                </Typography>

                {categorySummary.length === 0 ? (
                  <Typography color="text.secondary">
                    Category-wise budget usage will appear after adding budgets and expenses.
                  </Typography>
                ) : (
                  <Stack spacing={2}>
                    {categorySummary.map((item) => {
                      const used =
                        Number(item.budget) > 0
                          ? (Number(item.expense) / Number(item.budget)) * 100
                          : 0;

                      return (
                        <Box key={item.category_name}>
                          <Stack direction="row" justifyContent="space-between">
                            <Typography fontWeight={800}>
                              {item.category_name}
                            </Typography>
                            <Typography fontWeight={900}>
                              {formatCurrency(item.expense)} / {formatCurrency(item.budget)}
                            </Typography>
                          </Stack>

                          <LinearProgress
                            variant="determinate"
                            value={Math.min(used, 100)}
                            color={getUsageColor(used)}
                            sx={{ height: 8, borderRadius: 10, mt: 1 }}
                          />

                          <Typography variant="caption" color="text.secondary">
                            Remaining: {formatCurrency(item.remaining)}
                          </Typography>
                        </Box>
                      );
                    })}
                  </Stack>
                )}
              </CardContent>
            </Card>
          </Stack>
        </Grid>
      </Grid>

      <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm">
        <DialogTitle fontWeight={900}>
          {editingBudget ? "Edit Budget" : "Add Budget"}
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
                  <MenuItem key={category.category_id} value={category.category_id}>
                    {category.category_name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth margin="normal">
                  <InputLabel>Month</InputLabel>
                  <Select
                    label="Month"
                    name="month"
                    value={formData.month}
                    onChange={handleChange}
                  >
                    {monthNames.map((month, index) => (
                      <MenuItem key={month} value={index + 1}>
                        {month}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  label="Year"
                  name="year"
                  type="number"
                  value={formData.year}
                  onChange={handleChange}
                  fullWidth
                  required
                  margin="normal"
                  inputProps={{ min: 2024 }}
                />
              </Grid>
            </Grid>

            <TextField
              label="Budget Amount"
              name="budget_amount"
              type="number"
              value={formData.budget_amount}
              onChange={handleChange}
              fullWidth
              required
              margin="normal"
              inputProps={{ min: 1, step: "0.01" }}
              InputProps={{
                startAdornment: <InputAdornment position="start">₹</InputAdornment>,
              }}
            />
          </DialogContent>

          <DialogActions sx={{ px: 3, pb: 3 }}>
            <Button onClick={handleClose} disabled={saving}>
              Cancel
            </Button>

            <Button type="submit" variant="contained" disabled={saving}>
              {saving
                ? "Saving..."
                : editingBudget
                ? "Update Budget"
                : "Create Budget"}
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
        <DialogTitle fontWeight={900}>Delete Budget</DialogTitle>

        <DialogContent>
          <Typography>
            Are you sure you want to delete this budget?
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
                {getCategoryName(deleteTarget.category_id)}
              </Typography>
              <Typography color="primary.main" fontWeight={900}>
                {formatCurrency(deleteTarget.budget_amount)}
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

export default BudgetPage;
---------------------------------------

