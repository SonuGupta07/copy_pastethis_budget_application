import api from "./axios";

export const getDashboardOverview = async (userId) => {
  const response = await api.get(`/dashboard/${userId}`);
  return response.data;
};

export const getFinancialHealth = async (userId) => {
  const response = await api.get(`/financial-health/${userId}`);
  return response.data;
};

export const getExpenseDistribution = async (userId) => {
  const response = await api.get(`/analytics/pie-chart/${userId}`);
  return response.data;
};

export const getIncomeExpenseYearChart = async (userId, year) => {
  const response = await api.get(`/analytics/bar-chart-year/${userId}`, {
    params: { year },
  });
  return response.data;
};

export const getTrendAnalysis = async (userId) => {
  const response = await api.get(`/analytics/trend/${userId}`);
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
--------------------------------------------------------------
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getBudgetCategorySummary,
  getBudgetSummary,
  getDashboardOverview,
  getExpenseDistribution,
  getFinancialHealth,
  getIncomeExpenseYearChart,
  getTrendAnalysis,
} from "../api/dashboardApi";
import { getUserIdFromToken } from "../utils/jwt";

const normalizeArray = (data) => {
  if (Array.isArray(data)) return data;
  if (!data) return [];
  return [data];
};

const useDashboard = () => {
  const userId = useMemo(() => getUserIdFromToken(), []);
  const [year, setYear] = useState(new Date().getFullYear());

  const [overview, setOverview] = useState(null);
  const [financialHealth, setFinancialHealth] = useState(null);
  const [expenseDistribution, setExpenseDistribution] = useState([]);
  const [yearChart, setYearChart] = useState([]);
  const [trend, setTrend] = useState(null);
  const [budgetSummary, setBudgetSummary] = useState(null);
  const [budgetCategorySummary, setBudgetCategorySummary] = useState([]);

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
        getExpenseDistribution(userId),
        getIncomeExpenseYearChart(userId, year),
        getTrendAnalysis(userId),
        getBudgetSummary(userId),
        getBudgetCategorySummary(userId),
      ]);

      if (results[0].status === "fulfilled") {
        setOverview(results[0].value);
      }

      if (results[1].status === "fulfilled") {
        setFinancialHealth(results[1].value);
      }

      if (results[2].status === "fulfilled") {
        setExpenseDistribution(normalizeArray(results[2].value));
      }

      if (results[3].status === "fulfilled") {
        setYearChart(normalizeArray(results[3].value));
      }

      if (results[4].status === "fulfilled") {
        setTrend(results[4].value);
      }

      if (results[5].status === "fulfilled") {
        setBudgetSummary(results[5].value);
      }

      if (results[6].status === "fulfilled") {
        setBudgetCategorySummary(normalizeArray(results[6].value));
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          "Failed to load dashboard"
      );
    } finally {
      setLoading(false);
    }
  }, [userId, year]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  return {
    userId,
    year,
    setYear,
    overview,
    financialHealth,
    expenseDistribution,
    yearChart,
    trend,
    budgetSummary,
    budgetCategorySummary,
    loading,
    error,
    fetchDashboard,
  };
};

export default useDashboard;
-------------------------------------------
import { Box, Card, CardContent, Stack, Typography } from "@mui/material";

const DashboardStatCard = ({ title, value, subtitle, icon, color }) => {
  return (
    <Card
      elevation={0}
      sx={{
        height: "100%",
        border: "1px solid",
        borderColor: "divider",
      }}
    >
      <CardContent>
        <Stack direction="row" justifyContent="space-between" spacing={2}>
          <Box>
            <Typography color="text.secondary" fontWeight={700}>
              {title}
            </Typography>

            <Typography variant="h5" fontWeight={900} mt={1}>
              {value}
            </Typography>

            {subtitle && (
              <Typography variant="body2" color="text.secondary" mt={0.8}>
                {subtitle}
              </Typography>
            )}
          </Box>

          <Box
            sx={{
              width: 52,
              height: 52,
              borderRadius: 3,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "white",
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

export default DashboardStatCard;
---------------------------------------------
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Grid,
  LinearProgress,
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
import WarningAmberIcon from "@mui/icons-material/WarningAmber";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import PageHeader from "../../components/common/PageHeader";
import DashboardStatCard from "../../components/cards/DashboardStatCard";
import useDashboard from "../../hooks/useDashboard";

const COLORS = [
  "#2563eb",
  "#dc2626",
  "#16a34a",
  "#7c3aed",
  "#f59e0b",
  "#0891b2",
  "#db2777",
];

const formatCurrency = (value) => {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(Number(value || 0));
};

const getHealthScore = (financialHealth) => {
  return Number(
    financialHealth?.score ||
      financialHealth?.financial_health_score ||
      financialHealth?.health_score ||
      financialHealth?.data?.score ||
      0
  );
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

const Dashboard = () => {
  const {
    year,
    setYear,
    overview,
    financialHealth,
    expenseDistribution,
    yearChart,
    trend,
    budgetSummary,
    budgetCategorySummary,
    loading,
    error,
    fetchDashboard,
  } = useDashboard();

  const totalIncome = Number(overview?.total_income || 0);
  const totalExpense = Number(overview?.total_expense || 0);
  const totalBudget = Number(
    overview?.total_budget || budgetSummary?.total_budget || 0
  );
  const netBalance = Number(overview?.net_balance || 0);
  const savingsTarget = Number(overview?.savings_target || 0);
  const currentSavings = Number(overview?.current_savings || 0);
  const savingsProgress = Number(overview?.savings_progress || 0);

  const healthScore = getHealthScore(financialHealth);

  const budgetUtilization = Number(
    budgetSummary?.utilization_percentage ||
      (totalBudget > 0 ? (totalExpense / totalBudget) * 100 : 0)
  );

  const remainingBudget = Number(
    budgetSummary?.remaining_budget || totalBudget - totalExpense
  );

  const expenseRatio =
    totalIncome > 0 ? ((totalExpense / totalIncome) * 100).toFixed(1) : "0.0";

  const savingsRatio =
    totalIncome > 0 ? ((currentSavings / totalIncome) * 100).toFixed(1) : "0.0";

  return (
    <Box>
      <PageHeader
        title="Financial Dashboard"
        subtitle="Complete analytics, budget health, savings progress and financial score for the logged-in user."
        breadcrumbs={["Overview", "Dashboard"]}
      />

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Stack
        direction={{ xs: "column", md: "row" }}
        justifyContent="space-between"
        spacing={2}
        mb={3}
      >
        <TextField
          label="Analytics Year"
          type="number"
          size="small"
          value={year}
          onChange={(event) => setYear(event.target.value)}
          sx={{ width: { xs: "100%", md: 180 } }}
        />

        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchDashboard}
        >
          Refresh Dashboard
        </Button>
      </Stack>

      {loading ? (
        <Box display="flex" justifyContent="center" py={10}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          <Grid container spacing={3} mb={3}>
            <Grid item xs={12} sm={6} lg={3}>
              <DashboardStatCard
                title="Total Income"
                value={formatCurrency(totalIncome)}
                subtitle="Income recorded by user"
                icon={<TrendingUpIcon />}
                color="linear-gradient(135deg, #16a34a, #22c55e)"
              />
            </Grid>

            <Grid item xs={12} sm={6} lg={3}>
              <DashboardStatCard
                title="Total Expense"
                value={formatCurrency(totalExpense)}
                subtitle={`${expenseRatio}% of income used`}
                icon={<ReceiptLongIcon />}
                color="linear-gradient(135deg, #dc2626, #ef4444)"
              />
            </Grid>

            <Grid item xs={12} sm={6} lg={3}>
              <DashboardStatCard
                title="Net Balance"
                value={formatCurrency(netBalance)}
                subtitle={netBalance >= 0 ? "Positive cash flow" : "Overspending"}
                icon={<AccountBalanceWalletIcon />}
                color="linear-gradient(135deg, #2563eb, #7c3aed)"
              />
            </Grid>

            <Grid item xs={12} sm={6} lg={3}>
              <DashboardStatCard
                title="Financial Health"
                value={`${healthScore}/100`}
                subtitle={getHealthLabel(healthScore)}
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
                  minHeight: 430,
                }}
              >
                <CardContent>
                  <Stack direction="row" justifyContent="space-between" mb={2}>
                    <Box>
                      <Typography variant="h6" fontWeight={900}>
                        Income vs Expense Analytics
                      </Typography>
                      <Typography color="text.secondary">
                        Month-wise income and expense comparison for {year}.
                      </Typography>
                    </Box>

                    <Chip label={year} color="primary" sx={{ fontWeight: 800 }} />
                  </Stack>

                  {yearChart.length === 0 ? (
                    <Box
                      sx={{
                        height: 320,
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
                      <Typography color="text.secondary">
                        No yearly analytics data available. Add income and
                        expense records to populate this chart.
                      </Typography>
                    </Box>
                  ) : (
                    <ResponsiveContainer width="100%" height={320}>
                      <BarChart data={yearChart}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="income" fill="#16a34a" name="Income" />
                        <Bar dataKey="expense" fill="#dc2626" name="Expense" />
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} lg={4}>
              <Card
                elevation={0}
                sx={{
                  border: "1px solid",
                  borderColor: "divider",
                  minHeight: 430,
                }}
              >
                <CardContent>
                  <Typography variant="h6" fontWeight={900}>
                    Expense Distribution
                  </Typography>

                  <Typography color="text.secondary" mb={2}>
                    Category-wise expense breakdown.
                  </Typography>

                  {expenseDistribution.length === 0 ? (
                    <Box
                      sx={{
                        height: 320,
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
                      <Typography color="text.secondary">
                        Add expenses to see pie chart distribution.
                      </Typography>
                    </Box>
                  ) : (
                    <ResponsiveContainer width="100%" height={320}>
                      <PieChart>
                        <Pie
                          data={expenseDistribution}
                          dataKey="amount"
                          nameKey="category"
                          outerRadius={105}
                          label
                        >
                          {expenseDistribution.map((entry, index) => (
                            <Cell
                              key={entry.category}
                              fill={COLORS[index % COLORS.length]}
                            />
                          ))}
                        </Pie>
                        <Tooltip />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Grid container spacing={3} mb={3}>
            <Grid item xs={12} md={4}>
              <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
                <CardContent>
                  <Stack direction="row" alignItems="center" spacing={1} mb={2}>
                    <HealthAndSafetyIcon color={getHealthColor(healthScore)} />
                    <Typography variant="h6" fontWeight={900}>
                      Financial Health Score
                    </Typography>
                  </Stack>

                  <Typography variant="h3" fontWeight={900}>
                    {healthScore}
                  </Typography>

                  <Chip
                    label={getHealthLabel(healthScore)}
                    color={getHealthColor(healthScore)}
                    sx={{ mt: 1, fontWeight: 800 }}
                  />

                  <LinearProgress
                    variant="determinate"
                    value={Math.min(healthScore, 100)}
                    color={getHealthColor(healthScore)}
                    sx={{ height: 12, borderRadius: 10, mt: 3 }}
                  />

                  <Typography color="text.secondary" mt={2}>
                    Score is based on income, spending, budget usage and savings
                    activity.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
                <CardContent>
                  <Stack direction="row" alignItems="center" spacing={1} mb={2}>
                    <InsightsIcon color="primary" />
                    <Typography variant="h6" fontWeight={900}>
                      Budget Utilization
                    </Typography>
                  </Stack>

                  <Typography variant="h3" fontWeight={900}>
                    {budgetUtilization.toFixed(1)}%
                  </Typography>

                  <LinearProgress
                    variant="determinate"
                    value={Math.min(budgetUtilization, 100)}
                    color={
                      budgetUtilization >= 90
                        ? "error"
                        : budgetUtilization >= 70
                        ? "warning"
                        : "success"
                    }
                    sx={{ height: 12, borderRadius: 10, mt: 3 }}
                  />

                  <Stack spacing={1.2} mt={3}>
                    <Stack direction="row" justifyContent="space-between">
                      <Typography color="text.secondary">Budget</Typography>
                      <Typography fontWeight={900}>
                        {formatCurrency(totalBudget)}
                      </Typography>
                    </Stack>

                    <Stack direction="row" justifyContent="space-between">
                      <Typography color="text.secondary">Expense</Typography>
                      <Typography fontWeight={900} color="error.main">
                        {formatCurrency(totalExpense)}
                      </Typography>
                    </Stack>

                    <Stack direction="row" justifyContent="space-between">
                      <Typography color="text.secondary">Remaining</Typography>
                      <Typography
                        fontWeight={900}
                        color={remainingBudget < 0 ? "error.main" : "success.main"}
                      >
                        {formatCurrency(remainingBudget)}
                      </Typography>
                    </Stack>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
                <CardContent>
                  <Stack direction="row" alignItems="center" spacing={1} mb={2}>
                    <SavingsIcon color="success" />
                    <Typography variant="h6" fontWeight={900}>
                      Savings Performance
                    </Typography>
                  </Stack>

                  <Typography variant="h3" fontWeight={900}>
                    {savingsProgress.toFixed(1)}%
                  </Typography>

                  <LinearProgress
                    variant="determinate"
                    value={Math.min(savingsProgress, 100)}
                    color="success"
                    sx={{ height: 12, borderRadius: 10, mt: 3 }}
                  />

                  <Stack spacing={1.2} mt={3}>
                    <Stack direction="row" justifyContent="space-between">
                      <Typography color="text.secondary">Target</Typography>
                      <Typography fontWeight={900}>
                        {formatCurrency(savingsTarget)}
                      </Typography>
                    </Stack>

                    <Stack direction="row" justifyContent="space-between">
                      <Typography color="text.secondary">Saved</Typography>
                      <Typography fontWeight={900} color="success.main">
                        {formatCurrency(currentSavings)}
                      </Typography>
                    </Stack>

                    <Stack direction="row" justifyContent="space-between">
                      <Typography color="text.secondary">Savings Ratio</Typography>
                      <Typography fontWeight={900}>{savingsRatio}%</Typography>
                    </Stack>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Grid container spacing={3}>
            <Grid item xs={12} lg={6}>
              <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
                <CardContent>
                  <Typography variant="h6" fontWeight={900} mb={2}>
                    Category Budget Summary
                  </Typography>

                  {budgetCategorySummary.length === 0 ? (
                    <Typography color="text.secondary">
                      Add budgets and expenses to view category-level budget
                      usage.
                    </Typography>
                  ) : (
                    <Stack spacing={2}>
                      {budgetCategorySummary.map((item) => {
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
                                {formatCurrency(item.expense)} /{" "}
                                {formatCurrency(item.budget)}
                              </Typography>
                            </Stack>

                            <LinearProgress
                              variant="determinate"
                              value={Math.min(used, 100)}
                              color={
                                used >= 90
                                  ? "error"
                                  : used >= 70
                                  ? "warning"
                                  : "success"
                              }
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
            </Grid>

            <Grid item xs={12} lg={6}>
              <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
                <CardContent>
                  <Stack direction="row" spacing={1} alignItems="center" mb={2}>
                    <WarningAmberIcon color="warning" />
                    <Typography variant="h6" fontWeight={900}>
                      Smart Trend Analysis
                    </Typography>
                  </Stack>

                  {!trend ? (
                    <Typography color="text.secondary">
                      Trend data will appear after income and expense records are
                      available.
                    </Typography>
                  ) : (
                    <Stack spacing={2}>
                      <Box>
                        <Typography color="text.secondary">Income Trend</Typography>
                        <Chip
                          label={`${trend.income_trend || "STABLE"} (${
                            trend.income_change_percent || 0
                          }%)`}
                          color={
                            trend.income_trend === "INCREASING"
                              ? "success"
                              : trend.income_trend === "DECREASING"
                              ? "warning"
                              : "default"
                          }
                          sx={{ fontWeight: 800, mt: 0.5 }}
                        />
                      </Box>

                      <Box>
                        <Typography color="text.secondary">Expense Trend</Typography>
                        <Chip
                          label={`${trend.expense_trend || "STABLE"} (${
                            trend.expense_change_percent || 0
                          }%)`}
                          color={
                            trend.expense_trend === "INCREASING"
                              ? "error"
                              : trend.expense_trend === "DECREASING"
                              ? "success"
                              : "default"
                          }
                          sx={{ fontWeight: 800, mt: 0.5 }}
                        />
                      </Box>

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
