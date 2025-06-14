package com.example.demo.exception;

import org.springframework.http.HttpStatus;
import lombok.Getter;

@Getter
public class BusinessException extends RuntimeException {
    private final String responseStatus;
    private final HttpStatus httpStatus;

    public BusinessException(String responseStatus, String message, HttpStatus httpStatus) {
        super(message);
        this.responseStatus = responseStatus;
        this.httpStatus = httpStatus;
    }
}