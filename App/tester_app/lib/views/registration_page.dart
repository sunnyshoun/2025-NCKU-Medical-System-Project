import 'dart:developer';

import 'package:flutter/material.dart';
import 'package:tester_app/configs/app_localizations.dart';
import '../controllers/registration_controller.dart';

class RegistrationPage extends StatefulWidget {
  final RegistrationController controller;

  const RegistrationPage({super.key, required this.controller});

  @override
  State<RegistrationPage> createState() => _RegistrationPageState();
}

class _RegistrationPageState extends State<RegistrationPage> {
  @override
  void initState() {
    log('init regitration page');

    super.initState();

    widget.controller.addListener(() => setState(() {}));
  }

  @override
  Widget build(BuildContext context) {
    final controller = widget.controller;
    final registrationState = controller.registrationState;
    final generalState = controller.generalState;
    final t = AppLocalizations(generalState.locale);

    return Scaffold(
      appBar: AppBar(
        title: Text(
          t.get(
            registrationState.isCreatingAccount ? 'createAccount' : 'loginOrSignUp',
          ),
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: ListView(
          children: [
            TextField(
              controller: controller.accountController,
              decoration: InputDecoration(labelText: t.get(registrationState.isCreatingAccount? 'username' : 'usernameOrEmail')),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: controller.passwordController,
              obscureText: registrationState.obscurePassword,
              decoration: InputDecoration(
                labelText: t.get('password'),
                suffixIcon: IconButton(
                  icon: Icon(
                    registrationState.obscurePassword
                        ? Icons.visibility_off
                        : Icons.visibility,
                  ),
                  onPressed: () {
                    setState(() {
                      registrationState.obscurePassword =
                          !registrationState.obscurePassword;
                    });
                  },
                ),
              ),
            ),
            if (registrationState.isCreatingAccount) ...[
              const SizedBox(height: 16),
              TextField(
                controller: controller.emailController,
                decoration: InputDecoration(labelText: t.get('email')),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: controller.ageController,
                keyboardType: TextInputType.number,
                decoration: InputDecoration(labelText: t.get('age')),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: controller.genderController,
                decoration: InputDecoration(labelText: t.get('gender')),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: controller.jobController,
                decoration: InputDecoration(labelText: t.get('job')),
              ),
            ],
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed:
                  registrationState.isCreatingAccount
                      ? () => controller.createAccount()
                      : () => controller.login(),
              child: Text(
                t.get(
                  registrationState.isCreatingAccount
                      ? 'createAccount'
                      : 'loginOrSignUp',
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
