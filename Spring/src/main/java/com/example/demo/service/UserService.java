package com.example.demo.service;

import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import com.example.demo.model.User;
import com.example.demo.repository.UserRepository;

import java.util.Optional;

import lombok.AllArgsConstructor;

@Service
@AllArgsConstructor
public class UserService implements UserDetailsService {

    private final UserRepository repository;

    @Override
    public UserDetails loadUserByUsername(String account) throws UsernameNotFoundException {
        
        Optional<User> userByEmailOptional = repository.findByEmail(account); 

        if (userByEmailOptional.isPresent()) {
            return userByEmailOptional.get();
        }

        Optional<User> userByUsernameOptional = repository.findByUsername(account); 

        if (userByUsernameOptional.isPresent()) {
            return userByUsernameOptional.get();
        }

        throw new UsernameNotFoundException("找不到使用者帳號: " + account);
    }
}