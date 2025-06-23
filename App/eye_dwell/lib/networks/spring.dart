import 'dart:convert';
import 'dart:developer';

import 'package:http/http.dart' as http;
import 'package:eye_dwell/models/networks_models.dart';
import 'package:eye_dwell/models/user_models.dart';

class SpringAPI {
  static String BASE_DOMAIN = '192.168.0.105:8080';
  static var client = http.Client();

  static Future<ApiResponse> register(RegistrationModel request) async {
    log('api:register, ${request.toJson()}');

    final response = await client.post(
      Uri.http(BASE_DOMAIN, '/api/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(request.toJson()),
    );

    return ApiResponse.fromHttp(response);
  }

  static Future<ApiResponse> loginByUsername(
    String username,
    String password,
  ) async {
    log('api:loginByUsername, username: $username');

    final response = await client.post(
      Uri.http(BASE_DOMAIN, '/api/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'username': username, 'password': password}),
    );

    return ApiResponse.fromHttp(response);
  }

  static Future<ApiResponse> loginByEmail(String email, String password) async {
    log('api:loginByEmail, email: $email');

    final response = await client.post(
      Uri.http(BASE_DOMAIN, '/api/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );

    return ApiResponse.fromHttp(response);
  }

  static Future<ApiResponse> logout(String refreshToken) async {
    log('api:logout, token: $refreshToken');

    final response = await client.post(
      Uri.http(BASE_DOMAIN, '/api/auth/logout'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $refreshToken',
      },
    );

    return ApiResponse.fromHttp(response);
  }

  static Future<ApiResponse> refresh(String refreshToken) async {
    log('api:refresh, token: $refreshToken');

    final response = await client.post(
      Uri.http(BASE_DOMAIN, '/api/auth/refresh'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $refreshToken',
      },
    );

    return ApiResponse.fromHttp(response);
  }

  static Future<ApiResponse> getrecords(String accessToken) async {
    log('api:getrecords, token: $accessToken');

    final response = await client.get(
      Uri.http(BASE_DOMAIN, '/api/user/records'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $accessToken',
      },
    );

    return ApiResponse.fromHttp(response);
  }

  static Future<ApiResponse> postrecords(String accessToken, VisionRecord record) async {
    log('api:postrecords, token: $accessToken');

    final response = await client.post(
      Uri.http(BASE_DOMAIN, '/api/user/records'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $accessToken',
      },
      body: jsonEncode(record.toJson()),
    );

    return ApiResponse.fromHttp(response);
  }

  static Future<ApiResponse> getProfile(String accessToken) async {
    log('api:getProfile, token: $accessToken');

    final response = await client.get(
      Uri.http(BASE_DOMAIN, '/api/user/profile'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $accessToken',
      },
    );

    return ApiResponse.fromHttp(response);
  }

  static Future<ApiResponse> putProfile(
    String accessToken,
    UserProfile request,
  ) async {
    log('api:putProfile, token: $accessToken');

    final response = await client.put(
      Uri.http(BASE_DOMAIN, '/api/user/profile'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $accessToken',
      },
      body: jsonEncode(request.toJson()),
    );

    return ApiResponse.fromHttp(response);
  }

  static Future<ApiResponse> postChat(
    String accessToken,
    String content,
  ) async {
    log('api:postChat, token: $accessToken');

    final response = await client.post(
      Uri.http(BASE_DOMAIN, '/api/chat'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $accessToken',
      },
      body: jsonEncode({"content": content}),
    );

    return ApiResponse.fromHttp(response);
  }

  static Future<ApiResponse> delChat(
    String accessToken,
  ) async {
    log('api:delChat, token: $accessToken');

    final response = await client.delete(
      Uri.http(BASE_DOMAIN, '/api/chat'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $accessToken',
      },
    );

    return ApiResponse.fromHttp(response);
  }
}
