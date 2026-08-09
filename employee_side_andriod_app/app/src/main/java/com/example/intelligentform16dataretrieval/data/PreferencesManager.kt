package com.example.intelligentform16dataretrieval.data

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "settings")

class PreferencesManager(private val context: Context) {
    companion object {
        val MPIN_KEY = stringPreferencesKey("user_mpin")
    }

    val userMpin: Flow<String?> = context.dataStore.data.map { preferences ->
        preferences[MPIN_KEY]
    }

    suspend fun saveMpin(mpin: String) {
        context.dataStore.edit { preferences ->
            preferences[MPIN_KEY] = mpin
        }
    }
}
