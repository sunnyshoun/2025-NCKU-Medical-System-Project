import 'package:flutter/material.dart';
import 'package:tester_app/configs/app_localizations.dart';
import 'package:tester_app/models/state_models.dart';

class RemotePage extends StatefulWidget {
  final GeneralStateModel states;
  const RemotePage({super.key, required this.states});

  @override
  State<RemotePage> createState() => _RemotePageState();
}

class _RemotePageState extends State<RemotePage> {
  String _message = '尚未操作';

  void _updateMessage(String msg) {
    setState(() {
      _message = msg;
    });
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations(widget.states.locale);
    final fontSize = widget.states.fontSize;

    return Scaffold(
      appBar: AppBar(
        title: Text(
          t.get('remote'), 
          style: TextStyle(
            fontSize: fontSize,
          ),
        ),
        actions: [
          PopupMenuButton<String>(
            onSelected: (value) {},
            itemBuilder:
                (context) => [
                  const PopupMenuItem(value: 'connect', child: Text('連線')),
                  const PopupMenuItem(value: 'disconnect', child: Text('中斷連線')),
                ],
            icon: const Icon(Icons.bluetooth),
          ),
        ],
      ),
      body: Column(
        mainAxisSize: MainAxisSize.max,
        children: [
          // 訊息欄
          Padding(
            padding: const EdgeInsets.all(12),
            child: Text(
              _message,
              style: TextStyle(
                fontSize: fontSize,
                color: Colors.black87),
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
                    onTap: () => _updateMessage('上'),
                  ),
                  Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      // ←
                      _DirectionButton(
                        icon: Icons.arrow_left,
                        onTap: () => _updateMessage('左'),
                      ),
                      // OK (確認)
                      Padding(
                        padding: const EdgeInsets.all(4.0),
                        child: ElevatedButton(
                          onPressed: () => _updateMessage('確認'),
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
                        onTap: () => _updateMessage('右'),
                      ),
                    ],
                  ),
                  // ↓
                  _DirectionButton(
                    icon: Icons.arrow_drop_down,
                    onTap: () => _updateMessage('下'),
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
