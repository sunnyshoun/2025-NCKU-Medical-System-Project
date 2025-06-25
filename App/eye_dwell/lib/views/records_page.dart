import 'dart:developer';

import 'package:eye_dwell/views/record_widget.dart';
import 'package:flutter/material.dart';
import 'package:eye_dwell/controllers/record_controller.dart';
import 'package:eye_dwell/models/state_models.dart';
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
