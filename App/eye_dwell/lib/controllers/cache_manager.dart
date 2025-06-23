import "dart:io";
import 'dart:convert';
import 'package:path_provider/path_provider.dart';
import 'package:eye_dwell/models/cache_models.dart';
import 'package:eye_dwell/models/state_models.dart';

class CacheManager {
  static void savePreference(CacheModel caches) async {
    final Directory cacheDir = await getApplicationCacheDirectory();
    if (!cacheDir.existsSync()) return;

    if (!await cacheDir.exists()) {
      await cacheDir.create(recursive: true);
    }

    final File jsonFile = File("${cacheDir.path}/preference.json");
    await jsonFile.writeAsString(jsonEncode(caches.cacheJson()));
  }

  static Future<GeneralStateModel?> loadPreference() async {
    final Directory cacheDir = await getApplicationCacheDirectory();
    if (!cacheDir.existsSync()) return null;

    final File jsonFile = File("${cacheDir.path}/preference.json");
    if (await jsonFile.exists()) {
      final String preference = await jsonFile.readAsString();
      final Map<String, dynamic> preferenceMap = jsonDecode(preference);
      return GeneralStateModel.fromJson(preferenceMap);
    } else {
      return null;
    }
  }
}
