package com.busops.inventory.data.repository

import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import com.busops.inventory.data.api.ACCESS_TOKEN_KEY
import com.busops.inventory.data.api.BusOpsApiService
import io.github.jan.supabase.SupabaseClient
import io.github.jan.supabase.auth.auth
import io.github.jan.supabase.auth.providers.builtin.Email
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

private val REFRESH_TOKEN_KEY = stringPreferencesKey("refresh_token")
private val USER_EMAIL_KEY = stringPreferencesKey("user_email")

@Singleton
class AuthRepository @Inject constructor(
    private val supabase: SupabaseClient,
    private val api: BusOpsApiService,
    private val dataStore: DataStore<Preferences>,
) {
    val isLoggedIn: Flow<Boolean> = dataStore.data.map { prefs ->
        prefs[ACCESS_TOKEN_KEY] != null
    }

    suspend fun login(email: String, password: String): Result<Unit> = runCatching {
        supabase.auth.signInWith(Email) {
            this.email = email
            this.password = password
        }
        val session = supabase.auth.currentSessionOrNull()
            ?: return Result.Error("Login failed — no session returned")
        dataStore.edit { prefs ->
            prefs[ACCESS_TOKEN_KEY] = session.accessToken
            prefs[REFRESH_TOKEN_KEY] = session.refreshToken
            prefs[USER_EMAIL_KEY] = email
        }
        Result.Success(Unit)
    }.getOrElse { Result.Error(it.message ?: "Unknown error") }

    suspend fun logout() {
        runCatching { supabase.auth.signOut() }
        dataStore.edit { it.clear() }
    }

    suspend fun refreshToken(): Boolean = runCatching {
        supabase.auth.refreshCurrentSession()
        val session = supabase.auth.currentSessionOrNull() ?: return false
        dataStore.edit { prefs ->
            prefs[ACCESS_TOKEN_KEY] = session.accessToken
            prefs[REFRESH_TOKEN_KEY] = session.refreshToken
        }
        true
    }.getOrDefault(false)
}
