import 'dart:developer';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:tester_app/controllers/cache_manager.dart';
import 'package:tester_app/controllers/registration_controller.dart';
import 'package:tester_app/models/state_models.dart';
import 'package:tester_app/models/user_models.dart';
import 'package:tester_app/networks/spring.dart';
import 'package:tester_app/views/registration_page.dart';
import 'views/home.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  Future<GeneralStateModel> builder() async {
    // load preference
    final cachedStates = await CacheManager.loadPreference();
    log('cached states: ${cachedStates?.toJson().toString()}');
    final states = cachedStates ?? GeneralStateModel();

    if (states.refreshToken.isEmpty) {
      log('no refresh token');
      states.profile = null;
      CacheManager.savePreference(states);
      return states;
    }
    final refreshReponse = await SpringAPI.refresh(states.refreshToken);
    if (refreshReponse.statusCode != 200) {
      // login failed
      log('login failed from entry');
      states.profile = null;
      CacheManager.savePreference(states);
      return states;
    }
    // login success
    final token = refreshReponse.asTokenData()!;
    states.accessToken = token.accessToken;
    states.refreshToken = token.refreshToken;
    CacheManager.savePreference(states);

    // update user profile
    final profileResponse = await SpringAPI.getProfile(states.accessToken);
    if (profileResponse.statusCode == 200) {
      states.profile = UserProfile.fromJson(
        profileResponse.data as Map<String, dynamic>,
      );
    } else {
      log(
        'login success but failed to get profile at entry with response: ${profileResponse.toJson()}',
      );
      exit(-1);
    }

    return states;
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<GeneralStateModel>(
      future: builder(),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return CircularProgressIndicator();
        } else if (snapshot.hasError) {
          return Text('Error: ${snapshot.error}');
        }

        return MaterialApp(
          routes: {
            '/':
                (context) => HomePage(
                  generalStates: snapshot.data!,
                  homeStates: HomeStateModel(),
                ),
            '/login':
                (context) => RegistrationPage(
                  controller: RegistrationController(
                    context: context,
                    generalState: snapshot.data!,
                    registrationState: RegistrationStateModel(),
                  ),
                ),
          },
          initialRoute: '/',
          title: 'Vision Test',
          theme: ThemeData(primarySwatch: Colors.blue),
        );
      },
    );
  }
}
