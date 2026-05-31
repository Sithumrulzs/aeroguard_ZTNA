class TelemetryPayload {
  final String deviceId;
  final String username;
  final String timestamp;
  final String signature;
  final Map<String, dynamic> telemetryData;

  TelemetryPayload({
    required this.deviceId,
    required this.username,
    required this.timestamp,
    required this.signature,
    required this.telemetryData,
  });

  // Converts the Dart object into a JSON-ready format for the HTTP request
  Map<String, dynamic> toJson() {
    return {
      "device_id": deviceId,
      "username": username,
      "timestamp": timestamp,
      "signature": signature,
      "telemetry": telemetryData,
    };
  }
}
