package com.example.demo.model;

import java.util.Optional;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface MyAppUserRepository extends JpaRepository<MyAppUser, UUID>{

    Optional<MyAppUser> findByUsername(String username);
    
    Optional<MyAppUser> findByEmail(String email);
    
}