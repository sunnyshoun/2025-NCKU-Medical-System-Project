package com.example.demo.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

/**
 * RestTemplate 配置類
 */
@Configuration
public class RestTemplateConfig {

    /**
     * 創建 RestTemplate Bean
     * 使用 SimpleClientHttpRequestFactory 避免依賴問題
     * @return RestTemplate 實例
     */
    @Bean
    public RestTemplate restTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        
        // 設置連接超時時間 (30秒)
        factory.setConnectTimeout(30000);
        
        // 設置讀取超時時間 (60秒)  
        factory.setReadTimeout(60000);
        
        return new RestTemplate(factory);
    }
}