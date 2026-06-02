class ApiConstants {
  // Replace with your Ubuntu Gateway's actual IP address
  static const String gatewayIp = "192.168.100.130";
  static const String gatewayPort = "8000";

  static const String baseUrl = "http://$gatewayIp:$gatewayPort/api/v1";

  // Zero Trust Endpoints
  static const String knockEndpoint = "$baseUrl/knock";
  static const String revokeEndpoint = "$baseUrl/device/revoke";

  // Network Timeouts (Crucial for mobile environments)
  static const int connectionTimeoutSeconds = 15;
}
