import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:eye_dwell/models/cache_models.dart';
import 'package:eye_dwell/models/networks_models.dart';
import 'user_models.dart';

class GeneralStateModel extends CacheModel {
  UserProfile? profile;
  BleModel? blue;

  GeneralStateModel({
    super.locale,
    super.fontSize,
    super.accessToken,
    super.refreshToken,
    this.profile,
  });

  factory GeneralStateModel.fromJson(Map<String, dynamic> json) {
    return GeneralStateModel(
      locale: json['locale'] as String?,
      fontSize: (json['fontSize'] as num?)?.toDouble(),
      accessToken: json['accessToken'] as String?,
      refreshToken: json['refreshToken'] as String?,
      profile:
          json['profile'] != null
              ? UserProfile.fromJson(json['profile'])
              : null,
    );
  }

  @override
  Map<String, dynamic> toJson() {
    return {...super.toJson(), 'profile': profile?.toJson()};
  }
}

class RecordsStateModel {
  String searchText = '';
  List<VisionRecord> records = [];
}

class HomeStateModel extends RecordsStateModel {
  int selectedIndex = 0;
}

class RegistrationStateModel {
  bool isCreatingAccount;
  bool obscurePassword;

  RegistrationStateModel({bool? isCreatingAccount, bool? obscurePassword})
    : this.isCreatingAccount = isCreatingAccount ?? false,
      this.obscurePassword = obscurePassword ?? true;
}

class ChatStateModel {
  final List<Map<String, dynamic>> messages;
  bool lockSendBtn;

  ChatStateModel({List<Map<String, dynamic>>? messages, bool? lockSendBtn})
    : this.messages =
          messages ??
          [
            {
              'sender': 'server',
              'message': '歡迎來到聊天系統，請問有什麼可以幫忙的？\n(回覆並非絕對正確，需諮詢專業醫護人員)',
              'color': Colors.black,
            },
          ],
      this.lockSendBtn = lockSendBtn ?? false;
}

class BlueListStateModel {
  List<ScanResult> scanResults = []; // 掃描結果
  BluetoothAdapterState adapterState = BluetoothAdapterState.unknown; // 藍牙狀態
  StreamSubscription<BluetoothAdapterState>? adapterStateSubscription;
}

class TestModel {
  bool isCorrectionEnabled = false;
  String? leftCorrection;
  String? rightCorrection;

  String? l;
  String? r;
  String? cl;
  String? cr;

  int get ind =>
      l == null
          ? 0
          : r == null
          ? 1
          : cl == null
          ? 2
          : 3;

  bool get isTestEnd => ind >= (isCorrectionEnabled ? 4 : 2);

  bool isRemoteEnable = false;

  VisionRecord toRecord() {
    return VisionRecord(
      uncorrectedVisionLeft: l!,
      uncorrectedVisionRight: r!,
      correctedPowerLeft: leftCorrection,
      correctedPowerRight: rightCorrection,
      correctedVisionLeft: cl,
      correctedVisionRight: cr,
      createdAt: DateTime.now().toUtc(),
    );
  }

  void clear() {
    l = null;
    r = null;
    cl = null;
    cr = null;
  }
}
