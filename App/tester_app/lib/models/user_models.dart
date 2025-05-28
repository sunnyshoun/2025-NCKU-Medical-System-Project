class UserProfile {
  String username;
  String email;
  int? age;
  String? gender;
  String? job;

  UserProfile._({
    required this.username,
    required this.email,
    this.age,
    this.gender,
    this.job,
  });

  /// 使用 factory 過濾無效欄位
  factory UserProfile({
    required String username,
    required String email,
    int? age,
    String? gender,
    String? job,
  }) {
    final cleanedUserName = username.trim().isEmpty ? '' : username.trim();
    final cleanedEmail = isEmailValid(email) ? email : '';
    final cleanedAge = (age != null && age > 0) ? age : null;
    final cleanedGender = (gender?.trim().isEmpty ?? true) ? null : gender;
    final cleanedJob = (job?.trim().isEmpty ?? true) ? null : job;

    return UserProfile._(
      username: cleanedUserName,
      email: cleanedEmail,
      age: cleanedAge,
      gender: cleanedGender,
      job: cleanedJob,
    );
  }

  Map<String, dynamic> toJson() => {
    'username': username,
    'email': email,
    if (age != null) 'age': age,
    if (gender != null) 'gender': gender,
    if (job != null) 'job': job,
  };

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile._(
      username: json['username'] ?? '',
      email: json['email'] ?? '',
      age: json['age'],
      gender: json['gender'],
      job: json['job'],
    );
  }

  bool get isValid => username.isNotEmpty && isEmailValid(email);

  static bool isEmailValid(String email) {
    final emailRegex = RegExp(r'^[^@]+@[^@]+\.[^@]+');
    return emailRegex.hasMatch(email);
  }
}

class RegistrationModel extends UserProfile {
  String password;

  RegistrationModel._({
    required super.username,
    required super.email,
    super.age,
    super.gender,
    super.job,
    required this.password,
  }) : super._();

  factory RegistrationModel({
    required String username,
    required String email,
    required String password,
    int? age,
    String? gender,
    String? job,
  }) {
    final cleanedPassword = password.trim();
    if (cleanedPassword.length < 6) {
      throw ArgumentError('Password must be at least 6 characters');
    }

    final base = UserProfile(
      username: username,
      email: email,
      age: age,
      gender: gender,
      job: job,
    );

    return RegistrationModel._(
      username: base.username,
      email: base.email,
      age: base.age,
      gender: base.gender,
      job: base.job,
      password: cleanedPassword,
    );
  }

  @override
  Map<String, dynamic> toJson() => {...super.toJson(), 'password': password};

  factory RegistrationModel.fromJson(Map<String, dynamic> json) {
    return RegistrationModel(
      username: json['username'] ?? '',
      email: json['email'] ?? '',
      password: json['password'] ?? '',
      age: json['age'],
      gender: json['gender'],
      job: json['job'],
    );
  }

  @override
  bool get isValid => super.isValid && password.length >= 6;
}

class VisionRecord {
  final String? correctedVisionLeft;
  final String? correctedPowerLeft;
  final String? correctedVisionRight;
  final String? correctedPowerRight;
  final String uncorrectedVisionLeft;
  final String uncorrectedVisionRight;
  final DateTime createdAt;

   VisionRecord({
    this.correctedVisionLeft,
    this.correctedPowerLeft,
    this.correctedVisionRight,
    this.correctedPowerRight,
    required this.uncorrectedVisionLeft,
    required this.uncorrectedVisionRight,
    required this.createdAt,
  });

  factory VisionRecord.mock({required int id}) {
    return VisionRecord(
      correctedVisionLeft: id % 2 == 0 ? '1.${id}' : null,
      correctedPowerLeft: id % 2 == 0 ? '-${id * 0.5}' : null,
      correctedVisionRight: id % 2 == 0 ? '1.${id - 1}' : null,
      correctedPowerRight: id % 2 == 0 ? '-${id * 0.4}' : null,
      uncorrectedVisionLeft: '1.${id % 3}',
      uncorrectedVisionRight: '1.${(id + 1) % 3}',
      createdAt: DateTime.now().subtract(Duration(days: id)),
    );
  }

  Map<String, dynamic> toJson() => {
    'corr_l': correctedVisionLeft,
    'diopter_l': correctedPowerLeft,
    'corr_r': correctedVisionRight,
    'diopter_r': correctedPowerRight,
    'unco_l': uncorrectedVisionLeft,
    'unco_r': uncorrectedVisionRight,
    'created_at': createdAt.toIso8601String(),
  };

  factory VisionRecord.fromJson(Map<String, dynamic> json) => VisionRecord(
    correctedVisionLeft: json['corr_l'],
    correctedPowerLeft: json['diopter_l'],
    correctedVisionRight: json['corr_r'],
    correctedPowerRight: json['diopter_r'],
    uncorrectedVisionLeft: json['unco_l'],
    uncorrectedVisionRight: json['unco_r'],
    createdAt: DateTime.parse(json['created_at']),
  );

  static List<VisionRecord> convertToVisionRecords(List<dynamic> jsonList) {
    return jsonList.map((json) {
      // Create a new map, only converting "NULL" strings to null
      Map<String, dynamic> cleanedJson = {
        'corr_l': json['corr_l'] == 'NULL' ? null : json['corr_l'],
        'diopter_l': json['diopter_l'] == 'NULL' ? null : json['diopter_l'],
        'corr_r': json['corr_r'] == 'NULL' ? null : json['corr_r'],
        'diopter_r': json['diopter_r'] == 'NULL' ? null : json['diopter_r'],
        'unco_l': json['unco_l'] == 'NULL' ? null : json['unco_l'],
        'unco_r': json['unco_r'] == 'NULL' ? null : json['unco_r'],
        'created_at': json['created_at'],
      };
      return VisionRecord.fromJson(cleanedJson);
    }).toList();
  }
}
