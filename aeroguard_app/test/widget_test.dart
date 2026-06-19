import 'package:flutter_test/flutter_test.dart';
import 'package:aeroguard_app/main.dart';

void main() {
  testWidgets('AeroGuard Boot Sequence Smoke Test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const AeroGuardApp());

    // Verify that the core application widget injects into the tree successfully.
    expect(find.byType(AeroGuardApp), findsOneWidget);
    
    // Since our app starts with the HomeLoadPage boot sequence, 
    // it should successfully pump without throwing any build errors.
  });
}