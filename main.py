import api from "./axios";

export const createPaymentOrder = async (userId) => {
  const response = await api.post("/payments/create-order", {
    user_id: Number(userId),
    plan_code: "PREMIUM_MONTHLY",
  });

  return response.data;
};

export const verifyPayment = async (data) => {
  const response = await api.post("/payments/verify-payment", data);
  return response.data;
};

export const getPremiumStatus = async (userId) => {
  const response = await api.get(`/payments/status/${userId}`);
  return response.data;
};
-----------------------------
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  createPaymentOrder,
  getPremiumStatus,
  verifyPayment,
} from "../api/paymentApi";
import { getUserIdFromToken } from "../utils/jwt";

const loadRazorpayScript = () => {
  return new Promise((resolve) => {
    if (window.Razorpay) {
      resolve(true);
      return;
    }

    const script = document.createElement("script");
    script.src = "https://checkout.razorpay.com/v1/checkout.js";
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);

    document.body.appendChild(script);
  });
};

const usePayments = () => {
  const userId = useMemo(() => getUserIdFromToken(), []);

  const [premiumStatus, setPremiumStatus] = useState(null);
  const [loadingStatus, setLoadingStatus] = useState(false);
  const [paying, setPaying] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const fetchPremiumStatus = useCallback(async () => {
    if (!userId) return;

    setLoadingStatus(true);
    setError("");

    try {
      const data = await getPremiumStatus(userId);
      setPremiumStatus(data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          "Failed to load premium status"
      );
    } finally {
      setLoadingStatus(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchPremiumStatus();
  }, [fetchPremiumStatus]);

  const startPayment = async () => {
    if (!userId) {
      setError("User ID not found. Please login again.");
      return;
    }

    setPaying(true);
    setError("");
    setSuccess("");

    try {
      const loaded = await loadRazorpayScript();

      if (!loaded) {
        setError("Razorpay SDK failed to load.");
        return;
      }

      const order = await createPaymentOrder(userId);

      const options = {
        key: order.key_id,
        amount: order.amount,
        currency: order.currency,
        name: "BudgetPro",
        description: order.description,
        order_id: order.order_id,
        theme: {
          color: "#2563eb",
        },
        handler: async function (response) {
          const verifyResponse = await verifyPayment({
            user_id: Number(userId),
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
          });

          setSuccess("Payment successful. You are now a Premium Member.");
          setPremiumStatus(verifyResponse);
          await fetchPremiumStatus();
        },
        modal: {
          ondismiss: function () {
            setPaying(false);
          },
        },
      };

      const razorpay = new window.Razorpay(options);
      razorpay.open();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.message ||
          err.message ||
          "Payment failed"
      );
    } finally {
      setPaying(false);
    }
  };

  return {
    userId,
    premiumStatus,
    isPremium: Boolean(premiumStatus?.is_premium),
    loadingStatus,
    paying,
    error,
    success,
    fetchPremiumStatus,
    startPayment,
  };
};

export default usePayments;
-------------------------------------
import { Button, Chip, Stack } from "@mui/material";
import WorkspacePremiumIcon from "@mui/icons-material/WorkspacePremium";
import usePayments from "../../hooks/usePayments";

const SubscribeButton = () => {
  const { isPremium, paying, startPayment } = usePayments();

  if (isPremium) {
    return (
      <Chip
        icon={<WorkspacePremiumIcon />}
        label="Premium Member"
        color="success"
        sx={{ fontWeight: 800 }}
      />
    );
  }

  return (
    <Stack direction="row" alignItems="center">
      <Button
        variant="contained"
        size="small"
        disabled={paying}
        onClick={startPayment}
        startIcon={<WorkspacePremiumIcon />}
      >
        {paying ? "Processing..." : "Subscribe"}
      </Button>
    </Stack>
  );
};

export default SubscribeButton;
----------------------------------
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Grid,
  Stack,
  Typography,
} from "@mui/material";
import WorkspacePremiumIcon from "@mui/icons-material/WorkspacePremium";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import { QRCodeCanvas } from "qrcode.react";
import PageHeader from "../../components/common/PageHeader";
import usePayments from "../../hooks/usePayments";

const SubscriptionPage = () => {
  const {
    premiumStatus,
    isPremium,
    paying,
    error,
    success,
    startPayment,
  } = usePayments();

  const subscriptionUrl = `${window.location.origin}/subscription`;

  return (
    <Box>
      <PageHeader
        title="Subscription"
        subtitle="Upgrade to Premium Member and show payment integration in your BudgetPro project."
        breadcrumbs={["Billing", "Subscription"]}
      />

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }}>
          {success}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={7}>
          <Card
            elevation={0}
            sx={{
              border: "1px solid",
              borderColor: isPremium ? "success.main" : "divider",
            }}
          >
            <CardContent>
              <Stack direction="row" spacing={1} alignItems="center" mb={2}>
                <WorkspacePremiumIcon color="primary" />
                <Typography variant="h5" fontWeight={900}>
                  Premium Membership
                </Typography>
              </Stack>

              <Typography color="text.secondary" mb={2}>
                Unlock premium badge and demonstrate secure Razorpay payment integration.
              </Typography>

              <Typography variant="h3" fontWeight={900}>
                ₹99
              </Typography>

              <Typography color="text.secondary" mb={3}>
                Valid for 30 days
              </Typography>

              <Stack spacing={1.5} mb={3}>
                <Stack direction="row" spacing={1} alignItems="center">
                  <CheckCircleIcon color="success" />
                  <Typography>Premium Member badge on navbar</Typography>
                </Stack>

                <Stack direction="row" spacing={1} alignItems="center">
                  <CheckCircleIcon color="success" />
                  <Typography>Payment stored in backend database</Typography>
                </Stack>

                <Stack direction="row" spacing={1} alignItems="center">
                  <CheckCircleIcon color="success" />
                  <Typography>Razorpay Checkout integration</Typography>
                </Stack>

                <Stack direction="row" spacing={1} alignItems="center">
                  <CheckCircleIcon color="success" />
                  <Typography>QR code shown on frontend</Typography>
                </Stack>
              </Stack>

              {isPremium ? (
                <Chip
                  icon={<WorkspacePremiumIcon />}
                  label={`Premium Member ${
                    premiumStatus?.end_date
                      ? `valid till ${new Date(
                          premiumStatus.end_date
                        ).toLocaleDateString("en-IN")}`
                      : ""
                  }`}
                  color="success"
                  sx={{ fontWeight: 900 }}
                />
              ) : (
                <Button
                  variant="contained"
                  size="large"
                  disabled={paying}
                  onClick={startPayment}
                  startIcon={<WorkspacePremiumIcon />}
                >
                  {paying ? "Processing..." : "Subscribe Now"}
                </Button>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={5}>
          <Card elevation={0} sx={{ border: "1px solid", borderColor: "divider" }}>
            <CardContent>
              <Typography variant="h6" fontWeight={900} mb={1}>
                Scan QR Code
              </Typography>

              <Typography color="text.secondary" mb={3}>
                Scan this QR code to open the subscription page on another device.
              </Typography>

              <Box
                sx={{
                  p: 3,
                  borderRadius: 3,
                  backgroundColor: "white",
                  display: "inline-flex",
                }}
              >
                <QRCodeCanvas value={subscriptionUrl} size={220} />
              </Box>

              <Typography variant="body2" color="text.secondary" mt={2}>
                QR opens: {subscriptionUrl}
              </Typography>

              <Alert severity="info" sx={{ mt: 3 }}>
                Payment will still happen through Razorpay Checkout after clicking Subscribe.
              </Alert>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default SubscriptionPage;
---------------------------------------