import 'package:flutter/material.dart';
import 'package:tester_app/configs/app_localizations.dart';
import 'package:tester_app/controllers/chat_controller.dart';

class ChatPage extends StatefulWidget {
  final ChatController controller;
  const ChatPage({super.key, required this.controller});

  @override
  createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> {
  @override
  void initState() {
    super.initState();
    widget.controller.onGetResponse.add(() => setState(() {}));
  }

  @override
  Widget build(BuildContext context) {
    final controller = widget.controller;
    final chatStates = widget.controller.chatStates;
    final states = controller.generalStates;
    final AppLocalizations t = AppLocalizations(states.locale);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Chat'),
        leading: BackButton(
          onPressed: () {
            controller.deleteChat();
            Navigator.pop(context);
          },
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(12),
              itemCount: chatStates.messages.length,
              itemBuilder:
                  (context, index) => _buildMessage(chatStates.messages[index]),
            ),
          ),
          const Divider(height: 1),
          Container(
            padding: const EdgeInsets.only(
              right: 12,
              left: 12,
              top: 8,
              bottom: 24,
            ),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: .15),
                  blurRadius: 5,
                  offset: const Offset(0, -1),
                ),
              ],
            ),
            child: Row(
              children: [
                Expanded(
                  child: Container(
                    decoration: BoxDecoration(
                      color: const Color(0xFFF0F0F0),
                      borderRadius: BorderRadius.circular(24),
                    ),
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    child: TextField(
                      controller: controller.textController,
                      textInputAction: TextInputAction.newline,
                      keyboardType: TextInputType.multiline,
                      minLines: 1,
                      maxLines: 5,
                      style: TextStyle(fontSize: states.fontSize), // ← 使用常數
                      decoration: InputDecoration(
                        hintText: t.get('input_msg'),
                        border: InputBorder.none,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                CircleAvatar(
                  backgroundColor:
                      chatStates.lockSendBtn ? Colors.black38 : Colors.blue,
                  child: IconButton(
                    icon: const Icon(Icons.send, color: Colors.white),
                    onPressed:
                        chatStates.lockSendBtn
                            ? () {}
                            : () {
                              controller.sendMessage(context);
                              setState(() {});
                            },
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMessage(Map<String, dynamic> msg) {
    final states = widget.controller.generalStates;
    final isUser = msg['sender'] == 'user';

    final alignment = isUser ? Alignment.centerRight : Alignment.centerLeft;
    final bgColor =
        isUser
            ? const Color(0xFFD2E3FC) // 淺藍（使用者）
            : const Color(0xFFEFEFEF); // 淺灰（伺服器）
    final textColor = msg['color'];
    final icon = isUser ? Icons.person : Icons.smart_toy;

    return Align(
      alignment: alignment,
      child: Row(
        mainAxisAlignment:
            isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!isUser)
            Padding(
              padding: const EdgeInsets.only(right: 6.0),
              child: Icon(icon, size: 20, color: Colors.grey),
            ),
          Flexible(
            child: Container(
              margin: const EdgeInsets.symmetric(vertical: 6, horizontal: 4),
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: bgColor,
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(16),
                  topRight: const Radius.circular(16),
                  bottomLeft: Radius.circular(isUser ? 16 : 0),
                  bottomRight: Radius.circular(isUser ? 0 : 16),
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.05),
                    blurRadius: 4,
                    offset: const Offset(1, 2),
                  ),
                ],
              ),
              child: Text(
                msg['message'],
                style: TextStyle(fontSize: states.fontSize, color: textColor),
              ),
            ),
          ),
          if (isUser)
            Padding(
              padding: const EdgeInsets.only(left: 6.0),
              child: Icon(icon, size: 20, color: Colors.blue),
            ),
        ],
      ),
    );
  }
}
