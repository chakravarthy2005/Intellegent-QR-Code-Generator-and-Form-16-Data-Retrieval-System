# Form 16 Android USB QR Scanner

This is a native Android application built in Kotlin using **Google ML Kit Barcode Scanning** and **Android Jetpack CameraX**. 

It uses your Android phone's camera to scan the Form 16 private QR codes and transmits the data instantly over a **USB Cable** to the desktop application running on your laptop.

---

## 🛠 Setup & Build Instructions

### Step 1: Open in Android Studio
1. Open **Android Studio**.
2. Click **File > Open** and select the `android_scanner` directory.
3. Allow Android Studio to sync the Gradle project dependencies.

### Step 2: Enable USB Debugging on Your Android Phone
1. On your phone, go to **Settings > About Phone** and tap **Build Number** 7 times to enable Developer Options.
2. Go to **Settings > System > Developer Options** and enable **USB Debugging**.
3. Connect your phone to your laptop using a high-quality USB cable.

### Step 3: Run the Android App
1. Select your connected Android device in the Android Studio device dropdown.
2. Click the **Run** button (Green Play Icon) or press `Shift + F10` to compile and install it on your device.
3. Accept the Camera permission when prompted on your phone.

---

## 🔌 How to connect the Phone to the Laptop over USB

Because the Android device and laptop need a secure connection without requiring local Wi-Fi configuration, we use **ADB Port Forwarding (adb reverse)**.

1. Ensure the desktop python application is running on your laptop. It automatically opens a listener port on `12345`.
2. Open a terminal (PowerShell or Command Prompt) on your laptop.
3. Run the following command to forward your phone's port `12345` to your laptop's port `12345`:
   ```powershell
   adb reverse tcp:12345 tcp:12345
   ```
   *(Note: You must have ADB installed and added to your System PATH. ADB is included in Android Studio under `AppData\Local\Android\Sdk\platform-tools`).*

4. In the Android App, make sure the settings remain:
   - **IP Address**: `127.0.0.1`
   - **Port**: `12345`
5. Tap **"Test USB Connection"** on your phone. It should show **Connected! Port forwarding is working correctly. ✅**.

---

## 📸 Workflow

1. In the laptop python app, log in as a **Manager**.
2. Run the `adb reverse tcp:12345 tcp:12345` command.
3. Keep the app open on any screen (e.g. Dashboard or Scanner Page).
4. Point your Android phone's camera at the employee's QR code.
5. The phone will beep/vibrate, scan the code instantly, and send it over USB.
6. The laptop application will detect the incoming scan immediately and pop open the authorization gate!
7. Enter the manager password on the laptop, and the employee's decrypted Form 16 will display!
