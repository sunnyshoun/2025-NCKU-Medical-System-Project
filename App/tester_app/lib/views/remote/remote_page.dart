import 'dart:developer';
import 'package:flutter/material.dart';
import 'package:tester_app/controllers/remote/bluetooth_controller.dart';
import 'package:tester_app/models/state_models.dart';
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
      final blueController = BluetoothController(
        generalStates: states,
        blueStates: BlueListStateModel(),
      );
      blueController.onConnected.add(() => setState(() {}));
      return BluetoothPage(
        generalStates: states,
        blueStates: BlueListStateModel(),
      );
    }

    return _started
        ? ControlPage(states: states)
        : TesterMenuPage(generalStates: states, menuStates: menuStates);
  }
}
