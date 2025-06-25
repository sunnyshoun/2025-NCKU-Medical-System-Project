import 'dart:developer';

import 'package:eye_dwell/configs/app_localizations.dart';
import 'package:eye_dwell/controllers/settings_controller.dart';
import 'package:eye_dwell/models/networks_models.dart';
import 'package:eye_dwell/models/state_models.dart';
import 'package:eye_dwell/models/wrappers.dart';
import 'package:eye_dwell/networks/spring.dart';
import 'package:flutter/material.dart';

class RemoteController {
  final TestModel testStates;
  final GeneralStateModel generalStates;
  final void Function() onTestEnd;

  RemoteController({required this.onTestEnd, required this.generalStates, required this.testStates});

  set testResult(String value) {
    switch (testStates.ind) {
      case 0:
        testStates.l = value;
        break;
      case 1:
        testStates.r = value;
        break;
      case 2:
        testStates.cl = value;
        break;
      case 3:
        testStates.cr = value;
        break;
      default:
        log('assign value to invalid index: ${testStates.ind}');
    }
  }

  Future<void> postRecord(BuildContext context) async {
    if (testStates.l == null || testStates.r == null) {
      log('err: l: ${testStates.l}, r: ${testStates.r}');
      return;
    }

    final record = testStates.toRecord();
    log(record.toJson().toString());

    ApiResponse response = ApiResponse.err();
    Future<bool> innerPost() async {
      response = await SpringAPI.postrecords(generalStates.accessToken, record);
      return response.statusCode == 401;
    }

    if (!await Wrappers.tryRefresh(innerPost, generalStates)) {
      // logout
      log('refresh token invalid');
      UpdateProfileController.clearProfile(generalStates, context);
      return;
    }

    if (response.statusCode != 201) {
      showDialog(
        context: context,
        builder:
            (_) => response.alertResponse(
              context,
              AppLocalizations(generalStates.locale),
            ),
      );
    }
  }
}
