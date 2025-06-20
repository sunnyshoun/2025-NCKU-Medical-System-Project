import 'dart:developer';

import 'package:flutter/material.dart';
import 'package:tester_app/controllers/record_controller.dart';
import 'package:tester_app/models/state_models.dart';
import '../configs/app_localizations.dart';
import '../models/user_models.dart';

class VisionRecordsWidget extends StatefulWidget {
  final GeneralStateModel generalStates;
  final RecordsStateModel recordsStates;

  const VisionRecordsWidget({
    super.key,
    required this.generalStates,
    required this.recordsStates,
  });

  @override
  State<StatefulWidget> createState() => _VisionRecordsWidgetState();
}

class _VisionRecordsWidgetState extends State<VisionRecordsWidget> {
  late RecordController _controller;

  @override
  void initState() {
    log('init records page');
    super.initState();

    final states = widget.recordsStates;
    _controller = RecordController(
      generalStates: widget.generalStates,
      context: context,
      recordsStates: widget.recordsStates,
    );

    _controller.searchController.text = states.searchText;
    _controller.addSearchListener(
      () => setState(() {
        states.searchText = _controller.searchController.text;
      }),
    );
    _controller.addFetchListener(() {
      setState(() {});
    });

    // fetch records
    _controller.fetchRecords();
  }

  @override
  Widget build(BuildContext context) {
    final generalStates = widget.generalStates;
    final t = AppLocalizations(generalStates.locale);
    
    List<VisionRecord> sortedFilteredRecords =
        _controller.sortedFilteredRecords();

    return SafeArea(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0),
            child: Text(
              t.get('search_date'),
              style: TextStyle(
                fontSize: generalStates.fontSize,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: 16.0,
              vertical: 8.0,
            ),
            child: TextField(
              decoration: InputDecoration(
                border: const OutlineInputBorder(),
                hintText: t.get('input_date_hint'),
              ),
              controller: _controller.searchController,
              style: TextStyle(fontSize: generalStates.fontSize),
            ),
          ),
          const Divider(height: 32),
          Expanded(
            child: ListView.builder(
              itemCount: sortedFilteredRecords.length,
              itemBuilder: (context, index) {
                return VisionRecordCard(
                  record: sortedFilteredRecords[index],
                  generalStates: generalStates,
                );
              },
            ),
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              label: Text(
                t.get('refresh_records'),
                style: TextStyle(fontSize: generalStates.fontSize),
              ),
              icon: const Icon(Icons.replay_outlined),
              onPressed: () {
                log('refresh record');
                _controller.fetchRecords();
              },
            ),
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }
}

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
          '${t.get('date')}: ${record.createdAt.toLocal().toIso8601String().split('T')[0]}',
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
