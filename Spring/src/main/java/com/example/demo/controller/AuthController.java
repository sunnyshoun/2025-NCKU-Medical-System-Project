package com.example.demo.controller;

import com.example.demo.annotation.JwtAuth;
import com.example.demo.dto.ApiResponse;
import com.example.demo.dto.AuthResponse;
import com.example.demo.model.JwtId;
import com.example.demo.model.User;
import com.example.demo.repository.UserRepository;
import com.example.demo.model.Role;
import com.example.demo.repository.RoleRepository;
import com.example.demo.dto.LoginRequest;
import com.example.demo.dto.RegisterRequest;
import com.example.demo.service.JwtIdService;
import com.example.demo.utils.JwtTokenUtil;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

import java.util.HashSet;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    @Autowired
    private AuthenticationManager authenticationManager;

    @Autowired
    private JwtTokenUtil jwtTokenUtil;

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
    public ResponseEntity<ApiResponse<AuthResponse>> registerUser(@Valid @RequestBody RegisterRequest registerRequest) {
        try {
            Optional<User> existingUserByUsernameOptional = userRepository.findByUsername(registerRequest.getUsername());
            Optional<User> existingUserByEmailOptional = userRepository.findByEmail(registerRequest.getEmail());

            if (existingUserByUsernameOptional.isPresent()) {
                return new ResponseEntity<>(ApiResponse.error("用戶名已存在"), HttpStatus.CONFLICT);
            }
            if (existingUserByEmailOptional.isPresent()) {
                return new ResponseEntity<>(ApiResponse.error("電子郵件已存在"), HttpStatus.CONFLICT);
            }

            User newUser = new User();
            newUser.setEmail(registerRequest.getEmail());
            newUser.setUsername(registerRequest.getUsername());
            newUser.setPassword(passwordEncoder.encode(registerRequest.getPassword()));
            newUser.setAge(registerRequest.getAge());
            newUser.setGender(registerRequest.getGender());
            newUser.setOccupation(registerRequest.getJob());

            Optional<Role> userRoleOptional = roleRepository.findByName("USER");
            if (userRoleOptional.isEmpty()) {
                return new ResponseEntity<>(ApiResponse.error("預期外的使用者身分"), HttpStatus.INTERNAL_SERVER_ERROR);
            }
            Role userRole = userRoleOptional.get();
            Set<Role> roles = new HashSet<>();
            roles.add(userRole);
            newUser.setRoles(roles);

            User savedUser = userRepository.save(newUser);
            String accessToken = jwtTokenUtil.generateAccessToken(savedUser.getId());
            String refreshToken = jwtIdService.createRefreshToken(savedUser);

            return new ResponseEntity<>(ApiResponse.success(new AuthResponse(accessToken, refreshToken)), HttpStatus.CREATED);

        } catch (Exception e) {
            System.err.println("註冊失敗: " + e.getMessage());
            e.printStackTrace();
            return new ResponseEntity<>(ApiResponse.error("伺服器內部錯誤"), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    @PostMapping("/login")
    public ResponseEntity<ApiResponse<AuthResponse>> login(@Valid @RequestBody LoginRequest loginRequest) {
        String accountIdentifier = null;

        if (loginRequest.getUsername() != null && !loginRequest.getUsername().isEmpty()) {
            accountIdentifier = loginRequest.getUsername();
        } else if (loginRequest.getEmail() != null && !loginRequest.getEmail().isEmpty()) {
            accountIdentifier = loginRequest.getEmail();
        } else {
            return new ResponseEntity<>(ApiResponse.error("必須提供用戶名或電子郵件"), HttpStatus.BAD_REQUEST);
        }

        try {
            Optional<User> userOptional;
            if (loginRequest.getUsername() != null && !loginRequest.getUsername().isEmpty()) {
                userOptional = userRepository.findByUsername(loginRequest.getUsername());
            } else {
                userOptional = userRepository.findByEmail(loginRequest.getEmail());
            }

            if (userOptional.isEmpty()) {
                return new ResponseEntity<>(ApiResponse.error("用戶不存在"), HttpStatus.NOT_FOUND);
            }
            User user = userOptional.get();

            if (!user.isEnabled()) {
                return new ResponseEntity<>(ApiResponse.error("帳戶已被禁用"), HttpStatus.FORBIDDEN);
            }

            authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(accountIdentifier, loginRequest.getPassword())
            );

            String accessToken = jwtTokenUtil.generateAccessToken(user.getId());
            String refreshToken = jwtIdService.createRefreshToken(user);

            return new ResponseEntity<>(ApiResponse.success(new AuthResponse(accessToken, refreshToken)), HttpStatus.OK);

        } catch (AuthenticationException e) {
            return new ResponseEntity<>(ApiResponse.error("無效的憑證"), HttpStatus.UNAUTHORIZED);
        } catch (Exception e) {
            System.err.println("登錄失敗: " + e.getMessage());
            e.printStackTrace();
            return new ResponseEntity<>(ApiResponse.error("伺服器內部錯誤"), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    @PostMapping("/refresh")
    @JwtAuth
    public ResponseEntity<ApiResponse<AuthResponse>> refreshToken() {
        try {
            // Aspect 已驗證 token 並設置用戶，獲取當前用戶
            User user = (User) request.getAttribute("current_user");
            if (user == null) {
                return new ResponseEntity<>(ApiResponse.error("用戶不存在"), HttpStatus.NOT_FOUND);
            }

            // 從 request 獲取 refresh token
            String refreshToken = (String) request.getAttribute("jwt_token");
            String jti = jwtTokenUtil.extractJti(refreshToken);
            Optional<JwtId> storedTokenOptional = jwtIdService.findByJti(jti);
            if (storedTokenOptional.isEmpty()) {
                return new ResponseEntity<>(ApiResponse.error("Refresh Token 不存在或已被註銷"), HttpStatus.UNAUTHORIZED);
            }

            // 生成新的 Access Token 和 Refresh Token
            String newAccessToken = jwtTokenUtil.generateAccessToken(user.getId());
            String newRefreshToken = jwtIdService.createRefreshToken(user); // 自動刪除舊 JTI

            return new ResponseEntity<>(ApiResponse.success(new AuthResponse(newAccessToken, newRefreshToken)), HttpStatus.OK);

        } catch (Exception e) {
            System.err.println("Token 刷新失敗: " + e.getMessage());
            e.printStackTrace();
            return new ResponseEntity<>(ApiResponse.error("伺服器內部錯誤"), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    @PostMapping("/logout")
    @JwtAuth
    public ResponseEntity<ApiResponse<Void>> logout() {
        try {
            // Aspect 已驗證 token，僅需刪除 JTI
            String refreshToken = (String) request.getAttribute("jwt_token");
            String jti = jwtTokenUtil.extractJti(refreshToken);
            jwtIdService.deleteRefreshToken(jti);

            return new ResponseEntity<>(ApiResponse.success(), HttpStatus.OK);
        } catch (Exception e) {
            System.err.println("登出失敗: " + e.getMessage());
            e.printStackTrace();
            return new ResponseEntity<>(ApiResponse.error("伺服器內部錯誤"), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    @GetMapping("/verify-email")
    public ResponseEntity<String> verifyEmail(@RequestParam String token) {
        return new ResponseEntity<>("Email verification is currently disabled.", HttpStatus.OK);
    }
}