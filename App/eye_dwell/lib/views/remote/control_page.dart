import 'dart:developer';

import 'package:flutter/material.dart';
import 'package:eye_dwell/configs/app_localizations.dart';
import 'package:eye_dwell/controllers/settings_controller.dart';
import 'package:eye_dwell/models/networks_models.dart';
import 'package:eye_dwell/models/state_models.dart';
import 'package:eye_dwell/models/user_models.dart';
import 'package:eye_dwell/models/wrappers.dart';
import 'package:eye_dwell/networks/blue.dart';
import 'package:eye_dwell/networks/spring.dart';

class ControlPage extends StatefulWidget {
  final GeneralStateModel states;
  final TestMenuModel menuStates;
  final void Function() disconnect;
  const ControlPage({
    super.key,
    required this.states,
    required this.disconnect,
    required this.menuStates,
  });

  @override
  State<ControlPage> createState() => _ControlPageState();
}

class _ControlPageState extends State<ControlPage> {
  String _message = '';
  List<String> messageKey = ['測左眼裸視', '測右眼裸視', '測左眼矯正', '測右眼矯正'];
  bool enable = false;

  String? l;
  String? r;
  String? cl;
  String? cr;
  int ind = 0;

  void _postRecord() async {
    if (l == null || r == null) {
      return;
    }

    final record = VisionRecord(
      uncorrectedVisionLeft: l!,
      uncorrectedVisionRight: r!,
      correctedVisionLeft: cl,
      correctedVisionRight: cr,
      createdAt: DateTime.now().toUtc(),
    );
    log(record.toJson().toString());

    ApiResponse response = ApiResponse.err();
    Future<bool> innerPost() async {
      response = await SpringAPI.postrecords(widget.states.accessToken, record);
      return response.statusCode == 401;
    }

    if (!await Wrappers.tryRefresh(innerPost, widget.states)) {
      // logout
      log('refresh token invalid');
      UpdateProfileController.clearProfile(widget.states, context);
      return;
    }

    if (response.statusCode != 201) {
      showDialog(
        context: context,
        builder:
            (_) => response.alertResponse(
              context,
              AppLocalizations(widget.states.locale),
            ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    log('build ControlPage');
    final states = widget.states;
    final t = AppLocalizations(states.locale);
    final fontSize = states.fontSize;
    BLEInterface.onData = [
      (value) {
        log(value.toString());
        if (value['type'] == 'ready_for_input') {
          enable = true;
        } else if (value['type'] == 'test_complete') {
          enable = false;
          log(value['score']);
          switch (ind) {
            case 0:
              l = value['score'];
              break;
            case 1:
              r = value['score'];
              break;
            case 2:
              cl = value['score'];
              break;
            case 3:
              cr = value['score'];
              break;
          }
          BLEInterface.sendCommand(states.blue!, {'type': 'start_test'});
          setState(() {});
        }
      },
    ];
    if (l == null) {
      ind = 0;
    } else if (r == null) {
      ind = 1;
    } else if (cl == null && widget.menuStates.isCorrectionEnabled) {
      ind = 2;
    } else if (cr == null && widget.menuStates.isCorrectionEnabled) {
      ind = 3;
    } else {
      _postRecord();
      l = null;
      r = null;
      cl = null;
      cr = null;
      ind = 0;
    }
    _message = messageKey[ind];

    log('l: $l, r: $r, cl: $cl, cr: $cr');

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
              _message,
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
                      if (enable) {
                        BLEInterface.sendCommand(states.blue!, {
                          'type': 'direction_response',
                          'direction': 1,
                        });
                        enable = false;
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
                          if (enable) {
                            BLEInterface.sendCommand(states.blue!, {
                              'type': 'direction_response',
                              'direction': 2,
                            });
                            enable = false;
                          } else {
                            log('ignore direction_response 2');
                          }
                        },
                      ),
                      // record
                      Padding(
                        padding: const EdgeInsets.all(4.0),
                        child: ElevatedButton(
                          onPressed: () => log('record'),
                          style: ElevatedButton.styleFrom(
                            shape: const CircleBorder(),
                            padding: const EdgeInsets.all(20),
                            backgroundColor: Colors.blue,
                          ),
                          child: const Icon(Icons.check, color: Colors.white),
                        ),
                      ),
                      // →
                      _DirectionButton(
                        icon: Icons.arrow_right,
                        onTap: () {
                          if (enable) {
                            BLEInterface.sendCommand(states.blue!, {
                              'type': 'direction_response',
                              'direction': 0,
                            });
                            enable = false;
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
                      if (enable) {
                        BLEInterface.sendCommand(states.blue!, {
                          'type': 'direction_response',
                          'direction': 3,
                        });
                        enable = false;
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
