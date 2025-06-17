package com.example.demo.config;

import com.example.demo.vectordb.VectorDBServiceGrpc;
import io.grpc.ManagedChannel;
import io.grpc.ManagedChannelBuilder;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class GrpcConfig {

    @Value("${vectordb.host}")
    private String vectorDbHost;

    @Value("${vectordb.port}")
    private int vectorDbPort;

    @Bean
    public VectorDBServiceGrpc.VectorDBServiceBlockingStub vectorDbStub() {
        ManagedChannel channel = ManagedChannelBuilder.forAddress(vectorDbHost, vectorDbPort)
                .usePlaintext() // 如果不需要 TLS，否則配置憑證
                .build();
        return VectorDBServiceGrpc.newBlockingStub(channel);
    }
}