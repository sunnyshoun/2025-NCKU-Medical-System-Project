package com.example.demo.Model;

import jakarta.persistence.*;

import java.time.LocalDateTime;
import java.util.UUID; // userID

@Table(name = "records") // records表
@Entity
public class Record {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "record_id") //  record_id欄
    private Long recordId;

    @Column(name = "user_id", nullable = false)
    private UUID userId;

    @Column(name = "corr_l", columnDefinition = "TEXT", nullable = true) // text NULLABLE
    private String corrL; // 左眼矯正視力

    @Column(name = "diopter_l", columnDefinition = "TEXT", nullable = true)
    private String diopterL; // 左眼矯正度數

    @Column(name = "corr_r", columnDefinition = "TEXT", nullable = true)
    private String corrR; // 右眼矯正視力

    @Column(name = "diopter_r", columnDefinition = "TEXT", nullable = true)
    private String diopterR; // 右眼矯正度數

    @Column(name = "unco_l", columnDefinition = "TEXT", nullable = false)
    private String uncoL; // 左眼裸視力

    @Column(name = "unco_r", columnDefinition = "TEXT", nullable = false)
    private String uncoR; // 右眼裸視力

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt; // 建立

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt; // 更新

    public Record() {
    }

    public Record(UUID userId, String corrL, String diopterL, String corrR, String diopterR, String uncoL, String uncoR) {
        this.userId = userId;
        this.corrL = corrL;
        this.diopterL = diopterL;
        this.corrR = corrR;
        this.diopterR = diopterR;
        this.uncoL = uncoL;
        this.uncoR = uncoR;
    }




    public Long getRecordId() {
        return recordId;
    }

    public void setRecordId(Long recordId) {
        this.recordId = recordId;
    }

    public UUID getUserId() {
        return userId;
    }

    public void setUserId(UUID userId) {
        this.userId = userId;
    }

    public String getCorrL() {
        return corrL;
    }

    public void setCorrL(String corrL) {
        this.corrL = corrL;
    }

    public String getDiopterL() {
        return diopterL;
    }

    public void setDiopterL(String diopterL) {
        this.diopterL = diopterL;
    }

    public String getCorrR() {
        return corrR;
    }

    public void setCorrR(String corrR) {
        this.corrR = corrR;
    }

    public String getDiopterR() {
        return diopterR;
    }

    public void setDiopterR(String diopterR) {
        this.diopterR = diopterR;
    }

    public String getUncoL() {
        return uncoL;
    }

    public void setUncoL(String uncoL) {
        this.uncoL = uncoL;
    }

    public String getUncoR() {
        return uncoR;
    }

    public void setUncoR(String uncoR) {
        this.uncoR = uncoR;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(LocalDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }

    @PrePersist
    protected void onCreate() {
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        this.updatedAt = LocalDateTime.now();
    }
}