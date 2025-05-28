import 'package:flutter/material.dart';
import 'package:tester_app/models/cache_models.dart';
import 'user_models.dart';

class GeneralStateModel extends CacheModel {
  UserProfile? profile;

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
            {'sender': 'server', 'message': '歡迎來到聊天系統，請問有什麼可以幫忙的？', 'color': Colors.black},
          ],
      this.lockSendBtn = lockSendBtn ?? false;
}
