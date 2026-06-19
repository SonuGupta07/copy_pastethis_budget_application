import {
  AppBar,
  Avatar,
  Box,
  IconButton,
  InputBase,
  Menu,
  MenuItem,
  Toolbar,
  Tooltip,
  Typography,
  alpha,
  useTheme,
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import SearchIcon from "@mui/icons-material/Search";
import DarkModeIcon from "@mui/icons-material/DarkMode";
import LightModeIcon from "@mui/icons-material/LightMode";
import LogoutIcon from "@mui/icons-material/Logout";
import PersonIcon from "@mui/icons-material/Person";
import { useState } from "react";
import useAuth from "../../hooks/useAuth";
import NotificationBell from "../notifications/NotificationBell";
import SubscribeButton from "../payment/SubscribeButton";

const drawerWidth = 280;

const Navbar = ({ onMenuClick, onThemeToggle, mode = "light" }) => {
  const theme = useTheme();
  const { user, logout } = useAuth();

  const [anchorEl, setAnchorEl] = useState(null);

  const userEmail = user?.email || "user@example.com";
  const initials = userEmail?.charAt(0)?.toUpperCase() || "U";

  return (
    <AppBar
      position="fixed"
      elevation={0}
      sx={{
        width: { lg: `calc(100% - ${drawerWidth}px)` },
        ml: { lg: `${drawerWidth}px` },
        backdropFilter: "blur(20px)",
        background:
          theme.palette.mode === "dark"
            ? "rgba(15,23,42,0.78)"
            : "rgba(255,255,255,0.82)",
        color: "text.primary",
        borderBottom: `1px solid ${theme.palette.divider}`,
      }}
    >
      <Toolbar sx={{ gap: 2 }}>
        <IconButton
          color="inherit"
          edge="start"
          onClick={onMenuClick}
          sx={{ display: { lg: "none" } }}
        >
          <MenuIcon />
        </IconButton>

        <Box>
          <Typography variant="h6" fontWeight={800}>
            Dashboard
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Track, plan and improve your financial health
          </Typography>
        </Box>

        <Box sx={{ flexGrow: 1 }} />

        <Box
          sx={{
            display: { xs: "none", md: "flex" },
            alignItems: "center",
            px: 2,
            py: 0.8,
            width: 320,
            borderRadius: 4,
            backgroundColor: alpha(theme.palette.text.primary, 0.06),
          }}
        >
          <SearchIcon
            fontSize="small"
            sx={{ mr: 1, color: "text.secondary" }}
          />
          <InputBase
            placeholder="Search transactions, budgets..."
            fullWidth
          />
        </Box>

        {/* RIGHT SIDE ACTIONS */}
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1,
          }}
        >
          <SubscribeButton />

          <NotificationBell />

          <Tooltip title="Toggle theme">
            <IconButton onClick={onThemeToggle}>
              {mode === "dark" ? <LightModeIcon /> : <DarkModeIcon />}
            </IconButton>
          </Tooltip>

          <Tooltip title="Account">
            <IconButton onClick={(event) => setAnchorEl(event.currentTarget)}>
              <Avatar
                sx={{
                  width: 38,
                  height: 38,
                  fontWeight: 800,
                  background: "linear-gradient(135deg, #2563eb, #7c3aed)",
                }}
              >
                {initials}
              </Avatar>
            </IconButton>
          </Tooltip>
        </Box>

        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={() => setAnchorEl(null)}
          PaperProps={{
            sx: {
              mt: 1.5,
              minWidth: 230,
              borderRadius: 3,
            },
          }}
        >
          <Box px={2} py={1.5}>
            <Typography fontWeight={800}>Signed in as</Typography>
            <Typography variant="body2" color="text.secondary">
              {userEmail}
            </Typography>
          </Box>

          <MenuItem onClick={() => setAnchorEl(null)}>
            <PersonIcon fontSize="small" sx={{ mr: 1 }} />
            Profile
          </MenuItem>

          <MenuItem
            onClick={() => {
              setAnchorEl(null);
              logout();
            }}
          >
            <LogoutIcon fontSize="small" sx={{ mr: 1 }} />
            Logout
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;