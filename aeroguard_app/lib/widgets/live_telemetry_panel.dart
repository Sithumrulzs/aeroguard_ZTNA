import 'package:flutter/material.dart';
import 'dashboard_panel.dart';

class LiveTelemetryPanel extends StatelessWidget {
  const LiveTelemetryPanel({super.key});

  @override
  Widget build(BuildContext context) {
    return DashboardPanel(
      title: 'Network Telemetry',
      icon: Icons.radar,
      child: Column(
        children: [
          _TelemetryRow(
            label: 'Active Admins',
            value: '1 · sithum.it',
            statusColor: const Color(0xFF10B981),
          ),
          const SizedBox(height: 14),
          _TelemetryRow(
            label: 'Active Vendors',
            value: '0 · Idle',
            statusColor: const Color(0xFF475569),
          ),
          const SizedBox(height: 14),
          _TelemetryRow(
            label: 'Gateway Status',
            value: 'SECURED',
            statusColor: const Color(0xFF00C3FF),
          ),
        ],
      ),
    );
  }
}

class _TelemetryRow extends StatelessWidget {
  final String label;
  final String value;
  final Color statusColor;

  const _TelemetryRow({
    required this.label,
    required this.value,
    required this.statusColor,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: const TextStyle(
            color: Color(0xFF94A3B8),
            fontSize: 13,
            fontWeight: FontWeight.w400,
          ),
        ),
        Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              height: 7,
              width: 7,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: statusColor,
                boxShadow: [
                  BoxShadow(
                    color: statusColor.withValues(alpha: 0.5),
                    blurRadius: 6,
                    spreadRadius: 1,
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            Text(
              value,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ],
    );
  }
}
