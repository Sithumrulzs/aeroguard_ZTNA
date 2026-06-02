import 'package:flutter/foundation.dart';
import 'package:local_auth/local_auth.dart';

class BiometricService {
  static final LocalAuthentication _auth = LocalAuthentication();

  /// Returns true if the device has a biometric sensor AND has enrolled fingers.
  static Future<bool> isAvailable() async {
    try {
      final bool canCheck = await _auth.canCheckBiometrics;
      if (!canCheck) return false;
      final List<BiometricType> available = await _auth.getAvailableBiometrics();
      return available.isNotEmpty;
    } catch (e) {
      debugPrint('[-] Biometric availability check failed: $e');
      return false;
    }
  }

  static Future<bool> authenticateAdmin() async {
    try {
      // 1. Check if the device actually has hardware support (Fingerprint/FaceID)
      final bool canAuthenticateWithBiometrics = await _auth.canCheckBiometrics;
      final bool canAuthenticate = canAuthenticateWithBiometrics || await _auth.isDeviceSupported();

      if (!canAuthenticate) {
        debugPrint("[-] Hardware missing: No biometric sensor detected or configured.");
        return false;
      }

      // 2. Trigger the OS-level prompt
      final bool didAuthenticate = await _auth.authenticate(
        localizedReason: 'AeroGuard ZTNA: Verify identity to unlock Datacenter Gateway.',
        options: const AuthenticationOptions(
          biometricOnly: true,
          stickyAuth: true,
          useErrorDialogs: true,
        ),
      );

      if (didAuthenticate) {
        debugPrint("[+] Biometric Signature Confirmed.");
      } else {
        debugPrint("[!] Biometric Verification Failed/Cancelled.");
      }

      return didAuthenticate;

    } catch (e) {
      debugPrint("[-] Critical Biometric Error: $e");
      return false;
    }
  }
}
