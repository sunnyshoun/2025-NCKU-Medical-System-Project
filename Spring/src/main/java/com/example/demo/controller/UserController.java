package com.example.demo.controller;

import com.example.demo.dto.ApiResponse;
import com.example.demo.dto.UserProfileRequest;
import com.example.demo.dto.UserProfileResponse;
import com.example.demo.model.User;
import com.example.demo.model.Record;
import com.example.demo.repository.UserRepository;
import com.example.demo.service.RecordService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * UserController個人資料管理和視力檢查記錄。
 * /api/user 路徑。
 */
@RestController
@RequestMapping("/api/user")
public class UserController {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @Autowired
    private RecordService recordService;

    /**
     * 獲取當前登入用戶的個人資料
     * Endpoint: GET /api/user/profile
     * 需要JWT Token
     */
    @GetMapping("/profile")
    public ResponseEntity<ApiResponse<UserProfileResponse>> getUserProfile(@AuthenticationPrincipal User currentUser) {
        UserProfileResponse responseData = UserProfileResponse.builder()
                .id(currentUser.getId())
                .username(currentUser.getUsername())
                .email(currentUser.getEmail())
                .age(currentUser.getAge())
                .gender(currentUser.getGender())
                .job(currentUser.getOccupation())
                .build();

        return new ResponseEntity<>(ApiResponse.success(responseData), HttpStatus.OK);
    }

    /**
     * 更新用戶資料。
     * Endpoint: PUT /api/user/profile
     * 需要 JWT Token
     */
    @PutMapping("/profile")
    public ResponseEntity<ApiResponse<UserProfileResponse>> updateUserProfile(@Valid @RequestBody UserProfileRequest profileRequest,
                                                                             @AuthenticationPrincipal User currentUser) {
        try {
            Optional<User> userOptional = userRepository.findById(currentUser.getId());
            if (userOptional.isEmpty()) {
                return new ResponseEntity<>(ApiResponse.error("查無用戶"), HttpStatus.NOT_FOUND);
            }
            User userToUpdate = userOptional.get();

            userToUpdate.setUsername(profileRequest.getUsername());
            userToUpdate.setEmail(profileRequest.getEmail());
            if (profileRequest.getPassword() != null && !profileRequest.getPassword().isEmpty()) {
                userToUpdate.setPassword(passwordEncoder.encode(profileRequest.getPassword()));
            }
            userToUpdate.setAge(profileRequest.getAge());
            userToUpdate.setGender(profileRequest.getGender());
            userToUpdate.setOccupation(profileRequest.getJob());

            userRepository.save(userToUpdate);

            return new ResponseEntity<>(ApiResponse.success(), HttpStatus.OK);
        } catch (Exception e) {
            System.err.println("用戶資料更新失敗: " + e.getMessage());
            e.printStackTrace();
            return new ResponseEntity<>(ApiResponse.error("伺服器內部錯誤"), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }

    /**
     * 獲取當前登入用戶的所有視力檢查記錄。
     * Endpoint: GET /api/user/records
     * 需要 JWT Token
     */
    @GetMapping("/records")
    public ResponseEntity<List<Record>> getUserRecords(@AuthenticationPrincipal User currentUser) {
        UUID userId = currentUser.getId();
        List<Record> records = recordService.getRecordsByUserId(userId);
        return new ResponseEntity<>(records, HttpStatus.OK);
    }

    /**
     * 為當前登入用戶新增一條視力檢查記錄
     * POST /api/user/records
     * 需要JWT Token
     */
    @PostMapping("/records")
    public ResponseEntity<Record> createRecord(@Valid @RequestBody Record record, @AuthenticationPrincipal User currentUser) {
        record.setUserId(currentUser.getId());
        Record savedRecord = recordService.saveRecord(record);
        return new ResponseEntity<>(savedRecord, HttpStatus.CREATED);
    }
}