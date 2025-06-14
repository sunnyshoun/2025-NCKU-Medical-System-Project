package com.example.demo.service;

import com.example.demo.model.Record;
import com.example.demo.model.User;
import com.example.demo.repository.UserRepository;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.UUID;


@Service
public class RAGService {

    @Autowired
    private UserRepository userRepository;

    public UserDetails processChatMessage(UUID userId) {
    }
}