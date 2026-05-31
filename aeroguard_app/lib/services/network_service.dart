import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../config/environment_config.dart';
import 'enclave_service.dart';

class NetworkService {
  static final Uri knockUri = Uri.parse(EnvironmentConfig.knockEndpoint);

  /// Executes the Zero Trust network knock.
  /// The gateway has a 30-second anti-replay window; the app enforces a
  /// 10-second connection timeout so it fails fast on unreachable hosts.
  static Future<bool> sendAuthorizationKnock(String username) async {
    debugPrint('[*] Initiating Zero Trust Knock → ${knockUri.toString()}');

    final Map<String, dynamic>? payload =
        await EnclaveService.generateZeroTrustPayload(username);

    if (payload == null) {
      debugPrint('[-] Aborting: enclave payload generation failed.');
      return false;
    }

    // FastAPI TelemetryPayload requires a sibling 'telemetry' dict field.
    final body = <String, dynamic>{
      ...payload,
      'telemetry': <String, dynamic>{},
    };

    try {
      final response = await http
          .post(
            knockUri,
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
            },
            body: jsonEncode(body),
          )
          .timeout(
            Duration(seconds: EnvironmentConfig.connectionTimeoutSeconds),
          );

      if (response.statusCode == 200) {
        debugPrint('[+] KNOCK ACCEPTED — gateway open.');
        return true;
      }
      debugPrint(
        '[-] KNOCK DENIED — HTTP ${response.statusCode}: ${response.body}',
      );
      return false;
    } catch (e) {
      debugPrint('[-] NETWORK ERROR — could not reach gateway: $e');
      return false;
    }
  }
}
