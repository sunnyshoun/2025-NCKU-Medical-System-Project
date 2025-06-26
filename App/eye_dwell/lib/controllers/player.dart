import 'dart:developer';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_sound/flutter_sound.dart';
import 'package:path_provider/path_provider.dart';

class Player {
  static final FlutterSoundPlayer _mPlayer = FlutterSoundPlayer();
  static bool playing = false;

  static Future<void> playAudioFromAssets(
    BuildContext context,
    String assetPath, {
    Codec codec = Codec.pcm16WAV, // Default to WAV codec
  }) async {
    if (!_mPlayer.isOpen()) {
      log('Initialize player');
      await _mPlayer.openPlayer();
    }

    if (playing) {
      log('Now playing');
      return;
    }

    // Get temporary directory
    final tempDir = await getTemporaryDirectory();
    final fileName = assetPath.split('/').last; // Extract file name
    final tempFilePath = '${tempDir.path}/$fileName';
    log('tempFilePath: $tempFilePath');

    // Copy asset to temporary file
    final assetData = await DefaultAssetBundle.of(context).load(assetPath);
    final bytes = assetData.buffer.asUint8List();
    await File(tempFilePath).writeAsBytes(bytes);

    // Verify temporary file exists
    final tempFile = File(tempFilePath);
    if (await tempFile.exists()) {
      log('Temporary file created: $tempFilePath');
    } else {
      log('Temporary file not found: $tempFilePath');
      return;
    }

    // Play the temporary file
    log('Playing: $tempFilePath');
    playing = true;
    await _mPlayer.startPlayer(
      fromURI: tempFilePath,
      codec: codec,
      whenFinished: () {
        log('Audio playback finished');
        tempFile.delete().catchError((e) {
          log('Error deleting temp file: $e');
        });
      },
    );
    playing = false;
  }

  static void dispose() async {
    log('Dispose player');
    await _mPlayer.closePlayer();
  }
}
