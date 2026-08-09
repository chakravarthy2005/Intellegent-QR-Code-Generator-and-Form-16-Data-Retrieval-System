package com.example.qrscanner

import android.util.Base64
import java.security.MessageDigest
import javax.crypto.Cipher
import javax.crypto.Mac
import javax.crypto.SecretKeyFactory
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.PBEKeySpec
import javax.crypto.spec.SecretKeySpec

object CryptoHelper {

    /**
     * Derive a key from a password using PBKDF2WithHmacSHA512.
     */
    fun deriveWrappingKey(password: String, salt: ByteArray): ByteArray {
        val spec = PBEKeySpec(password.toCharArray(), salt, 200000, 256)
        val factory = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA512")
        return factory.generateSecret(spec).encoded
    }

    /**
     * Decrypt the app_secret payload using the manager password.
     */
    fun decryptAppSecret(saltB64: String, nonceB64: String, ciphertextB64: String, password: String): ByteArray {
        val salt = Base64.decode(saltB64, Base64.DEFAULT)
        val nonce = Base64.decode(nonceB64, Base64.DEFAULT)
        val ciphertext = Base64.decode(ciphertextB64, Base64.DEFAULT)

        val wrappingKey = deriveWrappingKey(password, salt)
        val keySpec = SecretKeySpec(wrappingKey, "AES")

        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val gcmSpec = GCMParameterSpec(128, nonce)
        cipher.init(Cipher.DECRYPT_MODE, keySpec, gcmSpec)
        return cipher.doFinal(ciphertext)
    }

    /**
     * Derive the system key from the app_secret.
     * Python equivalent:
     * system_key = hashlib.sha256(app_secret[:32] + b"system_encryption_key").digest()
     */
    fun deriveSystemKey(appSecret: ByteArray): ByteArray {
        val prefix = appSecret.copyOfRange(0, 32)
        val label = "system_encryption_key".toByteArray(Charsets.UTF_8)
        val combined = prefix + label
        val md = MessageDigest.getInstance("SHA-256")
        return md.digest(combined)
    }

    /**
     * HKDF Extract and Expand for Triple AES-256-GCM.
     */
    private fun hkdfExpand(prk: ByteArray, info: ByteArray, length: Int): ByteArray {
        // T(1) = HMAC-SHA512(PRK, info | 0x01)
        val mac = Mac.getInstance("HmacSHA512")
        mac.init(SecretKeySpec(prk, "HmacSHA512"))
        val combined = info + byteArrayOf(0x01.toByte())
        val t1 = mac.doFinal(combined)
        return t1.copyOfRange(0, length)
    }

    private fun hkdfExtract(ikm: ByteArray): ByteArray {
        val zeros = ByteArray(64) // HMAC-SHA512 output size is 64 bytes
        val mac = Mac.getInstance("HmacSHA512")
        mac.init(SecretKeySpec(zeros, "HmacSHA512"))
        return mac.doFinal(ikm)
    }

    private fun deriveThreeKeys(systemKey: ByteArray): Triple<ByteArray, ByteArray, ByteArray> {
        val infoStrings = listOf("aes256_layer_1_key", "aes256_layer_2_key", "aes256_layer_3_key")
        val prk = hkdfExtract(systemKey)
        val keys = infoStrings.map { info ->
            hkdfExpand(prk, info.toByteArray(Charsets.UTF_8), 32)
        }
        return Triple(keys[0], keys[1], keys[2])
    }

    /**
     * Decrypt data encrypted using the Triple AES-256-GCM scheme.
     * Python equivalent:
     * decrypt_data(ciphertext, system_key)
     */
    fun decryptData(ciphertextB64: String, systemKey: ByteArray): String {
        if (ciphertextB64.isEmpty()) return ""
        try {
            val (k1, k2, k3) = deriveThreeKeys(systemKey)
            val data = Base64.decode(ciphertextB64, Base64.DEFAULT)

            // Layer 3 Decryption
            val nonce3 = data.copyOfRange(0, 12)
            val enc3 = data.copyOfRange(12, data.size)
            val blob2 = decryptAesGcm(enc3, k3, nonce3)

            // Layer 2 Decryption
            val nonce2 = blob2.copyOfRange(0, 12)
            val enc2 = blob2.copyOfRange(12, blob2.size)
            val blob1 = decryptAesGcm(enc2, k2, nonce2)

            // Layer 1 Decryption
            val nonce1 = blob1.copyOfRange(0, 12)
            val enc1 = blob1.copyOfRange(12, blob1.size)
            val plaintextBytes = decryptAesGcm(enc1, k1, nonce1)

            return String(plaintextBytes, Charsets.UTF_8)
        } catch (e: Exception) {
            return "[Decryption Error: ${e.message}]"
        }
    }

    private fun decryptAesGcm(ciphertext: ByteArray, key: ByteArray, nonce: ByteArray): ByteArray {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        val keySpec = SecretKeySpec(key, "AES")
        val gcmSpec = GCMParameterSpec(128, nonce)
        cipher.init(Cipher.DECRYPT_MODE, keySpec, gcmSpec)
        return cipher.doFinal(ciphertext)
    }
}
