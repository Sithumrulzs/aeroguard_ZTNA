import 'package:flutter/material.dart';

// ── Duration constants ─────────────────────────────────────────────────────
const Duration _kForward  = Duration(milliseconds: 420);
const Duration _kReverse  = Duration(milliseconds: 260);
const Duration _kFast     = Duration(milliseconds: 320);
const Duration _kFastRev  = Duration(milliseconds: 200);
const Duration _kBoot     = Duration(milliseconds: 950);

// ── premiumRoute ───────────────────────────────────────────────────────────
// Main forward navigation — fade + micro-scale + tiny upward lift.
// Used for primary screen pushes (login → dashboard, etc.).
PageRouteBuilder<T> premiumRoute<T>(Widget page) {
  return PageRouteBuilder<T>(
    transitionDuration:        _kForward,
    reverseTransitionDuration: _kReverse,
    pageBuilder: (_, _, _) => page,
    transitionsBuilder: (_, animation, _, child) {
      final curve = CurvedAnimation(parent: animation, curve: Curves.easeOutCubic);
      return FadeTransition(
        opacity: CurvedAnimation(parent: animation, curve: Curves.easeOut),
        child: ScaleTransition(
          scale: Tween<double>(begin: 0.97, end: 1.0).animate(curve),
          child: SlideTransition(
            position: Tween<Offset>(
              begin: const Offset(0.0, 0.025),
              end:   Offset.zero,
            ).animate(curve),
            child: child,
          ),
        ),
      );
    },
  );
}

// ── slideUpRoute ───────────────────────────────────────────────────────────
// Panel / modal screens (ProvisionToken, DeviceIdentity, VendorScanner).
// Slides in from slightly below with a fade — feels like a drawer opening.
PageRouteBuilder<T> slideUpRoute<T>(Widget page) {
  return PageRouteBuilder<T>(
    transitionDuration:        _kForward,
    reverseTransitionDuration: _kReverse,
    pageBuilder: (_, _, _) => page,
    transitionsBuilder: (_, animation, _, child) {
      final curve = CurvedAnimation(parent: animation, curve: Curves.easeOutCubic);
      return FadeTransition(
        opacity: CurvedAnimation(
          parent: animation,
          curve: const Interval(0.0, 0.7, curve: Curves.easeOut),
        ),
        child: SlideTransition(
          position: Tween<Offset>(
            begin: const Offset(0.0, 0.06),
            end:   Offset.zero,
          ).animate(curve),
          child: child,
        ),
      );
    },
  );
}

// ── slideBackRoute ─────────────────────────────────────────────────────────
// Going backward in the flow (biometric → login, logout, revoke).
// Incoming screen slides from left with fade — signals regression.
PageRouteBuilder<T> slideBackRoute<T>(Widget page) {
  return PageRouteBuilder<T>(
    transitionDuration:        _kFast,
    reverseTransitionDuration: _kFastRev,
    pageBuilder: (_, _, _) => page,
    transitionsBuilder: (_, animation, _, child) {
      final curve = CurvedAnimation(parent: animation, curve: Curves.easeOutCubic);
      return FadeTransition(
        opacity: CurvedAnimation(
          parent: animation,
          curve: const Interval(0.0, 0.75, curve: Curves.easeOut),
        ),
        child: SlideTransition(
          position: Tween<Offset>(
            begin: const Offset(-0.05, 0.0),
            end:   Offset.zero,
          ).animate(curve),
          child: child,
        ),
      );
    },
  );
}

// ── fadeRoute ──────────────────────────────────────────────────────────────
// Neutral crossfade — for session expiry, vendor logout, or same-level swaps.
PageRouteBuilder<T> fadeRoute<T>(Widget page) {
  return PageRouteBuilder<T>(
    transitionDuration:        _kFast,
    reverseTransitionDuration: _kFastRev,
    pageBuilder: (_, _, _) => page,
    transitionsBuilder: (_, animation, _, child) => FadeTransition(
      opacity: CurvedAnimation(parent: animation, curve: Curves.easeInOut),
      child: child,
    ),
  );
}

// ── bootToAuthRoute ────────────────────────────────────────────────────────
// Cinematic boot → biometric screen transition.
// Scale gently zooms in while fading — "security barrier opening" feel.
PageRouteBuilder<T> bootToAuthRoute<T>(Widget page) {
  return PageRouteBuilder<T>(
    transitionDuration:        _kBoot,
    reverseTransitionDuration: _kReverse,
    pageBuilder: (_, _, _) => page,
    transitionsBuilder: (_, animation, _, child) {
      final fade = CurvedAnimation(
        parent: animation,
        curve: const Interval(0.2, 1.0, curve: Curves.easeOut),
      );
      final scale = Tween<double>(begin: 1.08, end: 1.0).animate(
        CurvedAnimation(parent: animation, curve: Curves.easeOutCubic),
      );
      return FadeTransition(
        opacity: fade,
        child: ScaleTransition(scale: scale, child: child),
      );
    },
  );
}

// ── slideLeftRoute ─────────────────────────────────────────────────────────
// Kept for backward compatibility — maps to slideBackRoute.
PageRouteBuilder<T> slideLeftRoute<T>(Widget page) => slideBackRoute<T>(page);
