import 'dart:developer';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_blue_plus/flutter_blue_plus.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:eye_dwell/configs/app_localizations.dart';
import 'package:eye_dwell/controllers/remote/bluetooth_controller.dart';
import 'package:eye_dwell/models/state_models.dart';

class BluetoothPage extends StatefulWidget {
  final GeneralStateModel generalStates;
  final BlueListStateModel blueStates;
  final void Function() onConnected;
  const BluetoothPage({
    super.key,
    required this.generalStates,
    required this.blueStates,
    required this.onConnected,
  });

  @override
  State<BluetoothPage> createState() => _BluetoothPageState();
}

class _BluetoothPageState extends State<BluetoothPage> {
  late BluetoothController _controller;

  @override
  void initState() {
    log('init BluetoothPage');
    super.initState();

    _controller = BluetoothController(
      generalStates: widget.generalStates,
      blueStates: widget.blueStates,
    );

    log('add to onListChanged');
    _controller.onListChanged.add((results) {
      if (mounted) {
        setState(() {
          widget.blueStates.scanResults = results;
        });
      }
    });
    _controller.onConnected.add(widget.onConnected);

    _checkPermissions();
    _initBluetooth();
  }

  Future<void> _checkPermissions() async {
    final permissions = [
      Permission.location,
      Permission.bluetoothScan,
      Permission.bluetoothConnect,
      Permission.bluetooth,
    ];
    final results = await permissions.request();

    if (results.values.any((status) => status.isDenied)) {
      if (mounted) {
        _controller.showErr("請授予所有必要的權限", context);
      }
    }
  }

  Future<void> _initBluetooth() async {
    final blueStates = widget.blueStates;

    if (await FlutterBluePlus.isSupported == false) {
      if (mounted) {
        _controller.showErr("此裝置不支援藍牙", context);
      }
      return;
    }

    blueStates.adapterStateSubscription = FlutterBluePlus.adapterState.listen((
      state,
    ) {
      log('set adapterState = $state');
      setState(() => blueStates.adapterState = state);
    });

    if (Platform.isAndroid) {
      await FlutterBluePlus.turnOn();
    }

    try {
      await FlutterBluePlus.adapterState
          .where((state) => state == BluetoothAdapterState.on)
          .first;
    } catch (e) {
      log('Error initializing Bluetooth: $e');
      if (mounted) {
        _controller.showErr("藍牙初始化失敗", context);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    log('build BluetoothPage');
    final generalStates = widget.generalStates;
    final blueStates = widget.blueStates;
    final t = AppLocalizations(generalStates.locale);

    if (blueStates.adapterState == BluetoothAdapterState.off) {
      return Scaffold(
        appBar: AppBar(
          title: Text(
            t.get('connect_bluetooth'),
            style: TextStyle(fontSize: generalStates.fontSize),
          ),
        ),
        body: Center(
          child: Text(
            '藍牙未開啟',
            style: TextStyle(fontSize: generalStates.fontSize),
          ),
        ),
      );
    }

    final sortedResults = List<ScanResult>.from(blueStates.scanResults)..sort((
      a,
      b,
    ) {
      final aHasName = a.device.platformName.isNotEmpty;
      final bHasName = b.device.platformName.isNotEmpty;

      // Prioritize devices with platformName
      if (aHasName && !bHasName) return -1;
      if (!aHasName && bHasName) return 1;

      // If both have or don't have platformName, sort by platformName or remoteId
      if (aHasName && bHasName) {
        return a.device.platformName.compareTo(b.device.platformName);
      }
      return a.device.remoteId.toString().compareTo(
        b.device.remoteId.toString(),
      );
    });

    return Scaffold(
      appBar: AppBar(
        title: Text(
          t.get('connect_bluetooth'),
          style: TextStyle(fontSize: generalStates.fontSize + 4),
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: ListView.builder(
                shrinkWrap: true,
                itemCount: blueStates.scanResults.length,
                itemBuilder: (context, index) {
                  final result = sortedResults[index];
                  return ListTile(
                    key: ValueKey(result.device.remoteId),
                    title: Text(
                      result.device.platformName.isNotEmpty
                          ? result.device.platformName
                          : result.device.remoteId.toString(),
                      style: TextStyle(fontSize: generalStates.fontSize),
                    ),
                    subtitle: Text(
                      result.device.advName,
                      style: TextStyle(fontSize: generalStates.fontSize / 2),
                    ),
                    trailing: Text(
                      '${result.rssi} dBm',
                      style: TextStyle(fontSize: generalStates.fontSize / 2),
                    ),
                    onTap: () => _controller.connectToDevice(result.device),
                  );
                },
              ),
            ),
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                label: Text(
                  t.get('refresh_bluetooth'),
                  style: TextStyle(fontSize: generalStates.fontSize),
                ),
                icon: const Icon(Icons.replay_outlined),
                onPressed: () {
                  log('refresh');
                  _controller.startScan(context);
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _controller.stopScan();
    _controller.blueStates.adapterStateSubscription?.cancel();
    _controller.onListChanged
        .clear(); // Clear listeners to prevent memory leaks
    FlutterBluePlus.stopScan();
    super.dispose();
  }
}
