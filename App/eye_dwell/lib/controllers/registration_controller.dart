import 'dart:developer';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:eye_dwell/configs/app_localizations.dart';
import 'package:eye_dwell/models/state_models.dart';
import 'package:eye_dwell/models/user_models.dart';
import 'package:eye_dwell/networks/spring.dart';

class RegistrationController {
  final formKey = GlobalKey<FormState>();
  final TextEditingController accountController = TextEditingController();
  final TextEditingController passwordController = TextEditingController();
  final TextEditingController emailController = TextEditingController();
  final TextEditingController ageController = TextEditingController();
  final TextEditingController genderController = TextEditingController();
  final TextEditingController jobController = TextEditingController();
  final BuildContext context;
  final RegistrationStateModel registrationState;
  final GeneralStateModel generalState;
  final List<void Function()> onChanged = [];

  RegistrationController({
    required this.context,
    required this.registrationState,
    required this.generalState,
  });

  void addListener(void Function() listener) => onChanged.add(listener);

  void login() async {
    AppLocalizations t = AppLocalizations(generalState.locale);

    // login
    final response =
        accountController.text.contains('@')
            ? await SpringAPI.loginByEmail(
              accountController.text,
              passwordController.text,
            )
            : await SpringAPI.loginByUsername(
              accountController.text,
              passwordController.text,
            );

    if (response.statusCode == 200) {
      // login success
      final token = response.asTokenData()!;

      generalState.accessToken = token.accessToken;
      generalState.refreshToken = token.refreshToken;

      // update user profile
      final profileResponse = await SpringAPI.getProfile(
        generalState.accessToken,
      );
      if (profileResponse.statusCode == 200) {
        log('got profile: ${profileResponse.data}');
        generalState.profile = UserProfile.fromJson(
          profileResponse.data as Map<String, dynamic>,
        );
      } else {
        log(
          'login success but failed to get profile at login with response: ${profileResponse.toJson()}',
        );
        exit(-1);
      }

      // delete chat
      SpringAPI.delChat(generalState.accessToken);

      Navigator.pushNamedAndRemoveUntil(context, '/', (route) => false);
    } else if (response.statusCode == 404) {
      // navigate to create account
      registrationState.isCreatingAccount = true;
      for (var listener in onChanged) {
        listener();
      }
      if (accountController.text.contains('@')) {
        emailController.text = accountController.text;
      }
    } else {
      // show err
      showDialog(
        context: context,
        builder: (_) => response.alertResponse(context, t),
      );
    }
  }

  void createAccount() async {
    final username = accountController.text;
    final password = passwordController.text;
    final email = emailController.text;
    final age = int.tryParse(ageController.text) ?? 0;
    final gender = genderController.text;
    final job = jobController.text;
    AppLocalizations t = AppLocalizations(generalState.locale);

    // create account
    final profile = RegistrationModel(
      email: email,
      username: username,
      password: password,
      age: age,
      gender: gender,
      job: job,
    );
    final response = await SpringAPI.register(profile);

    if (response.statusCode == 201) {
      // register success
      log('created user: ${profile.username}');
      generalState.profile = profile;

      final token = response.asTokenData()!;
      generalState.accessToken = token.accessToken;
      generalState.refreshToken = token.refreshToken;

      Navigator.pushNamedAndRemoveUntil(context, '/', (route) => false);
    } else {
      log('code: ${response.statusCode}');
      showDialog(
        context: context,
        builder: (_) => response.alertResponse(context, t),
      );
    }
  }
}
