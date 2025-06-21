import 'dart:developer';
import 'package:flutter/material.dart';
import 'package:sprintf/sprintf.dart';
import 'package:tester_app/configs/app_localizations.dart';
import 'package:tester_app/models/state_models.dart';

class TesterMenuPage extends StatefulWidget {
  final GeneralStateModel generalStates;
  final TestMenuModel menuStates;

  const TesterMenuPage({
    super.key,
    required this.generalStates,
    required this.menuStates,
  });

  @override
  State<TesterMenuPage> createState() => _TesterMenuPageState();
}

class _TesterMenuPageState extends State<TesterMenuPage> {
  final List<String> correctionOptions = List.generate(
    21,
    (i) => sprintf("%.2fD", [i / 4]),
  );

  @override
  Widget build(BuildContext context) {
    final generalStates = widget.generalStates;
    final menuStates = widget.menuStates;
    final t = AppLocalizations(generalStates.locale);
    final fontSize = generalStates.fontSize;

    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(height: fontSize*12),
          ElevatedButton.icon(
            icon: Icon(Icons.play_arrow),
            label: Text(
              t.get('start_measure'),
              style: TextStyle(fontSize: fontSize),
            ),
            onPressed: () {
              // 開始測量邏輯
              log("start_measure");
            },
          ),
          const SizedBox(height: 20),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(t.get('measure_corr'), style: TextStyle(fontSize: fontSize)),
              SizedBox(width: fontSize,),
              Switch(
                value: menuStates.isCorrectionEnabled,
                onChanged: (val) {
                  setState(() {
                    menuStates.isCorrectionEnabled = val;
                  });
                },
              ),
            ],
          ),
          const SizedBox(height: 10),
          SizedBox(
            height: fontSize*10,
            child: AnimatedSwitcher(
              duration: Duration(milliseconds: 100),
              child:
                  menuStates.isCorrectionEnabled
                      ? Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            "${t.get('uncorrected_left')}: ",
                            style: TextStyle(fontSize: fontSize),
                          ),
                          DropdownButton<String>(
                            value: menuStates.leftCorrection,
                            hint: Text(
                              t.get("select_diopler"),
                              style: TextStyle(fontSize: fontSize),
                            ),
                            items:
                                correctionOptions.map((value) {
                                  return DropdownMenuItem<String>(
                                    value: value,
                                    child: Text(
                                      value,
                                      style: TextStyle(fontSize: fontSize),
                                    ),
                                  );
                                }).toList(),
                            onChanged: (value) {
                              setState(() {
                                menuStates.leftCorrection = value;
                              });
                            },
                          ),
                          const SizedBox(height: 10),
                          Text(
                            "${t.get('uncorrected_right')}: ",
                            style: TextStyle(fontSize: fontSize),
                          ),
                          DropdownButton<String>(
                            value: menuStates.rightCorrection,
                            hint: Text(
                              t.get("select_diopler"),
                              style: TextStyle(fontSize: fontSize),
                            ),
                            items:
                                correctionOptions.map((value) {
                                  return DropdownMenuItem<String>(
                                    value: value,
                                    child: Text(
                                      value,
                                      style: TextStyle(fontSize: fontSize),
                                    ),
                                  );
                                }).toList(),
                            onChanged: (value) {
                              setState(() {
                                menuStates.rightCorrection = value;
                              });
                            },
                          ),
                        ],
                      )
                      : SizedBox(key: ValueKey(false)),
            ),
          ),
        ],
      ),
    );
  }
}
