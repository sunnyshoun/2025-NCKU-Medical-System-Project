class CacheModel {
  String locale;
  double fontSize;
  String accessToken;
  String refreshToken;

  CacheModel({
    String? locale,
    double? fontSize,
    String? accessToken,
    String? refreshToken,
  }) : this.locale = locale ?? 'zh',
       this.fontSize = fontSize ?? 16,
       this.accessToken = accessToken ?? '',
       this.refreshToken = refreshToken ?? '';

  factory CacheModel.fromJson(Map<String, dynamic> json) {
    return CacheModel(
      locale: json['locale'] as String?,
      fontSize: (json['fontSize'] as num?)?.toDouble(),
      accessToken: json['accessToken'] as String?,
      refreshToken: json['refreshToken'] as String?,
    );
  }

  Map<String, dynamic> cacheJson() {
    return {
      'locale': locale,
      'fontSize': fontSize,
      'accessToken': accessToken,
      'refreshToken': refreshToken,
    };
  }

  Map<String, dynamic> toJson() => cacheJson();
}
