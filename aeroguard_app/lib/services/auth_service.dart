import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;
import '../config/api_constants.dart';

/// Manages authentication with the AeroGuard backend
class AuthService {
  static const String _usernameKey = 'aeroguard_username';
  static const String _deviceIdKey = 'aeroguard_device_id_from_backend';

  static final _vault = const FlutterSecureStorage();

  // Offline test credentials — used only when the gateway is unreachable.
  static const Map<String, Map<String, String>> _offlineAdmins = {
    'sithum.it': {'password': 'It@kss69', 'device_id': 'admin_kss_jayamanna'},
    'dulshi.it': {'password': 'It@ds69',  'device_id': 'admin_ds_kalansooriya'},
    'yasas.it':  {'password': 'It@syl69', 'device_id': 'admin_syl_geeganage'},
    'dulen.it':  {'password': 'It@ads69', 'device_id': 'admin_ads_abayarathna'},
  };

  static AuthResponse _offlineLogin(String username, String password) {
    final admin = _offlineAdmins[username];
    if (admin == null || admin['password'] != password) {
      return AuthResponse(success: false, message: 'Invalid username or password');
    }
    debugPrint('[+] OFFLINE LOGIN: $username');
    return AuthResponse(
      success: true,
      username: username,
      deviceId: admin['device_id']!,
      message: 'Offline mode — gateway unreachable',
    );
  }

  /// Authenticate using credentials.
  /// Tries the live gateway first; falls back to offline credentials
  /// when the gateway is unreachable (no server / no network).
  static Future<AuthResponse> login(String username, String password) async {
    try {
      final uri = Uri.parse('${ApiConstants.baseUrl}/login');

      debugPrint('[*] Attempting login for user: $username');
      debugPrint('[*] Gateway: ${uri.toString()}');

      final response = await http
          .post(
            uri,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'username': username, 'password': password}),
          )
          .timeout(
            const Duration(seconds: 6),
            onTimeout: () => throw Exception('timeout'),
          );

      debugPrint('[*] Login response status: ${response.statusCode}');

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;

        await _vault.write(key: _usernameKey, value: data['username'] ?? username);
        await _vault.write(key: _deviceIdKey, value: data['device_id'] ?? '');

        debugPrint('[+] LOGIN SUCCESSFUL: ${data['username']}');

        return AuthResponse(
          success: true,
          username: data['username'] ?? username,
          deviceId: data['device_id'] ?? '',
          message: data['message'] ?? 'Authentication successful',
        );
      } else if (response.statusCode == 401) {
        return AuthResponse(success: false, message: 'Invalid username or password');
      } else {
        return AuthResponse(success: false, message: 'Login failed: ${response.statusCode}');
      }
    } catch (_) {
      // Gateway unreachable — fall back to offline credential check
      debugPrint('[!] Gateway unreachable — trying offline mode');
      final result = _offlineLogin(username, password);
      if (result.success) {
        await _vault.write(key: _usernameKey, value: result.username!);
        await _vault.write(key: _deviceIdKey, value: result.deviceId ?? '');
      }
      return result;
    }
  }

  /// Get currently authenticated username
  static Future<String?> getUsername() async {
    return await _vault.read(key: _usernameKey);
  }

  /// Get device_id from backend
  static Future<String?> getBackendDeviceId() async {
    return await _vault.read(key: _deviceIdKey);
  }

  /// Check if user is authenticated
  static Future<bool> isAuthenticated() async {
    final username = await getUsername();
    return username != null && username.isNotEmpty;
  }

  /// Logout and clear credentials
  static Future<void> logout() async {
    await _vault.delete(key: _usernameKey);
    await _vault.delete(key: _deviceIdKey);
    debugPrint('[+] User logged out');
  }
}

/// Response model for login
class AuthResponse {
  final bool success;
  final String? username;
  final String? deviceId;
  final String message;

  AuthResponse({
    required this.success,
    this.username,
    this.deviceId,
    required this.message,
  });
}

