/// Single source of truth for all environment-dependent values.
///
/// Values are injected at build/run time via --dart-define or
/// --dart-define-from-file. Nothing is ever hardcoded here.
///
/// Inject with:
///   flutter run --dart-define-from-file=.dart_defines/local.json
///   flutter run --dart-define=GATEWAY_IP=192.168.1.45
class EnvironmentConfig {
  // ── Gateway coordinates ───────────────────────────────────────────────────
  static const String gatewayIp = String.fromEnvironment(
    'GATEWAY_IP',
    defaultValue: '127.0.0.1', // safe fallback: localhost web testing
  );

  static const String gatewayPort = String.fromEnvironment(
    'GATEWAY_PORT',
    defaultValue: '8000',
  );

  // ── Derived URLs (computed from above — never hardcoded) ──────────────────
  static const String baseUrl = 'http://$gatewayIp:$gatewayPort/api/v1';
  static const String knockEndpoint  = '$baseUrl/knock';
  static const String vendorEndpoint = '$baseUrl/vendor_knock';
  static const String revokeEndpoint = '$baseUrl/device/revoke';

  // ── Timeouts ──────────────────────────────────────────────────────────────
  static const int connectionTimeoutSeconds = 10;

  // ── Debug helper ─────────────────────────────────────────────────────────
  static void printActive() {
    // ignore: avoid_print
    print('┌─ EnvironmentConfig ─────────────────────────');
    // ignore: avoid_print
    print('│  Gateway : $gatewayIp:$gatewayPort');
    // ignore: avoid_print
    print('│  Knock   : $knockEndpoint');
    // ignore: avoid_print
    print('└─────────────────────────────────────────────');
  }
}
