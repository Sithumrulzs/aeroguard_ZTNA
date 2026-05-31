import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:qr_flutter/qr_flutter.dart';
import '../config/transitions.dart';
import '../services/enclave_service.dart';
import 'sign_in_page.dart';

class DeviceIdentityScreen extends StatefulWidget {
  const DeviceIdentityScreen({super.key});

  @override
  State<DeviceIdentityScreen> createState() => _DeviceIdentityScreenState();
}

class _DeviceIdentityScreenState extends State<DeviceIdentityScreen>
    with SingleTickerProviderStateMixin {
  String? _deviceId;
  String? _publicKey;
  bool _loadingIdentity = true;

  late AnimationController _entryCtrl;
  late Animation<double> _fadeAnim;
  late Animation<Offset> _slideAnim;

  @override
  void initState() {
    super.initState();
    _entryCtrl = AnimationController(
      duration: const Duration(milliseconds: 600),
      vsync: this,
    )..forward();
    _fadeAnim = CurvedAnimation(parent: _entryCtrl, curve: Curves.easeOut);
    _slideAnim = Tween<Offset>(
      begin: const Offset(0, 0.04),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _entryCtrl, curve: Curves.easeOutCubic));
    _loadIdentity();
  }

  @override
  void dispose() {
    _entryCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadIdentity() async {
    final deviceId = await EnclaveService.getDeviceId();
    final publicKey = await EnclaveService.getPublicKey();

    if (!mounted) return;
    setState(() {
      _deviceId = deviceId;
      _publicKey = publicKey ?? 'Not available yet';
      _loadingIdentity = false;
    });
  }

  void _copyToClipboard(String text) {
    Clipboard.setData(ClipboardData(text: text));
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text(
          'Key copied to clipboard',
          style: TextStyle(
            color: Colors.black,
            fontWeight: FontWeight.w600,
            fontSize: 13,
          ),
        ),
        backgroundColor: const Color(0xFF00C3FF),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        margin: const EdgeInsets.all(16),
        duration: const Duration(seconds: 2),
      ),
    );
  }

  void _revokeDevice() {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF0D1421),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const Text(
          'REVOKE DEVICE?',
          style: TextStyle(
            color: Color(0xFFEF4444),
            fontSize: 15,
            letterSpacing: 2.0,
            fontWeight: FontWeight.bold,
          ),
        ),
        content: const Text(
          'This will permanently destroy all hardware keys. You will need to re-provision this device.',
          style: TextStyle(color: Color(0xFF94A3B8), fontSize: 13, height: 1.5),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text(
              'CANCEL',
              style: TextStyle(color: Color(0xFF475569), letterSpacing: 1.0),
            ),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(ctx);
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: const Text(
                    'DEVICE REVOKED — Keys destroyed',
                    style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.w600,
                      fontSize: 13,
                    ),
                  ),
                  backgroundColor: const Color(0xFFEF4444),
                  behavior: SnackBarBehavior.floating,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                  margin: const EdgeInsets.all(16),
                ),
              );
              Navigator.pushReplacement(
                context,
                premiumRoute(const SignInPage()),
              );
            },
            child: const Text(
              'REVOKE',
              style: TextStyle(
                color: Color(0xFFEF4444),
                letterSpacing: 1.0,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF050810),
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFF050810), Color(0xFF0A1628)],
          ),
        ),
        child: SafeArea(
          child: FadeTransition(
            opacity: _fadeAnim,
            child: SlideTransition(
              position: _slideAnim,
              child: Column(
                children: [
                  // ── AppBar ──────────────────────────────────────
                  Padding(
                    padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
                    child: Row(
                      children: [
                        GestureDetector(
                          onTap: () => Navigator.pop(context),
                          child: Container(
                            padding: const EdgeInsets.all(9),
                            decoration: BoxDecoration(
                              color: const Color(0xFF0D1421),
                              borderRadius: BorderRadius.circular(10),
                              border: Border.all(
                                color: Colors.white.withValues(alpha: 0.07),
                              ),
                            ),
                            child: const Icon(
                              Icons.arrow_back_ios_new,
                              color: Color(0xFF00C3FF),
                              size: 15,
                            ),
                          ),
                        ),
                        const SizedBox(width: 16),
                        const Text(
                          'HARDWARE IDENTITY',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 14,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 3.0,
                          ),
                        ),
                      ],
                    ),
                  ),

                  // ── Scrollable content ──────────────────────────
                  Expanded(
                    child: SingleChildScrollView(
                      padding: const EdgeInsets.all(24),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Register this public key with the gateway to authorize Zero Trust access.',
                            style: TextStyle(
                              color: const Color(
                                0xFF94A3B8,
                              ).withValues(alpha: 0.8),
                              fontSize: 12,
                              height: 1.6,
                              letterSpacing: 0.2,
                            ),
                          ),
                          const SizedBox(height: 28),

                          // Device ID card
                          _buildPanel(
                            title: 'DEVICE ID',
                            icon: Icons.devices,
                            child: Container(
                              width: double.infinity,
                              padding: const EdgeInsets.symmetric(
                                horizontal: 16,
                                vertical: 14,
                              ),
                              decoration: BoxDecoration(
                                color: const Color(0xFF080E1A),
                                borderRadius: BorderRadius.circular(10),
                                border: Border.all(
                                  color: Colors.white.withValues(alpha: 0.07),
                                ),
                              ),
                              child: Text(
                                _loadingIdentity
                                    ? 'Loading device ID...'
                                    : (_deviceId ?? 'Device ID unavailable'),
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 14,
                                  fontFamily: 'monospace',
                                  letterSpacing: 0.5,
                                ),
                              ),
                            ),
                          ),

                          const SizedBox(height: 16),

                          // Public key card
                          _buildPanel(
                            title: 'ECDSA PUBLIC KEY',
                            icon: Icons.key,
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Container(
                                  width: double.infinity,
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 16,
                                    vertical: 14,
                                  ),
                                  decoration: BoxDecoration(
                                    color: const Color(0xFF080E1A),
                                    borderRadius: BorderRadius.circular(10),
                                    border: Border.all(
                                      color: Colors.white.withValues(
                                        alpha: 0.07,
                                      ),
                                    ),
                                  ),
                                  child: Text(
                                    _loadingIdentity
                                        ? 'Loading public key...'
                                        : (_publicKey ??
                                              'Public key unavailable'),
                                    style: const TextStyle(
                                      color: Color(0xFF94A3B8),
                                      fontFamily: 'monospace',
                                      fontSize: 12,
                                      height: 1.5,
                                    ),
                                  ),
                                ),
                                const SizedBox(height: 12),
                                GestureDetector(
                                  onTap: _loadingIdentity || _publicKey == null
                                      ? null
                                      : () => _copyToClipboard(_publicKey!),
                                  child: Container(
                                    padding: const EdgeInsets.symmetric(
                                      horizontal: 14,
                                      vertical: 10,
                                    ),
                                    decoration: BoxDecoration(
                                      borderRadius: BorderRadius.circular(10),
                                      border: Border.all(
                                        color: const Color(
                                          0xFF00C3FF,
                                        ).withValues(alpha: 0.35),
                                      ),
                                      color: const Color(
                                        0xFF00C3FF,
                                      ).withValues(alpha: 0.05),
                                    ),
                                    child: const Row(
                                      mainAxisSize: MainAxisSize.min,
                                      children: [
                                        Icon(
                                          Icons.copy_outlined,
                                          color: Color(0xFF00C3FF),
                                          size: 14,
                                        ),
                                        SizedBox(width: 8),
                                        Text(
                                          'COPY KEY',
                                          style: TextStyle(
                                            color: Color(0xFF00C3FF),
                                            fontSize: 11,
                                            letterSpacing: 1.5,
                                            fontWeight: FontWeight.w600,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),

                          const SizedBox(height: 16),

                          // QR code card
                          _buildPanel(
                            title: 'GATEWAY QR CODE',
                            icon: Icons.qr_code_2,
                            child: Center(
                              child: Container(
                                padding: const EdgeInsets.all(14),
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(14),
                                  boxShadow: [
                                    BoxShadow(
                                      color: const Color(
                                        0xFF00C3FF,
                                      ).withValues(alpha: 0.18),
                                      blurRadius: 24,
                                      spreadRadius: 2,
                                    ),
                                  ],
                                ),
                                child: QrImageView(
                                  data: _publicKey ?? '',
                                  version: QrVersions.auto,
                                  size: 160,
                                  backgroundColor: Colors.white,
                                ),
                              ),
                            ),
                          ),

                          const SizedBox(height: 28),

                          // Kill switch
                          GestureDetector(
                            onTap: _revokeDevice,
                            child: Container(
                              height: 54,
                              width: double.infinity,
                              decoration: BoxDecoration(
                                borderRadius: BorderRadius.circular(14),
                                border: Border.all(
                                  color: const Color(
                                    0xFFEF4444,
                                  ).withValues(alpha: 0.5),
                                ),
                                color: const Color(
                                  0xFFEF4444,
                                ).withValues(alpha: 0.06),
                              ),
                              child: const Row(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(
                                    Icons.delete_forever_outlined,
                                    color: Color(0xFFEF4444),
                                    size: 18,
                                  ),
                                  SizedBox(width: 10),
                                  Text(
                                    'REVOKE THIS DEVICE',
                                    style: TextStyle(
                                      color: Color(0xFFEF4444),
                                      fontSize: 13,
                                      fontWeight: FontWeight.w700,
                                      letterSpacing: 2.0,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),

                          const SizedBox(height: 8),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildPanel({
    required String title,
    required IconData icon,
    required Widget child,
  }) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF0D1421),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: const Color(0xFF00C3FF).withValues(alpha: 0.1),
        ),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF00C3FF).withValues(alpha: 0.03),
            blurRadius: 20,
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(7),
                decoration: BoxDecoration(
                  color: const Color(0xFF00C3FF).withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(icon, color: const Color(0xFF00C3FF), size: 14),
              ),
              const SizedBox(width: 10),
              Text(
                title,
                style: const TextStyle(
                  color: Color(0xFF94A3B8),
                  fontSize: 10,
                  letterSpacing: 2.0,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          Divider(color: Colors.white.withValues(alpha: 0.05), height: 22),
          child,
        ],
      ),
    );
  }
}
