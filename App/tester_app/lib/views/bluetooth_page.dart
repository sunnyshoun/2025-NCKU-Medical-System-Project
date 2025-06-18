import 'dart:developer';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:tester_app/configs/app_localizations.dart';
import 'package:tester_app/controllers/bluetooth_controller.dart';

class BluetoothPage extends StatefulWidget {
  final BluetoothController controller;
  const BluetoothPage({super.key, required this.controller});

  @override
  State<BluetoothPage> createState() => _BluetoothPageState();
}

class _BluetoothPageState extends State<BluetoothPage> {
  @override
  void initState() {
    super.initState();
    _checkPermissions();
    _initBluetooth();
  }

  void _checkPermissions() async {
    await [
      Permission.location,
      Permission.bluetoothScan,
      Permission.bluetoothConnect,
      Permission.bluetooth,
    ].request();
  }

  void _initBluetooth() async {
    final controller = widget.controller;
    final blueStates = controller.blueStates;

    if (await FlutterBluePlus.isSupported == false) {
      controller.showErr("此裝置不支援藍牙", context);
      return;
    }

    blueStates.adapterStateSubscription = FlutterBluePlus.adapterState.listen((
      state,
    ) {
      setState(() => blueStates.adapterState = state);
    });

    if (Platform.isAndroid) {
      await FlutterBluePlus.turnOn();
    }
    // 等待藍牙開啟
    await FlutterBluePlus.adapterState
        .where((state) => state == BluetoothAdapterState.on)
        .first;

    controller.onListChanged.add(
      (results) => setState(() {
        controller.blueStates.scanResults = results;
      }),
    );
    controller.startScan(context);
  }

  @override
  Widget build(BuildContext context) {
    final controller = widget.controller;
    final generalStates = controller.generalStates;
    final blueStates = controller.blueStates;
    final t = AppLocalizations(generalStates.locale);

    if (blueStates.adapterState == BluetoothAdapterState.off) {
      return const Text('藍牙未開啟');
    }

    return Scaffold(
      appBar: AppBar(title: Text(t.get('connect_bluetooth'))),
      body: ListView.builder(
        itemCount: blueStates.scanResults.length,
        itemBuilder: (context, index) {
          final result = blueStates.scanResults[index];
          return ListTile(
            title: Text(
              result.device.platformName.isNotEmpty
                  ? result.device.platformName
                  : result.device.remoteId.toString(),
              style: TextStyle(fontSize: generalStates.fontSize),
            ),
            subtitle: Text(result.device.advName),
            trailing: Text('${result.rssi} dBm'),
            onTap: () => controller.connectToDevice(result.device),
          );
        },
      ),
    );
  }

  @override
  void dispose() {
    log('dispose');
    widget.controller.stopScan();
    widget.controller.blueStates.adapterStateSubscription?.cancel();
    FlutterBluePlus.stopScan();
    super.dispose();
  }
}
