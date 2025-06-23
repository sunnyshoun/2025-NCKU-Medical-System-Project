import 'package:eye_dwell/controllers/cache_manager.dart';
import 'package:eye_dwell/models/state_models.dart';
import 'package:eye_dwell/networks/spring.dart';

class Wrappers {
  /// Retry when tryFn returned true at first time,
  /// return false if refresh token failed
  static Future<bool> tryRefresh(
    Future<bool> Function() tryFn,
    GeneralStateModel states,
  ) async {
    if (!await tryFn()) {
      return true;
    }
    final refreshResponse = await SpringAPI.refresh(states.refreshToken);
    if (refreshResponse.statusCode != 200) {
      // failed at refresh
      return false;
    }

    final token = refreshResponse.asTokenData()!;
    states.accessToken = token.accessToken;
    states.refreshToken = token.refreshToken;
    CacheManager.savePreference(states);

    await tryFn();
    return true;
  }
}
