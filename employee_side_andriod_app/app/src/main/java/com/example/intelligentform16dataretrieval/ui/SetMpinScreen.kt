package com.example.intelligentform16dataretrieval.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Backspace
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.intelligentform16dataretrieval.data.PreferencesManager
import kotlinx.coroutines.launch

@Composable
fun SetMpinScreen(onMpinSet: () -> Unit) {
    var mpin by remember { mutableStateOf("") }
    val maxMpinLength = 4
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()
    val preferencesManager = remember { PreferencesManager(context) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = "Set up your MPIN",
            fontSize = 28.sp,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.onBackground
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = "Enter a 4-digit PIN to secure your app",
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
                            if (i < mpin.length) MaterialTheme.colorScheme.primary
                            else MaterialTheme.colorScheme.surfaceVariant
                        )
                )
            }
        }

        Spacer(modifier = Modifier.height(64.dp))

        // Number Pad
        NumberPad(
            onNumberClick = { number ->
                if (mpin.length < maxMpinLength) {
                    mpin += number
                }
            },
            onBackspaceClick = {
                if (mpin.isNotEmpty()) {
                    mpin = mpin.dropLast(1)
                }
            }
        )

        Spacer(modifier = Modifier.height(32.dp))

        Button(
            onClick = {
                if (mpin.length == maxMpinLength) {
                    coroutineScope.launch {
                        preferencesManager.saveMpin(mpin)
                        onMpinSet()
                    }
                }
            },
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp),
            enabled = mpin.length == maxMpinLength,
            shape = MaterialTheme.shapes.large
        ) {
            Text("Confirm MPIN", fontSize = 18.sp)
        }
    }
}

@Composable
fun NumberPad(onNumberClick: (String) -> Unit, onBackspaceClick: () -> Unit) {
    val rows = listOf(
        listOf("1", "2", "3"),
        listOf("4", "5", "6"),
        listOf("7", "8", "9"),
        listOf("", "0", "backspace")
    )

    Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
        for (row in rows) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                for (key in row) {
                    if (key == "") {
                        Spacer(modifier = Modifier.size(72.dp))
                    } else if (key == "backspace") {
                        IconButton(
                            onClick = onBackspaceClick,
                            modifier = Modifier
                                .size(72.dp)
                                .background(MaterialTheme.colorScheme.surfaceVariant, CircleShape)
                        ) {
                            Icon(
                                imageVector = Icons.AutoMirrored.Filled.Backspace,
                                contentDescription = "Backspace",
                                tint = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    } else {
                        TextButton(
                            onClick = { onNumberClick(key) },
                            modifier = Modifier
                                .size(72.dp)
                                .background(MaterialTheme.colorScheme.surfaceVariant, CircleShape),
                            shape = CircleShape
                        ) {
                            Text(
                                text = key,
                                fontSize = 28.sp,
                                fontWeight = FontWeight.Medium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                }
            }
        }
    }
}
