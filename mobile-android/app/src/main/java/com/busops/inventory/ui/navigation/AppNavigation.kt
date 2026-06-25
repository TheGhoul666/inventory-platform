package com.busops.inventory.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.busops.inventory.ui.screens.auth.LoginScreen
import com.busops.inventory.ui.screens.auth.AuthViewModel
import com.busops.inventory.ui.screens.dashboard.DashboardScreen
import com.busops.inventory.ui.screens.inventory.InventoryListScreen
import com.busops.inventory.ui.screens.alerts.AlertsScreen

sealed class Screen(val route: String) {
    data object Login : Screen("login")
    data object Dashboard : Screen("dashboard")
    data object Inventory : Screen("inventory")
    data object Alerts : Screen("alerts")
}

@Composable
fun AppNavigation(navController: NavHostController = rememberNavController()) {
    val authViewModel: AuthViewModel = hiltViewModel()
    val isLoggedIn by authViewModel.isLoggedIn.collectAsState(initial = false)

    NavHost(
        navController = navController,
        startDestination = if (isLoggedIn) Screen.Dashboard.route else Screen.Login.route,
    ) {
        composable(Screen.Login.route) {
            LoginScreen(
                viewModel = hiltViewModel(),
                onLoginSuccess = {
                    navController.navigate(Screen.Dashboard.route) {
                        popUpTo(Screen.Login.route) { inclusive = true }
                    }
                },
            )
        }

        composable(Screen.Dashboard.route) {
            DashboardScreen(
                viewModel = hiltViewModel(),
                onNavigateToInventory = { navController.navigate(Screen.Inventory.route) },
                onNavigateToAlerts = { navController.navigate(Screen.Alerts.route) },
                onLogout = {
                    navController.navigate(Screen.Login.route) {
                        popUpTo(0) { inclusive = true }
                    }
                },
            )
        }

        composable(Screen.Inventory.route) {
            InventoryListScreen(
                viewModel = hiltViewModel(),
                onBack = { navController.popBackStack() },
            )
        }

        composable(Screen.Alerts.route) {
            AlertsScreen(
                viewModel = hiltViewModel(),
                onBack = { navController.popBackStack() },
            )
        }
    }
}
