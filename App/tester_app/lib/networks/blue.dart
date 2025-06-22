import 'dart:convert';
import 'dart:developer';
import 'package:tester_app/models/networks_models.dart';

class BLEInterface {
  static List<void Function(Map<String, dynamic>)> onData = [];

  static Future<void> subscribeToData(BleModel bleStates) async {
    await bleStates.dataChar.setNotifyValue(true);
    bleStates.dataChar.lastValueStream.listen((value) {
      final jsonStr = utf8.decode(value);
      final data = jsonDecode(jsonStr);
      log('run ${onData.toString()}');
      for (var fn in onData) {
        fn(data);
      }
    });
  }

  static Future<void> sendCommand(
    BleModel bleStates,
    Map<String, dynamic> command,
  ) async {
    log('BLEInterface:sendCommand: $command');
    final jsonStr = jsonEncode(command);
    final bytes = utf8.encode(jsonStr);
    await bleStates.commandChar.write(bytes);
  }
}
