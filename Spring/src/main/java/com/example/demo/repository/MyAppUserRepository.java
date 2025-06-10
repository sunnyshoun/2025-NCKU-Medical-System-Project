package com.example.demo.repository;

import java.util.Optional;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.example.demo.model.MyAppUser;

@Repository
public interface MyAppUserRepository extends JpaRepository<MyAppUser, UUID>{

    Optional<MyAppUser> findByUsername(String username);
    
    Optional<MyAppUser> findByEmail(String email);
    
}