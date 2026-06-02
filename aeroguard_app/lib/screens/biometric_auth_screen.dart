import 'package:flutter/material.dart';
import '../services/biometric_service.dart';
import '../config/transitions.dart';
import 'admin_dashboard.dart';
import 'sign_in_page.dart';

enum _AuthStatus { idle, scanning, success, failed, unavailable }

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

    // Check hardware availability first
    final available = await BiometricService.isAvailable();
    if (!mounted) return;

    if (!available) {
      // No fingerprint sensor or none enrolled — skip to login
      setState(() => _status = _AuthStatus.unavailable);
      await Future.delayed(const Duration(milliseconds: 1200));
      if (mounted) {
        Navigator.pushReplacement(context, slideLeftRoute(const SignInPage()));
      }
      return;
    }

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
    if (_status == _AuthStatus.success || _status == _AuthStatus.unavailable) {
      return;
    }
    Navigator.pushReplacement(context, slideLeftRoute(const SignInPage()));
  }

  Color get _color => switch (_status) {
        _AuthStatus.success     => const Color(0xFF10B981),
        _AuthStatus.failed      => const Color(0xFFEF4444),
        _AuthStatus.unavailable => const Color(0xFF475569),
        _                       => const Color(0xFF00C3FF),
      };

  String get _statusLabel => switch (_status) {
        _AuthStatus.idle        => 'Touch sensor to authenticate',
        _AuthStatus.scanning    => 'Scanning...',
        _AuthStatus.success     => 'Authentication successful',
        _AuthStatus.failed      => 'Authentication failed — tap to retry',
        _AuthStatus.unavailable => 'No biometric found — redirecting...',
      };

  @override
  Widget build(BuildContext context) {
    final size   = MediaQuery.of(context).size;
    final height = size.height;

    // Badge scales proportionally to screen height
    final badgeOuter  = height * 0.185;
    final badgeMiddle = height * 0.142;
    final badgeInner  = height * 0.105;
    final iconSize    = height * 0.058;

    return GestureDetector(
      onTap: _status == _AuthStatus.failed
          ? _triggerBiometric   // tap badge area retries biometric
          : _goToManualLogin,
      behavior: HitTestBehavior.opaque,
      child: Scaffold(
        backgroundColor: const Color(0xFF050810),
        body: SizedBox.expand(
          child: Container(
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
                  // Brand mark
                  Padding(
                    padding: EdgeInsets.only(top: height * 0.034),
                    child: Text(
                      'AEROGUARD',
                      style: TextStyle(
                        color: const Color(0xFF475569).withValues(alpha: 0.5),
                        fontSize: height * 0.013,
                        letterSpacing: 4.5,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),

                  const Spacer(flex: 7),

                  // Fingerprint badge — tappable to retry on failure
                  _FingerprintBadge(
                    color:        _color,
                    status:       _status,
                    pulseScale:   _pulseScale,
                    pulseOpacity: _pulseOpacity,
                    glowAnim:     _glowCtrl,
                    outerSize:    badgeOuter,
                    middleSize:   badgeMiddle,
                    innerSize:    badgeInner,
                    iconSize:     iconSize,
                  ),

                  SizedBox(height: height * 0.034),

                  // Status label
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
                        color: _color.withValues(alpha: 0.75),
                        fontSize: height * 0.016,
                        letterSpacing: 0.3,
                        fontWeight: FontWeight.w400,
                      ),
                    ),
                  ),

                  // Retry chip — only visible on failure
                  AnimatedSize(
                    duration: const Duration(milliseconds: 250),
                    child: _status == _AuthStatus.failed
                        ? Padding(
                            padding: EdgeInsets.only(top: height * 0.018),
                            child: GestureDetector(
                              onTap: _triggerBiometric,
                              child: Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 20, vertical: 10),
                                decoration: BoxDecoration(
                                  borderRadius: BorderRadius.circular(30),
                                  border: Border.all(
                                    color: const Color(0xFFEF4444)
                                        .withValues(alpha: 0.4),
                                  ),
                                  color: const Color(0xFFEF4444)
                                      .withValues(alpha: 0.06),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    const Icon(Icons.refresh,
                                        color: Color(0xFFEF4444), size: 14),
                                    const SizedBox(width: 8),
                                    Text(
                                      'TRY AGAIN',
                                      style: TextStyle(
                                        color: const Color(0xFFEF4444),
                                        fontSize: height * 0.013,
                                        fontWeight: FontWeight.w700,
                                        letterSpacing: 1.5,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          )
                        : const SizedBox.shrink(),
                  ),

                  const Spacer(flex: 2),

                  // Manual login hint
                  Padding(
                    padding: EdgeInsets.only(bottom: height * 0.046),
                    child: Text(
                      _status == _AuthStatus.failed
                          ? 'or tap anywhere to sign in manually'
                          : 'tap anywhere to sign in manually',
                      style: TextStyle(
                        color: const Color(0xFF475569).withValues(alpha: 0.4),
                        fontSize: height * 0.013,
                        letterSpacing: 0.5,
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
}

// ── Fingerprint badge ─────────────────────────────────────────────────────────

class _FingerprintBadge extends StatelessWidget {
  final Color color;
  final _AuthStatus status;
  final Animation<double> pulseScale;
  final Animation<double> pulseOpacity;
  final AnimationController glowAnim;
  final double outerSize;
  final double middleSize;
  final double innerSize;
  final double iconSize;

  const _FingerprintBadge({
    required this.color,
    required this.status,
    required this.pulseScale,
    required this.pulseOpacity,
    required this.glowAnim,
    required this.outerSize,
    required this.middleSize,
    required this.innerSize,
    required this.iconSize,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: outerSize,
      width:  outerSize,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Outermost pulsing ring
          AnimatedBuilder(
            animation: pulseScale,
            builder: (context, _) => Transform.scale(
              scale: pulseScale.value,
              child: Container(
                height: outerSize * 0.95,
                width:  outerSize * 0.95,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: color.withValues(
                        alpha: pulseOpacity.value * 0.18),
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
              height: middleSize,
              width:  middleSize,
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
            height: innerSize,
            width:  innerSize,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: color.withValues(alpha: 0.06),
              border: Border.all(
                color: color.withValues(alpha: 0.45),
                width: 1.5,
              ),
            ),
          ),
          // Fingerprint icon
          AnimatedBuilder(
            animation: pulseOpacity,
            builder: (context, _) => Opacity(
              opacity: 0.55 + pulseOpacity.value * 0.45,
              child: Icon(
                status == _AuthStatus.success
                    ? Icons.check_circle_outline
                    : Icons.fingerprint,
                size:  iconSize,
                color: color,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
