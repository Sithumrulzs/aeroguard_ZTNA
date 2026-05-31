import 'package:flutter/material.dart';
import '../widgets/vendor_countdown_timer.dart';
import '../config/transitions.dart';
import 'sign_in_page.dart';

class VendorDashboard extends StatefulWidget {
  final String vendorName;
  final String company;
  final int sessionHours;

  const VendorDashboard({
    super.key,
    required this.vendorName,
    required this.company,
    required this.sessionHours,
  });

  @override
  State<VendorDashboard> createState() => _VendorDashboardState();
}

class _VendorDashboardState extends State<VendorDashboard> {
  bool _isKnocking = false;

  Future<void> _handleVendorKnock() async {
    setState(() => _isKnocking = true);
    await Future.delayed(const Duration(milliseconds: 1500));
    setState(() => _isKnocking = false);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: const Text(
          'TUNNEL AUTHORIZED — Vendor session active',
          style: TextStyle(
            color: Colors.black,
            fontWeight: FontWeight.w600,
            fontSize: 13,
            letterSpacing: 0.3,
          ),
        ),
        backgroundColor: Colors.orangeAccent,
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        margin: const EdgeInsets.all(16),
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
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // ── Header bar ────────────────────────────────────
                Padding(
                  padding: const EdgeInsets.only(top: 20, bottom: 28),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: Colors.orangeAccent.withValues(alpha: 0.08),
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(
                              color:
                                  Colors.orangeAccent.withValues(alpha: 0.35)),
                        ),
                        child: const Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.warning_amber_rounded,
                                color: Colors.orangeAccent, size: 14),
                            SizedBox(width: 6),
                            Text(
                              'RESTRICTED ACCESS',
                              style: TextStyle(
                                color: Colors.orangeAccent,
                                fontSize: 10,
                                fontWeight: FontWeight.w700,
                                letterSpacing: 1.5,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const Spacer(),
                      GestureDetector(
                        onTap: () => Navigator.pushReplacement(
                            context, premiumRoute(const SignInPage())),
                        child: Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: const Color(0xFF0D1421),
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(
                                color: Colors.white.withValues(alpha: 0.07)),
                          ),
                          child: const Icon(Icons.logout,
                              color: Color(0xFF475569), size: 16),
                        ),
                      ),
                    ],
                  ),
                ),

                // ── Vendor identity card ──────────────────────────
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0D1421),
                    borderRadius: BorderRadius.circular(18),
                    border: Border.all(
                        color: Colors.orangeAccent.withValues(alpha: 0.2)),
                  ),
                  child: Row(
                    children: [
                      Container(
                        height: 46,
                        width: 46,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: Colors.orangeAccent.withValues(alpha: 0.1),
                          border: Border.all(
                              color:
                                  Colors.orangeAccent.withValues(alpha: 0.3)),
                        ),
                        child: const Center(
                          child: Icon(Icons.person_outline,
                              color: Colors.orangeAccent, size: 22),
                        ),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              widget.vendorName,
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 15,
                                fontWeight: FontWeight.w700,
                              ),
                              overflow: TextOverflow.ellipsis,
                            ),
                            const SizedBox(height: 2),
                            Text(
                              widget.company,
                              style: TextStyle(
                                color: const Color(0xFF94A3B8)
                                    .withValues(alpha: 0.8),
                                fontSize: 12,
                              ),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ],
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 10, vertical: 5),
                        decoration: BoxDecoration(
                          color: Colors.orangeAccent.withValues(alpha: 0.1),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(
                              color:
                                  Colors.orangeAccent.withValues(alpha: 0.3)),
                        ),
                        child: Text(
                          '${widget.sessionHours}H',
                          style: const TextStyle(
                            color: Colors.orangeAccent,
                            fontSize: 11,
                            fontWeight: FontWeight.w800,
                            letterSpacing: 1.0,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 16),

                // ── Session timer card ────────────────────────────
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0D1421),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(
                        color: Colors.orangeAccent.withValues(alpha: 0.14)),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.orangeAccent.withValues(alpha: 0.04),
                        blurRadius: 24,
                      ),
                    ],
                  ),
                  child: Column(
                    children: [
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(7),
                            decoration: BoxDecoration(
                              color:
                                  Colors.orangeAccent.withValues(alpha: 0.1),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: const Icon(Icons.timer_outlined,
                                color: Colors.orangeAccent, size: 15),
                          ),
                          const SizedBox(width: 12),
                          const Text(
                            'SESSION TIMER',
                            style: TextStyle(
                              color: Color(0xFF94A3B8),
                              fontSize: 11,
                              letterSpacing: 2.0,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          const Spacer(),
                          Text(
                            '${widget.sessionHours}h granted',
                            style: TextStyle(
                              color: Colors.orangeAccent.withValues(alpha: 0.6),
                              fontSize: 10,
                              letterSpacing: 0.3,
                            ),
                          ),
                        ],
                      ),
                      Divider(
                          color: Colors.white.withValues(alpha: 0.05),
                          height: 24),
                      VendorCountdownTimer(
                        initialSeconds: widget.sessionHours * 3600,
                        onExpire: () {
                          if (mounted) {
                            Navigator.pushReplacement(
                                context, premiumRoute(const SignInPage()));
                          }
                        },
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 16),

                // ── Info chips ────────────────────────────────────
                Row(
                  children: [
                    _InfoChip(
                        icon: Icons.visibility_outlined, label: 'MONITORED'),
                    const SizedBox(width: 10),
                    _InfoChip(
                        icon: Icons.save_outlined, label: 'LOGGED'),
                    const SizedBox(width: 10),
                    _InfoChip(
                        icon: Icons.access_time, label: 'JIT ACCESS'),
                  ],
                ),

                const Spacer(),

                // ── Authorize button ──────────────────────────────
                GestureDetector(
                  onTap: _isKnocking ? null : _handleVendorKnock,
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    height: 56,
                    width: double.infinity,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(14),
                      gradient: _isKnocking
                          ? LinearGradient(colors: [
                              Colors.orangeAccent.withValues(alpha: 0.6),
                              Colors.orange.withValues(alpha: 0.6),
                            ])
                          : const LinearGradient(
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                              colors: [Colors.orangeAccent, Colors.orange],
                            ),
                      boxShadow: _isKnocking
                          ? null
                          : [
                              BoxShadow(
                                color: Colors.orangeAccent
                                    .withValues(alpha: 0.28),
                                blurRadius: 20,
                                offset: const Offset(0, 6),
                              ),
                            ],
                    ),
                    child: Center(
                      child: _isKnocking
                          ? const SizedBox(
                              height: 20,
                              width: 20,
                              child: CircularProgressIndicator(
                                  color: Colors.black, strokeWidth: 2),
                            )
                          : const Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(Icons.vpn_key_outlined,
                                    color: Colors.black, size: 18),
                                SizedBox(width: 10),
                                Text(
                                  'AUTHORIZE TUNNEL',
                                  style: TextStyle(
                                    color: Colors.black,
                                    fontSize: 14,
                                    fontWeight: FontWeight.w800,
                                    letterSpacing: 3.0,
                                  ),
                                ),
                              ],
                            ),
                    ),
                  ),
                ),

                const SizedBox(height: 28),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _InfoChip extends StatelessWidget {
  final IconData icon;
  final String label;

  const _InfoChip({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.orangeAccent.withValues(alpha: 0.05),
        borderRadius: BorderRadius.circular(8),
        border:
            Border.all(color: Colors.orangeAccent.withValues(alpha: 0.15)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon,
              size: 11, color: Colors.orangeAccent.withValues(alpha: 0.7)),
          const SizedBox(width: 5),
          Text(
            label,
            style: TextStyle(
              color: Colors.orangeAccent.withValues(alpha: 0.7),
              fontSize: 9,
              letterSpacing: 1.0,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}
