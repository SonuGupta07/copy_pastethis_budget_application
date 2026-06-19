import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getAllBudgets,
  getAllCategories,
  getAllExpenses,
  getAllIncome,
  getAllRecurringTransactions,
  getAllSavingsGoals,
  getAnalyticsDateRange,
  getAnalyticsExpensePie,
  getAnalyticsMonthlyBar,
  getAnalyticsTrend,
  getAnalyticsYearlyBar,
} from "../api/analyticsPageApi";
import { getUserIdFromToken } from "../utils/jwt";

const monthLabels = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
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

const isWithinDateRange = (dateValue, startDate, endDate) => {
  if (!dateValue) return false;

  const recordDate = new Date(dateValue);
  recordDate.setHours(0, 0, 0, 0);

  if (startDate) {
    const start = new Date(startDate);
    start.setHours(0, 0, 0, 0);

    if (recordDate < start) return false;
  }

  if (endDate) {
    const end = new Date(endDate);
    end.setHours(0, 0, 0, 0);

    if (recordDate > end) return false;
  }

  return true;
};

const buildCategoryMap = (categories) => {
  const map = {};

  categories.forEach((category) => {
    map[Number(category.category_id)] = category.category_name;
  });

  return map;
};

const groupByCategory = (records, categoryMap) => {
  const grouped = {};

  records.forEach((record) => {
    const categoryName =
      categoryMap[Number(record.category_id)] || "Unknown Category";

    grouped[categoryName] =
      (grouped[categoryName] || 0) + Number(record.amount || 0);
  });

  return Object.entries(grouped)
    .map(([category, amount]) => ({
      category,
      amount,
    }))
    .sort((a, b) => b.amount - a.amount);
};

const formatAmountForInsight = (value) => {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(Number(value || 0));
};

const useAnalyticsPage = () => {
  const userId = useMemo(() => getUserIdFromToken(), []);

  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState("ALL");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const [categories, setCategories] = useState([]);
  const [incomeList, setIncomeList] = useState([]);
  const [expenseList, setExpenseList] = useState([]);
  const [budgetList, setBudgetList] = useState([]);
  const [savingsGoals, setSavingsGoals] = useState([]);
  const [recurringList, setRecurringList] = useState([]);

  const [backendExpensePie, setBackendExpensePie] = useState([]);
  const [backendMonthlyBar, setBackendMonthlyBar] = useState(null);
  const [backendYearlyBar, setBackendYearlyBar] = useState([]);
  const [backendDateRangeSummary, setBackendDateRangeSummary] = useState(null);
  const [backendTrend, setBackendTrend] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchAnalytics = useCallback(async () => {
    if (!userId) {
      setError("User ID not found in token. Please login again.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const selectedMonthForBackend =
        month === "ALL" ? new Date().getMonth() + 1 : Number(month);

      const safeStartDate = startDate || `${year}-01-01`;
      const safeEndDate = endDate || `${year}-12-31`;

      const results = await Promise.allSettled([
        getAllCategories(),
        getAllIncome(),
        getAllExpenses(),
        getAllBudgets(),
        getAllSavingsGoals(),
        getAllRecurringTransactions(),

        getAnalyticsExpensePie(userId),
        getAnalyticsMonthlyBar(userId, selectedMonthForBackend, year),
        getAnalyticsYearlyBar(userId, year),
        getAnalyticsDateRange(userId, safeStartDate, safeEndDate),
        getAnalyticsTrend(userId),
      ]);

      const allCategories =
        results[0].status === "fulfilled"
          ? normalizeArray(results[0].value)
          : [];

      const allIncome =
        results[1].status === "fulfilled"
          ? normalizeArray(results[1].value)
          : [];

      const allExpenses =
        results[2].status === "fulfilled"
          ? normalizeArray(results[2].value)
          : [];

      const allBudgets =
        results[3].status === "fulfilled"
          ? normalizeArray(results[3].value)
          : [];

      const allSavings =
        results[4].status === "fulfilled"
          ? normalizeArray(results[4].value)
          : [];

      const allRecurring =
        results[5].status === "fulfilled"
          ? normalizeArray(results[5].value)
          : [];

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

      setBackendExpensePie(
        results[6].status === "fulfilled"
          ? normalizeArray(results[6].value)
          : []
      );

      setBackendMonthlyBar(
        results[7].status === "fulfilled" ? results[7].value : null
      );

      setBackendYearlyBar(
        results[8].status === "fulfilled"
          ? normalizeArray(results[8].value)
          : []
      );

      setBackendDateRangeSummary(
        results[9].status === "fulfilled" ? results[9].value : null
      );

      setBackendTrend(
        results[10].status === "fulfilled" ? results[10].value : null
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          "Failed to load analytics data"
      );
    } finally {
      setLoading(false);
    }
  }, [userId, year, month, startDate, endDate]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  const resetFilters = () => {
    setYear(new Date().getFullYear());
    setMonth("ALL");
    setStartDate("");
    setEndDate("");
  };

  const categoryMap = useMemo(() => {
    return buildCategoryMap(categories);
  }, [categories]);

  const filterTransactionsByPeriod = useCallback(
    (records, dateKey) => {
      return records.filter((record) => {
        const recordDate = record[dateKey];

        if (!recordDate) return false;

        const matchesYear = Number(getYear(recordDate)) === Number(year);

        const matchesMonth =
          month === "ALL" || Number(getMonth(recordDate)) === Number(month);

        const matchesDateRange = isWithinDateRange(
          recordDate,
          startDate,
          endDate
        );

        return matchesYear && matchesMonth && matchesDateRange;
      });
    },
    [year, month, startDate, endDate]
  );

  const periodIncome = useMemo(() => {
    return filterTransactionsByPeriod(incomeList, "income_date");
  }, [incomeList, filterTransactionsByPeriod]);

  const periodExpenses = useMemo(() => {
    return filterTransactionsByPeriod(expenseList, "expense_date");
  }, [expenseList, filterTransactionsByPeriod]);

  const periodBudgets = useMemo(() => {
    return budgetList.filter((budget) => {
      const matchesYear = Number(budget.year) === Number(year);

      const matchesMonth =
        month === "ALL" || Number(budget.month) === Number(month);

      if (!matchesYear || !matchesMonth) return false;

      if (!startDate && !endDate) return true;

      const budgetDate = `${budget.year}-${String(budget.month).padStart(
        2,
        "0"
      )}-01`;

      return isWithinDateRange(budgetDate, startDate, endDate);
    });
  }, [budgetList, year, month, startDate, endDate]);

  const periodSavingsGoals = useMemo(() => {
    return savingsGoals.filter((goal) => {
      if (!goal.target_date) return false;

      const matchesYear = Number(getYear(goal.target_date)) === Number(year);

      const matchesMonth =
        month === "ALL" || Number(getMonth(goal.target_date)) === Number(month);

      const matchesDateRange = isWithinDateRange(
        goal.target_date,
        startDate,
        endDate
      );

      return matchesYear && matchesMonth && matchesDateRange;
    });
  }, [savingsGoals, year, month, startDate, endDate]);

  const periodRecurring = useMemo(() => {
    return recurringList.filter((item) => {
      if (!item.next_run_date) return false;

      const matchesYear = Number(getYear(item.next_run_date)) === Number(year);

      const matchesMonth =
        month === "ALL" ||
        Number(getMonth(item.next_run_date)) === Number(month);

      const matchesDateRange = isWithinDateRange(
        item.next_run_date,
        startDate,
        endDate
      );

      return matchesYear && matchesMonth && matchesDateRange;
    });
  }, [recurringList, year, month, startDate, endDate]);

  const monthlyCashFlow = useMemo(() => {
    return monthLabels.map((monthName, index) => {
      const monthNumber = index + 1;

      const income = incomeList
        .filter(
          (item) =>
            Number(getYear(item.income_date)) === Number(year) &&
            Number(getMonth(item.income_date)) === Number(monthNumber)
        )
        .reduce((sum, item) => sum + Number(item.amount || 0), 0);

      const expense = expenseList
        .filter(
          (item) =>
            Number(getYear(item.expense_date)) === Number(year) &&
            Number(getMonth(item.expense_date)) === Number(monthNumber)
        )
        .reduce((sum, item) => sum + Number(item.amount || 0), 0);

      return {
        month: monthName,
        income,
        expense,
        balance: income - expense,
      };
    });
  }, [incomeList, expenseList, year]);

  const incomeDistribution = useMemo(() => {
    return groupByCategory(periodIncome, categoryMap);
  }, [periodIncome, categoryMap]);

  const expenseDistribution = useMemo(() => {
    return groupByCategory(periodExpenses, categoryMap);
  }, [periodExpenses, categoryMap]);

  const incomeRanking = useMemo(() => {
    return incomeDistribution.slice(0, 8);
  }, [incomeDistribution]);

  const expenseRanking = useMemo(() => {
    return expenseDistribution.slice(0, 8);
  }, [expenseDistribution]);

  const budgetVsActual = useMemo(() => {
    return periodBudgets.map((budget) => {
      const expense = periodExpenses
        .filter((item) => {
          const sameCategory =
            Number(item.category_id) === Number(budget.category_id);

          const sameMonth =
            Number(getMonth(item.expense_date)) === Number(budget.month);

          const sameYear =
            Number(getYear(item.expense_date)) === Number(budget.year);

          return sameCategory && sameMonth && sameYear;
        })
        .reduce((sum, item) => sum + Number(item.amount || 0), 0);

      const budgetAmount = Number(budget.budget_amount || 0);

      return {
        category: categoryMap[Number(budget.category_id)] || "Unknown",
        month: budget.month,
        year: budget.year,
        budget: budgetAmount,
        expense,
        remaining: budgetAmount - expense,
        utilization:
          budgetAmount > 0
            ? Number(((expense / budgetAmount) * 100).toFixed(2))
            : 0,
      };
    });
  }, [periodBudgets, periodExpenses, categoryMap]);

  const savingsProgress = useMemo(() => {
    return periodSavingsGoals.map((goal) => {
      const target = Number(goal.target_amount || 0);
      const current = Number(goal.current_amount || 0);

      return {
        goal: goal.goal_name,
        target,
        current,
        remaining: Math.max(target - current, 0),
        progress: target > 0 ? Number(((current / target) * 100).toFixed(2)) : 0,
        status: goal.status,
        target_date: goal.target_date,
      };
    });
  }, [periodSavingsGoals]);

  const recurringSummary = useMemo(() => {
    return periodRecurring.map((item) => ({
      ...item,
      category: categoryMap[Number(item.category_id)] || "Unknown",
    }));
  }, [periodRecurring, categoryMap]);

  const recentTransactions = useMemo(() => {
    const incomeTransactions = periodIncome.map((item) => ({
      id: `income-${item.income_id}`,
      type: "INCOME",
      category: categoryMap[Number(item.category_id)] || "Income",
      description: item.description,
      amount: Number(item.amount || 0),
      date: item.income_date,
    }));

    const expenseTransactions = periodExpenses.map((item) => ({
      id: `expense-${item.expense_id}`,
      type: "EXPENSE",
      category: categoryMap[Number(item.category_id)] || "Expense",
      description: item.description,
      amount: Number(item.amount || 0),
      date: item.expense_date,
    }));

    return [...incomeTransactions, ...expenseTransactions]
      .sort((a, b) => new Date(b.date) - new Date(a.date))
      .slice(0, 10);
  }, [periodIncome, periodExpenses, categoryMap]);

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

    const savingsTarget = periodSavingsGoals.reduce(
      (sum, item) => sum + Number(item.target_amount || 0),
      0
    );

    const currentSavings = periodSavingsGoals.reduce(
      (sum, item) => sum + Number(item.current_amount || 0),
      0
    );

    return {
      totalIncome,
      totalExpense,
      netBalance: totalIncome - totalExpense,
      totalBudget,
      remainingBudget: totalBudget - totalExpense,
      budgetUtilization:
        totalBudget > 0
          ? Number(((totalExpense / totalBudget) * 100).toFixed(2))
          : 0,
      savingsTarget,
      currentSavings,
      savingsProgress:
        savingsTarget > 0
          ? Number(((currentSavings / savingsTarget) * 100).toFixed(2))
          : 0,
      expenseRatio:
        totalIncome > 0
          ? Number(((totalExpense / totalIncome) * 100).toFixed(2))
          : 0,
    };
  }, [periodIncome, periodExpenses, periodBudgets, periodSavingsGoals]);

  const bestWorstMonths = useMemo(() => {
    const sorted = [...monthlyCashFlow].sort((a, b) => b.balance - a.balance);

    return {
      bestMonth: sorted[0] || null,
      worstMonth: sorted[sorted.length - 1] || null,
    };
  }, [monthlyCashFlow]);

  const smartInsights = useMemo(() => {
    const insights = [];

    if (totals.totalIncome === 0) {
      insights.push("No income found for the selected filter.");
    }

    if (totals.totalExpense === 0) {
      insights.push("No expenses found for the selected filter.");
    }

    if (totals.totalIncome > 0) {
      if (totals.expenseRatio > 80) {
        insights.push(
          "Expenses are above 80% of income. Spending control is strongly recommended."
        );
      } else if (totals.expenseRatio > 50) {
        insights.push(
          "Expenses are moderate. Monitor top spending categories carefully."
        );
      } else {
        insights.push(
          "Expense-to-income ratio looks healthy for the selected period."
        );
      }
    }

    if (expenseRanking.length > 0) {
      insights.push(
        `Highest spending category is ${
          expenseRanking[0].category
        } with ${formatAmountForInsight(expenseRanking[0].amount)}.`
      );
    }

    if (incomeRanking.length > 0) {
      insights.push(
        `Top income source is ${
          incomeRanking[0].category
        } with ${formatAmountForInsight(incomeRanking[0].amount)}.`
      );
    }

    const overBudget = budgetVsActual.filter((item) => item.utilization > 100);

    if (overBudget.length > 0) {
      insights.push(
        `${overBudget.length} budget category/categories exceeded the planned amount.`
      );
    }

    if (totals.savingsProgress >= 100) {
      insights.push("Savings goals are fully achieved for the selected filter.");
    } else if (totals.savingsProgress > 0) {
      insights.push(
        `Savings progress is ${totals.savingsProgress}% for selected goals.`
      );
    }

    if (recurringSummary.length > 0) {
      insights.push(
        `${recurringSummary.length} recurring transaction(s) found for the selected filter.`
      );
    }

    return insights;
  }, [
    totals,
    expenseRanking,
    incomeRanking,
    budgetVsActual,
    recurringSummary,
  ]);

  return {
    filters: {
      year,
      setYear,
      month,
      setMonth,
      startDate,
      setStartDate,
      endDate,
      setEndDate,
      resetFilters,
    },
    loading,
    error,
    fetchAnalytics,

    totals,
    monthlyCashFlow,
    incomeDistribution,
    expenseDistribution,
    incomeRanking,
    expenseRanking,
    budgetVsActual,
    savingsProgress,
    recurringSummary,
    recentTransactions,
    bestWorstMonths,
    smartInsights,

    backendExpensePie,
    backendMonthlyBar,
    backendYearlyBar,
    backendDateRangeSummary,
    backendTrend,
  };
};

export default useAnalyticsPage;