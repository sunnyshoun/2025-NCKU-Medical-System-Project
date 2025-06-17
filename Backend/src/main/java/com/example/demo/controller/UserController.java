package com.example.demo.controller;

import com.example.demo.dto.ApiResponse;
import com.example.demo.dto.RecordRequest;
import com.example.demo.dto.RecordResponse;
import com.example.demo.dto.UserProfileRequest;
import com.example.demo.dto.UserProfileResponse;
import com.example.demo.exception.BusinessException;
import com.example.demo.model.User;
import com.example.demo.model.Record;
import com.example.demo.repository.UserRepository;
import com.example.demo.service.RecordService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;

import java.util.ArrayList;
import java.util.List;
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
    private RecordService recordService;

    /**
     * 獲取當前登入用戶的個人資料
     * Endpoint: GET /api/user/profile
     * 需要JWT Token
     */
    @GetMapping("/profile")
    public ResponseEntity<ApiResponse<UserProfileResponse>> getUserProfile(@AuthenticationPrincipal User currentUser) {
        UserProfileResponse responseData = UserProfileResponse.builder()
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
    public ResponseEntity<ApiResponse<Void>> updateUserProfile(@Valid @RequestBody UserProfileRequest profileRequest,
                                                              @AuthenticationPrincipal User currentUser) {
        User userToUpdate = userRepository.findById(currentUser.getId())
            .orElseThrow(() -> new BusinessException("USER_NOT_FOUND", "查無用戶", HttpStatus.NOT_FOUND));

        if (userRepository.findByUsername(profileRequest.getUsername()).isPresent() && !userToUpdate.getUsername().equals(profileRequest.getUsername())) {
            throw new BusinessException("USERNAME_EXISTS", "用戶名已存在", HttpStatus.CONFLICT);
        }
        if (userRepository.findByEmail(profileRequest.getEmail()).isPresent() && !userToUpdate.getEmail().equals(profileRequest.getEmail())) {
            throw new BusinessException("EMAIL_EXISTS", "電子郵件已存在", HttpStatus.CONFLICT);
        }
        if (profileRequest.getAge() != null && (profileRequest.getAge() < 1 || profileRequest.getAge() > 110)) {
            throw new BusinessException("INVALID_AGE", "年齡要在1到110歲之間", HttpStatus.BAD_REQUEST);
        }

        userToUpdate.setUsername(profileRequest.getUsername());
        userToUpdate.setEmail(profileRequest.getEmail());
        userToUpdate.setAge(profileRequest.getAge());
        userToUpdate.setGender(profileRequest.getGender());
        userToUpdate.setOccupation(profileRequest.getJob());

        userRepository.save(userToUpdate);
        return new ResponseEntity<>(ApiResponse.success(), HttpStatus.OK);
    }

    /**
     * 獲取當前登入用戶的所有視力檢查記錄。
     * Endpoint: GET /api/user/records
     * 需要 JWT Token
     */
    @GetMapping("/records")
    public ResponseEntity<ApiResponse<List<RecordResponse>>> getUserRecords(@AuthenticationPrincipal User currentUser) {
        UUID userId = currentUser.getId();
        List<Record> records = recordService.getRecordsByUserId(userId);

        List<RecordResponse> recordResponses = new ArrayList<>();
        for (Record record : records) {
            recordResponses.add(
                RecordResponse.builder()
                .user_id(record.getUserId())
                .record_id(record.getRecordId())
                .corr_l(record.getCorrL())
                .corr_r(record.getCorrR())
                .diopter_l(record.getDiopterL())
                .diopter_r(record.getDiopterR())
                .unco_l(record.getUncoL())
                .unco_r(record.getUncoR())
                .created_at(record.getCreatedAt())
                .updated_at(record.getUpdatedAt())
                .build()
            );
        }
        
        return new ResponseEntity<>(ApiResponse.success(recordResponses), HttpStatus.OK);
    }

    /**
     * 為當前登入用戶新增一條視力檢查記錄
     * POST /api/user/records
     * 需要JWT Token
     */
    @PostMapping("/records")
    public ResponseEntity<ApiResponse<Void>> createRecord(@Valid @RequestBody RecordRequest recordRequest, 
                                                         @AuthenticationPrincipal User currentUser) {
        Record record = Record.builder()
            .userId(currentUser.getId())
            .uncoL(recordRequest.getUnco_l())
            .uncoR(recordRequest.getUnco_r())
            .corrL(recordRequest.getCorr_l())
            .corrR(recordRequest.getCorr_r())
            .diopterL(recordRequest.getDiopter_l())
            .diopterR(recordRequest.getDiopter_l())
            .createdAt(recordRequest.getCreated_at())
            .updatedAt(recordRequest.getCreated_at())
            .build();

        recordService.saveRecord(record);
        return new ResponseEntity<>(ApiResponse.success(), HttpStatus.CREATED);
    }
}