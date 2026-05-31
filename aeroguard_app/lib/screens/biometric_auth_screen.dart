import 'package:flutter/material.dart';
import '../services/biometric_service.dart';
import '../config/transitions.dart';
import 'admin_dashboard.dart';
import 'sign_in_page.dart';

enum _AuthStatus { idle, scanning, success, failed }

class BiometricAuthScreen extends StatefulWidget {
  const BiometricAuthScreen({super.key});

  @override
  State<BiometricAuthScreen> createState() => _BiometricAuthScreenState();
}

class _BiometricAuthScreenState extends State<BiometricAuthScreen>
    with TickerProviderStateMixin {
  late AnimationController _pulseCtrl;
  late AnimationController _glowCtrl;
  late Animation<double> _pulseScale;
  late Animation<double> _pulseOpacity;

  _AuthStatus _status = _AuthStatus.idle;

  @override
  void initState() {
    super.initState();

    _pulseCtrl = AnimationController(
        duration: const Duration(milliseconds: 1800), vsync: this)
      ..repeat(reverse: true);
    _glowCtrl = AnimationController(
        duration: const Duration(milliseconds: 1100), vsync: this)
      ..repeat(reverse: true);

    _pulseScale = Tween<double>(begin: 0.94, end: 1.06).animate(
        CurvedAnimation(parent: _pulseCtrl, curve: Curves.easeInOut));
    _pulseOpacity = Tween<double>(begin: 0.3, end: 0.85).animate(
        CurvedAnimation(parent: _pulseCtrl, curve: Curves.easeInOut));

    Future.delayed(const Duration(milliseconds: 600), _triggerBiometric);
  }

  @override
  void dispose() {
    _pulseCtrl.dispose();
    _glowCtrl.dispose();
    super.dispose();
  }

  Future<void> _triggerBiometric() async {
    if (!mounted) return;
    setState(() => _status = _AuthStatus.scanning);

    final success = await BiometricService.authenticateAdmin();
    if (!mounted) return;

    if (success) {
      setState(() => _status = _AuthStatus.success);
      await Future.delayed(const Duration(milliseconds: 800));
      if (mounted) {
        Navigator.pushReplacement(
            context, premiumRoute(const AdminDashboard()));
      }
    } else {
      setState(() => _status = _AuthStatus.failed);
    }
  }

  void _goToManualLogin() {
    // Ignore tap while navigating away on success
    if (_status == _AuthStatus.success) return;
    Navigator.pushReplacement(context, slideLeftRoute(const SignInPage()));
  }

  Color get _color => switch (_status) {
        _AuthStatus.success => const Color(0xFF10B981),
        _AuthStatus.failed  => const Color(0xFFEF4444),
        _                   => const Color(0xFF00C3FF),
      };

  String get _statusLabel => switch (_status) {
        _AuthStatus.idle     => 'Touch sensor to authenticate',
        _AuthStatus.scanning => 'Scanning...',
        _AuthStatus.success  => 'Authentication successful',
        _AuthStatus.failed   => 'Authentication failed',
      };

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      // Single tap anywhere navigates to manual login
      onTap: _goToManualLogin,
      behavior: HitTestBehavior.opaque,
      child: Scaffold(
        backgroundColor: const Color(0xFF050810),
        body: Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [Color(0xFF050810), Color(0xFF0A1628)],
            ),
          ),
          child: SafeArea(
            child: Column(
              children: [
                // Subtle brand mark at top
                Padding(
                  padding: const EdgeInsets.only(top: 28),
                  child: Text(
                    'AEROGUARD',
                    style: TextStyle(
                      color: const Color(0xFF475569).withValues(alpha: 0.5),
                      fontSize: 10,
                      letterSpacing: 4.5,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),

                // Top spacer — pushes fingerprint to ~78% down the screen,
                // matching where in-display scanners sit on most phones
                const Spacer(flex: 7),

                // Fingerprint badge
                _FingerprintBadge(
                  color: _color,
                  status: _status,
                  pulseScale: _pulseScale,
                  pulseOpacity: _pulseOpacity,
                  glowAnim: _glowCtrl,
                ),

                const SizedBox(height: 28),

                // Status text
                AnimatedSwitcher(
                  duration: const Duration(milliseconds: 350),
                  transitionBuilder: (child, anim) => FadeTransition(
                    opacity: anim,
                    child: SlideTransition(
                      position: Tween<Offset>(
                        begin: const Offset(0, 0.25),
                        end: Offset.zero,
                      ).animate(anim),
                      child: child,
                    ),
                  ),
                  child: Text(
                    _statusLabel,
                    key: ValueKey(_status),
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: _color.withValues(alpha: 0.65),
                      fontSize: 13,
                      letterSpacing: 0.3,
                      fontWeight: FontWeight.w400,
                    ),
                  ),
                ),

                // Bottom spacer
                const Spacer(flex: 2),

                // Tap hint
                Padding(
                  padding: const EdgeInsets.only(bottom: 38),
                  child: Text(
                    'tap anywhere to sign in manually',
                    style: TextStyle(
                      color: const Color(0xFF475569).withValues(alpha: 0.4),
                      fontSize: 11,
                      letterSpacing: 0.5,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// ── Fingerprint badge ────────────────────────────────────────────────────────

class _FingerprintBadge extends StatelessWidget {
  final Color color;
  final _AuthStatus status;
  final Animation<double> pulseScale;
  final Animation<double> pulseOpacity;
  final AnimationController glowAnim;

  const _FingerprintBadge({
    required this.color,
    required this.status,
    required this.pulseScale,
    required this.pulseOpacity,
    required this.glowAnim,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 156,
      width: 156,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Outermost pulsing ring
          AnimatedBuilder(
            animation: pulseScale,
            builder: (context, _) => Transform.scale(
              scale: pulseScale.value,
              child: Container(
                height: 148,
                width: 148,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(
                    color:
                        color.withValues(alpha: pulseOpacity.value * 0.18),
                    width: 1,
                  ),
                ),
              ),
            ),
          ),
          // Middle ring with breathing glow
          AnimatedBuilder(
            animation: glowAnim,
            builder: (context, _) => Container(
              height: 114,
              width: 114,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                border: Border.all(
                  color: color.withValues(
                      alpha: 0.12 + glowAnim.value * 0.16),
                  width: 1.5,
                ),
                boxShadow: [
                  BoxShadow(
                    color: color.withValues(
                        alpha: 0.04 + glowAnim.value * 0.1),
                    blurRadius: 20,
                    spreadRadius: 2,
                  ),
                ],
              ),
            ),
          ),
          // Inner glass circle
          Container(
            height: 84,
            width: 84,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: color.withValues(alpha: 0.06),
              border: Border.all(
                color: color.withValues(alpha: 0.45),
                width: 1.5,
              ),
            ),
          ),
          // Icon — fingerprint always, color shifts on state change
          AnimatedBuilder(
            animation: pulseOpacity,
            builder: (context, _) => Opacity(
              opacity: 0.55 + pulseOpacity.value * 0.45,
              child: Icon(Icons.fingerprint, size: 46, color: color),
            ),
          ),
        ],
      ),
    );
  }
}
