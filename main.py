import api from "./axios";

export const getDashboardOverview = async (userId) => {
  const response = await api.get(`/dashboard/${userId}`);
  return response.data;
};

export const getFinancialHealth = async (userId) => {
  const response = await api.get(`/financial-health/${userId}`);
  return response.data;
};

export const getTrendAnalysis = async (userId) => {
  const response = await api.get(`/analytics/trend/${userId}`);
  return response.data;
};

export const getAllCategories = async () => {
  const response = await api.get("/categories/");
  return response.data;
};

export const getAllIncome = async () => {
  const response = await api.get("/income/");
  return response.data;
};

export const getAllExpenses = async () => {
  const response = await api.get("/expense/");
  return response.data;
};

export const getAllBudgets = async () => {
  const response = await api.get("/budget/");
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
--------------------------
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getAllBudgets,
  getAllCategories,
  getAllExpenses,
  getAllIncome,
  getAllRecurringTransactions,
  getAllSavingsGoals,
  getDashboardOverview,
  getFinancialHealth,
  getTrendAnalysis,
} from "../api/dashboardApi";
import { getUserIdFromToken } from "../utils/jwt";

const monthLabels = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

const normalizeArray = (data) => {
  if (Array.isArray(data)) return data;
  if (!data) return [];
  return [data];
};

const getYear = (dateValue) => {
  if (!dateValue) return null;
  return new Date(dateValue).getFullYear();
};

const getMonth = (dateValue) => {
  if (!dateValue) return null;
  return new Date(dateValue).getMonth() + 1;
};

const groupByCategory = (records, categories, amountKey) => {
  const categoryMap = {};

  categories.forEach((category) => {
    categoryMap[Number(category.category_id)] = category.category_name;
  });

  const grouped = {};

  records.forEach((record) => {
    const categoryName =
      categoryMap[Number(record.category_id)] || "Unknown Category";

    grouped[categoryName] =
      (grouped[categoryName] || 0) + Number(record[amountKey] || 0);
  });

  return Object.entries(grouped).map(([category, amount]) => ({
    category,
    amount,
  }));
};

const useDashboard = () => {
  const userId = useMemo(() => getUserIdFromToken(), []);

  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState("ALL");

  const [overview, setOverview] = useState(null);
  const [financialHealth, setFinancialHealth] = useState(null);
  const [trend, setTrend] = useState(null);

  const [categories, setCategories] = useState([]);
  const [incomeList, setIncomeList] = useState([]);
  const [expenseList, setExpenseList] = useState([]);
  const [budgetList, setBudgetList] = useState([]);
  const [savingsGoals, setSavingsGoals] = useState([]);
  const [recurringList, setRecurringList] = useState([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchDashboard = useCallback(async () => {
    if (!userId) {
      setError("User ID not found in token. Please login again.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const results = await Promise.allSettled([
        getDashboardOverview(userId),
        getFinancialHealth(userId),
        getTrendAnalysis(userId),
        getAllCategories(),
        getAllIncome(),
        getAllExpenses(),
        getAllBudgets(),
        getAllSavingsGoals(),
        getAllRecurringTransactions(),
      ]);

      if (results[0].status === "fulfilled") setOverview(results[0].value);
      if (results[1].status === "fulfilled") setFinancialHealth(results[1].value);
      if (results[2].status === "fulfilled") setTrend(results[2].value);

      const allCategories =
        results[3].status === "fulfilled" ? normalizeArray(results[3].value) : [];

      const allIncome =
        results[4].status === "fulfilled" ? normalizeArray(results[4].value) : [];

      const allExpenses =
        results[5].status === "fulfilled" ? normalizeArray(results[5].value) : [];

      const allBudgets =
        results[6].status === "fulfilled" ? normalizeArray(results[6].value) : [];

      const allSavings =
        results[7].status === "fulfilled" ? normalizeArray(results[7].value) : [];

      const allRecurring =
        results[8].status === "fulfilled" ? normalizeArray(results[8].value) : [];

      setCategories(allCategories);

      setIncomeList(
        allIncome.filter((item) => Number(item.user_id) === Number(userId))
      );

      setExpenseList(
        allExpenses.filter((item) => Number(item.user_id) === Number(userId))
      );

      setBudgetList(
        allBudgets.filter((item) => Number(item.user_id) === Number(userId))
      );

      setSavingsGoals(
        allSavings.filter((item) => Number(item.user_id) === Number(userId))
      );

      setRecurringList(
        allRecurring.filter((item) => Number(item.user_id) === Number(userId))
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          "Failed to load dashboard"
      );
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const categoryMap = useMemo(() => {
    const map = {};

    categories.forEach((category) => {
      map[Number(category.category_id)] = category.category_name;
    });

    return map;
  }, [categories]);

  const yearIncome = useMemo(() => {
    return incomeList.filter(
      (item) => Number(getYear(item.income_date)) === Number(year)
    );
  }, [incomeList, year]);

  const yearExpenses = useMemo(() => {
    return expenseList.filter(
      (item) => Number(getYear(item.expense_date)) === Number(year)
    );
  }, [expenseList, year]);

  const periodIncome = useMemo(() => {
    if (month === "ALL") return yearIncome;

    return yearIncome.filter(
      (item) => Number(getMonth(item.income_date)) === Number(month)
    );
  }, [yearIncome, month]);

  const periodExpenses = useMemo(() => {
    if (month === "ALL") return yearExpenses;

    return yearExpenses.filter(
      (item) => Number(getMonth(item.expense_date)) === Number(month)
    );
  }, [yearExpenses, month]);

  const periodBudgets = useMemo(() => {
    return budgetList.filter((budget) => {
      const matchesYear = Number(budget.year) === Number(year);
      const matchesMonth =
        month === "ALL" || Number(budget.month) === Number(month);

      return matchesYear && matchesMonth;
    });
  }, [budgetList, year, month]);

  const monthlyCashFlow = useMemo(() => {
    return monthLabels.map((monthName, index) => {
      const monthNumber = index + 1;

      const income = yearIncome
        .filter((item) => Number(getMonth(item.income_date)) === monthNumber)
        .reduce((sum, item) => sum + Number(item.amount || 0), 0);

      const expense = yearExpenses
        .filter((item) => Number(getMonth(item.expense_date)) === monthNumber)
        .reduce((sum, item) => sum + Number(item.amount || 0), 0);

      return {
        month: monthName,
        income,
        expense,
        balance: income - expense,
      };
    });
  }, [yearIncome, yearExpenses]);

  const incomeDistribution = useMemo(() => {
    return groupByCategory(periodIncome, categories, "amount");
  }, [periodIncome, categories]);

  const expenseDistribution = useMemo(() => {
    return groupByCategory(periodExpenses, categories, "amount");
  }, [periodExpenses, categories]);

  const budgetCategorySummary = useMemo(() => {
    return periodBudgets.map((budget) => {
      const expenseForBudget = yearExpenses
        .filter((expense) => {
          const sameCategory =
            Number(expense.category_id) === Number(budget.category_id);

          const sameMonth =
            Number(getMonth(expense.expense_date)) === Number(budget.month);

          return sameCategory && sameMonth;
        })
        .reduce((sum, expense) => sum + Number(expense.amount || 0), 0);

      const budgetAmount = Number(budget.budget_amount || 0);

      return {
        category_id: budget.category_id,
        category_name: categoryMap[Number(budget.category_id)] || "Unknown",
        month: budget.month,
        year: budget.year,
        budget: budgetAmount,
        expense: expenseForBudget,
        remaining: budgetAmount - expenseForBudget,
        utilization_percentage:
          budgetAmount > 0
            ? Number(((expenseForBudget / budgetAmount) * 100).toFixed(2))
            : 0,
      };
    });
  }, [periodBudgets, yearExpenses, categoryMap]);

  const recentTransactions = useMemo(() => {
    const incomeTransactions = incomeList.map((item) => ({
      id: `income-${item.income_id}`,
      type: "INCOME",
      description: item.description,
      amount: Number(item.amount || 0),
      date: item.income_date,
      category: categoryMap[Number(item.category_id)] || "Income",
    }));

    const expenseTransactions = expenseList.map((item) => ({
      id: `expense-${item.expense_id}`,
      type: "EXPENSE",
      description: item.description,
      amount: Number(item.amount || 0),
      date: item.expense_date,
      category: categoryMap[Number(item.category_id)] || "Expense",
    }));

    return [...incomeTransactions, ...expenseTransactions]
      .sort((a, b) => new Date(b.date) - new Date(a.date))
      .slice(0, 8);
  }, [incomeList, expenseList, categoryMap]);

  const upcomingRecurring = useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    return recurringList
      .map((item) => {
        const nextDate = new Date(item.next_run_date);
        nextDate.setHours(0, 0, 0, 0);

        const daysLeft = Math.ceil(
          (nextDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)
        );

        return {
          ...item,
          category_name: categoryMap[Number(item.category_id)] || "Unknown",
          days_left: daysLeft,
        };
      })
      .filter((item) => item.days_left >= 0)
      .sort((a, b) => a.days_left - b.days_left)
      .slice(0, 5);
  }, [recurringList, categoryMap]);

  const totals = useMemo(() => {
    const totalIncome = periodIncome.reduce(
      (sum, item) => sum + Number(item.amount || 0),
      0
    );

    const totalExpense = periodExpenses.reduce(
      (sum, item) => sum + Number(item.amount || 0),
      0
    );

    const totalBudget = periodBudgets.reduce(
      (sum, item) => sum + Number(item.budget_amount || 0),
      0
    );

    const savingsTarget = savingsGoals.reduce(
      (sum, item) => sum + Number(item.target_amount || 0),
      0
    );

    const currentSavings = savingsGoals.reduce(
      (sum, item) => sum + Number(item.current_amount || 0),
      0
    );

    const savingsProgress =
      savingsTarget > 0
        ? Number(((currentSavings / savingsTarget) * 100).toFixed(2))
        : 0;

    const budgetUtilization =
      totalBudget > 0
        ? Number(((totalExpense / totalBudget) * 100).toFixed(2))
        : 0;

    return {
      totalIncome,
      totalExpense,
      totalBudget,
      netBalance: totalIncome - totalExpense,
      savingsTarget,
      currentSavings,
      savingsProgress,
      budgetUtilization,
      remainingBudget: totalBudget - totalExpense,
    };
  }, [periodIncome, periodExpenses, periodBudgets, savingsGoals]);

  const computedHealthScore = useMemo(() => {
    let score = 50;

    if (totals.totalIncome > 0) {
      const expenseRatio = totals.totalExpense / totals.totalIncome;
      const savingsRatio = totals.currentSavings / totals.totalIncome;

      if (expenseRatio <= 0.5) score += 20;
      else if (expenseRatio <= 0.75) score += 10;
      else score -= 10;

      if (savingsRatio >= 0.2) score += 20;
      else if (savingsRatio >= 0.1) score += 10;
    }

    if (totals.totalBudget > 0) {
      const budgetUsage = totals.totalExpense / totals.totalBudget;

      if (budgetUsage <= 0.8) score += 10;
      else if (budgetUsage > 1) score -= 15;
    }

    return Math.max(0, Math.min(100, score));
  }, [totals]);

  return {
    userId,
    year,
    setYear,
    month,
    setMonth,
    overview,
    financialHealth,
    trend,
    monthlyCashFlow,
    incomeDistribution,
    expenseDistribution,
    budgetCategorySummary,
    recentTransactions,
    upcomingRecurring,
    totals,
    computedHealthScore,
    loading,
    error,
    fetchDashboard,
  };
};

export default useDashboard;
-------------------------------------------
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  FormControl,
  Grid,
  InputLabel,
  LinearProgress,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from "@mui/material";

import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import ReceiptLongIcon from "@mui/icons-material/ReceiptLong";
import AccountBalanceWalletIcon from "@mui/icons-material/AccountBalanceWallet";
import SavingsIcon from "@mui/icons-material/Savings";
import HealthAndSafetyIcon from "@mui/icons-material/HealthAndSafety";
import RefreshIcon from "@mui/icons-material/Refresh";
import InsightsIcon from "@mui/icons-material/Insights";
import RepeatIcon from "@mui/icons-material/Repeat";

import {
  Area,
  Bar,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import PageHeader from "../../components/common/PageHeader";
import useDashboard from "../../hooks/useDashboard";

const COLORS = [
  "#2563eb",
  "#dc2626",
  "#16a34a",
  "#7c3aed",
  "#f59e0b",
  "#0891b2",
  "#db2777",
  "#65a30d",
];

const monthOptions = [
  { label: "All Months", value: "ALL" },
  { label: "January", value: 1 },
  { label: "February", value: 2 },
  { label: "March", value: 3 },
  { label: "April", value: 4 },
  { label: "May", value: 5 },
  { label: "June", value: 6 },
  { label: "July", value: 7 },
  { label: "August", value: 8 },
  { label: "September", value: 9 },
  { label: "October", value: 10 },
  { label: "November", value: 11 },
  { label: "December", value: 12 },
];

const formatCurrency = (value) => {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
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

const getHealthLabel = (score) => {
  if (score >= 80) return "Excellent";
  if (score >= 60) return "Good";
  if (score >= 40) return "Average";
  return "Needs Attention";
};

const getHealthColor = (score) => {
  if (score >= 80) return "success";
  if (score >= 60) return "primary";
  if (score >= 40) return "warning";
  return "error";
};

const KpiCard = ({ title, value, subtitle, icon, color }) => {
  return (
    <Card
      elevation={0}
      sx={{
        height: "100%",
        border: "1px solid",
        borderColor: "divider",
        background:
          "linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.01))",
      }}
    >
      <CardContent>
        <Stack direction="row" justifyContent="space-between" spacing={2}>
          <Box>
            <Typography color="text.secondary" fontWeight={800}>
              {title}
            </Typography>

            <Typography variant="h5" fontWeight={900} mt={1}>
              {value}
            </Typography>

            <Typography variant="body2" color="text.secondary" mt={0.6}>
              {subtitle}
            </Typography>
          </Box>

          <Box
            sx={{
              width: 52,
              height: 52,
              borderRadius: 3,
              color: "white",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: color,
              flexShrink: 0,
            }}
          >
            {icon}
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
};

const DonutChartCard = ({ title, subtitle, data, emptyText }) => {
  return (
    <Card
      elevation={0}
      sx={{
        border: "1px solid",
        borderColor: "divider",
        height: "100%",
      }}
    >
      <CardContent>
        <Typography variant="h6" fontWeight={900}>
          {title}
        </Typography>

        <Typography color="text.secondary" mb={2}>
          {subtitle}
        </Typography>

        {data.length === 0 ? (
          <Box
            sx={{
              height: 280,
              border: "1px dashed",
              borderColor: "divider",
              borderRadius: 3,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              textAlign: "center",
              px: 2,
            }}
          >
            <Typography color="text.secondary">{emptyText}</Typography>
          </Box>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={data}
                dataKey="amount"
                nameKey="category"
                innerRadius={55}
                outerRadius={100}
                paddingAngle={3}
                label={({ category }) => category}
              >
                {data.map((entry, index) => (
                  <Cell
                    key={entry.category}
                    fill={COLORS[index % COLORS.length]}
                  />
                ))}
              </Pie>

              <Tooltip formatter={(value) => formatCurrency(value)} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
};

const Dashboard = () => {
  const {
    year,
    setYear,
    month,
    setMonth,
    trend,
    monthlyCashFlow,
    incomeDistribution,
    expenseDistribution,
    budgetCategorySummary,
    recentTransactions,
    upcomingRecurring,
    totals,
    computedHealthScore,
    loading,
    error,
    fetchDashboard,
  } = useDashboard();

  const expenseRatio =
    totals.totalIncome > 0
      ? ((totals.totalExpense / totals.totalIncome) * 100).toFixed(1)
      : "0.0";

  return (
    <Box>
      <PageHeader
        title="Financial Intelligence Dashboard"
        subtitle="Power BI-style view of income, expenses, savings, budgets, recurring transactions and financial health."
        breadcrumbs={["Overview", "Dashboard"]}
      />

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Card
        elevation={0}
        sx={{
          mb: 3,
          border: "1px solid",
          borderColor: "divider",
        }}
      >
        <CardContent>
          <Stack
            direction={{ xs: "column", md: "row" }}
            spacing={2}
            alignItems={{ xs: "stretch", md: "center" }}
            justifyContent="space-between"
          >
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <TextField
                label="Policy / Dashboard Year"
                type="number"
                size="small"
                value={year}
                onChange={(event) => setYear(event.target.value)}
                sx={{ width: { xs: "100%", sm: 180 } }}
              />

              <FormControl size="small" sx={{ minWidth: 180 }}>
                <InputLabel>Month Filter</InputLabel>
                <Select
                  label="Month Filter"
                  value={month}
                  onChange={(event) => setMonth(event.target.value)}
                >
                  {monthOptions.map((item) => (
                    <MenuItem key={item.label} value={item.value}>
                      {item.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Stack>

            <Button
              variant="contained"
              startIcon={<RefreshIcon />}
              onClick={fetchDashboard}
            >
              Refresh Intelligence
            </Button>
          </Stack>
        </CardContent>
      </Card>

      {loading ? (
        <Box display="flex" justifyContent="center" py={10}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          <Grid container spacing={2.5} mb={3}>
            <Grid item xs={12} sm={6} lg={2.4}>
              <KpiCard
                title="Income"
                value={formatCurrency(totals.totalIncome)}
                subtitle={`${year} selected period`}
                icon={<TrendingUpIcon />}
                color="linear-gradient(135deg, #16a34a, #22c55e)"
              />
            </Grid>

            <Grid item xs={12} sm={6} lg={2.4}>
              <KpiCard
                title="Expense"
                value={formatCurrency(totals.totalExpense)}
                subtitle={`${expenseRatio}% of income`}
                icon={<ReceiptLongIcon />}
                color="linear-gradient(135deg, #dc2626, #ef4444)"
              />
            </Grid>

            <Grid item xs={12} sm={6} lg={2.4}>
              <KpiCard
                title="Balance"
                value={formatCurrency(totals.netBalance)}
                subtitle={totals.netBalance >= 0 ? "Positive cash flow" : "Overspent"}
                icon={<AccountBalanceWalletIcon />}
                color="linear-gradient(135deg, #2563eb, #7c3aed)"
              />
            </Grid>

            <Grid item xs={12} sm={6} lg={2.4}>
              <KpiCard
                title="Savings"
                value={`${totals.savingsProgress.toFixed(1)}%`}
                subtitle={`${formatCurrency(totals.currentSavings)} saved`}
                icon={<SavingsIcon />}
                color="linear-gradient(135deg, #059669, #10b981)"
              />
            </Grid>

            <Grid item xs={12} sm={6} lg={2.4}>
              <KpiCard
                title="Health"
                value={`${computedHealthScore}/100`}
                subtitle={getHealthLabel(computedHealthScore)}
                icon={<HealthAndSafetyIcon />}
                color="linear-gradient(135deg, #0891b2, #2563eb)"
              />
            </Grid>
          </Grid>

          <Grid container spacing={3} mb={3}>
            <Grid item xs={12} lg={8}>
              <Card
                elevation={0}
                sx={{
                  border: "1px solid",
                  borderColor: "divider",
                  minHeight: 470,
                }}
              >
                <CardContent>
                  <Stack direction="row" justifyContent="space-between" mb={2}>
                    <Box>
                      <Typography variant="h6" fontWeight={900}>
                        Cash Flow Performance
                      </Typography>
                      <Typography color="text.secondary">
                        Income, expense and net balance month-wise for {year}.
                      </Typography>
                    </Box>

                    <Chip label={year} color="primary" sx={{ fontWeight: 800 }} />
                  </Stack>

                  <ResponsiveContainer width="100%" height={360}>
                    <ComposedChart data={monthlyCashFlow}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.35} />
                      <XAxis dataKey="month" />
                      <YAxis />
                      <Tooltip formatter={(value) => formatCurrency(value)} />
                      <Legend />

                      <Bar
                        dataKey="income"
                        name="Income"
                        fill="#16a34a"
                        radius={[8, 8, 0, 0]}
                        maxBarSize={34}
                      />

                      <Bar
                        dataKey="expense"
                        name="Expense"
                        fill="#dc2626"
                        radius={[8, 8, 0, 0]}
                        maxBarSize={34}
                      />

                      <Area
                        type="monotone"
                        dataKey="balance"
                        name="Balance Area"
                        fill="#2563eb"
                        stroke="none"
                        fillOpacity={0.08}
                      />

                      <Line
                        type="monotone"
                        dataKey="balance"
                        name="Net Balance"
                        stroke="#2563eb"
                        strokeWidth={3}
                        dot={{ r: 4 }}
                      />
                    </ComposedChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} lg={4}>
              <Stack spacing={3}>
                <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
                  <CardContent>
                    <Typography variant="h6" fontWeight={900}>
                      Budget Utilization
                    </Typography>

                    <Typography variant="h3" fontWeight={900} mt={1}>
                      {totals.budgetUtilization.toFixed(1)}%
                    </Typography>

                    <LinearProgress
                      variant="determinate"
                      value={Math.min(totals.budgetUtilization, 100)}
                      color={
                        totals.budgetUtilization >= 90
                          ? "error"
                          : totals.budgetUtilization >= 70
                          ? "warning"
                          : "success"
                      }
                      sx={{ height: 12, borderRadius: 10, mt: 2 }}
                    />

                    <Stack spacing={1.2} mt={2}>
                      <Stack direction="row" justifyContent="space-between">
                        <Typography color="text.secondary">Budget</Typography>
                        <Typography fontWeight={900}>
                          {formatCurrency(totals.totalBudget)}
                        </Typography>
                      </Stack>

                      <Stack direction="row" justifyContent="space-between">
                        <Typography color="text.secondary">Expense</Typography>
                        <Typography fontWeight={900} color="error.main">
                          {formatCurrency(totals.totalExpense)}
                        </Typography>
                      </Stack>

                      <Stack direction="row" justifyContent="space-between">
                        <Typography color="text.secondary">Remaining</Typography>
                        <Typography
                          fontWeight={900}
                          color={
                            totals.remainingBudget < 0
                              ? "error.main"
                              : "success.main"
                          }
                        >
                          {formatCurrency(totals.remainingBudget)}
                        </Typography>
                      </Stack>
                    </Stack>
                  </CardContent>
                </Card>

                <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
                  <CardContent>
                    <Typography variant="h6" fontWeight={900}>
                      Financial Health
                    </Typography>

                    <Typography variant="h3" fontWeight={900} mt={1}>
                      {computedHealthScore}
                    </Typography>

                    <Chip
                      label={getHealthLabel(computedHealthScore)}
                      color={getHealthColor(computedHealthScore)}
                      sx={{ mt: 1, fontWeight: 800 }}
                    />

                    <LinearProgress
                      variant="determinate"
                      value={computedHealthScore}
                      color={getHealthColor(computedHealthScore)}
                      sx={{ height: 12, borderRadius: 10, mt: 2 }}
                    />
                  </CardContent>
                </Card>
              </Stack>
            </Grid>
          </Grid>

          <Grid container spacing={3} mb={3}>
            <Grid item xs={12} md={6}>
              <DonutChartCard
                title="Expense Distribution"
                subtitle={`Category-wise expenses for selected period in ${year}.`}
                data={expenseDistribution}
                emptyText={`No expense data found for selected period in ${year}.`}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <DonutChartCard
                title="Income Distribution"
                subtitle={`Category-wise income for selected period in ${year}.`}
                data={incomeDistribution}
                emptyText={`No income data found for selected period in ${year}.`}
              />
            </Grid>
          </Grid>

          <Grid container spacing={3} mb={3}>
            <Grid item xs={12} lg={6}>
              <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
                <CardContent>
                  <Typography variant="h6" fontWeight={900} mb={2}>
                    Category Budget Matrix
                  </Typography>

                  {budgetCategorySummary.length === 0 ? (
                    <Typography color="text.secondary">
                      No budget summary available for selected period.
                    </Typography>
                  ) : (
                    <Stack spacing={2}>
                      {budgetCategorySummary.slice(0, 8).map((item) => (
                        <Box key={`${item.category_id}-${item.month}`}>
                          <Stack direction="row" justifyContent="space-between">
                            <Typography fontWeight={800}>
                              {item.category_name}
                            </Typography>

                            <Typography fontWeight={900}>
                              {formatCurrency(item.expense)} /{" "}
                              {formatCurrency(item.budget)}
                            </Typography>
                          </Stack>

                          <LinearProgress
                            variant="determinate"
                            value={Math.min(item.utilization_percentage, 100)}
                            color={
                              item.utilization_percentage >= 90
                                ? "error"
                                : item.utilization_percentage >= 70
                                ? "warning"
                                : "success"
                            }
                            sx={{ height: 9, borderRadius: 10, mt: 1 }}
                          />

                          <Typography variant="caption" color="text.secondary">
                            Remaining: {formatCurrency(item.remaining)} • Usage:{" "}
                            {item.utilization_percentage}%
                          </Typography>
                        </Box>
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
                    Recent Transactions
                  </Typography>

                  {recentTransactions.length === 0 ? (
                    <Typography color="text.secondary">
                      No recent transactions found.
                    </Typography>
                  ) : (
                    <Stack spacing={1.4}>
                      {recentTransactions.map((item) => (
                        <Box
                          key={item.id}
                          sx={{
                            p: 1.5,
                            borderRadius: 3,
                            backgroundColor: "action.hover",
                          }}
                        >
                          <Stack direction="row" justifyContent="space-between">
                            <Box>
                              <Typography fontWeight={900}>
                                {item.description || item.category}
                              </Typography>

                              <Typography variant="body2" color="text.secondary">
                                {item.category} • {formatDate(item.date)}
                              </Typography>
                            </Box>

                            <Typography
                              fontWeight={900}
                              color={
                                item.type === "INCOME"
                                  ? "success.main"
                                  : "error.main"
                              }
                            >
                              {item.type === "INCOME" ? "+" : "-"}
                              {formatCurrency(item.amount)}
                            </Typography>
                          </Stack>
                        </Box>
                      ))}
                    </Stack>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Grid container spacing={3}>
            <Grid item xs={12} lg={6}>
              <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
                <CardContent>
                  <Stack direction="row" spacing={1} alignItems="center" mb={2}>
                    <RepeatIcon color="secondary" />
                    <Typography variant="h6" fontWeight={900}>
                      Upcoming Recurring Transactions
                    </Typography>
                  </Stack>

                  {upcomingRecurring.length === 0 ? (
                    <Typography color="text.secondary">
                      No upcoming recurring transactions.
                    </Typography>
                  ) : (
                    <Stack spacing={1.4}>
                      {upcomingRecurring.map((item) => (
                        <Box
                          key={item.recurring_id}
                          sx={{
                            p: 1.5,
                            borderRadius: 3,
                            backgroundColor: "action.hover",
                          }}
                        >
                          <Stack direction="row" justifyContent="space-between">
                            <Box>
                              <Typography fontWeight={900}>
                                {item.category_name}
                              </Typography>

                              <Typography variant="body2" color="text.secondary">
                                {item.frequency} • {formatDate(item.next_run_date)} •{" "}
                                {item.days_left} day(s) left
                              </Typography>
                            </Box>

                            <Typography
                              fontWeight={900}
                              color={
                                item.transaction_type === "INCOME"
                                  ? "success.main"
                                  : "error.main"
                              }
                            >
                              {formatCurrency(item.amount)}
                            </Typography>
                          </Stack>
                        </Box>
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
                    Smart Trend Insight
                  </Typography>

                  {!trend ? (
                    <Typography color="text.secondary">
                      Add income and expense records to view trend insights.
                    </Typography>
                  ) : (
                    <Stack spacing={2}>
                      <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
                        <Chip
                          label={`Income: ${trend.income_trend || "STABLE"} (${
                            trend.income_change_percent || 0
                          }%)`}
                          color={
                            trend.income_trend === "INCREASING"
                              ? "success"
                              : trend.income_trend === "DECREASING"
                              ? "warning"
                              : "default"
                          }
                          sx={{ fontWeight: 800 }}
                        />

                        <Chip
                          label={`Expense: ${trend.expense_trend || "STABLE"} (${
                            trend.expense_change_percent || 0
                          }%)`}
                          color={
                            trend.expense_trend === "INCREASING"
                              ? "error"
                              : trend.expense_trend === "DECREASING"
                              ? "success"
                              : "default"
                          }
                          sx={{ fontWeight: 800 }}
                        />
                      </Stack>

                      <Alert severity="info">
                        {trend.summary || "Trend summary not available."}
                      </Alert>
                    </Stack>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </>
      )}
    </Box>
  );
};

export default Dashboard;