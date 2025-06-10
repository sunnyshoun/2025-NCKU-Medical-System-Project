package com.example.demo.controller;

import com.example.demo.model.MyAppUser;
import com.example.demo.model.MyAppUserRepository;
import com.example.demo.model.Role; // <-- 導入 Role 實體
import com.example.demo.model.RoleRepository; // <-- 導入 RoleRepository
import com.example.demo.dto.AuthResponse;
import com.example.demo.dto.RegisterRequest;
import com.example.demo.utils.JwtTokenUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashSet;
import java.util.Optional;
import java.util.Set;

@RestController
@RequestMapping("/api/auth")
public class RegistrationController {

    @Autowired
    private MyAppUserRepository myAppUserRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @Autowired
    private JwtTokenUtil jwtTokenUtil;

    @Autowired
    private RoleRepository roleRepository;


    /**
     * /api/auth/register
     * @param registerRequest 包含 Username, Password, Email, (age, gender, job)
     * @return ResponseEntity<AuthResponse> 回傳 AuthResponse (status, JWT)
     */
    @PostMapping("/register")
    public ResponseEntity<AuthResponse> registerUser(@RequestBody RegisterRequest registerRequest) {
        try {

            Optional<MyAppUser> existingUserByUsernameOptional = myAppUserRepository.findByUsername(registerRequest.getUsername());
            Optional<MyAppUser> existingUserByEmailOptional = myAppUserRepository.findByEmail(registerRequest.getEmail());

            if (existingUserByUsernameOptional.isPresent() || existingUserByEmailOptional.isPresent()) {
                return new ResponseEntity<>(AuthResponse.builder().status("error").jwt("").build(), HttpStatus.CONFLICT);
            }

            // 創建新用戶
            MyAppUser newUser = new MyAppUser();
            newUser.setEmail(registerRequest.getEmail());
            newUser.setUsername(registerRequest.getUsername());
            newUser.setPassword(passwordEncoder.encode(registerRequest.getPassword()));

            newUser.setAge(registerRequest.getAge());
            newUser.setGender(registerRequest.getGender());
            newUser.setOccupation(registerRequest.getJob());

            Optional<Role> userRoleOptional = roleRepository.findByName("ROLE_USER");
            if (userRoleOptional.isEmpty()) {
                System.err.println("Error: 'ROLE_USER' not found in roles table. Please initialize roles data.");
                return new ResponseEntity<>(AuthResponse.builder().status("error").jwt("").build(), HttpStatus.INTERNAL_SERVER_ERROR);
            }
            Role userRole = userRoleOptional.get();

            Set<Role> roles = new HashSet<>();
            roles.add(userRole);
            newUser.setRoles(roles);

            MyAppUser savedUser = myAppUserRepository.save(newUser);

            final String jwt = jwtTokenUtil.generateToken(savedUser.getId().toString());

            return new ResponseEntity<>(AuthResponse.builder().status("ok").jwt(jwt).build(), HttpStatus.CREATED);

        } catch (Exception e) {
            System.err.println("Registration failed: " + e.getMessage());
            e.printStackTrace();
            return new ResponseEntity<>(AuthResponse.builder().status("error").jwt("").build(), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    @GetMapping("/verify-email")
    public ResponseEntity<String> verifyEmail(@RequestParam String token) {
        return new ResponseEntity<>("Email verification is currently disabled.", HttpStatus.OK);
    }
}