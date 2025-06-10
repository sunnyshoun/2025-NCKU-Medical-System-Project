package com.example.demo.service;

import com.example.demo.Model.Record;
import com.example.demo.Model.RecordRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.UUID;

@Service
public class RecordService {

    @Autowired
    private RecordRepository recordRepository;

    /**
     * @param userId 用戶UUID ID
     * @return 用戶的視力檢查記錄表
     */
    public List<Record> getRecordsByUserId(UUID userId) {
        return recordRepository.findByUserId(userId);
    }

    /**
     * @param record 要保存的視力檢查記錄物件
     * @return 保存後的 Record 物件
     */
    public Record saveRecord(Record record) {
        return recordRepository.save(record);
    }

    // 更新記錄
    // 刪除記錄
}