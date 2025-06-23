import 'dart:developer';

import 'package:flutter/material.dart';
import 'package:eye_dwell/configs/app_localizations.dart';
import 'package:eye_dwell/controllers/cache_manager.dart';
import 'package:eye_dwell/models/networks_models.dart';
import 'package:eye_dwell/models/state_models.dart';
import 'package:eye_dwell/models/user_models.dart';
import 'package:eye_dwell/models/wrappers.dart';
import 'package:eye_dwell/networks/spring.dart';

class SettingsController {
  final Function(String? locale) setLocaleChanged;
  final Function(double fontSize) setFontSizeChanged;
  final GeneralStateModel states;
  final BuildContext context;

  SettingsController({
    required this.states,
    required this.setFontSizeChanged,
    required this.setLocaleChanged,
    required this.context,
  });

  void onLocaleChanged(String? locale) {
    setLocaleChanged(locale);
    CacheManager.savePreference(states);
  }

  void onFontSizeChanged(double fontSize) {
    setFontSizeChanged(fontSize);
    CacheManager.savePreference(states);
  }

  void logout() {
    SpringAPI.logout(states.refreshToken);

    UpdateProfileController.clearProfile(states, context);
  }
}

class UpdateProfileController {
  final formKey = GlobalKey<FormState>();
  final usernameController = TextEditingController();
  final emailController = TextEditingController();
  final ageController = TextEditingController();
  final genderController = TextEditingController();
  final jobController = TextEditingController();
  final GeneralStateModel states;
  final BuildContext context;

  UpdateProfileController({required this.states, required this.context}) {
    final profile = states.profile;
    usernameController.text = profile?.username ?? '';
    emailController.text = profile?.email ?? '';
    ageController.text = profile?.age.toString() ?? '';
    genderController.text = profile?.gender ?? '';
    jobController.text = profile?.job ?? '';
  }

  UserProfile _getProfile() {
    return UserProfile(
      username: usernameController.text,
      email: emailController.text,
      age: int.tryParse(ageController.text) ?? 0,
      gender: genderController.text.isEmpty ? null : genderController.text,
      job: jobController.text.isEmpty ? null : jobController.text,
    );
  }

  // submit
  void submitForm() async {
    final t = AppLocalizations(states.locale);

    if (!formKey.currentState!.validate()) {
      return;
    }

    final userProfile = _getProfile();

    if (!userProfile.isValid) {
      log('invalid user profile');
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(t.get('update_profile_failed'))));
      return;
    }

    // submit
    ApiResponse response = ApiResponse.err();
    Future<bool> innerSubmit() async {
      response = await SpringAPI.putProfile(states.accessToken, userProfile);
      // only retry when 401
      return response.statusCode == 401;
    }

    if (!await Wrappers.tryRefresh(innerSubmit, states)) {
      // logout
      log('refresh token invalid');
      clearProfile(states, context);
      return;
    }

    if (response.statusCode == 200) {
      log('submit success');
      states.profile = userProfile;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(t.get('update_profile_success'))),
      );
    } else {
      showDialog(
        context: context,
        builder: (_) => response.alertResponse(context, t),
      );
    }
  }

  void dispose() {
    usernameController.dispose();
    emailController.dispose();
    ageController.dispose();
    genderController.dispose();
    jobController.dispose();
  }

  static void clearProfile(GeneralStateModel states, BuildContext context) {
    states.accessToken = '';
    states.refreshToken = '';
    states.profile = null;
    CacheManager.savePreference(states);
    Navigator.pushNamedAndRemoveUntil(context, '/login', (route) => false);
  }
}
