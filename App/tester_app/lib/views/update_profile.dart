import 'package:flutter/material.dart';
import 'package:tester_app/configs/app_localizations.dart';
import 'package:tester_app/controllers/settings_controller.dart';
import 'package:tester_app/models/user_models.dart';

class UpdateProfileForm extends StatefulWidget {
  final UpdateProfileController controller;

  const UpdateProfileForm({super.key, required this.controller});

  @override
  UpdateProfileFormState createState() => UpdateProfileFormState();
}

class UpdateProfileFormState extends State<UpdateProfileForm> {
  @override
  void initState() {
    super.initState();
  }

  @override
  void dispose() {
    widget.controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final controller = widget.controller;
    final states = controller.states;
    final t = AppLocalizations(states.locale);

    return Scaffold(
      appBar: AppBar(
        title: Text(t.get('update_profile')),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: controller.formKey,
          child: ListView(
            children: [
              TextFormField(
                controller: controller.usernameController,
                decoration: InputDecoration(labelText: t.get('username')),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return t.get('require_username');
                  }
                  return null;
                },
              ),
              TextFormField(
                controller: controller.emailController,
                decoration: InputDecoration(
                  labelText: '${t.get('email')} (${t.get('optional')})',
                ),
                keyboardType: TextInputType.emailAddress,
                validator: (value) {
                  if (value != null && value.isNotEmpty) {
                    if (!UserProfile.isEmailValid(value)) {
                      return t.get('email_invalid');
                    }
                  }
                  return null;
                },
              ),
              TextFormField(
                controller: controller.ageController,
                decoration: InputDecoration(
                  labelText: t.get('age'),
                ),
                keyboardType: TextInputType.number,
                validator: (value) {
                  if (value != null && value.isNotEmpty) {
                    final age = int.tryParse(value) ?? 0;
                    if (age <= 0) {
                      return t.get('age_invalid');
                    }
                  }
                  return null;
                },
              ),
              TextFormField(
                controller: controller.genderController,
                decoration: InputDecoration(
                  labelText: '${t.get('gender')} (${t.get('optional')})',
                ),
              ),
              TextFormField(
                controller: controller.jobController,
                decoration: InputDecoration(
                  labelText: '${t.get('job')} (${t.get('optional')})',
                ),
              ),
              const SizedBox(height: 20),
              ElevatedButton(
                onPressed: controller.submitForm,
                child: Text(t.get('confirm')),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
