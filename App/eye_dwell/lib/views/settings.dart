import 'dart:developer';
import 'package:flutter/material.dart';
import 'package:eye_dwell/controllers/settings_controller.dart';
import 'package:eye_dwell/models/state_models.dart';
import 'package:eye_dwell/configs/app_localizations.dart';
import 'package:eye_dwell/views/update_profile.dart';

class SettingsPage extends StatefulWidget {
  final SettingsController controller;
  final GeneralStateModel states;

  const SettingsPage({
    super.key,
    required this.controller,
    required this.states,
  });

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  late SettingsController _controller;

  @override
  void initState() {
    super.initState();

    log('init settingspage');
    _controller = widget.controller;
  }

  @override
  Widget build(BuildContext context) {
    final states = widget.states;
    final t = AppLocalizations(states.locale);

    return Scaffold(
      appBar: AppBar(
        title: Text(
          t.get('settings'),
          style: TextStyle(fontSize: states.fontSize + 4),
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              t.get('language'),
              style: TextStyle(fontSize: states.fontSize + 2),
            ),
            DropdownButton<String>(
              value: states.locale,
              items: [
                DropdownMenuItem(
                  value: 'en',
                  child: Text(
                    'English',
                    style: TextStyle(fontSize: states.fontSize),
                  ),
                ),
                DropdownMenuItem(
                  value: 'zh',
                  child: Text(
                    '繁體中文',
                    style: TextStyle(fontSize: states.fontSize),
                  ),
                ),
              ],
              onChanged: (val) => _controller.onLocaleChanged(val),
            ),
            const SizedBox(height: 24),
            Text(
              t.get('fontSize'),
              style: TextStyle(fontSize: states.fontSize + 2),
            ),
            Slider(
              min: 12,
              max: 24,
              value: states.fontSize,
              divisions: 6,
              label: states.fontSize.round().toString(),
              onChanged: (val) => _controller.onFontSizeChanged(val),
            ),
            const Spacer(),
            if (states.profile != null)
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  label: Text(
                    t.get('update_profile'),
                    style: TextStyle(fontSize: states.fontSize),
                  ),
                  onPressed: () {
                    Navigator.of(context).push(
                      MaterialPageRoute(
                        builder:
                            (context) => UpdateProfileForm(
                              controller: UpdateProfileController(
                                states: states,
                                context: context,
                              ),
                            ),
                      ),
                    );
                  },
                ),
              ),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                icon: const Icon(Icons.logout),
                label: Text(
                  t.get('logout'),
                  style: TextStyle(fontSize: states.fontSize),
                ),
                onPressed: _controller.logout,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
