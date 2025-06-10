
package com.example.demo.MessageController;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController // 標記為 RESTful 控制器
public class HomeControl {

    @GetMapping("/") // 處理根路徑 / 的 GET 請求
    public String welcome() {
        return "Good Morning !!!";
    }
    
    
}