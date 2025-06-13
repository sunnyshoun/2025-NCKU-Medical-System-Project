package com.example.demo.controller;

import com.example.demo.dto.ApiResponse;
import com.example.demo.dto.AuthResponse;
import com.example.demo.dto.LoginRequest;
import com.example.demo.dto.RegisterRequest;
import com.example.demo.model.JwtId;
import com.example.demo.model.Role;
import com.example.demo.model.User;
import com.example.demo.repository.RoleRepository;
import com.example.demo.repository.UserRepository;
import com.example.demo.service.JwtIdService;
import com.example.demo.utils.JwtTokenUtils;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.util.HashSet;
import java.util.Optional;
import java.util.Set;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    @Autowired
    private AuthenticationManager authenticationManager;

    @Autowired
    private JwtTokenUtils jwtTokenUtil;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @Autowired
    private RoleRepository roleRepository;

    @Autowired
    private JwtIdService jwtIdService;

    @Autowired
    private HttpServletRequest request;

    @PostMapping("/register")
    @Transactional
    public ResponseEntity<ApiResponse<AuthResponse>> registerUser(@Valid @RequestBody RegisterRequest registerRequest) {
        if (userRepository.findByUsername(registerRequest.getUsername()).isPresent()) {
            return new ResponseEntity<>(ApiResponse.error("USERNAME_EXISTS", "用戶名已存在"), HttpStatus.CONFLICT);
        }
        if (userRepository.findByEmail(registerRequest.getEmail()).isPresent()) {
            return new ResponseEntity<>(ApiResponse.error("EMAIL_EXISTS", "電子郵件已存在"), HttpStatus.CONFLICT);
        }

        try {
            User newUser = new User();
            newUser.setEmail(registerRequest.getEmail());
            newUser.setUsername(registerRequest.getUsername());
            newUser.setPassword(passwordEncoder.encode(registerRequest.getPassword()));
            newUser.setAge(registerRequest.getAge());
            newUser.setGender(registerRequest.getGender());
            newUser.setOccupation(registerRequest.getJob());

            Optional<Role> userRoleOptional = roleRepository.findByName("USER");
            if (userRoleOptional.isEmpty()) {
                return new ResponseEntity<>(ApiResponse.error("ROLE_NOT_FOUND", "無法找到使用者角色"), HttpStatus.INTERNAL_SERVER_ERROR);
            }
            newUser.setRoles(new HashSet<>(Set.of(userRoleOptional.get())));

            User savedUser = userRepository.save(newUser);
            String accessToken = jwtTokenUtil.generateAccessToken(savedUser.getId());
            String refreshToken = jwtIdService.createRefreshToken(savedUser);

            return new ResponseEntity<>(ApiResponse.success(new AuthResponse(accessToken, refreshToken)), HttpStatus.CREATED);
        } catch (Exception e) {
            return new ResponseEntity<>(ApiResponse.error("REGISTRATION_FAILED", "註冊失敗: " + e.getMessage()), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    @PostMapping("/login")
    @Transactional
    public ResponseEntity<ApiResponse<AuthResponse>> login(@Valid @RequestBody LoginRequest loginRequest) {
        String accountIdentifier = loginRequest.getUsername() != null && !loginRequest.getUsername().isEmpty()
                ? loginRequest.getUsername()
                : loginRequest.getEmail();
        if (accountIdentifier == null || accountIdentifier.isEmpty()) {
            return new ResponseEntity<>(ApiResponse.error("INVALID_INPUT", "必須提供用戶名或電子郵件"), HttpStatus.BAD_REQUEST);
        }

        try {
            Optional<User> userOptional = loginRequest.getUsername() != null && !loginRequest.getUsername().isEmpty()
                    ? userRepository.findByUsername(loginRequest.getUsername())
                    : userRepository.findByEmail(loginRequest.getEmail());
            if (userOptional.isEmpty()) {
                return new ResponseEntity<>(ApiResponse.error("USER_NOT_FOUND", "用戶不存在"), HttpStatus.NOT_FOUND);
            }
            User user = userOptional.get();

            if (!user.isEnabled()) {
                return new ResponseEntity<>(ApiResponse.error("ACCOUNT_DISABLED", "帳戶已被禁用"), HttpStatus.FORBIDDEN);
            }

            authenticationManager.authenticate(
                    new UsernamePasswordAuthenticationToken(accountIdentifier, loginRequest.getPassword())
            );

            String accessToken = jwtTokenUtil.generateAccessToken(user.getId());
            String refreshToken = jwtIdService.createRefreshToken(user);

            return new ResponseEntity<>(ApiResponse.success(new AuthResponse(accessToken, refreshToken)), HttpStatus.OK);
        } catch (AuthenticationException e) {
            return new ResponseEntity<>(ApiResponse.error("INVALID_CREDENTIALS", "無效的憑證"), HttpStatus.UNAUTHORIZED);
        } catch (Exception e) {
            return new ResponseEntity<>(ApiResponse.error("LOGIN_FAILED", "登入失敗: " + e.getMessage()), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    @PostMapping("/refresh")
    @Transactional
    public ResponseEntity<ApiResponse<AuthResponse>> refreshToken(@AuthenticationPrincipal User currentUser) {
        String jwt = (String) request.getAttribute("jwt_token");

        try {
            String jti = jwtTokenUtil.extractJti(jwt);
            Optional<JwtId> storedTokenOptional = jwtIdService.findByJti(jti);
            if (storedTokenOptional.isEmpty()) {
                return new ResponseEntity<>(ApiResponse.error("REVOKED_TOKEN", "Refresh Token 不存在或已被註銷"), HttpStatus.UNAUTHORIZED);
            }

            String newAccessToken = jwtTokenUtil.generateAccessToken(currentUser.getId());
            String newRefreshToken = jwtIdService.createRefreshToken(currentUser);

            return new ResponseEntity<>(ApiResponse.success(new AuthResponse(newAccessToken, newRefreshToken)), HttpStatus.OK);
        } catch (Exception e) {
            return new ResponseEntity<>(ApiResponse.error("REFRESH_FAILED", "Token 刷新失敗: " + e.getMessage()), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    @PostMapping("/logout")
    @Transactional
    public ResponseEntity<ApiResponse<Void>> logout(@AuthenticationPrincipal User currentUser) {
        String jwt = (String) request.getAttribute("jwt_token");

        try {
            String jti = jwtTokenUtil.extractJti(jwt);
            jwtIdService.deleteRefreshToken(jti);

            return new ResponseEntity<>(ApiResponse.success(), HttpStatus.OK);
        } catch (Exception e) {
            return new ResponseEntity<>(ApiResponse.error("LOGOUT_FAILED", "登出失敗: " + e.getMessage()), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    @GetMapping("/verify-email")
    public ResponseEntity<String> verifyEmail(@RequestParam String token) {
        return new ResponseEntity<>("電子郵件驗證目前已禁用", HttpStatus.OK);
    }
}