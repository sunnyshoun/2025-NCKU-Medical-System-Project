import 'dart:developer';
import 'package:flutter/material.dart';
import 'package:eye_dwell/configs/app_localizations.dart';
import 'package:eye_dwell/controllers/settings_controller.dart';
import 'package:eye_dwell/models/networks_models.dart';
import 'package:eye_dwell/models/state_models.dart';
import 'package:eye_dwell/models/wrappers.dart';
import 'package:eye_dwell/networks/spring.dart';
import '/models/user_models.dart';

class RecordController {
  final GeneralStateModel generalStates;
  final RecordsStateModel recordsStates;
  final TextEditingController searchController = TextEditingController();
  final List<void Function()> onFetchRecords = [];
  final BuildContext context;

  RecordController({
    required this.generalStates,
    required this.context,
    required this.recordsStates,
  }) {
    log('RecordController construct');
    this.searchController.text = this.recordsStates.searchText;
  }

  List<VisionRecord> sortedFilteredRecords() {
    log('search record by \"${recordsStates.searchText}\"');
    return (recordsStates.records
        .where(
          (record) => record.createdAt
              .toIso8601String()
              .split('T')[0]
              .contains(recordsStates.searchText),
        )
        .toList()
      ..sort((a, b) => b.createdAt.compareTo(a.createdAt)));
  }

  addSearchListener(listener) => searchController.addListener(listener);
  addFetchListener(void Function() listener) => onFetchRecords.add(listener);

  void fetchRecords() async {
    ApiResponse response = ApiResponse.err();
    Future<bool> innerFetchRecords() async {
      response = await SpringAPI.getrecords(generalStates.accessToken);
      // only retry when 401
      return response.statusCode == 401;
    }

    if (!await Wrappers.tryRefresh(innerFetchRecords, generalStates)) {
      // logout
      log('refresh token invalid');
      UpdateProfileController.clearProfile(generalStates, context);
      return;
    }

    if (response.statusCode == 200) {
      log('fetched records');
      recordsStates.records = VisionRecord.convertToVisionRecords(
        response.data,
      );
      for (var listener in onFetchRecords) {
        listener();
      }
    } else {
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
