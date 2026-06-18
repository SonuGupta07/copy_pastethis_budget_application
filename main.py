export const decodeJwtPayload = (token) => {
  try {
    if (!token) return null;

    const base64Url = token.split(".")[1];
    if (!base64Url) return null;

    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((char) => {
          return `%${`00${char.charCodeAt(0).toString(16)}`.slice(-2)}`;
        })
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
--------------------------------------
import api from "./axios";

export const getIncome = async () => {
  const response = await api.get("/income/");
  return response.data;
};

export const createIncome = async (data) => {
  const response = await api.post("/income/", data);
  return response.data;
};

export const updateIncome = async (incomeId, data) => {
  const response = await api.put(`/income/${incomeId}`, data);
  return response.data;
};

export const deleteIncome = async (incomeId) => {
  const response = await api.delete(`/income/${incomeId}`);
  return response.data;
};
---------------------------------
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  createIncome,
  deleteIncome,
  getIncome,
  updateIncome,
} from "../api/incomeApi";
import { getUserIdFromToken } from "../utils/jwt";

const useIncome = () => {
  const [incomeList, setIncomeList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState("");

  const userId = useMemo(() => getUserIdFromToken(), []);

  const fetchIncome = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await getIncome();
      const list = Array.isArray(data) ? data : [];

      const userSpecificIncome = userId
        ? list.filter((item) => Number(item.user_id) === Number(userId))
        : list;

      setIncomeList(userSpecificIncome);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          "Failed to load income records"
      );
    } finally {
      setLoading(false);
    }
  }, [userId]);

  const addIncome = async (payload) => {
    setSaving(true);
    setError("");

    try {
      if (!userId) {
        throw new Error("User ID not found in token. Please login again.");
      }

      await createIncome({
        user_id: Number(userId),
        category_id: Number(payload.category_id),
        amount: Number(payload.amount),
        description: payload.description,
        income_date: payload.income_date,
      });

      await fetchIncome();
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        err.message ||
        "Failed to create income";

      setError(message);
      throw new Error(message);
    } finally {
      setSaving(false);
    }
  };

  const editIncome = async (incomeId, payload) => {
    setSaving(true);
    setError("");

    try {
      await updateIncome(incomeId, {
        category_id: Number(payload.category_id),
        amount: Number(payload.amount),
        description: payload.description,
        income_date: payload.income_date,
      });

      await fetchIncome();
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        "Failed to update income";

      setError(message);
      throw new Error(message);
    } finally {
      setSaving(false);
    }
  };

  const removeIncome = async (incomeId) => {
    setDeleting(true);
    setError("");

    try {
      await deleteIncome(incomeId);
      await fetchIncome();
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        "Failed to delete income";

      setError(message);
      throw new Error(message);
    } finally {
      setDeleting(false);
    }
  };

  useEffect(() => {
    fetchIncome();
  }, [fetchIncome]);

  return {
    incomeList,
    loading,
    saving,
    deleting,
    error,
    userId,
    fetchIncome,
    addIncome,
    editIncome,
    removeIncome,
  };
};

export default useIncome;
--------------------------------
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
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import AddIcon from "@mui/icons-material/Add";
import RefreshIcon from "@mui/icons-material/Refresh";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import CurrencyRupeeIcon from "@mui/icons-material/CurrencyRupee";
import PageHeader from "../../components/common/PageHeader";
import useIncome from "../../hooks/useIncome";
import useCategories from "../../hooks/useCategories";

const getToday = () => {
  return new Date().toISOString().slice(0, 10);
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

const IncomePage = () => {
  const {
    incomeList,
    loading,
    saving,
    deleting,
    error,
    fetchIncome,
    addIncome,
    editIncome,
    removeIncome,
  } = useIncome();

  const { categories, loading: categoryLoading } = useCategories();

  const incomeCategories = useMemo(() => {
    return categories.filter((category) => category.category_type === "INCOME");
  }, [categories]);

  const [open, setOpen] = useState(false);
  const [editingIncome, setEditingIncome] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [formError, setFormError] = useState("");
  const [search, setSearch] = useState("");

  const [formData, setFormData] = useState({
    category_id: "",
    amount: "",
    description: "",
    income_date: getToday(),
  });

  const totalIncome = useMemo(() => {
    return incomeList.reduce((sum, item) => sum + Number(item.amount || 0), 0);
  }, [incomeList]);

  const currentMonthIncome = useMemo(() => {
    const now = new Date();
    const currentMonth = now.getMonth();
    const currentYear = now.getFullYear();

    return incomeList.reduce((sum, item) => {
      const date = new Date(item.income_date);

      if (
        date.getMonth() === currentMonth &&
        date.getFullYear() === currentYear
      ) {
        return sum + Number(item.amount || 0);
      }

      return sum;
    }, 0);
  }, [incomeList]);

  const highestIncome = useMemo(() => {
    if (incomeList.length === 0) return 0;

    return Math.max(...incomeList.map((item) => Number(item.amount || 0)));
  }, [incomeList]);

  const filteredIncome = useMemo(() => {
    return incomeList.filter((income) => {
      const category = incomeCategories.find(
        (item) => Number(item.category_id) === Number(income.category_id)
      );

      const searchValue = `${income.description || ""} ${
        category?.category_name || ""
      }`
        .toLowerCase()
        .trim();

      return searchValue.includes(search.toLowerCase());
    });
  }, [incomeList, incomeCategories, search]);

  const getCategoryName = (categoryId) => {
    const category = incomeCategories.find(
      (item) => Number(item.category_id) === Number(categoryId)
    );

    return category?.category_name || "Unknown Category";
  };

  const handleOpenAdd = () => {
    setEditingIncome(null);
    setFormError("");
    setFormData({
      category_id: "",
      amount: "",
      description: "",
      income_date: getToday(),
    });
    setOpen(true);
  };

  const handleOpenEdit = (income) => {
    setEditingIncome(income);
    setFormError("");
    setFormData({
      category_id: income.category_id || "",
      amount: income.amount || "",
      description: income.description || "",
      income_date: income.income_date || getToday(),
    });
    setOpen(true);
  };

  const handleClose = () => {
    if (!saving) {
      setOpen(false);
      setEditingIncome(null);
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
      return "Please select an income category";
    }

    if (!formData.amount || Number(formData.amount) <= 0) {
      return "Amount must be greater than zero";
    }

    if (!formData.description.trim()) {
      return "Description is required";
    }

    if (!formData.income_date) {
      return "Income date is required";
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
        income_date: formData.income_date,
      };

      if (editingIncome) {
        await editIncome(editingIncome.income_id, payload);
      } else {
        await addIncome(payload);
      }

      handleClose();
    } catch (err) {
      setFormError(err.message || "Something went wrong");
    }
  };

  const handleConfirmDelete = async () => {
    if (!deleteTarget) return;

    try {
      await removeIncome(deleteTarget.income_id);
      setDeleteTarget(null);
    } catch {
      // error is already handled in hook
    }
  };

  return (
    <Box>
      <PageHeader
        title="Income Tracking"
        subtitle="Track salary, business income, freelance income, investment returns and other income sources."
        breadcrumbs={["Finance", "Income"]}
        actionText="Add Income"
        onAction={handleOpenAdd}
      />

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={4}>
          <Card
            elevation={0}
            sx={{
              border: "1px solid",
              borderColor: "divider",
              height: "100%",
            }}
          >
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
                    background: "linear-gradient(135deg, #16a34a, #22c55e)",
                  }}
                >
                  <TrendingUpIcon />
                </Box>

                <Box>
                  <Typography color="text.secondary" fontWeight={700}>
                    Total Income
                  </Typography>
                  <Typography variant="h5" fontWeight={900}>
                    {formatCurrency(totalIncome)}
                  </Typography>
                </Box>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card
            elevation={0}
            sx={{
              border: "1px solid",
              borderColor: "divider",
              height: "100%",
            }}
          >
            <CardContent>
              <Typography color="text.secondary" fontWeight={700}>
                Current Month Income
              </Typography>
              <Typography variant="h5" fontWeight={900} color="success.main">
                {formatCurrency(currentMonthIncome)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Income recorded for this month.
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card
            elevation={0}
            sx={{
              border: "1px solid",
              borderColor: "divider",
              height: "100%",
            }}
          >
            <CardContent>
              <Typography color="text.secondary" fontWeight={700}>
                Highest Income Entry
              </Typography>
              <Typography variant="h5" fontWeight={900}>
                {formatCurrency(highestIncome)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Highest single income transaction.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Card
        elevation={0}
        sx={{
          border: "1px solid",
          borderColor: "divider",
        }}
      >
        <CardContent>
          <Stack
            direction={{ xs: "column", md: "row" }}
            justifyContent="space-between"
            spacing={2}
            mb={3}
          >
            <TextField
              label="Search income"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              size="small"
              sx={{ minWidth: { xs: "100%", md: 340 } }}
            />

            <Stack direction="row" spacing={2}>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={fetchIncome}
              >
                Refresh
              </Button>

              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleOpenAdd}
              >
                Add Income
              </Button>
            </Stack>
          </Stack>

          {loading || categoryLoading ? (
            <Box display="flex" justifyContent="center" py={6}>
              <CircularProgress />
            </Box>
          ) : incomeCategories.length === 0 ? (
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
                No income category found
              </Typography>
              <Typography color="text.secondary" mt={1}>
                Please create at least one category with type INCOME before
                adding income.
              </Typography>
            </Box>
          ) : filteredIncome.length === 0 ? (
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
                No income records found
              </Typography>
              <Typography color="text.secondary" mt={1}>
                Add your first income record to start tracking your earnings.
              </Typography>

              <Button
                variant="contained"
                startIcon={<AddIcon />}
                sx={{ mt: 3 }}
                onClick={handleOpenAdd}
              >
                Add Income
              </Button>
            </Box>
          ) : (
            <Stack spacing={2}>
              {filteredIncome.map((income) => (
                <Card
                  key={income.income_id}
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
                            backgroundColor: "success.light",
                            color: "success.contrastText",
                          }}
                        >
                          <CurrencyRupeeIcon />
                        </Box>

                        <Box>
                          <Typography variant="h6" fontWeight={900}>
                            {income.description}
                          </Typography>

                          <Stack
                            direction="row"
                            spacing={1}
                            alignItems="center"
                            flexWrap="wrap"
                            mt={0.5}
                          >
                            <Chip
                              label={getCategoryName(income.category_id)}
                              color="success"
                              size="small"
                            />

                            <Typography
                              variant="body2"
                              color="text.secondary"
                            >
                              {formatDate(income.income_date)}
                            </Typography>
                          </Stack>
                        </Box>
                      </Stack>

                      <Stack
                        direction="row"
                        spacing={2}
                        alignItems="center"
                        sx={{ width: { xs: "100%", md: "auto" } }}
                      >
                        <Typography
                          variant="h6"
                          fontWeight={900}
                          color="success.main"
                          sx={{ minWidth: 130 }}
                        >
                          {formatCurrency(income.amount)}
                        </Typography>

                        <Tooltip title="Edit income">
                          <IconButton onClick={() => handleOpenEdit(income)}>
                            <EditIcon />
                          </IconButton>
                        </Tooltip>

                        <Tooltip title="Delete income">
                          <IconButton
                            color="error"
                            onClick={() => setDeleteTarget(income)}
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

      <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm">
        <DialogTitle fontWeight={900}>
          {editingIncome ? "Edit Income" : "Add Income"}
        </DialogTitle>

        <Box component="form" onSubmit={handleSubmit}>
          <DialogContent>
            {formError && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {formError}
              </Alert>
            )}

            <FormControl fullWidth margin="normal">
              <InputLabel>Income Category</InputLabel>
              <Select
                label="Income Category"
                name="category_id"
                value={formData.category_id}
                onChange={handleChange}
              >
                {incomeCategories.map((category) => (
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
              placeholder="Example: June salary, Freelance project, Bonus"
            />

            <TextField
              label="Income Date"
              name="income_date"
              type="date"
              value={formData.income_date}
              onChange={handleChange}
              fullWidth
              required
              margin="normal"
              InputLabelProps={{
                shrink: true,
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
                : editingIncome
                ? "Update Income"
                : "Create Income"}
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
        <DialogTitle fontWeight={900}>Delete Income</DialogTitle>

        <DialogContent>
          <Typography>
            Are you sure you want to delete this income record?
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
              <Typography color="success.main" fontWeight={900}>
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

export default IncomePage;
-----------------------------------
