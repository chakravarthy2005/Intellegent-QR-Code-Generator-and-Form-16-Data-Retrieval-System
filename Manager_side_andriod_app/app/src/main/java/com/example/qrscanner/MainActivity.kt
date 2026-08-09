package com.example.qrscanner

import android.Manifest

import android.content.pm.PackageManager
import android.os.Build
import java.net.URLEncoder
import android.os.Bundle
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.util.Base64
import android.util.Log
import android.view.View
import android.widget.*
import androidx.annotation.OptIn
import androidx.appcompat.app.AppCompatActivity
import androidx.biometric.BiometricManager
import androidx.biometric.BiometricPrompt
import androidx.camera.core.*
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.example.qrscanner.databinding.ActivityMainBinding
import com.google.mlkit.vision.barcode.BarcodeScanner
import com.google.mlkit.vision.barcode.BarcodeScannerOptions
import com.google.mlkit.vision.barcode.BarcodeScanning
import com.google.mlkit.vision.barcode.common.Barcode
import com.google.mlkit.vision.common.InputImage
import kotlinx.coroutines.*
import org.json.JSONArray
import org.json.JSONObject
import org.mindrot.jbcrypt.BCrypt
import java.io.*
import java.net.HttpURLConnection
import java.net.InetSocketAddress
import java.net.Socket
import java.net.URL
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.UUID
import java.util.concurrent.Executor
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class MainActivity : AppCompatActivity() {

    // ── View binding ──────────────────────────────────────────────────────────
    private lateinit var binding: ActivityMainBinding

    // ── Screens ───────────────────────────────────────────────────────────────
    private enum class Screen { LOGIN, HOME, METHOD_PICKER, SCANNER, RESULT, DETAIL }

    // ── Connection mode ───────────────────────────────────────────────────────
    private enum class ConnectionMode { USB, WIFI }
    private var connectionMode = ConnectionMode.USB
    private var viewOnMobileMode = false

    // ── Supabase Configuration ────────────────────────────────────────────────
    private val SUPABASE_URL = "https://gkhsgzrpnvxdiyruusgj.supabase.co"
    private val SUPABASE_KEY = "sb_secret_1N6A5lbfgnVpKUg0pOVfOA_sr_cIkzY"

    // ── Active Manager Session ────────────────────────────────────────────────
    private var managerUsername: String = ""
    private var managerDisplayName: String = ""
    private var appSecret: ByteArray? = null
    private var systemKey: ByteArray? = null

    // ── WiFi Target ───────────────────────────────────────────────────────────
    private var wifiTargetIp = "127.0.0.1"
    private val targetPort = 12345


    // ── Camera / ML Kit ───────────────────────────────────────────────────────
    private lateinit var cameraExecutor: ExecutorService
    private lateinit var barcodeScanner: BarcodeScanner
    private var isScanningPaused = false

    // ── Coroutines ────────────────────────────────────────────────────────────
    private val scope = CoroutineScope(Dispatchers.Main + SupervisorJob())

    // ── Permission Codes ──────────────────────────────────────────────────────
    companion object {
        private const val TAG = "Form16Scanner"
        private const val REQ_CAMERA = 101
    }

    // ══════════════════════════════════════════════════════════════════════════
    // Lifecycle
    // ══════════════════════════════════════════════════════════════════════════

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)


        cameraExecutor = Executors.newSingleThreadExecutor()

        val options = BarcodeScannerOptions.Builder()
            .setBarcodeFormats(Barcode.FORMAT_QR_CODE)
            .build()
        barcodeScanner = BarcodeScanning.getClient(options)

        setupLoginScreen()
        setupHomeScreen()
        setupMethodPicker()
        setupScannerScreen()
        setupResultScreen()
        setupDetailScreen()

        showScreen(Screen.LOGIN)
    }

    override fun onDestroy() {
        super.onDestroy()
        cameraExecutor.shutdown()
        scope.cancel()
    }

    private fun showScreen(screen: Screen) {
        runOnUiThread {
            binding.viewFlipper.displayedChild = screen.ordinal
        }
    }

    // ══════════════════════════════════════════════════════════════════════════
    // SCREEN 0: Manager Login
    // ══════════════════════════════════════════════════════════════════════════

    private fun setupLoginScreen() {
        binding.btnLoginSubmit.setOnClickListener {
            val username = binding.loginUsername.text.toString().trim()
            val password = binding.loginPassword.text.toString().trim()

            if (username.isEmpty() || password.isEmpty()) {
                Toast.makeText(this, "Please enter username and password", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            binding.btnLoginSubmit.isEnabled = false
            binding.btnLoginSubmit.text = "Authenticating..."

            scope.launch {
                val success = attemptLogin(username, password)
                binding.btnLoginSubmit.isEnabled = true
                binding.btnLoginSubmit.text = "Sign In"

                if (success) {
                    binding.loginUsername.text.clear()
                    binding.loginPassword.text.clear()
                    binding.homeTitleWelcome.text = "Welcome, $managerDisplayName"
                    showScreen(Screen.HOME)
                } else {
                    Toast.makeText(this@MainActivity, "Invalid username or password", Toast.LENGTH_LONG).show()
                }
            }
        }
    }

    private suspend fun attemptLogin(username: String, password: String): Boolean =
        withContext(Dispatchers.IO) {
            try {
                // PostgREST REST API call
                val urlStr = "$SUPABASE_URL/rest/v1/managers?username=eq.$username"
                val response = makeHttpRequest(urlStr) ?: return@withContext false
                val arr = JSONArray(response)
                if (arr.length() == 0) return@withContext false

                val mObj = arr.getJSONObject(0)
                val pwdHash = mObj.getString("password_hash")

                // BCrypt check
                // BCrypt check
                val compatibleHash = pwdHash.replaceFirst("$2b$", "$2a$")
                if (!BCrypt.checkpw(password, compatibleHash)) return@withContext false

                // Decrypt app_secret
                val displayStr = mObj.optString("display_name", "")
                var realName = username
                var secretBytes: ByteArray? = null

                if (displayStr.startsWith("{")) {
                    val displayPayload = JSONObject(displayStr)
                    realName = displayPayload.optString("real_name", username)
                    if (displayPayload.has("enc_app_secret")) {
                        val enc = displayPayload.getJSONObject("enc_app_secret")
                        secretBytes = CryptoHelper.decryptAppSecret(
                            saltB64 = enc.getString("salt"),
                            nonceB64 = enc.getString("nonce"),
                            ciphertextB64 = enc.getString("ciphertext"),
                            password = password
                        )
                    }
                }

                // Initialize manager session keys
                managerUsername = username
                managerDisplayName = realName
                if (secretBytes != null) {
                    appSecret = secretBytes
                    systemKey = CryptoHelper.deriveSystemKey(secretBytes)
                } else {
                    appSecret = null
                    systemKey = null
                }
                true
            } catch (e: Exception) {
                Log.e(TAG, "Login attempt error", e)
                false
            }
        }

    // ══════════════════════════════════════════════════════════════════════════
    // SCREEN 1: Home
    // ══════════════════════════════════════════════════════════════════════════

    private fun setupHomeScreen() {
        binding.btnHomeLogout.setOnClickListener {
            managerUsername = ""
            managerDisplayName = ""
            appSecret = null
            systemKey = null
            showScreen(Screen.LOGIN)
        }

        binding.btnSendToDesktop.setOnClickListener {
            viewOnMobileMode = false
            showScreen(Screen.METHOD_PICKER)
        }

        binding.btnViewOnMobile.setOnClickListener {
            if (appSecret == null) {
                Toast.makeText(
                    this@MainActivity,
                    "Decryption keys not synced. Please log in on the desktop app first to upload keys.",
                    Toast.LENGTH_LONG
                ).show()
                return@setOnClickListener
            }
            viewOnMobileMode = true
            requestCameraAndStartScanner()
        }
    }


    // ══════════════════════════════════════════════════════════════════════════
    // SCREEN 2: Method Picker
    // ══════════════════════════════════════════════════════════════════════════

    private fun setupMethodPicker() {
        binding.btnMethodBack.setOnClickListener { showScreen(Screen.HOME) }

        // USB
        binding.btnMethodUsb.setOnClickListener {
            connectionMode = ConnectionMode.USB
            binding.connectionBadge.text = "🔌 USB"
            binding.connectionBadge.setTextColor(ContextCompat.getColor(this, R.color.color_primary))
            hideMethodSubViews()
            requestCameraAndStartScanner()
        }


        // WiFi
        binding.btnMethodWifi.setOnClickListener {
            connectionMode = ConnectionMode.WIFI
            binding.connectionBadge.text = "📶 WiFi"
            binding.connectionBadge.setTextColor(ContextCompat.getColor(this, R.color.color_warning))
            hideMethodSubViews()
            showWifiInput()
        }

        binding.wifiConnectBtn.setOnClickListener {
            val ip = binding.wifiIpInput.text.toString().trim()
            if (ip.isEmpty()) {
                Toast.makeText(this, "Please enter laptop IP address", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            wifiTargetIp = ip
            requestCameraAndStartScanner()
        }
    }

    private fun hideMethodSubViews() {
        binding.wifiInputLayout.visibility = View.GONE
    }

    private fun showWifiInput() {
        binding.wifiInputLayout.visibility = View.VISIBLE
    }



    // ══════════════════════════════════════════════════════════════════════════
    // SCREEN 3: QR Scanner
    // ══════════════════════════════════════════════════════════════════════════

    private fun setupScannerScreen() {
        binding.btnScannerBack.setOnClickListener {
            isScanningPaused = true
            if (viewOnMobileMode) showScreen(Screen.HOME)
            else showScreen(Screen.METHOD_PICKER)
        }
    }

    private fun requestCameraAndStartScanner() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA)
            == PackageManager.PERMISSION_GRANTED) {
            showScreen(Screen.SCANNER)
            isScanningPaused = false
            setScanStatus("📸  Align QR code within the frame", "Hold steady — auto-detects when in frame")
            startCamera()
        } else {
            ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.CAMERA), REQ_CAMERA)
        }
    }

    private fun startCamera() {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(this)
        cameraProviderFuture.addListener({
            val cameraProvider = cameraProviderFuture.get()
            val preview = Preview.Builder().build().also {
                it.setSurfaceProvider(binding.previewView.surfaceProvider)
            }
            val analyzer = ImageAnalysis.Builder()
                .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                .build().also {
                    it.setAnalyzer(cameraExecutor) { imageProxy -> processImageProxy(imageProxy) }
                }

            try {
                cameraProvider.unbindAll()
                cameraProvider.bindToLifecycle(this, CameraSelector.DEFAULT_BACK_CAMERA, preview, analyzer)
            } catch (e: Exception) {
                Log.e(TAG, "Camera binding failed", e)
            }
        }, ContextCompat.getMainExecutor(this))
    }

    @OptIn(ExperimentalGetImage::class)
    private fun processImageProxy(imageProxy: ImageProxy) {
        if (isScanningPaused) { imageProxy.close(); return }
        val mediaImage = imageProxy.image ?: run { imageProxy.close(); return }
        val image = InputImage.fromMediaImage(mediaImage, imageProxy.imageInfo.rotationDegrees)

        barcodeScanner.process(image)
            .addOnSuccessListener { barcodes ->
                barcodes.firstOrNull()?.rawValue?.let { onQrDetected(it) }
            }
            .addOnFailureListener { Log.e(TAG, "ML Kit error", it) }
            .addOnCompleteListener { imageProxy.close() }
    }

    // ══════════════════════════════════════════════════════════════════════════
    // QR Payload processing & share
    // ══════════════════════════════════════════════════════════════════════════

    private fun onQrDetected(rawValue: String) {
        if (isScanningPaused) return
        isScanningPaused = true
        triggerVibration()

        if (viewOnMobileMode) {
            // Fingerprint check then decrypt
            authenticateFingerprint {
                fetchAndDisplayForm16(rawValue)
            }
        } else {
            // Share to desktop
            setScanStatus("🔌 Sending QR payload...", "Connecting to desktop...")
            scope.launch {
                val success = when (connectionMode) {
                    ConnectionMode.USB -> sendViaTcp(rawValue, "127.0.0.1", targetPort)
                    ConnectionMode.WIFI -> sendViaTcp(rawValue, wifiTargetIp, targetPort)
                }
                if (success) {
                    showDesktopSentResult(rawValue)
                } else {
                    showErrorResult("Desktop connection failed.")
                }
            }
        }
    }

    private fun authenticateFingerprint(onSuccess: () -> Unit) {
        val biometricManager = BiometricManager.from(this)
        if (biometricManager.canAuthenticate(BiometricManager.Authenticators.BIOMETRIC_STRONG)
            != BiometricManager.BIOMETRIC_SUCCESS) {
            // Biometric not available, bypass or warn
            onSuccess()
            return
        }

        val executor = ContextCompat.getMainExecutor(this)
        val prompt = BiometricPrompt(this, executor, object : BiometricPrompt.AuthenticationCallback() {
            override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                super.onAuthenticationSucceeded(result)
                runOnUiThread { onSuccess() }
            }

            override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                super.onAuthenticationError(errorCode, errString)
                Toast.makeText(this@MainActivity, "Auth Error: $errString", Toast.LENGTH_SHORT).show()
                isScanningPaused = false // retry scan
                showScreen(Screen.HOME)
            }

            override fun onAuthenticationFailed() {
                super.onAuthenticationFailed()
                Toast.makeText(this@MainActivity, "Auth Failed", Toast.LENGTH_SHORT).show()
            }
        })

        val info = BiometricPrompt.PromptInfo.Builder()
            .setTitle("Authenticate scan")
            .setSubtitle("Confirm manager identity to decrypt data on this device.")
            .setNegativeButtonText("Cancel")
            .build()

        prompt.authenticate(info)
    }

    // ══════════════════════════════════════════════════════════════════════════
    // Fetch and Decrypt details (Mobile mode)
    // ══════════════════════════════════════════════════════════════════════════

    private fun fetchAndDisplayForm16(qrData: String) {
        val sKey = systemKey ?: return

        scope.launch {
            setScanStatus("⏳ Fetching...", "Downloading tax records from cloud...")
            showScreen(Screen.SCANNER)

            val form16Data = withContext(Dispatchers.IO) {
                try {

                    // ==========================
                    // QR VALUE
                    // ==========================
                    val qrValue = qrData.trim()

                    Log.d(TAG, "========================================")
                    Log.d(TAG, "SCANNED QR:")
                    Log.d(TAG, qrValue)
                    Log.d(TAG, "========================================")

                    val encodedQr = URLEncoder.encode(qrValue, "UTF-8")

                    Log.d(TAG, "ENCODED QR:")
                    Log.d(TAG, encodedQr)
                    Log.d(TAG, "========================================")

                    // ==========================
                    // SEARCH QR TABLE
                    // ==========================
                    val qrUrl =
                        "$SUPABASE_URL/rest/v1/qr_code?qr_value=eq.$encodedQr"

                    Log.d(TAG, "REQUEST URL:")
                    Log.d(TAG, qrUrl)

                    val qrRes = makeHttpRequest(qrUrl) ?: return@withContext null

                    Log.d(TAG, "SUPABASE RESPONSE:")
                    Log.d(TAG, qrRes)

                    val qrArray = JSONArray(qrRes)

                    if (qrArray.length() == 0) {
                        Log.e(TAG, "QR NOT FOUND")
                        Log.e(TAG, "Scanned QR:")
                        Log.e(TAG, qrValue)
                        Log.e(TAG, "Encoded QR:")
                        Log.e(TAG, encodedQr)
                        return@withContext null
                    }

                    val qrObj = qrArray.getJSONObject(0)

                    val employeeId = qrObj.getInt("employee_id")

                    Log.d(TAG, "Employee ID = $employeeId")

                    // ==========================
                    // EMPLOYEE
                    // ==========================
                    val empUrl =
                        "$SUPABASE_URL/rest/v1/employee?employee_id=eq.$employeeId"

                    val empRes = makeHttpRequest(empUrl) ?: return@withContext null
                    val empObj = JSONArray(empRes).getJSONObject(0)

                    val employerId = empObj.getInt("employer_id")

                    // ==========================
                    // EMPLOYER
                    // ==========================
                    val erUrl =
                        "$SUPABASE_URL/rest/v1/employer?employer_id=eq.$employerId"

                    val erRes = makeHttpRequest(erUrl) ?: return@withContext null
                    val erObj = JSONArray(erRes).getJSONObject(0)

                    // ==========================
                    // FORM16
                    // ==========================
                    val f16Url =
                        "$SUPABASE_URL/rest/v1/form16?employee_id=eq.$employeeId&order=form16_id.desc"

                    val f16Res = makeHttpRequest(f16Url) ?: return@withContext null
                    val f16Obj = JSONArray(f16Res).getJSONObject(0)

                    val form16Id = f16Obj.getInt("form16_id")

                    // ==========================
                    // SALARY
                    // ==========================
                    val salObj = JSONArray(
                        makeHttpRequest(
                            "$SUPABASE_URL/rest/v1/salary_details?form16_id=eq.$form16Id"
                        ) ?: "[]"
                    ).optJSONObject(0)

                    // ==========================
                    // OTHER INCOME
                    // ==========================
                    val othObj = JSONArray(
                        makeHttpRequest(
                            "$SUPABASE_URL/rest/v1/other_income?form16_id=eq.$form16Id"
                        ) ?: "[]"
                    ).optJSONObject(0)

                    // ==========================
                    // DEDUCTIONS
                    // ==========================
                    val dedObj = JSONArray(
                        makeHttpRequest(
                            "$SUPABASE_URL/rest/v1/deductions?form16_id=eq.$form16Id"
                        ) ?: "[]"
                    ).optJSONObject(0)

                    // ==========================
                    // TAX
                    // ==========================
                    val taxObj = JSONArray(
                        makeHttpRequest(
                            "$SUPABASE_URL/rest/v1/tax_details?form16_id=eq.$form16Id"
                        ) ?: "[]"
                    ).optJSONObject(0)

                    // ==========================
                    // TDS
                    // ==========================
                    val tdsArray = JSONArray(
                        makeHttpRequest(
                            "$SUPABASE_URL/rest/v1/tds_details?form16_id=eq.$form16Id&order=quarter.asc"
                        ) ?: "[]"
                    )

                    JSONObject().apply {
                        put("employee", empObj)
                        put("employer", erObj)
                        put("form16", f16Obj)
                        put("salary", salObj)
                        put("other_income", othObj)
                        put("deductions", dedObj)
                        put("tax", taxObj)
                        put("tds", tdsArray)
                    }

                } catch (e: Exception) {
                    Log.e(TAG, "Form16 retrieval error", e)
                    null
                }
            }

            if (form16Data != null) {
                decryptAndPopulateDetailScreen(form16Data, sKey)
                showScreen(Screen.DETAIL)
            } else {
                showErrorResult("Record could not be retrieved from database.")
            }
        }
    }

    private fun decryptAndPopulateDetailScreen(data: JSONObject, systemKey: ByteArray) {
        val dec = { k: String, obj: JSONObject -> CryptoHelper.decryptData(obj.optString(k, ""), systemKey) }

        // Employee
        val emp = data.getJSONObject("employee")
        val name = dec("employee_name", emp)
        binding.detailEmpName.text = name
        binding.detailEmpInfoBlock.text = """
            PAN: ${dec("pan", emp)}
            Email: ${dec("email", emp)}
            Mobile: ${dec("mobile_number", emp)}
            Reference: ${dec("reference_number", emp)}
            Address: ${dec("address", emp)}, ${dec("city", emp)} - ${dec("pin_code", emp)}
        """.trimIndent()

        // Form16 Header
        val f16 = data.getJSONObject("form16")
        binding.detailEmpYears.text = "FY: ${dec("financial_year", f16)}  |  AY: ${dec("assessment_year", f16)}\nPeriod: ${dec("employment_from", f16)} to ${dec("employment_to", f16)}"

        // Employer
        val er = data.getJSONObject("employer")
        binding.detailEmployerBlock.text = """
            Name: ${dec("employer_name", er)}
            PAN: ${dec("pan", er)}
            TAN: ${dec("tan", er)}
        """.trimIndent()

        // Salary
        val sal = data.optJSONObject("salary")
        if (sal != null) {
            binding.detailSalaryBlock.text = """
                Gross Salary: ₹${dec("gross_salary", sal)}
                Perquisites: ₹${dec("perquisites", sal)}
                Total Salary: ₹${dec("total_salary", sal)}
                Standard Deduction: ₹${dec("standard_deduction", sal)}
                Professional Tax: ₹${dec("professional_tax", sal)}
                HRA Exemption: ₹${dec("hra_exemption", sal)}
                Net Salary: ₹${dec("total_salary_after_exemptions", sal)}
            """.trimIndent()
        }

        // Deductions
        val ded = data.optJSONObject("deductions")
        if (ded != null) {
            binding.detailDeductionsBlock.text = """
                80C: ₹${dec("deduction_80c", ded)}
                80D: ₹${dec("deduction_80d", ded)}
                80E: ₹${dec("deduction_80e", ded)}
                Other: ₹${dec("other_deductions", ded)}
                Total Deductions: ₹${dec("total_deductions", ded)}
            """.trimIndent()
        }

        // Tax details
        val tax = data.optJSONObject("tax")
        if (tax != null) {
            binding.detailTaxBlock.text = """
                Taxable Income: ₹${dec("taxable_income", tax)}
                Income Tax: ₹${dec("income_tax", tax)}
                Rebate 87A: ₹${dec("rebate_87a", tax)}
                Health & Cess: ₹${dec("health_education_cess", tax)}
                Net Tax Payable: ₹${dec("net_tax_payable", tax)}
            """.trimIndent()
        }

        // TDS
        val tds = data.optJSONArray("tds")
        binding.detailTdsLayout.removeAllViews()
        if (tds != null && tds.length() > 0) {
            for (i in 0 until tds.length()) {
                val tObj = tds.getJSONObject(i)
                val row = TextView(this).apply {
                    text = "Q${tObj.optString("quarter")} — Paid: ₹${dec("amount_paid", tObj)} | Deposited: ₹${dec("tax_deposited", tObj)}\nChallan: ${dec("challan_number", tObj)} (${dec("challan_date", tObj)})"
                    textSize = 12f
                    setTextColor(ContextCompat.getColor(context, R.color.text_muted))
                    setPadding(0, 4, 0, 8)
                }
                binding.detailTdsLayout.addView(row)
            }
        } else {
            binding.detailTdsLayout.addView(TextView(this).apply {
                text = "No quarterly TDS reports found."
                textSize = 12f
                setTextColor(ContextCompat.getColor(context, R.color.text_muted))
            })
        }
    }

    // ══════════════════════════════════════════════════════════════════════════
    // SCREEN 4 & 5: Result / Detail actions
    // ══════════════════════════════════════════════════════════════════════════

    private fun setupResultScreen() {
        binding.btnScanAgain.setOnClickListener {
            isScanningPaused = false
            requestCameraAndStartScanner()
        }
        binding.btnResultHome.setOnClickListener {
            showScreen(Screen.HOME)
        }
    }

    private fun setupDetailScreen() {
        binding.btnDetailBack.setOnClickListener {
            showScreen(Screen.HOME)
        }
    }

    private fun showDesktopSentResult(rawValue: String) {
        updateResultScreen(
            icon = "✅",
            title = "Sent to Desktop!",
            subtitle = "Data received by the laptop.\nEnter your manager password on the desktop app to decrypt and view the Form 16.",
            payload = rawValue.take(60) + if (rawValue.length > 60) "…" else "",
            isSuccess = true
        )
        showScreen(Screen.RESULT)
    }

    private fun showErrorResult(error: String) {
        updateResultScreen(
            icon = "❌",
            title = "Scan Failed",
            subtitle = "$error\n\nPlease check connection status and try again.",
            payload = "Error",
            isSuccess = false
        )
        showScreen(Screen.RESULT)
    }

    private fun updateResultScreen(icon: String, title: String, subtitle: String,
                                   payload: String, isSuccess: Boolean) {
        runOnUiThread {
            binding.resultIcon.text = icon
            binding.resultTitle.text = title
            binding.resultTitle.setTextColor(
                ContextCompat.getColor(this, if (isSuccess) R.color.color_success else R.color.color_error)
            )
            binding.resultSubtitle.text = subtitle
            binding.resultPayloadText.text = payload
            binding.resultIcon.backgroundTintList =
                ContextCompat.getColorStateList(this, if (isSuccess) R.color.color_primary else R.color.color_error)
            binding.btnScanAgain.visibility = if (isSuccess) View.GONE else View.VISIBLE
        }
    }

    // ══════════════════════════════════════════════════════════════════════════
    // Networking (HTTP / TCP / Bluetooth)
    // ══════════════════════════════════════════════════════════════════════════

    private suspend fun makeHttpRequest(urlStr: String): String? =
        withContext(Dispatchers.IO) {

            var conn: HttpURLConnection? = null

            try {

                Log.d(TAG, "========================================")
                Log.d(TAG, "HTTP GET:")
                Log.d(TAG, urlStr)

                val url = URL(urlStr)
                conn = url.openConnection() as HttpURLConnection

                conn.requestMethod = "GET"
                conn.setRequestProperty("apikey", SUPABASE_KEY)
                conn.setRequestProperty("Authorization", "Bearer $SUPABASE_KEY")
                conn.connectTimeout = 6000
                conn.readTimeout = 6000

                val code = conn.responseCode

                Log.d(TAG, "HTTP CODE = $code")

                if (code == HttpURLConnection.HTTP_OK) {

                    val response = conn.inputStream.bufferedReader().use {
                        it.readText()
                    }

                    Log.d(TAG, "HTTP RESPONSE:")
                    Log.d(TAG, response)
                    Log.d(TAG, "========================================")

                    response

                } else {

                    val error = conn.errorStream?.bufferedReader()?.use {
                        it.readText()
                    }

                    Log.e(TAG, "HTTP ERROR:")
                    Log.e(TAG, error ?: "No error body")
                    Log.d(TAG, "========================================")

                    null
                }

            } catch (e: Exception) {

                Log.e(TAG, "HTTP EXCEPTION", e)
                null

            } finally {
                conn?.disconnect()
            }
        }

    private suspend fun sendViaTcp(payload: String, ip: String, port: Int): Boolean =
        withContext(Dispatchers.IO) {
            var socket: Socket? = null
            return@withContext try {
                socket = Socket()
                socket.connect(InetSocketAddress(ip, port), 4000)
                PrintWriter(BufferedWriter(OutputStreamWriter(socket.getOutputStream())), true)
                    .also { it.println(payload); it.flush(); it.close() }
                true
            } catch (e: Exception) {
                Log.e(TAG, "TCP send failed", e)
                false
            } finally {
                try { socket?.close() } catch (_: Exception) {}
            }
        }


    // ══════════════════════════════════════════════════════════════════════════
    // Helpers
    // ══════════════════════════════════════════════════════════════════════════

    private fun setScanStatus(primary: String, secondary: String) {
        runOnUiThread {
            binding.scanStatusText.text = primary
            binding.scanSubText.text = secondary
        }
    }

    private fun triggerVibration() {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                val vm = getSystemService(VIBRATOR_MANAGER_SERVICE) as VibratorManager
                vm.defaultVibrator.vibrate(VibrationEffect.createOneShot(120, VibrationEffect.DEFAULT_AMPLITUDE))
            } else {
                @Suppress("DEPRECATION")
                val v = getSystemService(VIBRATOR_SERVICE) as Vibrator
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O)
                    v.vibrate(VibrationEffect.createOneShot(120, VibrationEffect.DEFAULT_AMPLITUDE))
                else
                    @Suppress("DEPRECATION") v.vibrate(120)
            }
        } catch (e: Exception) { Log.e(TAG, "Vibration failed", e) }
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        when (requestCode) {
            REQ_CAMERA -> {
                if (grantResults.firstOrNull() == PackageManager.PERMISSION_GRANTED) {
                    showScreen(Screen.SCANNER)
                    isScanningPaused = false
                    startCamera()
                } else {
                    Toast.makeText(this, "Camera permission required", Toast.LENGTH_LONG).show()
                }
            }
        }
    }
}
