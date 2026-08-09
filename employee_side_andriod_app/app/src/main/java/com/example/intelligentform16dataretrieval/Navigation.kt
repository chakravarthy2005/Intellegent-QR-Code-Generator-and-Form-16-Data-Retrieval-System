package com.example.intelligentform16dataretrieval

import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.navigation3.runtime.entryProvider
import androidx.navigation3.runtime.rememberNavBackStack
import androidx.navigation3.ui.NavDisplay
import com.example.intelligentform16dataretrieval.ui.*

@Composable
fun MainNavigation() {
  val backStack = rememberNavBackStack(Splash)

  NavDisplay(
    backStack = backStack,
    onBack = { backStack.removeLastOrNull() },
    entryProvider =
      entryProvider {
        entry<Splash> {
          SplashScreen(
            onNavigateToSetMpin = { 
                backStack.removeLastOrNull()
                backStack.add(SetMpin) 
            },
            onNavigateToMpin = { 
                backStack.removeLastOrNull()
                backStack.add(Mpin) 
            }
          )
        }
        entry<SetMpin> {
          SetMpinScreen(
            onMpinSet = { 
                backStack.removeLastOrNull()
                backStack.add(Mpin) 
            }
          )
        }
        entry<Mpin> {
          MpinScreen(
            onMpinSuccess = { 
                backStack.add(QrCode) 
            },
            onBack = {
                backStack.removeLastOrNull()
            }
          )
        }
        entry<QrCode> {
          QrCodeScreen(
            onBack = {
                backStack.removeLastOrNull()
            }
          )
        }
      },
  )
}
