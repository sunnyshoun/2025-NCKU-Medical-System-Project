import 'dart:developer';

import 'package:flutter/material.dart';
import 'package:tester_app/configs/app_localizations.dart';
import 'package:tester_app/models/user_models.dart';
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
            registrationState.isCreatingAccount
                ? 'createAccount'
                : 'loginOrSignUp',
          ),
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: ListView(
          children: [
            Form(
              key: controller.formKey,
              child: Column(
                children: [
                  TextFormField(
                    controller: controller.accountController,
                    decoration: InputDecoration(
                      labelText: t.get(
                        registrationState.isCreatingAccount
                            ? 'username'
                            : 'usernameOrEmail',
                      ),
                    ),
                    validator: (value) {
                      if (value == null || value.trim().isEmpty) {
                        return t.get('require_username_or_email');
                      }
                      return null;
                    },
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
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
                    validator: (value) {
                      if (value == null || value.trim().isEmpty) {
                        return t.get('require_password');
                      } else if (value.trim().length < 8) {
                        return t.get('short_password');
                      }
                      return null;
                    },
                  ),
                  if (registrationState.isCreatingAccount) ...[
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: controller.emailController,
                      keyboardType: TextInputType.emailAddress,
                      decoration: InputDecoration(labelText: t.get('email')),
                      validator: (value) {
                        if (value == null || value.trim().isEmpty) {
                          return t.get('require_email');
                        }
                        if (!UserProfile.isEmailValid(value)) {
                          return t.get('email_invalid');
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: controller.ageController,
                      keyboardType: TextInputType.number,
                      decoration: InputDecoration(labelText: t.get('age')),
                      validator: (value) {
                        if (value != null && value.isNotEmpty) {
                          final age = int.tryParse(value) ?? 0;
                          if (age <= 0) {
                            return t.get('age_invalid');
                          }
                          return null;
                        }
                        return t.get('require_age');
                      },
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: controller.genderController,
                      decoration: InputDecoration(
                        labelText: '${t.get('gender')} (${t.get('optional')})',
                      ),
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: controller.jobController,
                      decoration: InputDecoration(
                        labelText: '${t.get('job')} (${t.get('optional')})',
                      ),
                    ),
                  ],
                  const SizedBox(height: 24),
                  ElevatedButton(
                    onPressed: () {
                      if (controller.formKey.currentState!.validate()) {
                        if (registrationState.isCreatingAccount) {
                          controller.createAccount();
                        } else {
                          controller.login();
                        }
                      }
                    },
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
          ],
        ),
      ),
    );
  }
}
