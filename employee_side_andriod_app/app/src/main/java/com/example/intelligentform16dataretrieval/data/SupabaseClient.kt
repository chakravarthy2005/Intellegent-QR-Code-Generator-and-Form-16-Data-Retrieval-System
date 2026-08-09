package com.example.intelligentform16dataretrieval.data

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONArray
import org.mindrot.jbcrypt.BCrypt

class SupabaseClient {
    // Supabase Project URL
    private val supabaseUrl = "https://gkhsgzrpnvxdiyruusgj.supabase.co"

    // Service Role Key (needed for private table/bucket access)
    private val supabaseKey = "sb_secret_1N6A5lbfgnVpKUg0pOVfOA_sr_cIkzY"

    private val client = OkHttpClient()

    /**
     * Looks up employee_id from the employee table using Bcrypt verification.
     * Fetches employee records and validates the password using jbcrypt, 
     * converting the python "$2b$" prefix to "$2a$" as expected by Android jbcrypt.
     */
    suspend fun getEmployeeIdByPassword(password: String): String? = withContext(Dispatchers.IO) {
        val url = "$supabaseUrl/rest/v1/employee?select=employee_id,password_hash"

        val request = Request.Builder()
            .url(url)
            .get()
            .addHeader("apikey", supabaseKey)
            .addHeader("Authorization", "Bearer $supabaseKey")
            .addHeader("Content-Type", "application/json")
            .build()

        return@withContext try {
            val response = client.newCall(request).execute()
            val body = response.body?.string()
            println("SupabaseClient: getEmployeeId status=${response.code}")
            
            if (!response.isSuccessful || body.isNullOrEmpty()) {
                null
            } else {
                val array = JSONArray(body)
                var matchedEmployeeId: String? = null
                
                for (i in 0 until array.length()) {
                    val obj = array.getJSONObject(i)
                    val dbHash = obj.optString("password_hash", "")
                    
                    if (dbHash.isNotBlank()) {
                        // Convert Python's $2b$ Bcrypt prefix to Java-compatible $2a$ prefix
                        val compatibleHash = if (dbHash.startsWith("$2b$")) {
                            dbHash.replaceFirst("$2b$", "$2a$")
                        } else {
                            dbHash
                        }
                        
                        try {
                            if (BCrypt.checkpw(password, compatibleHash)) {
                                matchedEmployeeId = obj.get("employee_id").toString()
                                break
                            }
                        } catch (e: Exception) {
                            println("Bcrypt check failed for employee at index $i: ${e.message}")
                        }
                    }
                }
                matchedEmployeeId
            }
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }

    /**
     * Looks up the qr_value from the qr_code table using employee_id.
     * This qr_value is the text data used to GENERATE the QR code in the app.
     */
    suspend fun getQrValueByEmployeeId(employeeId: String): String? = withContext(Dispatchers.IO) {
        val url = "$supabaseUrl/rest/v1/qr_code?employee_id=eq.$employeeId&select=qr_value"

        val request = Request.Builder()
            .url(url)
            .get()
            .addHeader("apikey", supabaseKey)
            .addHeader("Authorization", "Bearer $supabaseKey")
            .addHeader("Content-Type", "application/json")
            .build()

        return@withContext try {
            val response = client.newCall(request).execute()
            val body = response.body?.string()
            println("SupabaseClient: getQrValue status=${response.code}")
            if (!response.isSuccessful || body.isNullOrEmpty()) {
                null
            } else {
                val array = JSONArray(body)
                if (array.length() == 0) null
                else array.getJSONObject(0).getString("qr_value")
            }
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }
}
