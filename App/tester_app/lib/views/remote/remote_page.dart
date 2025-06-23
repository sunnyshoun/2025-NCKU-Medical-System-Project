import 'dart:developer';
import 'package:flutter/material.dart';
import 'package:tester_app/models/state_models.dart';
import 'package:tester_app/networks/blue.dart';
import 'package:tester_app/views/remote/bluetooth_page.dart';
import 'package:tester_app/views/remote/control_page.dart';
import 'package:tester_app/views/remote/tester_menu.dart';

class RemotePage extends StatefulWidget {
  final GeneralStateModel states;
  const RemotePage({super.key, required this.states});

  @override
  State<RemotePage> createState() => _RemotePageState();
}

class _RemotePageState extends State<RemotePage> {
  late bool _started;
  late TestMenuModel menuStates;

  @override
  void initState() {
    super.initState();
    _started = false;
    menuStates = TestMenuModel();
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
          states: states,
          menuStates: menuStates,
          disconnect:
              () => setState(() {
                BLEInterface.sendCommand(states.blue!, {"type": "disconnect"});
                states.blue = null;
                _started = false;
              }),
        )
        : TesterMenuPage(
          generalStates: states,
          menuStates: menuStates,
          start:
              () => setState(() {
                _started = true;
                BLEInterface.sendCommand(states.blue!, {'type': 'start_test'});
              }),
        );
  }
}
