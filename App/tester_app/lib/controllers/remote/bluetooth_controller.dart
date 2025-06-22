import 'dart:developer';

import 'package:flutter/material.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:tester_app/configs/app_localizations.dart';
import 'package:tester_app/models/networks_models.dart';
import 'package:tester_app/models/state_models.dart';
import 'package:tester_app/networks/blue.dart';

class BluetoothController {
  final GeneralStateModel generalStates;
  final BlueListStateModel blueStates;
  final List<void Function(List<ScanResult>)> onListChanged = [];
  final List<void Function()> onConnected = [];

  BluetoothController({required this.generalStates, required this.blueStates});

  void showErr(String message, BuildContext context) => showDialog(
    context: context,
    builder:
        (_) => AlertDialog(
          title: Text(":("),
          content: Text(message),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text(
                AppLocalizations(generalStates.locale).get('confirm'),
              ),
            ),
          ],
        ),
  );

  Future<void> startScan(BuildContext context) async {
    // if (blueStates.adapterState != BluetoothAdapterState.on) {
    //   showErr('藍牙未開啟', context);
    //   return;
    // }

    log('startScan');

    try {
      await FlutterBluePlus.startScan(timeout: const Duration(seconds: 15));
      FlutterBluePlus.scanResults.listen((results) {
        for (var fn in onListChanged) {
          fn(results);
        }
      });
    } catch (e) {
      log("開始掃描時發生錯誤: $e");
    }
  }

  Future<void> stopScan() async {
    log('stopScan');
    await FlutterBluePlus.stopScan();
    blueStates.scanResults.clear();
  }

  void connectToDevice(BluetoothDevice device) async {
    try {
      await device.connect(autoConnect: false);
      log('已連接到設備: ${device.platformName}');
      final services = await device.discoverServices();
      generalStates.blue = BleModel(
        services: services,
        bluetoothDevice: device,
      );
      BLEInterface.sendCommand(generalStates.blue!, {'type': 'connect'});
      BLEInterface.subscribeToData(generalStates.blue!);
      for (var fn in onConnected) {
        fn();
      }
    } catch (e) {
      log('連接設備時發生錯誤: $e');
    }
  }
}
