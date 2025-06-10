package com.example.demo.model;

import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import com.example.demo.repository.MyAppUserRepository;

import java.util.Optional;

import lombok.AllArgsConstructor;

@Service
@AllArgsConstructor
public class MyAppUserService implements UserDetailsService {

    private final MyAppUserRepository repository;

    @Override
    public UserDetails loadUserByUsername(String account) throws UsernameNotFoundException {
        
        Optional<MyAppUser> userByEmailOptional = repository.findByEmail(account); 

        if (userByEmailOptional.isPresent()) {
            return userByEmailOptional.get();
        }

        Optional<MyAppUser> userByUsernameOptional = repository.findByUsername(account); 

        if (userByUsernameOptional.isPresent()) {
            return userByUsernameOptional.get();
        }

        throw new UsernameNotFoundException("找不到使用者帳號: " + account);
    }
}