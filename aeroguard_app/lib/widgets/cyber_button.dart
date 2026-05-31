import 'package:flutter/material.dart';

class CyberButton extends StatefulWidget {
  final String label;
  final IconData icon;
  final VoidCallback? onPressed;
  final bool isLoading;
  final Color? overrideColor;
  final bool outlined;

  const CyberButton({
    super.key,
    required this.label,
    required this.icon,
    required this.onPressed,
    this.isLoading = false,
    this.overrideColor,
    this.outlined = false,
  });

  @override
  State<CyberButton> createState() => _CyberButtonState();
}

class _CyberButtonState extends State<CyberButton>
    with SingleTickerProviderStateMixin {
  late AnimationController _pressCtrl;
  late Animation<double> _scale;

  @override
  void initState() {
    super.initState();
    _pressCtrl = AnimationController(
      duration: const Duration(milliseconds: 80),
      vsync: this,
    );
    _scale = Tween<double>(begin: 1.0, end: 0.97)
        .animate(CurvedAnimation(parent: _pressCtrl, curve: Curves.easeInOut));
  }

  @override
  void dispose() {
    _pressCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final color = widget.overrideColor ?? const Color(0xFF00C3FF);
    final disabled = widget.isLoading || widget.onPressed == null;

    return ScaleTransition(
      scale: _scale,
      child: GestureDetector(
        onTapDown: disabled ? null : (details) => _pressCtrl.forward(),
        onTapUp: disabled ? null : (details) => _pressCtrl.reverse(),
        onTapCancel: () => _pressCtrl.reverse(),
        onTap: disabled ? null : widget.onPressed,
        child: Container(
          height: 58,
          width: double.infinity,
          decoration: widget.outlined
              ? BoxDecoration(
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(
                    color: color.withValues(alpha: disabled ? 0.25 : 0.5),
                  ),
                  color: color.withValues(alpha: 0.06),
                )
              : BoxDecoration(
                  borderRadius: BorderRadius.circular(14),
                  gradient: disabled
                      ? LinearGradient(colors: [
                          color.withValues(alpha: 0.3),
                          color.withValues(alpha: 0.2),
                        ])
                      : LinearGradient(
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                          colors: [
                            color,
                            Color.lerp(color, const Color(0xFF0055FF), 0.4)!,
                          ],
                        ),
                  boxShadow: disabled
                      ? null
                      : [
                          BoxShadow(
                            color: color.withValues(alpha: 0.28),
                            blurRadius: 20,
                            offset: const Offset(0, 6),
                          ),
                        ],
                ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (widget.isLoading)
                SizedBox(
                  height: 18,
                  width: 18,
                  child: CircularProgressIndicator(
                    strokeWidth: 2.0,
                    color: widget.outlined ? color : Colors.black,
                  ),
                )
              else
                Icon(
                  widget.icon,
                  size: 19,
                  color: widget.outlined ? color : Colors.black,
                ),
              const SizedBox(width: 10),
              Text(
                widget.label,
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 2.0,
                  color: widget.outlined ? color : Colors.black,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
