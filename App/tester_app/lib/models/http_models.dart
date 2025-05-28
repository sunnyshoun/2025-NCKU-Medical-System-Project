import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:tester_app/configs/app_localizations.dart';

class TokenData {
  final String accessToken;
  final String refreshToken;

  TokenData({required this.accessToken, required this.refreshToken});

  factory TokenData.fromJson(Map<String, dynamic> json) {
    return TokenData(
      accessToken: json['access_token'],
      refreshToken: json['refresh_token'],
    );
  }

  Map<String, dynamic> toJson() {
    return {'accessToken': accessToken, 'refreshToken': refreshToken};
  }
}

class ApiResponse {
  final String status;
  final dynamic data;
  final String message;
  final int statusCode;

  ApiResponse({
    required this.data,
    required this.message,
    required this.status,
    required this.statusCode,
  });

  factory ApiResponse.err() {
    return ApiResponse(
      data: "",
      message: "default err message",
      status: "error",
      statusCode: 400,
    );
  }

  factory ApiResponse.fromJson(Map<String, dynamic> json, int statusCode) {
    return ApiResponse(
      status: json['status'],
      message: json['message'],
      data: json['data'],
      statusCode: statusCode,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'status': status,
      'data': data,
      'message': message,
      'statusCode': statusCode,
    };
  }

  factory ApiResponse.fromHttp(http.Response response) {
    return ApiResponse.fromJson(jsonDecode(response.body), response.statusCode);
  }

  AlertDialog alertResponse(BuildContext context, AppLocalizations t) {
    return AlertDialog(
      title: Text('$status, code: $statusCode'),
      content: Text(message),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: Text(t.get('confirm')),
        ),
      ],
    );
  }

  TokenData? asTokenData() {
    if (data is Map<String, dynamic>) {
      final map = data as Map<String, dynamic>;
      if (map.containsKey('access_token') && map.containsKey('refresh_token')) {
        return TokenData.fromJson(map);
      }
    }
    return null;
  }
}
