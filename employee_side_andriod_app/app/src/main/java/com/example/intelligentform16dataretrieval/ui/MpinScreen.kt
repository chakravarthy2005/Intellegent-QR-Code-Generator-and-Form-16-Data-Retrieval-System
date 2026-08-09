package com.example.intelligentform16dataretrieval.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.intelligentform16dataretrieval.data.PreferencesManager

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MpinScreen(onMpinSuccess: () -> Unit, onBack: () -> Unit) {
    var inputMpin by remember { mutableStateOf("") }
    var isError by remember { mutableStateOf(false) }
    val maxMpinLength = 4
    val context = LocalContext.current
    val preferencesManager = remember { PreferencesManager(context) }
    val savedMpin by preferencesManager.userMpin.collectAsState(initial = null)

    LaunchedEffect(inputMpin) {
        isError = false
        if (inputMpin.length == maxMpinLength) {
            if (inputMpin == savedMpin) {
                onMpinSuccess()
            } else {
                isError = true
                inputMpin = "" // clear on error
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("App Lock") },
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
                text = "Welcome Back",
                fontSize = 28.sp,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onBackground
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "Enter your MPIN to continue",
                fontSize = 16.sp,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(modifier = Modifier.height(48.dp))

            // MPIN Indicators
            Row(
                horizontalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                for (i in 0 until maxMpinLength) {
                    Box(
                        modifier = Modifier
                            .size(24.dp)
                            .clip(CircleShape)
                            .background(
                                when {
                                    isError -> MaterialTheme.colorScheme.error
                                    i < inputMpin.length -> MaterialTheme.colorScheme.primary
                                    else -> MaterialTheme.colorScheme.surfaceVariant
                                }
                            )
                    )
                }
            }
            
            if (isError) {
                Spacer(modifier = Modifier.height(16.dp))
                Text(
                    text = "Incorrect MPIN, please try again",
                    color = MaterialTheme.colorScheme.error,
                    fontSize = 14.sp
                )
            } else {
                Spacer(modifier = Modifier.height(36.dp)) // keeping consistent space
            }

            Spacer(modifier = Modifier.height(32.dp))

            // Number Pad reuse
            NumberPad(
                onNumberClick = { number ->
                    if (inputMpin.length < maxMpinLength) {
                        inputMpin += number
                    }
                },
                onBackspaceClick = {
                    if (inputMpin.isNotEmpty()) {
                        inputMpin = inputMpin.dropLast(1)
                    }
                }
            )
        }
    }
}
