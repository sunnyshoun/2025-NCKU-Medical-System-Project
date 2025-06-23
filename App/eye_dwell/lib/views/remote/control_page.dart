import 'dart:developer';
import 'package:eye_dwell/controllers/remote/remote_controller.dart';
import 'package:flutter/material.dart';
import 'package:eye_dwell/configs/app_localizations.dart';
import 'package:eye_dwell/models/state_models.dart';
import 'package:eye_dwell/networks/blue.dart';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';
import 'package:permission_handler/permission_handler.dart';

class ControlPage extends StatefulWidget {
  final GeneralStateModel generalStates;
  final TestModel testStates;
  final RemoteController controller;
  final void Function() disconnect;

  const ControlPage({
    super.key,
    required this.generalStates,
    required this.disconnect,
    required this.testStates,
    required this.controller,
  });

  @override
  State<ControlPage> createState() => _ControlPageState();
}

class _ControlPageState extends State<ControlPage> {
  final List<String> _messageKey = [
    'measure_l',
    'measure_r',
    'measure_cl',
    'measure_cr',
  ];
  final _record = AudioRecorder();
  bool _isRecording = false;

  @override
  void initState() {
    super.initState();
    final testStates = widget.testStates;
    final controller = widget.controller;
    BLEInterface.onData = [
      (value) {
        log(value.toString());
        if (value['type'] == 'ready_for_input') {
          testStates.isRemoteEnable = true;
        } else if (value['type'] == 'test_complete') {
          testStates.isRemoteEnable = false;
          controller.testResult = value['score'];

          if (testStates.isTestEnd) {
            controller.postRecord(context);
            controller.clearResult();
          } else {
            BLEInterface.sendCommand(widget.generalStates.blue!, {
              'type': 'start_test',
            });
          }
          setState(() {});
        }
      },
    ];
    _checkPermission();
  }

  Future<void> _checkPermission() async {
    if (await Permission.microphone.request().isGranted) {
      log('Microphone permission granted');
    } else {
      log('Microphone permission denied');
    }
  }

  Future<void> _toggleRecording() async {
    try {
      if (_isRecording) {
        await _record.stop();
        log('Recording stopped');
        setState(() {
          _isRecording = false;
        });
      } else {
        if (await Permission.microphone.isGranted) {
          final cacheDir = await getApplicationCacheDirectory();
          await _record.start(
            RecordConfig(
              numChannels: 1,
              encoder: AudioEncoder.wav,
              bitRate: 16000,
              sampleRate: 44100,
            ),
            path: '${cacheDir.path}/record.wav'
          );
          log('Recording started');
          setState(() {
            _isRecording = true;
          });
        } else {
          log('Microphone permission not granted');
          await _checkPermission();
        }
      }
    } catch (e) {
      log('Error in recording: $e');
    }
  }

  @override
  void dispose() {
    _record.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    log('build ControlPage');
    final generalStates = widget.generalStates;
    final testStates = widget.testStates;
    final t = AppLocalizations(generalStates.locale);
    final fontSize = generalStates.fontSize;
    final message = t.get(_messageKey[testStates.ind]);

    log(
      'l: ${testStates.l}, r: ${testStates.r}, cl: ${testStates.cl}, cr: ${testStates.cr}',
    );

    return Scaffold(
      appBar: AppBar(
        title: Text(t.get('remote'), style: TextStyle(fontSize: fontSize)),
      ),
      body: Column(
        mainAxisSize: MainAxisSize.max,
        children: [
          // 訊息欄
          Padding(
            padding: const EdgeInsets.all(12),
            child: Text(
              message,
              style: TextStyle(fontSize: fontSize, color: Colors.black87),
            ),
          ),

          // 中心按鍵控制區
          Expanded(
            child: Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // ↑
                  _DirectionButton(
                    icon: Icons.arrow_drop_up,
                    onTap: () {
                      if (testStates.isRemoteEnable) {
                        BLEInterface.sendCommand(generalStates.blue!, {
                          'type': 'direction_response',
                          'direction': 1,
                        });
                        testStates.isRemoteEnable = false;
                      } else {
                        log('ignore direction_response 1');
                      }
                    },
                  ),
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      // ←
                      _DirectionButton(
                        icon: Icons.arrow_left,
                        onTap: () {
                          if (testStates.isRemoteEnable) {
                            BLEInterface.sendCommand(generalStates.blue!, {
                              'type': 'direction_response',
                              'direction': 2,
                            });
                            testStates.isRemoteEnable = false;
                          } else {
                            log('ignore direction_response 2');
                          }
                        },
                      ),
                      // record
                      Padding(
                        padding: const EdgeInsets.all(4.0),
                        child: ElevatedButton(
                          onPressed: _toggleRecording,
                          style: ElevatedButton.styleFrom(
                            shape: const CircleBorder(),
                            padding: const EdgeInsets.all(20),
                            backgroundColor: _isRecording ? Colors.red : Colors.blue,
                          ),
                          child: Icon(
                            _isRecording ? Icons.stop : Icons.mic,
                            color: Colors.white,
                          ),
                        ),
                      ),
                      // →
                      _DirectionButton(
                        icon: Icons.arrow_right,
                        onTap: () {
                          if (testStates.isRemoteEnable) {
                            BLEInterface.sendCommand(generalStates.blue!, {
                              'type': 'direction_response',
                              'direction': 0,
                            });
                            testStates.isRemoteEnable = false;
                          } else {
                            log('ignore direction_response 0');
                          }
                        },
                      ),
                    ],
                  ),
                  // ↓
                  _DirectionButton(
                    icon: Icons.arrow_drop_down,
                    onTap: () {
                      if (testStates.isRemoteEnable) {
                        BLEInterface.sendCommand(generalStates.blue!, {
                          'type': 'direction_response',
                          'direction': 3,
                        });
                        testStates.isRemoteEnable = false;
                      } else {
                        log('ignore direction_response 3');
                      }
                    },
                  ),
                  Spacer(),
                  ElevatedButton.icon(
                    icon: Icon(Icons.bluetooth),
                    onPressed: widget.disconnect,
                    label: Text(t.get('disconnect')),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// 共用方向鍵元件
class _DirectionButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;

  const _DirectionButton({required this.icon, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(4.0),
      child: SizedBox(
        width: 60,
        height: 60,
        child: ElevatedButton(
          onPressed: onTap,
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.grey.shade300,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
          child: Icon(icon, color: Colors.black87),
        ),
      ),
    );
  }
}
