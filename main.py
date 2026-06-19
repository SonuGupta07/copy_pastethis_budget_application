import api from "./axios";

export const categorizeExpense = async (data) => {
  const response = await api.post("/ai/categorize-expense", data);
  return response.data;
};

export const getBudgetAdvisor = async (userId) => {
  const response = await api.post("/ai/budget-advisor", {
    user_id: Number(userId),
  });

  return response.data;
};

export const getSpendingInsights = async (userId) => {
  const response = await api.get(`/ai/spending-insights/${userId}`);
  return response.data;
};

export const getSavingsRecommendation = async (userId) => {
  const response = await api.get(`/ai/savings-recommendation/${userId}`);
  return response.data;
};

export const askFinancialChatbot = async (userId, question) => {
  const response = await api.post("/ai/financial-chatbot", {
    user_id: Number(userId),
    question,
  });

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
------------------------------------
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  askFinancialChatbot,
  categorizeExpense,
  getAllBudgets,
  getAllCategories,
  getAllExpenses,
  getAllIncome,
  getAllRecurringTransactions,
  getAllSavingsGoals,
  getBudgetAdvisor,
  getSavingsRecommendation,
  getSpendingInsights,
} from "../api/aiAssistantApi";
import { getUserIdFromToken } from "../utils/jwt";

const normalizeArray = (data) => {
  if (Array.isArray(data)) return data;
  if (!data) return [];
  return [data];
};

const buildCategoryMap = (categories) => {
  const map = {};

  categories.forEach((category) => {
    map[Number(category.category_id)] = category.category_name;
  });

  return map;
};

const getDaysRemaining = (dateValue) => {
  if (!dateValue) return null;

  const today = new Date();
  const target = new Date(dateValue);

  today.setHours(0, 0, 0, 0);
  target.setHours(0, 0, 0, 0);

  return Math.ceil((target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
};

const detectAnomalies = ({ expenses, categoryMap }) => {
  const anomalies = [];

  const expenseAmounts = expenses.map((expense) => Number(expense.amount || 0));

  const averageExpense =
    expenseAmounts.length > 0
      ? expenseAmounts.reduce((sum, amount) => sum + amount, 0) /
        expenseAmounts.length
      : 0;

  expenses.forEach((expense) => {
    const amount = Number(expense.amount || 0);

    if (averageExpense > 0 && amount >= averageExpense * 2) {
      anomalies.push({
        title: "Unusual High Expense",
        message: `${expense.description || "Expense"} is much higher than your average expense.`,
        amount,
        category:
          categoryMap[Number(expense.category_id)] || "Unknown Category",
        date: expense.expense_date,
      });
    }
  });

  return anomalies.slice(0, 5);
};

const useAiAssistant = () => {
  const userId = useMemo(() => getUserIdFromToken(), []);

  const [categories, setCategories] = useState([]);
  const [incomeList, setIncomeList] = useState([]);
  const [expenseList, setExpenseList] = useState([]);
  const [budgetList, setBudgetList] = useState([]);
  const [savingsGoals, setSavingsGoals] = useState([]);
  const [recurringList, setRecurringList] = useState([]);

  const [spendingInsights, setSpendingInsights] = useState(null);
  const [savingsRecommendation, setSavingsRecommendation] = useState(null);
  const [budgetAdvisor, setBudgetAdvisor] = useState(null);
  const [expensePrediction, setExpensePrediction] = useState(null);

  const [chatMessages, setChatMessages] = useState([
    {
      role: "assistant",
      text: "Hi! I can help you understand your spending, budgets, savings goals and financial health. Ask me anything about your finances.",
    },
  ]);

  const [loading, setLoading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);
  const [categorizing, setCategorizing] = useState(false);
  const [error, setError] = useState("");

  const fetchAiData = useCallback(async () => {
    if (!userId) {
      setError("User ID not found in token. Please login again.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const results = await Promise.allSettled([
        getAllCategories(),
        getAllIncome(),
        getAllExpenses(),
        getAllBudgets(),
        getAllSavingsGoals(),
        getAllRecurringTransactions(),
        getSpendingInsights(userId),
        getSavingsRecommendation(userId),
      ]);

      const allCategories =
        results[0].status === "fulfilled" ? normalizeArray(results[0].value) : [];

      const allIncome =
        results[1].status === "fulfilled" ? normalizeArray(results[1].value) : [];

      const allExpenses =
        results[2].status === "fulfilled" ? normalizeArray(results[2].value) : [];

      const allBudgets =
        results[3].status === "fulfilled" ? normalizeArray(results[3].value) : [];

      const allSavings =
        results[4].status === "fulfilled" ? normalizeArray(results[4].value) : [];

      const allRecurring =
        results[5].status === "fulfilled" ? normalizeArray(results[5].value) : [];

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

      if (results[6].status === "fulfilled") {
        setSpendingInsights(results[6].value);
      }

      if (results[7].status === "fulfilled") {
        setSavingsRecommendation(results[7].value);
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          "Failed to load AI assistant data"
      );
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchAiData();
  }, [fetchAiData]);

  const categoryMap = useMemo(() => {
    return buildCategoryMap(categories);
  }, [categories]);

  const financialSummary = useMemo(() => {
    const totalIncome = incomeList.reduce(
      (sum, item) => sum + Number(item.amount || 0),
      0
    );

    const totalExpense = expenseList.reduce(
      (sum, item) => sum + Number(item.amount || 0),
      0
    );

    const totalBudget = budgetList.reduce(
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

    const expenseRatio =
      totalIncome > 0 ? Number(((totalExpense / totalIncome) * 100).toFixed(2)) : 0;

    const savingsProgress =
      savingsTarget > 0
        ? Number(((currentSavings / savingsTarget) * 100).toFixed(2))
        : 0;

    const budgetUsage =
      totalBudget > 0
        ? Number(((totalExpense / totalBudget) * 100).toFixed(2))
        : 0;

    return {
      totalIncome,
      totalExpense,
      netBalance: totalIncome - totalExpense,
      totalBudget,
      savingsTarget,
      currentSavings,
      expenseRatio,
      savingsProgress,
      budgetUsage,
    };
  }, [incomeList, expenseList, budgetList, savingsGoals]);

  const recentExpenses = useMemo(() => {
    return [...expenseList]
      .sort((a, b) => new Date(b.expense_date) - new Date(a.expense_date))
      .slice(0, 8)
      .map((expense) => ({
        ...expense,
        category_name:
          categoryMap[Number(expense.category_id)] || "Unknown Category",
      }));
  }, [expenseList, categoryMap]);

  const anomalies = useMemo(() => {
    return detectAnomalies({
      expenses: expenseList,
      categoryMap,
    });
  }, [expenseList, categoryMap]);

  const upcomingRecurring = useMemo(() => {
    return recurringList
      .map((item) => ({
        ...item,
        category_name: categoryMap[Number(item.category_id)] || "Unknown",
        days_remaining: getDaysRemaining(item.next_run_date),
      }))
      .filter((item) => item.days_remaining !== null && item.days_remaining >= 0)
      .sort((a, b) => a.days_remaining - b.days_remaining)
      .slice(0, 5);
  }, [recurringList, categoryMap]);

  const generateBudgetAdvisor = async () => {
    if (!userId) return;

    setAiLoading(true);
    setError("");

    try {
      const data = await getBudgetAdvisor(userId);
      setBudgetAdvisor(data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          "Failed to generate budget advisor"
      );
    } finally {
      setAiLoading(false);
    }
  };

  const askQuestion = async (question) => {
    if (!question.trim()) return;

    setChatMessages((previous) => [
      ...previous,
      {
        role: "user",
        text: question,
      },
    ]);

    setChatLoading(true);
    setError("");

    try {
      const data = await askFinancialChatbot(userId, question);

      setChatMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          text: data.answer || data.response || "I could not generate an answer.",
        },
      ]);
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        "AI assistant could not answer right now.";

      setChatMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          text: message,
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const runExpenseCategorization = async (expense) => {
    setCategorizing(true);
    setError("");

    try {
      const data = await categorizeExpense({
        expense_id: Number(expense.expense_id),
        description: expense.description || "",
      });

      setExpensePrediction(data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          "Failed to categorize expense"
      );
    } finally {
      setCategorizing(false);
    }
  };

  return {
    userId,
    loading,
    aiLoading,
    chatLoading,
    categorizing,
    error,
    fetchAiData,
    financialSummary,
    spendingInsights,
    savingsRecommendation,
    budgetAdvisor,
    expensePrediction,
    recentExpenses,
    anomalies,
    upcomingRecurring,
    chatMessages,
    askQuestion,
    generateBudgetAdvisor,
    runExpenseCategorization,
  };
};

export default useAiAssistant;
------------------------------------------
import { useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Grid,
  IconButton,
  InputAdornment,
  Stack,
  TextField,
  Typography,
} from "@mui/material";

import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import SendIcon from "@mui/icons-material/Send";
import RefreshIcon from "@mui/icons-material/Refresh";
import PsychologyIcon from "@mui/icons-material/Psychology";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import ReceiptLongIcon from "@mui/icons-material/ReceiptLong";
import SavingsIcon from "@mui/icons-material/Savings";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import CategoryIcon from "@mui/icons-material/Category";
import RepeatIcon from "@mui/icons-material/Repeat";

import PageHeader from "../../components/common/PageHeader";
import useAiAssistant from "../../hooks/useAiAssistant";

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

const SummaryCard = ({ title, value, subtitle, icon, color }) => {
  return (
    <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
      <CardContent>
        <Stack direction="row" spacing={2} justifyContent="space-between">
          <Box>
            <Typography color="text.secondary" fontWeight={800}>
              {title}
            </Typography>

            <Typography variant="h5" fontWeight={900} mt={1}>
              {value}
            </Typography>

            <Typography variant="body2" color="text.secondary" mt={0.5}>
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

const AiAssistantPage = () => {
  const {
    loading,
    aiLoading,
    chatLoading,
    categorizing,
    error,
    fetchAiData,
    financialSummary,
    spendingInsights,
    savingsRecommendation,
    budgetAdvisor,
    expensePrediction,
    recentExpenses,
    anomalies,
    upcomingRecurring,
    chatMessages,
    askQuestion,
    generateBudgetAdvisor,
    runExpenseCategorization,
  } = useAiAssistant();

  const [question, setQuestion] = useState("");

  const quickPrompts = [
    "How is my spending this month?",
    "Where am I spending the most?",
    "How can I improve my savings?",
    "Am I overspending compared to my income?",
    "Give me practical budget advice.",
  ];

  const handleSend = async () => {
    if (!question.trim()) return;

    const currentQuestion = question;
    setQuestion("");
    await askQuestion(currentQuestion);
  };

  return (
    <Box>
      <PageHeader
        title="AI Financial Assistant"
        subtitle="GenAI-powered budget advisor, spending insights, savings recommendations and financial chatbot."
        breadcrumbs={["Insights", "AI Assistant"]}
      />

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box display="flex" justifyContent="center" py={10}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          <Stack direction="row" justifyContent="flex-end" mb={3}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={fetchAiData}
            >
              Refresh AI Context
            </Button>
          </Stack>

          <Grid container spacing={2.5} mb={3}>
            <Grid item xs={12} sm={6} lg={3}>
              <SummaryCard
                title="Income"
                value={formatCurrency(financialSummary.totalIncome)}
                subtitle="User-specific total income"
                icon={<TrendingUpIcon />}
                color="linear-gradient(135deg, #16a34a, #22c55e)"
              />
            </Grid>

            <Grid item xs={12} sm={6} lg={3}>
              <SummaryCard
                title="Expense"
                value={formatCurrency(financialSummary.totalExpense)}
                subtitle={`${financialSummary.expenseRatio}% of income`}
                icon={<ReceiptLongIcon />}
                color="linear-gradient(135deg, #dc2626, #ef4444)"
              />
            </Grid>

            <Grid item xs={12} sm={6} lg={3}>
              <SummaryCard
                title="Savings"
                value={`${financialSummary.savingsProgress}%`}
                subtitle={`${formatCurrency(financialSummary.currentSavings)} saved`}
                icon={<SavingsIcon />}
                color="linear-gradient(135deg, #059669, #10b981)"
              />
            </Grid>

            <Grid item xs={12} sm={6} lg={3}>
              <SummaryCard
                title="Budget Usage"
                value={`${financialSummary.budgetUsage}%`}
                subtitle={`${formatCurrency(financialSummary.totalBudget)} planned`}
                icon={<PsychologyIcon />}
                color="linear-gradient(135deg, #2563eb, #7c3aed)"
              />
            </Grid>
          </Grid>

          <Grid container spacing={3}>
            <Grid item xs={12} lg={7}>
              <Card
                elevation={0}
                sx={{ border: "1px solid", borderColor: "divider", height: "100%" }}
              >
                <CardContent>
                  <Stack direction="row" spacing={1} alignItems="center" mb={2}>
                    <AutoAwesomeIcon color="primary" />
                    <Typography variant="h6" fontWeight={900}>
                      Financial Chatbot
                    </Typography>
                  </Stack>

                  <Box
                    sx={{
                      height: 420,
                      overflowY: "auto",
                      border: "1px solid",
                      borderColor: "divider",
                      borderRadius: 3,
                      p: 2,
                      mb: 2,
                      backgroundColor: "background.default",
                    }}
                  >
                    <Stack spacing={2}>
                      {chatMessages.map((message, index) => (
                        <Box
                          key={`${message.role}-${index}`}
                          sx={{
                            display: "flex",
                            justifyContent:
                              message.role === "user" ? "flex-end" : "flex-start",
                          }}
                        >
                          <Box
                            sx={{
                              maxWidth: "80%",
                              p: 1.6,
                              borderRadius: 3,
                              backgroundColor:
                                message.role === "user"
                                  ? "primary.main"
                                  : "action.hover",
                              color:
                                message.role === "user"
                                  ? "primary.contrastText"
                                  : "text.primary",
                            }}
                          >
                            <Typography variant="body2" whiteSpace="pre-line">
                              {message.text}
                            </Typography>
                          </Box>
                        </Box>
                      ))}

                      {chatLoading && (
                        <Typography color="text.secondary">
                          AI is thinking...
                        </Typography>
                      )}
                    </Stack>
                  </Box>

                  <Stack direction="row" spacing={1} flexWrap="wrap" mb={2}>
                    {quickPrompts.map((prompt) => (
                      <Chip
                        key={prompt}
                        label={prompt}
                        clickable
                        color="primary"
                        variant="outlined"
                        onClick={() => setQuestion(prompt)}
                        sx={{ mb: 1 }}
                      />
                    ))}
                  </Stack>

                  <TextField
                    fullWidth
                    placeholder="Ask about your spending, budget, savings or financial health..."
                    value={question}
                    onChange={(event) => setQuestion(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter") {
                        event.preventDefault();
                        handleSend();
                      }
                    }}
                    InputProps={{
                      endAdornment: (
                        <InputAdornment position="end">
                          <IconButton
                            color="primary"
                            disabled={chatLoading || !question.trim()}
                            onClick={handleSend}
                          >
                            <SendIcon />
                          </IconButton>
                        </InputAdornment>
                      ),
                    }}
                  />
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} lg={5}>
              <Stack spacing={3}>
                <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
                  <CardContent>
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                      <Box>
                        <Typography variant="h6" fontWeight={900}>
                          AI Budget Advisor
                        </Typography>
                        <Typography color="text.secondary">
                          Generate personalized budget recommendations.
                        </Typography>
                      </Box>

                      <Button
                        variant="contained"
                        disabled={aiLoading}
                        onClick={generateBudgetAdvisor}
                      >
                        {aiLoading ? "Generating..." : "Generate"}
                      </Button>
                    </Stack>

                    {budgetAdvisor && (
                      <Alert severity="info" sx={{ mt: 2, whiteSpace: "pre-line" }}>
                        {budgetAdvisor.recommendation}
                      </Alert>
                    )}
                  </CardContent>
                </Card>

                <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
                  <CardContent>
                    <Typography variant="h6" fontWeight={900} mb={2}>
                      AI Spending Insights
                    </Typography>

                    {!spendingInsights ? (
                      <Typography color="text.secondary">
                        Spending insights will appear after AI response loads.
                      </Typography>
                    ) : (
                      <Stack spacing={1.5}>
                        <Stack direction="row" justifyContent="space-between">
                          <Typography color="text.secondary">
                            Highest Category
                          </Typography>
                          <Typography fontWeight={900}>
                            {spendingInsights.highest_spending_category || "-"}
                          </Typography>
                        </Stack>

                        <Stack direction="row" justifyContent="space-between">
                          <Typography color="text.secondary">
                            Highest Amount
                          </Typography>
                          <Typography fontWeight={900} color="error.main">
                            {formatCurrency(
                              spendingInsights.highest_spending_amount
                            )}
                          </Typography>
                        </Stack>

                        <Stack direction="row" justifyContent="space-between">
                          <Typography color="text.secondary">
                            Savings Rate
                          </Typography>
                          <Typography fontWeight={900}>
                            {spendingInsights.savings_rate || 0}%
                          </Typography>
                        </Stack>

                        <Alert severity="info" sx={{ whiteSpace: "pre-line" }}>
                          {spendingInsights.insights}
                        </Alert>
                      </Stack>
                    )}
                  </CardContent>
                </Card>

                <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
                  <CardContent>
                    <Typography variant="h6" fontWeight={900} mb={2}>
                      AI Savings Recommendation
                    </Typography>

                    {!savingsRecommendation ? (
                      <Typography color="text.secondary">
                        No savings recommendation available.
                      </Typography>
                    ) : savingsRecommendation.message ? (
                      <Typography color="text.secondary">
                        {savingsRecommendation.message}
                      </Typography>
                    ) : (
                      <Stack spacing={1.5}>
                        <Typography fontWeight={900}>
                          {savingsRecommendation.goal_name}
                        </Typography>

                        <Typography color="text.secondary">
                          {formatCurrency(savingsRecommendation.current_amount)} saved of{" "}
                          {formatCurrency(savingsRecommendation.target_amount)}
                        </Typography>

                        <Alert severity="success" sx={{ whiteSpace: "pre-line" }}>
                          {savingsRecommendation.recommendation}
                        </Alert>
                      </Stack>
                    )}
                  </CardContent>
                </Card>
              </Stack>
            </Grid>

            <Grid item xs={12} lg={6}>
              <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
                <CardContent>
                  <Stack direction="row" spacing={1} alignItems="center" mb={2}>
                    <CategoryIcon color="primary" />
                    <Typography variant="h6" fontWeight={900}>
                      AI Expense Categorization
                    </Typography>
                  </Stack>

                  {recentExpenses.length === 0 ? (
                    <Typography color="text.secondary">
                      No expenses found for categorization.
                    </Typography>
                  ) : (
                    <Stack spacing={1.5}>
                      {recentExpenses.map((expense) => (
                        <Box
                          key={expense.expense_id}
                          sx={{
                            p: 1.5,
                            borderRadius: 3,
                            backgroundColor: "action.hover",
                          }}
                        >
                          <Stack direction="row" justifyContent="space-between" spacing={2}>
                            <Box>
                              <Typography fontWeight={900}>
                                {expense.description || "Expense"}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                {expense.category_name} • {formatDate(expense.expense_date)}
                              </Typography>
                            </Box>

                            <Stack alignItems="flex-end" spacing={1}>
                              <Typography fontWeight={900} color="error.main">
                                {formatCurrency(expense.amount)}
                              </Typography>

                              <Button
                                size="small"
                                variant="outlined"
                                disabled={categorizing}
                                onClick={() => runExpenseCategorization(expense)}
                              >
                                Predict
                              </Button>
                            </Stack>
                          </Stack>
                        </Box>
                      ))}
                    </Stack>
                  )}

                  {expensePrediction && (
                    <Alert severity="success" sx={{ mt: 2 }}>
                      Expense #{expensePrediction.expense_id} predicted as{" "}
                      <strong>{expensePrediction.category}</strong> with{" "}
                      {expensePrediction.confidence}% confidence.
                    </Alert>
                  )}
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} lg={6}>
              <Stack spacing={3}>
                <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
                  <CardContent>
                    <Stack direction="row" spacing={1} alignItems="center" mb={2}>
                      <WarningAmberIcon color="warning" />
                      <Typography variant="h6" fontWeight={900}>
                        AI Anomaly Detection
                      </Typography>
                    </Stack>

                    {anomalies.length === 0 ? (
                      <Typography color="text.secondary">
                        No unusual expenses detected.
                      </Typography>
                    ) : (
                      <Stack spacing={1.5}>
                        {anomalies.map((item) => (
                          <Alert
                            key={`${item.title}-${item.amount}-${item.date}`}
                            severity="warning"
                          >
                            <Typography fontWeight={900}>{item.title}</Typography>
                            <Typography variant="body2">
                              {item.message} Amount: {formatCurrency(item.amount)} •{" "}
                              Category: {item.category}
                            </Typography>
                          </Alert>
                        ))}
                      </Stack>
                    )}
                  </CardContent>
                </Card>

                <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
                  <CardContent>
                    <Stack direction="row" spacing={1} alignItems="center" mb={2}>
                      <RepeatIcon color="secondary" />
                      <Typography variant="h6" fontWeight={900}>
                        Upcoming Recurring Context
                      </Typography>
                    </Stack>

                    {upcomingRecurring.length === 0 ? (
                      <Typography color="text.secondary">
                        No upcoming recurring transactions.
                      </Typography>
                    ) : (
                      <Stack spacing={1.5}>
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
                                  {item.frequency} • {item.days_remaining} day(s) left
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
              </Stack>
            </Grid>
          </Grid>
        </>
      )}
    </Box>
  );
};

export default AiAssistantPage;
----------------------------------------------