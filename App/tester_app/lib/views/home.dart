import 'dart:developer';
import 'package:flutter/material.dart';
import 'package:tester_app/controllers/cache_manager.dart';
import 'package:tester_app/controllers/chat_controller.dart';
import 'package:tester_app/controllers/record_controller.dart';
import 'package:tester_app/controllers/settings_controller.dart';
import 'package:tester_app/models/state_models.dart';
import 'package:tester_app/views/chat_page.dart';
import 'package:tester_app/views/remote_page.dart';
import 'package:tester_app/views/settings.dart';
import 'package:tester_app/views/records_page.dart';
import 'package:tester_app/configs/app_localizations.dart';

class HomePage extends StatefulWidget {
  final GeneralStateModel generalStates;
  final HomeStateModel homeStates;

  const HomePage({
    super.key,
    required this.generalStates,
    required this.homeStates,
  });

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  @override
  void initState() {
    super.initState();

    log('init homepage');

    final profile = widget.generalStates.profile;
    log('profile: ${profile?.toJson().toString()}');

    if (profile == null) {
      log('profile is null, redirect to registration page');
      WidgetsBinding.instance.addPostFrameCallback((_) {
        Navigator.of(context).pushReplacementNamed('/login');
      });
      return;
    }

    log('generalStates: ${widget.generalStates.toJson().toString()}');
    CacheManager.savePreference(widget.generalStates);
  }

  @override
  Widget build(BuildContext context) {
    final generalStates = widget.generalStates;
    final homeStates = widget.homeStates;
    final t = AppLocalizations(generalStates.locale);

    return Scaffold(
      body: IndexedStack(
        index: homeStates.selectedIndex,
        children: [
          VisionRecordsWidget(
            generalStates: generalStates,
            recordsStates: homeStates,
            controller: RecordController(
              generalStates: generalStates,
              context: context,
              recordsStates: homeStates,
            ),
          ),
          RemotePage(states: generalStates),
          SettingsPage(
            controller: SettingsController(
              states: generalStates,
              setFontSizeChanged:
                  (val) => setState(() => generalStates.fontSize = val),
              setLocaleChanged:
                  (val) => setState(() => generalStates.locale = val ?? 'zh'),
              context: context,
            ),
            states: generalStates,
          ),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: homeStates.selectedIndex,
        onTap: (index) {
          setState(() => homeStates.selectedIndex = index);
        },
        items: [
          BottomNavigationBarItem(
            icon: const Icon(Icons.visibility),
            label: t.get('record'),
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.control_camera_outlined),
            label: t.get('remote'),
          ),
          BottomNavigationBarItem(
            icon: const Icon(Icons.settings),
            label: t.get('settings'),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          Navigator.of(context).push(
            MaterialPageRoute(
              builder:
                  (_) => ChatPage(
                    controller: ChatController(
                      generalStates: generalStates,
                      chatStates: ChatStateModel(),
                    ),
                  ),
            ),
          );
        },
        child: const Icon(Icons.chat),
      ),
    );
  }
}
