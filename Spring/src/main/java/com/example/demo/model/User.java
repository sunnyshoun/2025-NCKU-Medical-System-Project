package com.example.demo.model;

import jakarta.persistence.*;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import com.fasterxml.jackson.annotation.JsonIgnore;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.LocalDateTime;
import java.util.Collection;
import java.util.HashSet;
import java.util.Set;
import java.util.UUID;
import java.util.List;
import java.util.ArrayList;

@Table(name = "users")
@Entity
@Data
@NoArgsConstructor
@AllArgsConstructor
public class User implements UserDetails {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id", columnDefinition = "UUID DEFAULT gen_random_uuid()")
    private UUID id;

    @Column(unique = true, nullable = false)
    private String username;

    @Column(nullable = false)
    @JsonIgnore
    private String password;

    @Column(unique = true, nullable = false)
    private String email;

    @Column(nullable = true)
    private int age;

    @Column(nullable = true)
    private String gender;

    @Column(name = "job", nullable = true)
    private String occupation;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    /**
     * 儲存對話訊息歷史，使用 JSON 格式
     * 格式：[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
     */
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "chat_context", columnDefinition = "jsonb")
    private List<ChatMessage> chatContext = new ArrayList<>();

    @ManyToMany(fetch = FetchType.EAGER, cascade = CascadeType.ALL)
    @JoinTable(
        name = "user_roles",
        joinColumns = @JoinColumn(name = "user_id"),
        inverseJoinColumns = @JoinColumn(name = "role_id")
    )
    private Set<Role> roles = new HashSet<>();

    // UserDetails interface methods
    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        Set<SimpleGrantedAuthority> authorities = new HashSet<>();
        for (Role role : roles) {
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
        if (this.chatContext == null) {
            this.chatContext = new ArrayList<>();
        }
    }

    @PreUpdate
    protected void onUpdate() {
        this.updatedAt = LocalDateTime.now();
    }

    /**
     * 添加使用者訊息到對話歷史
     * @param content 訊息內容
     */
    public void addUserMessage(String content) {
        if (this.chatContext == null) {
            this.chatContext = new ArrayList<>();
        }
        this.chatContext.add(new ChatMessage("user", content));
    }

    /**
     * 添加助理回應到對話歷史
     * @param content 回應內容
     */
    public void addAssistantMessage(String content) {
        if (this.chatContext == null) {
            this.chatContext = new ArrayList<>();
        }
        this.chatContext.add(new ChatMessage("assistant", content));
    }

    /**
     * 清空對話歷史
     */
    public void clearChatContext() {
        if (this.chatContext != null) {
            this.chatContext.clear();
        }
    }

    /**
     * 獲取最近的 N 條訊息（用於控制上下文長度）
     * @param count 訊息數量
     * @return 最近的訊息列表
     */
    public List<ChatMessage> getRecentMessages(int count) {
        if (this.chatContext == null || this.chatContext.isEmpty()) {
            return new ArrayList<>();
        }
        
        int fromIndex = Math.max(0, this.chatContext.size() - count);
        return new ArrayList<>(this.chatContext.subList(fromIndex, this.chatContext.size()));
    }

    /**
     * 內部類別：聊天訊息
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ChatMessage {
        private String role;    // "user" 或 "assistant"
        private String content; // 訊息內容
    }
}