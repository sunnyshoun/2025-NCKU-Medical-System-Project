import 'dart:developer';
import 'package:eye_dwell/controllers/remote/remote_controller.dart';
import 'package:eye_dwell/networks/stt.dart';
import 'package:flutter/material.dart';
import 'package:eye_dwell/configs/app_localizations.dart';
import 'package:eye_dwell/models/state_models.dart';
import 'package:eye_dwell/networks/blue.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:flutter_sound/flutter_sound.dart';
import 'package:flutter/foundation.dart' show kIsWeb;

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

  FlutterSoundRecorder? _mRecorder = FlutterSoundRecorder();
  bool _mRecorderIsInited = false;
  Codec _codec = Codec.aacMP4;
  String _mPath = 'record.mp4';
  final theSource = AudioSource.microphone;

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

          log('ind: ${testStates.ind}, isTestEnd: ${testStates.isTestEnd}');
          if (testStates.isTestEnd) {
            controller.postRecord(context);
            controller.onTestEnd();
          } else {
            BLEInterface.sendCommand(widget.generalStates.blue!, {
              'type': 'start_test',
            });
          }
          setState(() {});
        }
      },
    ];

    openTheRecorder().then((value) {
      setState(() {
        _mRecorderIsInited = true;
      });
    });
  }

  Future<void> openTheRecorder() async {
    if (!kIsWeb) {
      var status = await Permission.microphone.request();
      if (status != PermissionStatus.granted) {
        throw RecordingPermissionException('Microphone permission not granted');
      }
    }
    await _mRecorder!.openRecorder();
    if (!await _mRecorder!.isEncoderSupported(_codec) && kIsWeb) {
      _codec = Codec.opusWebM;
      _mPath = 'record.webm';
      if (!await _mRecorder!.isEncoderSupported(_codec) && kIsWeb) {
        _mRecorderIsInited = true;
        return;
      }
    }
    _mRecorderIsInited = true;
  }

  void record() {
    _mRecorder!
        .startRecorder(toFile: _mPath, codec: _codec, audioSource: theSource)
        .then((value) {
          setState(() {});
        });
  }

  void stopRecorder() async {
    final t = AppLocalizations(widget.generalStates.locale);
    await _mRecorder!.stopRecorder().then((value) {
      setState(() {});
      if (value != null) {
        log('Recording saved to: $value');
        request(value, t.get('api_lang')).then((result) {
          log('stt result: ${result ?? '<{silent}>'}');
          BLEInterface.sendCommand(widget.generalStates.blue!, {
            'type': 'stt_response',
            'text': result,
          });
        });
      }
    });
  }

  void Function()? getRecorderFn() {
    if (!_mRecorderIsInited) {
      return null;
    }
    return _mRecorder!.isStopped ? record : stopRecorder;
  }

  @override
  void dispose() {
    _mRecorder!.closeRecorder();
    _mRecorder = null;
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
      'l: ${testStates.l}, r: ${testStates.r}, cl: ${testStates.cl}, cr: ${testStates.cr} ',
    );

    return Scaffold(
      appBar: AppBar(
        title: Text(t.get('remote'), style: TextStyle(fontSize: fontSize)),
      ),
      body: Column(
        mainAxisSize: MainAxisSize.max,
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Text(
              message,
              style: TextStyle(fontSize: fontSize, color: Colors.black87),
            ),
          ),

          Expanded(
            child: Center(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
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
                      Padding(
                        padding: const EdgeInsets.all(4.0),
                        child: ElevatedButton(
                          onPressed: getRecorderFn(),
                          style: ElevatedButton.styleFrom(
                            shape: const CircleBorder(),
                            padding: const EdgeInsets.all(20),
                            backgroundColor:
                                _mRecorder!.isRecording
                                    ? Colors.red
                                    : Colors.blue,
                          ),
                          child: Icon(Icons.mic, color: Colors.white),
                        ),
                      ),
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
