import 'package:eye_dwell/configs/app_localizations.dart';
import 'package:eye_dwell/models/state_models.dart';
import 'package:eye_dwell/models/user_models.dart';
import 'package:flutter/material.dart';

class VisionRecordCard extends StatelessWidget {
  final VisionRecord record;
  final GeneralStateModel generalStates;

  const VisionRecordCard({
    super.key,
    required this.record,
    required this.generalStates,
  });

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations(generalStates.locale);

    List<Widget> subtitleWidgets = [
      Text(
        '${t.get('uncorrected_left')}: ${record.uncorrectedVisionLeft}  ${t.get('uncorrected_right')}: ${record.uncorrectedVisionRight}',
        style: TextStyle(fontSize: generalStates.fontSize),
      ),
    ];

    final hasCorrection =
        record.correctedVisionLeft != null &&
        record.correctedPowerLeft != null &&
        record.correctedVisionRight != null &&
        record.correctedPowerRight != null;

    if (hasCorrection) {
      subtitleWidgets.add(
        Text(
          '${t.get('corrected_left')}: ${t.get('vision')}${record.correctedVisionLeft}, ${t.get('power')}${record.correctedPowerLeft}',
          style: TextStyle(fontSize: generalStates.fontSize),
        ),
      );
      subtitleWidgets.add(
        Text(
          '${t.get('corrected_right')}: ${t.get('vision')}${record.correctedVisionRight}, ${t.get('power')}${record.correctedPowerRight}',
          style: TextStyle(fontSize: generalStates.fontSize),
        ),
      );
    }

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      elevation: 4,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: ListTile(
        title: Text(
          '${t.get('date')}: ${record.time}',
          style: TextStyle(
            fontSize: generalStates.fontSize,
            fontWeight: FontWeight.bold,
          ),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: subtitleWidgets,
        ),
        leading: const Icon(Icons.remove_red_eye),
      ),
    );
  }
}
