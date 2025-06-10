package com.example.demo.controller;

import com.example.demo.model.Record;
import com.example.demo.model.MyAppUser;
import com.example.demo.service.RecordService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/user")
public class RecordController {

    @Autowired
    private RecordService recordService;

    @GetMapping("/records")
    public ResponseEntity<List<Record>> getUserRecords(@AuthenticationPrincipal MyAppUser currentUser) {
        if (currentUser == null) {
            return new ResponseEntity<>(HttpStatus.UNAUTHORIZED);
        }
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
    public ResponseEntity<Record> createRecord(@RequestBody Record record,
                                                @AuthenticationPrincipal MyAppUser currentUser) {
        if (currentUser == null) {
            return new ResponseEntity<>(HttpStatus.UNAUTHORIZED);
        }

        record.setUserId(currentUser.getId());
        Record savedRecord = recordService.saveRecord(record);
        return new ResponseEntity<>(savedRecord, HttpStatus.CREATED); // 201 Created
    }
}