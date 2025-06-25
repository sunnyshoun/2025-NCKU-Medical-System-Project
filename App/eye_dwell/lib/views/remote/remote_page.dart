import 'dart:developer';
import 'package:eye_dwell/controllers/remote/remote_controller.dart';
import 'package:flutter/material.dart';
import 'package:eye_dwell/models/state_models.dart';
import 'package:eye_dwell/networks/blue.dart';
import 'package:eye_dwell/views/remote/bluetooth_page.dart';
import 'package:eye_dwell/views/remote/control_page.dart';
import 'package:eye_dwell/views/remote/tester_menu.dart';

class RemotePage extends StatefulWidget {
  final GeneralStateModel states;

  const RemotePage({super.key, required this.states});

  @override
  State<RemotePage> createState() => _RemotePageState();
}

class _RemotePageState extends State<RemotePage> {
  late bool _started;
  late TestModel testStates;
  late RemoteController controller;

  @override
  void initState() {
    super.initState();
    _started = false;
    testStates = TestModel();
    controller = RemoteController(
      generalStates: widget.states,
      testStates: testStates,
      onTestEnd:
          () => setState(() {
            _started = false;
            testStates.clear();
          }),
    );
  }

  @override
  Widget build(BuildContext context) {
    log('build RemotePage');
    final states = widget.states;

    if (states.blue == null) {
      return BluetoothPage(
        generalStates: states,
        blueStates: BlueListStateModel(),
        onConnected: () => setState(() {}),
      );
    }

    return _started
        ? ControlPage(
          generalStates: states,
          testStates: testStates,
          controller: controller,
          disconnect:
              () => setState(() {
                BLEInterface.sendCommand(states.blue!, {"type": "disconnect"});
                states.blue = null;
                _started = false;
              }),
        )
        : TesterMenuPage(
          generalStates: states,
          menuStates: testStates,
          start:
              () => setState(() {
                testStates.clear();
                _started = true;
                BLEInterface.sendCommand(states.blue!, {'type': 'start_test'});
              }),
        );
  }
}
