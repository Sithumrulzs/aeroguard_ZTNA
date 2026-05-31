import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

// --- CORE SCREENS & CONFIG ---
import 'screens/home_load_page.dart';
import 'screens/sign_in_page.dart';
import 'config/environment_config.dart';
import 'services/auth_service.dart';

// --- BACKGROUND SERVICES ---
// import 'services/enclave_service.dart';
// import 'services/notification_service.dart';

void main() async {
  // Ensure the Flutter engine is fully booted before initializing native hardware
  WidgetsFlutterBinding.ensureInitialized();

  // Print active gateway config to debug console on every launch
  EnvironmentConfig.printActive();

  // Lock the app in portrait mode for a consistent, terminal-like dashboard experience
  SystemChrome.setPreferredOrientations([
    DeviceOrientation.portraitUp,
    DeviceOrientation.portraitDown,
  ]);

  // Make the top OS status bar transparent for a cinematic edge-to-edge look
  SystemChrome.setSystemUIOverlayStyle(
    const SystemUiOverlayStyle(
      statusBarColor: Colors.transparent,
      statusBarIconBrightness: Brightness.light,
    ),
  );

  // --- INITIALIZE HARDWARE & SECURITY SERVICES ---
  // (Uncomment these once your Python backend is ready to receive data)
  // await EnclaveService.initializeDevice("system_init");
  // await NotificationService.initialize();

  runApp(const AeroGuardApp());
}

class AeroGuardApp extends StatelessWidget {
  const AeroGuardApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AeroGuard ZTNA',
      debugShowCheckedModeBanner: false,

      // --- DEFINING THE GLOBAL AEROGUARD THEME ---
      theme: ThemeData(
        useMaterial3: true,
        fontFamily: 'Roboto',

        colorScheme: const ColorScheme(
          brightness: Brightness.dark,
          primary: Color(0xFF00C3FF),
          onPrimary: Colors.black,
          secondary: Colors.orangeAccent,
          onSecondary: Colors.black,
          error: Color(0xFFCF6679),
          onError: Colors.white,
          surface: Color(0xFF1E1E1E),
          onSurface: Colors.white,
        ),

        scaffoldBackgroundColor: const Color(0xFF0A0A0A),

        textTheme: const TextTheme(
          displayLarge: TextStyle(
            fontSize: 28,
            color: Colors.white,
            letterSpacing: 3.0,
            fontWeight: FontWeight.bold,
          ),
          titleMedium: TextStyle(
            fontSize: 16,
            color: Colors.white70,
            letterSpacing: 1.5,
          ),
          bodyLarge: TextStyle(
            fontSize: 14,
            color: Colors.white,
            letterSpacing: 0.5,
          ),
          bodyMedium: TextStyle(fontSize: 12, color: Colors.white70),
        ),
      ),

      home: const AuthWrapper(),
    );
  }
}

// Wrapper to check authentication status
class AuthWrapper extends StatefulWidget {
  const AuthWrapper({super.key});

  @override
  State<AuthWrapper> createState() => _AuthWrapperState();
}

class _AuthWrapperState extends State<AuthWrapper> {
  late Future<bool> _authCheck;

  @override
  void initState() {
    super.initState();
    _authCheck = AuthService.isAuthenticated();
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<bool>(
      future: _authCheck,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          // Show loading screen while checking auth
          return Scaffold(
            backgroundColor: const Color(0xFF050810),
            body: Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  SizedBox(
                    height: 50,
                    width: 50,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(
                        Colors.cyan.shade500,
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                  const Text(
                    'Initializing...',
                    style: TextStyle(color: Colors.white70),
                  ),
                ],
              ),
            ),
          );
        }

        if (snapshot.hasData && snapshot.data == true) {
          // User is authenticated, show home load page
          return const HomeLoadPage();
        } else {
          // User is not authenticated, show login page
          return const SignInPage();
        }
      },
    );
  }
}
