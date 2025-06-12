package com.example.demo.model;

import jakarta.persistence.*;
import java.io.Serializable;
import java.util.Objects;

import java.util.UUID;

@Table(name = "user_roles")
@Entity
@IdClass(UserRole.UserRoleId.class)
public class UserRole {

    @Id
    @Column(name = "user_id", nullable = false)
    private UUID userId; // 用戶id user_id -> userID

    @Id
    @Column(name = "role_id", nullable = false)
    private Integer roleId; // 角色id

    public UserRole() {
    }

    public UserRole(UUID userId, Integer roleId) {
        this.userId = userId;
        this.roleId = roleId;
    }


    public UUID getUserId() {
        return userId;
    }

    public void setUserId(UUID userId) {
        this.userId = userId;
    }

    public Integer getRoleId() {
        return roleId;
    }

    public void setRoleId(Integer roleId) {
        this.roleId = roleId;
    }


    public static class UserRoleId implements Serializable {
        private UUID userId;
        private Integer roleId;

        public UserRoleId() {}

        public UserRoleId(UUID userId, Integer roleId) {
            this.userId = userId;
            this.roleId = roleId;
        }

        @Override
        public boolean equals(Object o) {
            if (this == o) return true;
            if (o == null || getClass() != o.getClass()) return false;
            UserRoleId that = (UserRoleId) o;
            return Objects.equals(userId, that.userId) && Objects.equals(roleId, that.roleId);
        }

        @Override
        public int hashCode() {
            return Objects.hash(userId, roleId);
        }
    }
}