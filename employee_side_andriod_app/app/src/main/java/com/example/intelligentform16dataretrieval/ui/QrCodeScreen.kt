package com.example.intelligentform16dataretrieval.ui

import android.graphics.Bitmap
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.QrCode
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.blur
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.ColorFilter
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.intelligentform16dataretrieval.data.QrCodeGenerator
import com.example.intelligentform16dataretrieval.data.SupabaseClient
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun QrCodeScreen(onBack: () -> Unit) {
    var qrBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var isLoading by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    var showPasswordDialog by remember { mutableStateOf(false) }
    var passwordInput by remember { mutableStateOf("") }

    val coroutineScope = rememberCoroutineScope()
    val supabaseClient = remember { SupabaseClient() }

    fun fetchQrCode(password: String) {
        isLoading = true
        errorMessage = null
        coroutineScope.launch {
            try {
                // Step 1: Hash password and find employee
                val empId = supabaseClient.getEmployeeIdByPassword(password)
                if (empId == null) {
                    errorMessage = "Invalid password or employee not found."
                    isLoading = false
                    return@launch
                }

                // Step 2: Get qr_value for the employee
                val qrVal = supabaseClient.getQrValueByEmployeeId(empId)
                if (qrVal == null) {
                    errorMessage = "QR Code data not found for this employee."
                    isLoading = false
                    return@launch
                }

                // Step 3: Generate QR code bitmap from the qr_value text
                val bitmap = QrCodeGenerator.generate(qrVal, 512)
                qrBitmap = bitmap

            } catch (e: Exception) {
                errorMessage = "Error: ${e.message}"
                e.printStackTrace()
            } finally {
                isLoading = false
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("View QR Code") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(imageVector = Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .background(MaterialTheme.colorScheme.background)
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(
                text = "Form 16 Data",
                fontSize = 28.sp,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onBackground
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = if (qrBitmap != null) "Here is your Form 16 QR Code"
                       else "Authenticate to view the QR Code",
                fontSize = 16.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )

            Spacer(modifier = Modifier.height(48.dp))

            // QR Code Display Box
            Box(
                modifier = Modifier
                    .size(280.dp)
                    .clip(RoundedCornerShape(16.dp))
                    .background(MaterialTheme.colorScheme.surfaceVariant)
                    .padding(16.dp),
                contentAlignment = Alignment.Center
            ) {
                if (qrBitmap != null) {
                    // Show the REAL generated QR code
                    Image(
                        bitmap = qrBitmap!!.asImageBitmap(),
                        contentDescription = "Form 16 QR Code",
                        modifier = Modifier.fillMaxSize(),
                        contentScale = ContentScale.Fit
                    )
                } else {
                    // Show blurred placeholder icon
                    Image(
                        imageVector = Icons.Default.QrCode,
                        contentDescription = "Blurred QR Code Placeholder",
                        modifier = Modifier
                            .fillMaxSize()
                            .blur(radius = 20.dp),
                        colorFilter = ColorFilter.tint(MaterialTheme.colorScheme.onSurfaceVariant)
                    )
                }
            }

            Spacer(modifier = Modifier.height(48.dp))

            if (isLoading) {
                CircularProgressIndicator()
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "Verifying password...",
                    fontSize = 14.sp,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            } else if (qrBitmap == null) {
                // Show "View QR Code" button
                Button(
                    onClick = { showPasswordDialog = true },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(56.dp),
                    shape = MaterialTheme.shapes.large
                ) {
                    Text("View QR Code", fontSize = 18.sp)
                }

                if (errorMessage != null) {
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(
                        text = errorMessage!!,
                        color = MaterialTheme.colorScheme.error,
                        fontSize = 14.sp
                    )
                }
            } else {
                // QR is visible, show hide button
                Button(
                    onClick = { qrBitmap = null },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(56.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.secondary),
                    shape = MaterialTheme.shapes.large
                ) {
                    Text("Hide QR Code", fontSize = 18.sp)
                }
            }
        }
    }

    // Password Dialog
    if (showPasswordDialog) {
        AlertDialog(
            onDismissRequest = { showPasswordDialog = false },
            title = { Text("Enter Your Password") },
            text = {
                Column {
                    Text(
                        text = "Enter your employee password to verify identity",
                        fontSize = 14.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    OutlinedTextField(
                        value = passwordInput,
                        onValueChange = { passwordInput = it },
                        label = { Text("Password") },
                        visualTransformation = PasswordVisualTransformation(),
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        val pwd = passwordInput
                        showPasswordDialog = false
                        passwordInput = ""
                        fetchQrCode(pwd)
                    },
                    enabled = passwordInput.isNotBlank()
                ) {
                    Text("Verify")
                }
            },
            dismissButton = {
                TextButton(onClick = {
                    showPasswordDialog = false
                    passwordInput = ""
                }) {
                    Text("Cancel")
                }
            }
        )
    }
}
