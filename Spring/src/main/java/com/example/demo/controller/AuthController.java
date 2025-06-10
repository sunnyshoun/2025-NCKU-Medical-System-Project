package com.example.demo.controller;

import com.example.demo.dto.AuthRequest;
import com.example.demo.dto.AuthResponse;
import com.example.demo.dto.RegisterRequest;
import com.example.demo.model.MyAppUser;
import com.example.demo.model.Role;
import com.example.demo.repository.MyAppUserRepository;
import com.example.demo.repository.RoleRepository;
import com.example.demo.utils.JwtTokenUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;

import java.util.HashSet;
import java.util.Optional;
import java.util.Set;

/**
 * Controller for handling authentication-related operations, including user registration and login.
 */
@RestController
@RequestMapping("/api/auth")
public class AuthController {

    @Autowired
    private AuthenticationManager authenticationManager;

    @Autowired
    private JwtTokenUtil jwtTokenUtil;

    @Autowired
    private MyAppUserRepository myAppUserRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @Autowired
    private RoleRepository roleRepository;

    /**
     * Handles user registration.
     * Endpoint: POST /api/auth/register
     * Creates a new user with the provided details and assigns a default "ROLE_USER" role.
     *
     * @param registerRequest DTO containing username, password, email, and optional fields (age, gender, job)
     * @return ResponseEntity with AuthResponse containing status and JWT
     */
    @PostMapping("/register")
    public ResponseEntity<AuthResponse> registerUser(@Valid @RequestBody RegisterRequest registerRequest) {
        try {
            // Check for existing username or email
            Optional<MyAppUser> existingUserByUsernameOptional = myAppUserRepository.findByUsername(registerRequest.getUsername());
            Optional<MyAppUser> existingUserByEmailOptional = myAppUserRepository.findByEmail(registerRequest.getEmail());

            if (existingUserByUsernameOptional.isPresent() || existingUserByEmailOptional.isPresent()) {
                return new ResponseEntity<>(AuthResponse.builder().status("error").jwt("").build(), HttpStatus.CONFLICT);
            }

            // Create new user
            MyAppUser newUser = new MyAppUser();
            newUser.setEmail(registerRequest.getEmail());
            newUser.setUsername(registerRequest.getUsername());
            newUser.setPassword(passwordEncoder.encode(registerRequest.getPassword()));
            newUser.setAge(registerRequest.getAge());
            newUser.setGender(registerRequest.getGender());
            newUser.setOccupation(registerRequest.getJob());

            // Assign default role
            Optional<Role> userRoleOptional = roleRepository.findByName("ROLE_USER");
            if (userRoleOptional.isEmpty()) {
                System.err.println("Error: 'ROLE_USER' not found in roles table. Please initialize roles data.");
                return new ResponseEntity<>(AuthResponse.builder().status("error").jwt("").build(), HttpStatus.INTERNAL_SERVER_ERROR);
            }
            Role userRole = userRoleOptional.get();
            Set<Role> roles = new HashSet<>();
            roles.add(userRole);
            newUser.setRoles(roles);

            // Save user and generate JWT
            MyAppUser savedUser = myAppUserRepository.save(newUser);
            final String jwt = jwtTokenUtil.generateToken(savedUser.getId().toString());

            return new ResponseEntity<>(AuthResponse.builder().status("ok").jwt(jwt).build(), HttpStatus.CREATED);

        } catch (Exception e) {
            System.err.println("Registration failed: " + e.getMessage());
            return new ResponseEntity<>(AuthResponse.builder().status("error").jwt("").build(), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    /**
     * Handles user login.
     * Endpoint: POST /api/auth/login
     * Supports login via username or email with password.
     *
     * @param authRequest DTO containing username/email and password
     * @return ResponseEntity with AuthResponse containing status and JWT
     */
    @PostMapping("/login")
    public ResponseEntity<AuthResponse> login(@Valid @RequestBody AuthRequest authRequest) {
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
            return new ResponseEntity<>(AuthResponse.builder().status("error").jwt("").build(), HttpStatus.UNAUTHORIZED);
        } catch (Exception e) {
            return new ResponseEntity<>(AuthResponse.builder().status("error").jwt("").build(), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    /**
     * Handles email verification.
     * Endpoint: GET /api/auth/verify-email
     *
     * @param token Verification token
     * @return ResponseEntity with verification status
     */
    @GetMapping("/verify-email")
    public ResponseEntity<String> verifyEmail(@RequestParam String token) {
        return new ResponseEntity<>("Email verification is currently disabled.", HttpStatus.OK);
    }
}