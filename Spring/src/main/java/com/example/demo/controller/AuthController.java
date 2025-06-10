package com.example.demo.controller;

import com.example.demo.model.MyAppUser;
import com.example.demo.model.MyAppUserRepository;
import com.example.demo.dto.AuthRequest;
import com.example.demo.dto.AuthResponse;
import com.example.demo.utils.JwtTokenUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Optional;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    @Autowired
    private AuthenticationManager authenticationManager;

    @Autowired
    private JwtTokenUtil jwtTokenUtil;

    @Autowired
    private MyAppUserRepository myAppUserRepository;

    /**
     * 處理用戶登入請求
     * 路徑: POST /api/auth/login
     * 支援 username/password 或 email/password 登入
     * @param authRequest 包含 Username/Email, Password 的登入請求 DTO
     * @return ResponseEntity<AuthResponse> 回傳 AuthResponse
     */
    @PostMapping("/login")
    public ResponseEntity<AuthResponse> login(@RequestBody AuthRequest authRequest) {
        String accountIdentifier = null;

        if (authRequest.getUsername() != null && !authRequest.getUsername().isEmpty()) {
            accountIdentifier = authRequest.getUsername();
        } else if (authRequest.getEmail() != null && !authRequest.getEmail().isEmpty()) {
            accountIdentifier = authRequest.getEmail();
        } else {
            return new ResponseEntity<>(AuthResponse.builder().status("error").jwt("").build(), HttpStatus.BAD_REQUEST);
        }

        try {
            Optional<MyAppUser> userOptional;
            if (authRequest.getUsername() != null && !authRequest.getUsername().isEmpty()) {
                userOptional = myAppUserRepository.findByUsername(authRequest.getUsername());
            } else {
                userOptional = myAppUserRepository.findByEmail(authRequest.getEmail());
            }

            if (userOptional.isEmpty()) {
                return new ResponseEntity<>(AuthResponse.builder().status("error").jwt("").build(), HttpStatus.NOT_FOUND);
            }
            MyAppUser user = userOptional.get();

            if (!user.isEnabled()) {
                return new ResponseEntity<>(AuthResponse.builder().status("error").jwt("").build(), HttpStatus.FORBIDDEN);
            }

            Authentication authentication = authenticationManager.authenticate(
                    new UsernamePasswordAuthenticationToken(accountIdentifier, authRequest.getPassword())
            );

            final String jwt = jwtTokenUtil.generateToken(user.getId().toString());

            return new ResponseEntity<>(AuthResponse.builder().status("ok").jwt(jwt).build(), HttpStatus.OK);

        } catch (AuthenticationException e) {
            return new ResponseEntity<>(AuthResponse.builder().status("error").jwt("").build(), HttpStatus.UNAUTHORIZED); // 401 Unauthorized
        } catch (Exception e) {
            return new ResponseEntity<>(AuthResponse.builder().status("error").jwt("").build(), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
}