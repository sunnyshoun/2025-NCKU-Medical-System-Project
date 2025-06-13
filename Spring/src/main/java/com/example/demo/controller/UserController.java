package com.example.demo.controller;

import com.example.demo.annotation.JwtAuth;
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
import org.springframework.web.bind.annotation.*; // RESTful API

import jakarta.validation.Valid; // 啟用數據驗證
import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * UserController個人資料管理和視力檢查記錄。
 *  /api/user 路徑。
 */

@RestController
@RequestMapping("/api/user")
public class UserController {

    @Autowired
    private UserRepository userRepository; // 用於用戶數據庫操作

    @Autowired
    private PasswordEncoder passwordEncoder; // 用於更新密碼時加密

    @Autowired
    private RecordService recordService; // 用於視力檢查記錄業務邏輯


    /**
     * 獲取當前登入用戶的個人資料
     * Endpoint: GET /api/user/profile
     * 需要JWT Token
     *
     * @param currentUser 當前已認證的 User 物件
     * @return ResponseEntity<UserProfileResponse> 回傳用戶個人資料
     */
    @GetMapping("/profile") //  GET /api/user/profile
    @JwtAuth
    public ResponseEntity<ApiResponse<UserProfileResponse>> getUserProfile(@AuthenticationPrincipal User currentUser) {
        // 從當前認證的用戶物件構建回應 DTO
        UserProfileResponse responseData = UserProfileResponse.builder()
                .id(currentUser.getId())
                .username(currentUser.getUsername())
                .email(currentUser.getEmail())
                .age(currentUser.getAge())
                .gender(currentUser.getGender())
                .job(currentUser.getOccupation())
                .build();

        return new ResponseEntity<>(ApiResponse.success(responseData), HttpStatus.OK); // 返回用戶資料 (200 OK)
    }

    /**
     * 更新用戶資料。
     * Endpoint: PUT /api/user/profile
     * 需要 JWT Token
     *
     * @param profileRequest 包含要更新資料的 DTO，@Valid 啟用數據驗證
     * @param currentUser 當前已認證的 User 物件
     * @return ResponseEntity<UserProfileResponse> 回傳更新後的個人資料。
     */
    @PutMapping("/profile") // PUT /api/user/profile
    @JwtAuth
    public ResponseEntity<ApiResponse<UserProfileResponse>> updateUserProfile(@Valid @RequestBody UserProfileRequest profileRequest,
                                                                                @AuthenticationPrincipal User currentUser) {
        try {
            // 從資料庫再次獲取用戶最新數據 (避免直接修改傳入的 currentUser 物件，因為它可能是代理物件)
            Optional<User> userOptional = userRepository.findById(currentUser.getId());
            if (userOptional.isEmpty()) {
                return new ResponseEntity<>(ApiResponse.error("查無用戶"), HttpStatus.NOT_FOUND); // currentUser from 資料庫
            }
            User userToUpdate = userOptional.get();

            // 更新用戶資料
            // 注意：這裡假設 DTO 中的字段如果為 null，則不更新資料庫中的對應字段
            // 但如果前端傳遞了空字串 ""，則會覆蓋原有數據
            userToUpdate.setUsername(profileRequest.getUsername());
            userToUpdate.setEmail(profileRequest.getEmail());
            // 如果有新密碼，則加密並更新
            if (profileRequest.getPassword() != null && !profileRequest.getPassword().isEmpty()) {
                userToUpdate.setPassword(passwordEncoder.encode(profileRequest.getPassword()));
            }
            // 不一定要更新
            userToUpdate.setAge(profileRequest.getAge());
            userToUpdate.setGender(profileRequest.getGender());
            userToUpdate.setOccupation(profileRequest.getJob());

            userRepository.save(userToUpdate); // 保存更新

            return new ResponseEntity<>(ApiResponse.success(), HttpStatus.OK); // 200 OK
        }
        catch (Exception e) {
            System.err.println("用戶資料更新失敗: " + e.getMessage());
            e.printStackTrace();
            return new ResponseEntity<>(ApiResponse.error("伺服器內部錯誤"), HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }


    /**
     * 獲取當前登入用戶的所有視力檢查記錄。
     * Endpoint: GET /api/user/records
     * 這個 API 受到保護，需要 JWT Token 進行身份驗證。
     *
     * @param currentUser 當前已認證的 User 物件。
     * @return ResponseEntity<List<Record>> 回傳視力檢查記錄列表。
     */
    @GetMapping("/records")
    @JwtAuth
    public ResponseEntity<List<Record>> getUserRecords(@AuthenticationPrincipal User currentUser) {
        UUID userId = currentUser.getId();
        List<Record> records = recordService.getRecordsByUserId(userId);
        return new ResponseEntity<>(records, HttpStatus.OK);
    }

    /**
     * 為當前登入用戶新增一條視力檢查記錄
     * POST /api/user/records
     * 需要JWT Token進行驗證
     * @param record 要新增的Record
     * @param currentUser 當前已認證的 MyAppUser
     * @return ResponseEntity<Record> 回傳新增後的Record
     */
    @PostMapping("/records") //新增POST API
    @JwtAuth
    public ResponseEntity<Record> createRecord(@Valid @RequestBody Record record, @AuthenticationPrincipal User currentUser) {
        record.setUserId(currentUser.getId());
        Record savedRecord = recordService.saveRecord(record);
        return new ResponseEntity<>(savedRecord, HttpStatus.CREATED); // 201 Created
    }
}