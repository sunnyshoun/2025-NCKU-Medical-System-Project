import 'dart:developer';

import 'package:flutter/material.dart';
import 'package:eye_dwell/configs/app_localizations.dart';
import 'package:eye_dwell/controllers/settings_controller.dart';
import 'package:eye_dwell/models/networks_models.dart';
import 'package:eye_dwell/models/state_models.dart';
import 'package:eye_dwell/models/wrappers.dart';
import 'package:eye_dwell/networks/spring.dart';

class ChatController {
  final TextEditingController textController = TextEditingController();
  final GeneralStateModel generalStates;
  final ChatStateModel chatStates;
  final List<void Function()> onGetResponse = [];

  ChatController({required this.generalStates, required this.chatStates});

  void sendMessage(BuildContext context) async {
    final text = textController.text.trim();
    final AppLocalizations t = AppLocalizations(generalStates.locale);

    if (text.isEmpty) return;
    chatStates.messages.add({
      'sender': 'user',
      'message': text,
      'color': Colors.black,
    });
    textController.clear();
    chatStates.messages.add({
      'sender': 'server',
      'message': t.get('wait_response'),
      'color': Colors.black54,
    });
    chatStates.lockSendBtn = true;

    ApiResponse response = ApiResponse.err();
    Future<bool> innerSend() async {
      response = await SpringAPI.postChat(generalStates.accessToken, text);
      return response.statusCode == 401;
    }

    if (!await Wrappers.tryRefresh(innerSend, generalStates)) {
      // logout
      log('refresh token invalid');
      chatStates.lockSendBtn = false;
      UpdateProfileController.clearProfile(generalStates, context);
      return;
    }

    chatStates.messages.removeLast();

    if (response.statusCode == 200) {
      chatStates.messages.add({
        'sender': 'server',
        'message': response.data['content'],
        'color': Colors.black,
      });
    } else {
      showDialog(
        context: context,
        builder: (_) => response.alertResponse(context, t),
      );
    }

    chatStates.lockSendBtn = false;
    for (var fn in onGetResponse) {
      fn();
    }
  }

  void deleteChat() {
    ApiResponse response = ApiResponse.err();
    Future<bool> innerDelChat() async {
      response = await SpringAPI.delChat(generalStates.accessToken);
      return response.statusCode == 401;
    }

    Wrappers.tryRefresh(innerDelChat, generalStates);
  }
}
