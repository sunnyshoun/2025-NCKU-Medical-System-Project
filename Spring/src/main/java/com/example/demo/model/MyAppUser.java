package com.example.demo.model;

import jakarta.persistence.*;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import java.time.LocalDateTime; // 用於 createdAt 和 updatedAt
import java.util.Collection;
import java.util.HashSet; // 用於 Set 集合
import java.util.Set;     // 用於 Set 集合
import java.util.UUID;    // 用於 ID 類型

@Table(name = "users") // <-- 映射到資料庫的 users 表
@Entity
public class MyAppUser implements UserDetails {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY) // <-- 讓 Hibernate 期望資料庫自動生成 ID
    @Column(name = "id", columnDefinition = "UUID DEFAULT gen_random_uuid()") // <-- 映射到資料庫的 'id' 欄位，並指定預設值
    private UUID id; // <-- Java 屬性名為 camelCase

    @Column(unique = true, nullable = false)
    private String username;

    @Column(nullable = false)
    private String password;

    @Column(unique = true, nullable = false)
    private String email;

    @Column(nullable = true)
    private String age;

    @Column(nullable = true)
    private String gender;

    @Column(name = "job", nullable = true) // <-- 映射到資料庫的 'job' 欄位 (init.sql 是 'job')
    private String occupation;

    // <-- 關鍵修改：屬性名為 camelCase，@Column(name = "...") 映射到 snake_case
    @Column(name = "created_at", nullable = false, updatable = false) // <-- 映射到資料庫的 'created_at' 欄位
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false) // <-- 映射到資料庫的 'updated_at' 欄位
    private LocalDateTime updatedAt;

    // Many-to-Many 關聯映射到 roles 表 (通過 user_roles 連接表)
    @ManyToMany(fetch = FetchType.EAGER, cascade = CascadeType.ALL)
    @JoinTable(
        name = "user_roles", // 連接表的名稱
        joinColumns = @JoinColumn(name = "user_id"), // 本實體 (users) 在連接表中的外鍵
        inverseJoinColumns = @JoinColumn(name = "role_id") // 對方實體 (roles) 在連接表中的外鍵
    )
    private Set<Role> roles = new HashSet<>();

    // JPA 無參構造函數
    public MyAppUser() {
    }

    // 常用構造函數 (根據新的欄位調整)
    public MyAppUser(String username, String password, String email, String age, String gender, String occupation) {
        this.username = username;
        this.password = password;
        this.email = email;
        this.age = age;
        this.gender = gender;
        this.occupation = occupation;
        // createdAt 和 updatedAt 會在 @PrePersist/@PreUpdate 自動填充
    }


    public UUID getId() {
        return id;
    }

    public void setId(UUID id) {
        this.id = id;
    }

    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    @Override
    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getAge() {
        return age;
    }

    public void setAge(String age) {
        this.age = age;
    }

    public String getGender() {
        return gender;
    }

    public void setGender(String gender) {
        this.gender = gender;
    }

    public String getOccupation() {
        return occupation;
    }

    public void setOccupation(String occupation) {
        this.occupation = occupation;
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

    public Set<Role> getRoles() {
        return roles;
    }

    public void setRoles(Set<Role> roles) {
        this.roles = roles;
    }

    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        Set<SimpleGrantedAuthority> authorities = new HashSet<>();
        for (Role role : roles) {
            // <-- 關鍵修正：這裡對從資料庫讀到的角色名加上 'ROLE_' 前綴
            // 因為 Spring Security 內部期望角色以 "ROLE_" 開頭
            authorities.add(new SimpleGrantedAuthority("ROLE_" + role.getName())); 
        }
        return authorities;
    }

    @Override
    public boolean isAccountNonExpired() {
        return true;
    }

    @Override
    public boolean isAccountNonLocked() {
        return true;
    }

    @Override
    public boolean isCredentialsNonExpired() {
        return true;
    }

    @Override
    public boolean isEnabled() {
        return true;
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