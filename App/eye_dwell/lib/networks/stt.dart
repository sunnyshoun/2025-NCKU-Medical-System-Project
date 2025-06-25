import 'dart:convert';
import 'dart:developer';
import 'dart:io';
import 'package:http/http.dart' as http;

Future<String?> request(String path, String apiLang) async {
  try {
    // 讀取音頻文件
    File file = File(path);
    List<int> fileBytes = await file.readAsBytes();

    // 轉換為 Base64
    String base64Audio = base64Encode(fileBytes);

    // 準備請求數據
    Map<String, dynamic> data = {
      'audio': base64Audio,
      'lang': apiLang,
      'source': '人本and多語',
      "timestamp": false,
    };

    // 發送 POST 請求
    Uri url = Uri.parse("http://140.116.245.147:9000/api/base64_recognition");
    http.Response response = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(data),
    );

    // 檢查響應
    if (response.statusCode == 200) {
      if (response.body == "<{silent}>") {
        log('reponse body is silent');
        return null;
      } else {
        return response.body;
      }
    } else {
      log("Request failed with status code: ${response.statusCode}");
      return null;
    }
  } catch (e) {
    log("An error occurred: $e");
    return null;
  }
}
