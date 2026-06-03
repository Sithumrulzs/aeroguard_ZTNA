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

  /// Authenticate against the central auth server (backend_central_auth:8001).
  static Future<AuthResponse> login(String username, String password) async {
    try {
      // Login goes to central auth server (port 8001), not the gateway
      final uri = Uri.parse(ApiConstants.loginEndpoint);

      debugPrint('[*] Attempting login for user: $username');
      debugPrint('[*] Central Auth: ${uri.toString()}');

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

        // Central auth returns: {status, username, role, device_id, token}
        await _vault.write(key: _usernameKey, value: data['username'] ?? username);
        await _vault.write(key: _deviceIdKey, value: data['device_id'] ?? '');

        debugPrint('[+] LOGIN SUCCESSFUL: ${data['username']}');

        return AuthResponse(
          success: true,
          username: data['username'] ?? username,
          deviceId: data['device_id'] ?? '',
          message: 'Authentication successful',
        );
      } else if (response.statusCode == 401) {
        return AuthResponse(success: false, message: 'Invalid username or password');
      } else {
        return AuthResponse(success: false, message: 'Login failed: ${response.statusCode}');
      }
    } catch (_) {
      debugPrint('[-] Central auth unreachable. Check server connection.');
      return AuthResponse(
        success: false,
        message: 'Cannot reach authentication server. Check your connection.',
      );
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

