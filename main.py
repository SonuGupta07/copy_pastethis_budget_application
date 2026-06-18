sonu
import api from "./axios";

export const getCategories = async () => {
  const response = await api.get("/categories/");
  return response.data;
};

export const createCategory = async (data) => {
  const response = await api.post("/categories/", data);
  return response.data;
};
----------------------------
import { useCallback, useEffect, useState } from "react";
import { createCategory, getCategories } from "../api/categoryApi";

const useCategories = () => {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  const fetchCategories = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const data = await getCategories();
      setCategories(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          "Failed to load categories"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  const addCategory = async (payload) => {
    setCreating(true);
    setError("");

    try {
      await createCategory(payload);
      await fetchCategories();
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        "Failed to create category";

      setError(message);
      throw new Error(message);
    } finally {
      setCreating(false);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  return {
    categories,
    loading,
    creating,
    error,
    fetchCategories,
    addCategory,
  };
};

export default useCategories;
-----------------
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
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import CategoryIcon from "@mui/icons-material/Category";
import AddIcon from "@mui/icons-material/Add";
import RefreshIcon from "@mui/icons-material/Refresh";
import PageHeader from "../../components/common/PageHeader";
import useCategories from "../../hooks/useCategories";

const CategoryPage = () => {
  const {
    categories,
    loading,
    creating,
    error,
    fetchCategories,
    addCategory,
  } = useCategories();

  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState({
    category_name: "",
    category_type: "EXPENSE",
  });
  const [formError, setFormError] = useState("");
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("ALL");

  const incomeCount = useMemo(
    () => categories.filter((item) => item.category_type === "INCOME").length,
    [categories]
  );

  const expenseCount = useMemo(
    () => categories.filter((item) => item.category_type === "EXPENSE").length,
    [categories]
  );

  const filteredCategories = useMemo(() => {
    return categories.filter((category) => {
      const matchesSearch = category.category_name
        ?.toLowerCase()
        .includes(search.toLowerCase());

      const matchesType =
        typeFilter === "ALL" || category.category_type === typeFilter;

      return matchesSearch && matchesType;
    });
  }, [categories, search, typeFilter]);

  const handleOpen = () => {
    setFormData({
      category_name: "",
      category_type: "EXPENSE",
    });
    setFormError("");
    setOpen(true);
  };

  const handleClose = () => {
    if (!creating) {
      setOpen(false);
    }
  };

  const handleChange = (event) => {
    setFormData({
      ...formData,
      [event.target.name]: event.target.value,
    });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setFormError("");

    if (!formData.category_name.trim()) {
      setFormError("Category name is required");
      return;
    }

    try {
      await addCategory({
        category_name: formData.category_name.trim(),
        category_type: formData.category_type,
      });

      setOpen(false);
    } catch (err) {
      setFormError(err.message || "Failed to create category");
    }
  };

  const getTypeChip = (type) => {
    if (type === "INCOME") {
      return <Chip label="INCOME" color="success" size="small" />;
    }

    return <Chip label="EXPENSE" color="error" size="small" />;
  };

  return (
    <Box>
      <PageHeader
        title="Category Management"
        subtitle="Create and manage income and expense categories used across finance modules."
        breadcrumbs={["Finance", "Categories"]}
        actionText="Add Category"
        onAction={handleOpen}
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
                    width: 48,
                    height: 48,
                    borderRadius: 3,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    background: "linear-gradient(135deg, #2563eb, #7c3aed)",
                    color: "white",
                  }}
                >
                  <CategoryIcon />
                </Box>

                <Box>
                  <Typography color="text.secondary" fontWeight={700}>
                    Total Categories
                  </Typography>
                  <Typography variant="h5">{categories.length}</Typography>
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
                Income Categories
              </Typography>
              <Typography variant="h5" color="success.main">
                {incomeCount}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Used for salary, business income, investments and more.
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
                Expense Categories
              </Typography>
              <Typography variant="h5" color="error.main">
                {expenseCount}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Used for food, travel, rent, shopping and other expenses.
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
            spacing={2}
            justifyContent="space-between"
            mb={3}
          >
            <TextField
              label="Search categories"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              size="small"
              sx={{ minWidth: { xs: "100%", md: 320 } }}
            />

            <Stack direction="row" spacing={2}>
              <FormControl size="small" sx={{ minWidth: 160 }}>
                <InputLabel>Type</InputLabel>
                <Select
                  label="Type"
                  value={typeFilter}
                  onChange={(event) => setTypeFilter(event.target.value)}
                >
                  <MenuItem value="ALL">All</MenuItem>
                  <MenuItem value="INCOME">Income</MenuItem>
                  <MenuItem value="EXPENSE">Expense</MenuItem>
                </Select>
              </FormControl>

              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={fetchCategories}
              >
                Refresh
              </Button>

              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleOpen}
              >
                Add
              </Button>
            </Stack>
          </Stack>

          {loading ? (
            <Box display="flex" justifyContent="center" py={6}>
              <CircularProgress />
            </Box>
          ) : filteredCategories.length === 0 ? (
            <Box
              sx={{
                py: 8,
                textAlign: "center",
                border: "1px dashed",
                borderColor: "divider",
                borderRadius: 3,
              }}
            >
              <Typography variant="h6" fontWeight={800}>
                No categories found
              </Typography>
              <Typography color="text.secondary" mt={1}>
                Create your first income or expense category.
              </Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                sx={{ mt: 3 }}
                onClick={handleOpen}
              >
                Add Category
              </Button>
            </Box>
          ) : (
            <Grid container spacing={2}>
              {filteredCategories.map((category) => (
                <Grid
                  item
                  xs={12}
                  sm={6}
                  md={4}
                  lg={3}
                  key={category.category_id}
                >
                  <Card
                    elevation={0}
                    sx={{
                      border: "1px solid",
                      borderColor: "divider",
                      height: "100%",
                      transition: "0.2s ease",
                      "&:hover": {
                        transform: "translateY(-3px)",
                        boxShadow: "0 12px 30px rgba(15, 23, 42, 0.12)",
                      },
                    }}
                  >
                    <CardContent>
                      <Stack
                        direction="row"
                        justifyContent="space-between"
                        alignItems="flex-start"
                      >
                        <Box
                          sx={{
                            width: 42,
                            height: 42,
                            borderRadius: 3,
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            backgroundColor: "action.hover",
                          }}
                        >
                          <CategoryIcon color="primary" />
                        </Box>

                        {getTypeChip(category.category_type)}
                      </Stack>

                      <Typography variant="h6" mt={2} fontWeight={900}>
                        {category.category_name}
                      </Typography>

                      <Typography variant="body2" color="text.secondary">
                        Category ID: {category.category_id}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </CardContent>
      </Card>

      <Dialog open={open} onClose={handleClose} fullWidth maxWidth="sm">
        <DialogTitle fontWeight={900}>Add New Category</DialogTitle>

        <Box component="form" onSubmit={handleSubmit}>
          <DialogContent>
            {formError && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {formError}
              </Alert>
            )}

            <TextField
              label="Category Name"
              name="category_name"
              value={formData.category_name}
              onChange={handleChange}
              fullWidth
              required
              margin="normal"
              placeholder="Example: Salary, Food, Rent, Travel"
            />

            <FormControl fullWidth margin="normal">
              <InputLabel>Category Type</InputLabel>
              <Select
                label="Category Type"
                name="category_type"
                value={formData.category_type}
                onChange={handleChange}
              >
                <MenuItem value="INCOME">Income</MenuItem>
                <MenuItem value="EXPENSE">Expense</MenuItem>
              </Select>
            </FormControl>
          </DialogContent>

          <DialogActions sx={{ px: 3, pb: 3 }}>
            <Button onClick={handleClose} disabled={creating}>
              Cancel
            </Button>

            <Button type="submit" variant="contained" disabled={creating}>
              {creating ? "Creating..." : "Create Category"}
            </Button>
          </DialogActions>
        </Box>
      </Dialog>
    </Box>
  );
};

export default CategoryPage;
----------------------------------
